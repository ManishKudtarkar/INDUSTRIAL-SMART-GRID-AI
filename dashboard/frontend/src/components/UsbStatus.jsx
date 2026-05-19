/**
 * UsbStatus — shows which USB/COM ports are active and which substation
 * is streaming from each one.  Polls /usb/status every 3 seconds.
 */
import { useEffect, useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function UsbStatus() {
  const [usbData, setUsbData] = useState(null)

  useEffect(() => {
    const fetch = () =>
      axios.get(`${API}/usb/status`).then(r => setUsbData(r.data)).catch(() => {})
    fetch()
    const id = setInterval(fetch, 3000)
    return () => clearInterval(id)
  }, [])

  if (!usbData) return null

  const { ports = [], connected_substations = [] } = usbData

  return (
    <div className="bg-grid-card border border-grid-border rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        {/* USB icon */}
        <svg className="w-5 h-5 text-grid-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M12 3v4m0 0l-2-2m2 2l2-2M5 12H3m18 0h-2M7.05 7.05L5.636 5.636M18.364 18.364l-1.414-1.414M7.05 16.95l-1.414 1.414M18.364 5.636l-1.414 1.414M12 17v4m-4-4h8" />
        </svg>
        <span className="text-sm font-semibold text-grid-accent tracking-wider uppercase">
          USB Devices
        </span>
      </div>

      {ports.length === 0 ? (
        <div className="flex items-center gap-2 text-sm text-grid-muted">
          <span className="w-2 h-2 rounded-full bg-grid-muted animate-pulse-slow" />
          No USB devices detected — plug in your sensor
        </div>
      ) : (
        <div className="space-y-2">
          {ports.map(p => (
            <div key={p.port}
              className="flex items-center justify-between bg-[#0a0e1a] rounded-lg px-3 py-2 border border-grid-border">
              <div className="flex items-center gap-2">
                {/* Animated ring when active */}
                <span className="relative flex h-3 w-3">
                  <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    p.active ? 'bg-grid-green usb-ring' : 'bg-grid-muted'
                  }`} />
                  <span className={`relative inline-flex rounded-full h-3 w-3 ${
                    p.active ? 'bg-grid-green' : 'bg-grid-muted'
                  }`} />
                </span>
                <span className="text-xs font-mono text-slate-300">{p.port}</span>
                <span className="text-xs text-grid-muted truncate max-w-[140px]">{p.description}</span>
              </div>
              <div className="flex items-center gap-2">
                {p.substation_id && (
                  <span className="text-xs bg-grid-accent/10 text-grid-accent border border-grid-accent/30 rounded px-2 py-0.5">
                    {p.substation_id}
                  </span>
                )}
                <span className={`text-xs ${p.active ? 'text-grid-green' : 'text-grid-muted'}`}>
                  {p.active ? 'Streaming' : 'Idle'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {connected_substations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-grid-border flex items-center gap-2 flex-wrap">
          <span className="text-xs text-grid-muted">Active:</span>
          {connected_substations.map(s => (
            <span key={s}
              className="text-xs bg-grid-green/10 text-grid-green border border-grid-green/30 rounded px-2 py-0.5">
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
