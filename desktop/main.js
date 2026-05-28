/**
 * main.js — Electron main process
 *
 * Responsibilities:
 *  1. Show a splash screen while the Python backend starts
 *  2. Start the Python FastAPI backend as a child process
 *  3. Start the 3 simulated substation clients
 *  4. Wait for the backend to be ready (poll /health)
 *  5. Open the main window loading the React dashboard
 *  6. Kill all child processes on app quit
 */

const { app, BrowserWindow, shell, ipcMain, dialog } = require('electron')
const path   = require('path')
const { spawn, exec } = require('child_process')
const http   = require('http')
const fs     = require('fs')
const log    = require('electron-log')

// ── Logging ───────────────────────────────────────────────────────────────────
log.transports.file.level = 'info'
log.transports.console.level = 'debug'
log.info('Smart Grid AI starting…')

// ── Paths ─────────────────────────────────────────────────────────────────────
const isDev       = !app.isPackaged
let appRoot       = null
let frontendDist  = null
const pythonExec  = findPython()

log.info('pythonExec:', pythonExec)

// ── State ─────────────────────────────────────────────────────────────────────
let mainWindow   = null
let splashWindow = null
const childProcesses = []

// ── Find Python ───────────────────────────────────────────────────────────────
function findPython() {
  // In packaged app, look for bundled Python first
  const bundled = path.join(process.resourcesPath, 'python', 'python.exe')
  if (fs.existsSync(bundled)) return { cmd: bundled, args: [] }

  // Fall back to system Python / Windows launcher
  const candidates = [
    { cmd: 'python', args: [] },
    { cmd: 'python3', args: [] },
    { cmd: 'py', args: ['-3'] },
    { cmd: 'py', args: [] },
  ]

  for (const candidate of candidates) {
    try {
      const versionCmd = `${candidate.cmd} ${candidate.args.join(' ')} --version`.trim()
      require('child_process').execSync(versionCmd, { stdio: 'ignore' })
      return candidate
    } catch {}
  }

  return { cmd: 'python', args: [] }
}

// ── Splash window ─────────────────────────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: { nodeIntegration: false },
  })
  splashWindow.loadFile(path.join(__dirname, 'splash.html'))
  splashWindow.center()
}

// ── Main window ───────────────────────────────────────────────────────────────
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'Smart Grid AI',
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    show: false,
    backgroundColor: '#0a0e1a',
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      nodeIntegration:  false,
      contextIsolation: true,
      webSecurity:      true,
    },
  })

  // Load the built React app (file://) — no browser needed
  const indexPath = path.join(frontendDist, 'index.html')
  if (fs.existsSync(indexPath)) {
    mainWindow.loadFile(indexPath)
  } else if (isDev) {
    // Dev fallback: load from Vite dev server
    mainWindow.loadURL('http://localhost:5173')
  } else {
    dialog.showErrorBox(
      'Smart Grid AI — Startup Failed',
      'Could not find the built dashboard at:\n' + indexPath + '\n\nPlease rebuild the app so dashboard/frontend/dist is included.'
    )
    app.quit()
    return
  }

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    log.error('Renderer failed to load:', errorCode, errorDescription, validatedURL)
    dialog.showErrorBox(
      'Smart Grid AI — Renderer Load Failed',
      `Could not load the dashboard page.\n\n${errorDescription} (${errorCode})\n${validatedURL}`
    )
  })

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    log.debug('Renderer console:', { level, message, line, sourceId })
  })

  mainWindow.webContents.on('crashed', () => {
    log.error('Renderer process crashed')
    dialog.showErrorBox('Smart Grid AI — Renderer Crashed', 'The dashboard renderer has crashed. Please restart the app.')
  })

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close()
    }
    mainWindow.show()
    mainWindow.maximize()
  })

  // Open external links in system browser, not Electron
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => { mainWindow = null })
}

