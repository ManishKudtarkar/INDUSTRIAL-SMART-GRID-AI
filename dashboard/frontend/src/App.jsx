/**
 * App.jsx — Distributed AI Smart Grid Dashboard
 *
 * Polls /state every 1.5s for live telemetry.
 * Polls /usb/status every 3s for USB device info.
 * Maintains rolling 60-point history for trend charts.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'

import SystemBanner     from './components/SystemBanner'
import SubstationCard   from './components/SubstationCard'
import LiveChart        from './components/LiveChart'
import LoadDistribution from './components/LoadDistribution'
import AlertFeed        from './components/AlertFeed'
import UsbStatus        from './components/UsbStatus'

const API          = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const POLL_MS      = 1500
const HISTORY_MAX  = 60

// ── helpers ───────────────────────────────────────────────────────────────────

function timeLabel() {
  return new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function appendHistory(prev, substations, telemetry, key) {
  const point = { time: timeLabel() }
  substations.forEach(sub => {
    const val = telemetry?.[sub]?.[key]
    point[sub] = val !== null && val !== undefined ? parseFloat(val.toFixed(2)) : null
  })
  const next = [...prev, point]
  return next.length > HISTORY_MAX ? next.slice(-HISTORY_MAX) : next
}

// ── main component ────────────────────────────────────────────────────────────

export default function App() {
  const [gridState,  setGridState]  = useState(null)
  const [apiOnline,  setApiOnline]  = useState(true)   // optimistic — avoids flash on load
  const [apiChecked, setApiChecked] = useState(false)  // true after first fetch attempt
  const [lastUpdate, setLastUpdate] = useState(null)

  // History buffers for charts
  const [tempHistory,   setTempHistory]   = useState([])
  const [voltHistory,   setVoltHistory]   = useState([])
  const [loadHistory,   setLoadHistory]   = useState([])
  const [healthHistory, setHealthHistory] = useState([])

  const [activeTab, setActiveTab] = useState('overview')

  const fetchState = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/state`, { timeout: 3000 })
      setGridState(data)
      setApiOnline(true)
      setApiChecked(true)
      setLastUpdate(timeLabel())

      const subs = Object.keys(data.telemetry || {})
      if (subs.length) {
        setTempHistory(prev => appendHistory(prev, subs, data.telemetry, 'temperature'))
        setVoltHistory(prev => appendHistory(prev, subs, data.telemetry, 'voltage'))
        setLoadHistory(prev => appendHistory(prev, subs, data.telemetry, 'load_percentage'))

        // Health score history
        const hPoint = { time: timeLabel() }
        subs.forEach(s => { hPoint[s] = data.health?.[s]?.health_score ?? null })
        setHealthHistory(prev => {
          const next = [...prev, hPoint]
          return next.length > HISTORY_MAX ? next.slice(-HISTORY_MAX) : next
        })
      }
    } catch {
      setApiOnline(false)
      setApiChecked(true)
    }
  }, [])

  useEffect(() => {
    fetchState()
    const id = setInterval(fetchState, POLL_MS)
    return () => clearInterval(id)
  }, [fetchState])

  const telemetry  = gridState?.telemetry       || {}
  const health     = gridState?.health          || {}
  const loadDist   = gridState?.load_distribution || {}
  const alerts     = gridState?.alerts          || []
  const faultRpts  = gridState?.fault_reports   || {}
  const substations = Object.keys(health).sort()

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'trends',   label: 'Live Trends' },
    { id: 'load',     label: 'Load Balance' },
    { id: 'alerts',   label: `Alerts${alerts.length ? ` (${alerts.length})` : ''}` },
  ]

  return (
    <div className="min-h-screen bg-grid-bg text-slate-200">

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header className="border-b border-grid-border bg-grid-card/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Lightning bolt */}
            <div className="w-8 h-8 rounded-lg bg-grid-accent/10 border border-grid-accent/30 flex items-center justify-center">
              <svg className="w-4 h-4 text-grid-accent" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-100 leading-none">Smart Grid AI</h1>
              <p className="text-[10px] text-grid-muted leading-none mt-0.5">Distributed Monitoring System</p>
            </div>
          </div>

          {/* Live indicator */}
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-grid-green animate-pulse-slow' : 'bg-grid-red animate-blink'}`} />
            <span className="text-xs text-grid-muted font-mono">
              {apiOnline ? `LIVE · ${lastUpdate || '—'}` : 'OFFLINE'}
            </span>
          </div>
        </div>

        {/* Tab bar */}
        <div className="max-w-screen-2xl mx-auto px-4 flex gap-1 pb-0">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors ${
                activeTab === t.id
                  ? 'bg-grid-bg text-grid-accent border-t border-x border-grid-border'
                  : 'text-grid-muted hover:text-slate-300'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      {/* ── Main content ────────────────────────────────────────────────── */}
      <main className="max-w-screen-2xl mx-auto px-4 py-4 space-y-4">

        {/* System banner */}
        <SystemBanner
          health={health}
          substationCount={substations.length}
          lastUpdated={lastUpdate}
          apiOnline={apiOnline}
          apiChecked={apiChecked}
        />

        {/* USB status — always visible */}
        <UsbStatus />

        {/* ── OVERVIEW TAB ──────────────────────────────────────────────── */}
        {activeTab === 'overview' && (
          <>
            {substations.length === 0 ? (
              <div className="bg-grid-card border border-grid-border rounded-xl p-8 text-center">
                <div className="text-4xl mb-3">🔌</div>
                <p className="text-slate-300 font-semibold">Waiting for substations to connect</p>
                <p className="text-sm text-grid-muted mt-1">
                  Plug in your USB sensors and run:<br />
                  <code className="text-grid-accent text-xs">
                    python substations/substation_client.py --id S1
                  </code>
                </p>
              </div>
            ) : (
              <div className={`grid gap-4 ${
                substations.length === 1 ? 'grid-cols-1 max-w-sm' :
                substations.length === 2 ? 'grid-cols-2' :
                'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
              }`}>
                {substations.map(sub => (
                  <SubstationCard
                    key={sub}
                    subId={sub}
                    telemetry={telemetry[sub]}
                    health={health[sub]}
                    loadTarget={loadDist[sub]}
                    faultReport={faultRpts[sub]}
                  />
                ))}
              </div>
            )}

            {/* Load + Alerts side by side */}
            {substations.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <LoadDistribution loadDist={loadDist} healthData={health} />
                <AlertFeed alerts={alerts} />
              </div>
            )}
          </>
        )}

        {/* ── TRENDS TAB ────────────────────────────────────────────────── */}
        {activeTab === 'trends' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <LiveChart
              title="Temperature"
              data={tempHistory}
              substations={substations}
              unit="°C"
              warnLine={75}
              dangerLine={85}
            />
            <LiveChart
              title="Voltage"
              data={voltHistory}
              substations={substations}
              unit="V"
              warnLine={245}
              dangerLine={250}
            />
            <LiveChart
              title="Load %"
              data={loadHistory}
              substations={substations}
              unit="%"
              warnLine={60}
              dangerLine={80}
            />
            <LiveChart
              title="Health Score"
              data={healthHistory}
              substations={substations}
              unit="/ 100"
              warnLine={50}
              dangerLine={30}
            />
          </div>
        )}

        {/* ── LOAD BALANCE TAB ──────────────────────────────────────────── */}
        {activeTab === 'load' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <LoadDistribution loadDist={loadDist} healthData={health} />

            {/* Load table */}
            <div className="bg-grid-card border border-grid-border rounded-xl p-4">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Load Details
              </h4>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-grid-muted border-b border-grid-border">
                    <th className="text-left pb-2 font-medium">Substation</th>
                    <th className="text-right pb-2 font-medium">Actual Load</th>
                    <th className="text-right pb-2 font-medium">Target</th>
                    <th className="text-right pb-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {substations.map(sub => {
                    const actual = telemetry[sub]?.load_percentage
                    const target = loadDist[sub]
                    const status = health[sub]?.risk_level || 'Unknown'
                    const statusColor = status === 'Healthy' ? 'text-grid-green' : status === 'Warning' ? 'text-grid-yellow' : 'text-grid-red'
                    return (
                      <tr key={sub} className="border-b border-grid-border/50 last:border-0">
                        <td className="py-2 font-semibold text-slate-200">{sub}</td>
                        <td className="py-2 text-right font-mono text-slate-300">
                          {actual !== null && actual !== undefined ? `${actual.toFixed(1)}%` : '—'}
                        </td>
                        <td className="py-2 text-right font-mono text-grid-accent">
                          {target !== undefined ? `${target.toFixed(1)}%` : '—'}
                        </td>
                        <td className={`py-2 text-right font-semibold ${statusColor}`}>{status}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {substations.length === 0 && (
                <p className="text-grid-muted text-xs text-center py-4">No substations connected</p>
              )}
            </div>
          </div>
        )}

        {/* ── ALERTS TAB ────────────────────────────────────────────────── */}
        {activeTab === 'alerts' && (
          <div className="max-w-2xl">
            <AlertFeed alerts={alerts} />
          </div>
        )}

      </main>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-grid-border mt-8 py-3 text-center">
        <p className="text-[10px] text-grid-muted font-mono">
          Industrial Smart Grid AI · API {API} · Polling every {POLL_MS}ms
        </p>
      </footer>
    </div>
  )
}
