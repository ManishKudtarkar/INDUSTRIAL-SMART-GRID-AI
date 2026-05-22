/**
 * preload.js — Secure bridge between Electron main process and React renderer.
 * Exposes only what the React app needs — nothing more.
 */
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  // Get app version and paths
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),

  // Platform info
  platform: process.platform,

  // App version
  version: process.env.npm_package_version || '1.0.0',
})