// ── Start Python backend ──────────────────────────────────────────────────────
function startBackend() {
  return new Promise((resolve, reject) => {
    log.info('Starting Python backend…')

    const backend = spawn(pythonExec.cmd, [...pythonExec.args, 'api/main.py'], {
      cwd: appRoot,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    })

    childProcesses.push(backend)

    backend.stdout.on('data', d => log.info('[backend]', d.toString().trim()))
    backend.stderr.on('data', d => log.info('[backend]', d.toString().trim()))
    backend.on('error', err => {
      const pythonCommand = `${pythonExec.cmd} ${pythonExec.args.join(' ')}`.trim()
      log.error('Backend failed to start:', err)
      log.error('Tried Python command:', pythonCommand)
      reject(new Error(`${err.message} (tried: ${pythonCommand})`))
    })

    // Poll until the API responds
    let attempts = 0
    const maxAttempts = 60   // 60 × 1s = 60 seconds max wait
    const poll = setInterval(() => {
      attempts++
      http.get('http://localhost:8000/', res => {
        if (res.statusCode === 200) {
          clearInterval(poll)
          log.info('Backend ready after', attempts, 'seconds')
          resolve()
        }
      }).on('error', () => {
        if (attempts >= maxAttempts) {
          clearInterval(poll)
          reject(new Error('Backend did not start within 60 seconds'))
        }
      })
    }, 1000)
  })
}

// ── Start substation clients ──────────────────────────────────────────────────
function startSubstations() {
  const substations = [
    { id: 'S1', args: ['--id', 'S1', '--simulate'] },
    { id: 'S2', args: ['--id', 'S2', '--simulate', '--faulty'] },
    { id: 'S3', args: ['--id', 'S3', '--simulate'] },
  ]

  for (const sub of substations) {
    const proc = spawn(pythonExec.cmd, [...pythonExec.args, 'substations/substation_client.py', ...sub.args], {
      cwd: appRoot,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    })
    childProcesses.push(proc)
    proc.stdout.on('data', d => log.debug(`[${sub.id}]`, d.toString().trim()))
    proc.stderr.on('data', d => log.debug(`[${sub.id}]`, d.toString().trim()))
    log.info(`Substation ${sub.id} started`)
  }
}

// ── Intercept API calls from the React app ────────────────────────────────────
// The built React app uses relative URLs (/state, /telemetry, etc.)
// When loaded as file://, these need to be redirected to http://localhost:8000
function setupApiProxy(window) {
  const { session } = require('electron')

  session.defaultSession.webRequest.onBeforeRequest(
    { urls: ['file://*/*state*', 'file://*/*telemetry*', 'file://*/*anomaly*',
             'file://*/*load*', 'file://*/*alerts*', 'file://*/*predict*',
             'file://*/*usb*', 'file://*/*summary*'] },
    (details, callback) => {
      // Extract the path from the file:// URL and redirect to localhost
      const url = new URL(details.url)
      const newUrl = 'http://localhost:8000' + url.pathname + url.search
      callback({ redirectURL: newUrl })
    }
  )
}

// ── Cleanup on quit ───────────────────────────────────────────────────────────
function cleanup() {
  log.info('Cleaning up child processes…')
  for (const proc of childProcesses) {
    try { proc.kill('SIGTERM') } catch {}
  }
  // On Windows, also kill by port to be sure
  if (process.platform === 'win32') {
    exec('for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8000\') do taskkill /F /PID %a', { shell: true })
    exec('for /f "tokens=5" %a in (\'netstat -aon ^| findstr :9999\') do taskkill /F /PID %a', { shell: true })
  }
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  appRoot = isDev
    ? path.join(__dirname, '..')                          // dev: project root
    : app.getAppPath()                                   // prod: app.asar or extracted path
  frontendDist = path.join(appRoot, 'dashboard', 'frontend', 'dist')

  log.info('appRoot:', appRoot)
  log.info('frontendDist:', frontendDist)

  createSplash()

  try {
    // Start backend
    await startBackend()

    // Start substations
    startSubstations()

    // Setup API proxy for file:// → localhost:8000
    setupApiProxy(mainWindow)

    // Open main window
    createMainWindow()

  } catch (err) {
    log.error('Startup failed:', err)
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close()

    dialog.showErrorBox(
      'Smart Grid AI — Startup Failed',
      `Could not start the backend server.\n\n${err.message}\n\nMake sure Python 3.10+ is installed.\nRun: pip install -r requirements.txt`
    )
    app.quit()
  }
})

app.on('window-all-closed', () => {
  cleanup()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', cleanup)
app.on('will-quit', cleanup)

// IPC: allow renderer to get app info
ipcMain.handle('get-app-info', () => ({
  version: app.getVersion(),
  appRoot,
  pythonExec,
}))
