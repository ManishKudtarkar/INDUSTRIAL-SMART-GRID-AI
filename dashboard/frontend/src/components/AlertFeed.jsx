/**
 * AlertFeed — live scrolling alert log with level-based styling.
 */

const LEVEL_CONFIG = {
  CRITICAL: { bg: 'bg-grid-red/10',    border: 'border-grid-red/30',    text: 'text-grid-red',    dot: 'bg-grid-red',    label: 'CRITICAL' },
  WARNING:  { bg: 'bg-grid-yellow/10', border: 'border-grid-yellow/30', text: 'text-grid-yellow', dot: 'bg-grid-yellow', label: 'WARNING'  },
  INFO:     { bg: 'bg-grid-accent/5',  border: 'border-grid-accent/20', text: 'text-grid-accent', dot: 'bg-grid-accent', label: 'INFO'     },
}

function AlertItem({ alert }) {
  const cfg = LEVEL_CONFIG[alert.level] || LEVEL_CONFIG.INFO
  const time = new Date(alert.timestamp).toLocaleTimeString()

  return (
    <div className={`flex items-start gap-2 rounded-lg px-3 py-2 border ${cfg.bg} ${cfg.border}`}>
      <span className={`mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot} ${
        alert.level === 'CRITICAL' ? 'animate-blink' : ''
      }`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-[10px] font-bold uppercase tracking-wider ${cfg.text}`}>
            {cfg.label}
          </span>
          <span className="text-[10px] font-semibold text-slate-300">{alert.substation_id}</span>
          <span className="text-[10px] text-grid-muted font-mono ml-auto">{time}</span>
        </div>
        <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{alert.message}</p>
      </div>
    </div>
  )
}

export default function AlertFeed({ alerts }) {
  if (!alerts?.length) {
    return (
      <div className="bg-grid-card border border-grid-border rounded-xl p-4">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Alert Feed
        </h4>
        <div className="flex items-center gap-2 text-sm text-grid-green">
          <span className="w-2 h-2 rounded-full bg-grid-green" />
          All systems nominal — no active alerts
        </div>
      </div>
    )
  }

  return (
    <div className="bg-grid-card border border-grid-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Alert Feed
        </h4>
        <span className="text-[10px] bg-grid-red/20 text-grid-red border border-grid-red/30 rounded px-2 py-0.5 font-semibold">
          {alerts.length} active
        </span>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {alerts.map((a, i) => <AlertItem key={i} alert={a} />)}
      </div>
    </div>
  )
}
