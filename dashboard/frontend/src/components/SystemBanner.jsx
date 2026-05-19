/**
 * SystemBanner — top-of-page status bar showing overall system health,
 * connected substation count, and last-update timestamp.
 */

export default function SystemBanner({ health, substationCount, lastUpdated, apiOnline, apiChecked }) {
  // Don't show offline error until we've actually tried to connect
  if (!apiChecked) {
    return (
      <div className="flex items-center gap-3 bg-grid-card border border-grid-border rounded-xl px-4 py-3">
        <span className="w-2.5 h-2.5 rounded-full bg-grid-accent animate-pulse flex-shrink-0" />
        <span className="text-sm text-grid-muted">Connecting to backend…</span>
      </div>
    )
  }

  if (!apiOnline) {
    return (
      <div className="flex items-center gap-3 bg-grid-red/10 border border-grid-red/30 rounded-xl px-4 py-3">
        <span className="w-2.5 h-2.5 rounded-full bg-grid-red animate-blink flex-shrink-0" />
        <div>
          <p className="text-sm font-semibold text-grid-red">Backend Offline</p>
          <p className="text-xs text-grid-muted">Cannot reach API at localhost:8000 — is the server running?</p>
        </div>
      </div>
    )
  }

  const values = Object.values(health || {})
  const criticalCount = values.filter(h => h.risk_level === 'Critical').length
  const warningCount  = values.filter(h => h.risk_level === 'Warning').length
  const healthyCount  = values.filter(h => h.risk_level === 'Healthy').length

  const overall = criticalCount > 0 ? 'CRITICAL' : warningCount > 0 ? 'WARNING' : 'HEALTHY'

  const bannerConfig = {
    CRITICAL: { bg: 'bg-grid-red/10',    border: 'border-grid-red/30',    dot: 'bg-grid-red',    text: 'text-grid-red',    label: '🚨 System Critical' },
    WARNING:  { bg: 'bg-grid-yellow/10', border: 'border-grid-yellow/30', dot: 'bg-grid-yellow', text: 'text-grid-yellow', label: '⚠️ System Warning'  },
    HEALTHY:  { bg: 'bg-grid-green/5',   border: 'border-grid-green/20',  dot: 'bg-grid-green',  text: 'text-grid-green',  label: '✓ All Systems Nominal' },
  }[overall]

  return (
    <div className={`flex items-center justify-between ${bannerConfig.bg} border ${bannerConfig.border} rounded-xl px-4 py-3`}>
      <div className="flex items-center gap-3">
        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${bannerConfig.dot} ${
          overall === 'CRITICAL' ? 'animate-blink' : ''
        }`} />
        <span className={`text-sm font-bold ${bannerConfig.text}`}>{bannerConfig.label}</span>

        {/* Counts */}
        <div className="flex items-center gap-2 ml-2">
          {healthyCount  > 0 && <span className="text-xs bg-grid-green/10  text-grid-green  border border-grid-green/30  rounded px-2 py-0.5">{healthyCount}  Healthy</span>}
          {warningCount  > 0 && <span className="text-xs bg-grid-yellow/10 text-grid-yellow border border-grid-yellow/30 rounded px-2 py-0.5">{warningCount}  Warning</span>}
          {criticalCount > 0 && <span className="text-xs bg-grid-red/10    text-grid-red    border border-grid-red/30    rounded px-2 py-0.5">{criticalCount} Critical</span>}
        </div>
      </div>

      <div className="flex items-center gap-4 text-[10px] text-grid-muted font-mono">
        <span>{substationCount} substation{substationCount !== 1 ? 's' : ''} connected</span>
        {lastUpdated && <span>Updated {lastUpdated}</span>}
      </div>
    </div>
  )
}
