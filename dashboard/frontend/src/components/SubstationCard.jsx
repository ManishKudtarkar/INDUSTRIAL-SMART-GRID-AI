/**
 * SubstationCard — live metrics card for one substation.
 * Handles both real hardware (ADB phone / USB sensor) and simulation data.
 */

const STATUS_CONFIG = {
  Healthy:  { color: 'text-grid-green',  border: 'border-grid-green/40',  bg: 'bg-grid-green/5',  ring: '#00ff88', dot: 'bg-grid-green'  },
  Warning:  { color: 'text-grid-yellow', border: 'border-grid-yellow/40', bg: 'bg-grid-yellow/5', ring: '#ffb800', dot: 'bg-grid-yellow' },
  Critical: { color: 'text-grid-red',    border: 'border-grid-red/40',    bg: 'bg-grid-red/5',    ring: '#ff3b5c', dot: 'bg-grid-red'    },
  Unknown:  { color: 'text-grid-muted',  border: 'border-grid-border',    bg: '',                 ring: '#4a5568', dot: 'bg-grid-muted'  },
}

// ── Health ring ───────────────────────────────────────────────────────────────
function HealthRing({ score, status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.Unknown
  const r = 26
  const circ = 2 * Math.PI * r
  const filled = circ * (Math.max(0, Math.min(100, score)) / 100)

  return (
    <div className="relative flex items-center justify-center w-[72px] h-[72px] flex-shrink-0">
      <svg className="absolute" width="72" height="72" viewBox="0 0 72 72">
        <circle cx="36" cy="36" r={r} fill="none" stroke="#1e2d4a" strokeWidth="5" />
        <circle
          cx="36" cy="36" r={r}
          fill="none"
          stroke={cfg.ring}
          strokeWidth="5"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeDashoffset={circ / 4}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.8s ease, stroke 0.5s ease' }}
        />
      </svg>
      <div className="text-center z-10">
        <div className={`text-base font-bold leading-none ${cfg.color}`}>{Math.round(score)}</div>
        <div className="text-[8px] text-grid-muted uppercase tracking-wider mt-0.5">score</div>
      </div>
    </div>
  )
}

// ── Single metric row ─────────────────────────────────────────────────────────
function MetricRow({ icon, label, value, unit, warn, danger, extra }) {
  const num = parseFloat(value)
  const isWarn   = warn   !== undefined && !isNaN(num) && num >= warn
  const isDanger = danger !== undefined && !isNaN(num) && num >= danger
  const color = isDanger ? 'text-grid-red' : isWarn ? 'text-grid-yellow' : 'text-slate-200'

  return (
    <div className="flex items-center justify-between py-[5px] border-b border-grid-border/40 last:border-0">
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] w-4 text-center">{icon}</span>
        <span className="text-[11px] text-grid-muted">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {extra && <span className="text-[9px] text-grid-muted/60 font-mono">{extra}</span>}
        <span className={`text-[11px] font-mono font-semibold ${color}`}>
          {value !== null && value !== undefined
            ? `${typeof value === 'number' ? value.toFixed(2) : value} ${unit}`
            : <span className="text-grid-muted/40 italic text-[10px]">—</span>
          }
        </span>
      </div>
    </div>
  )
}

// ── Load bar ──────────────────────────────────────────────────────────────────
function LoadBar({ actual, target }) {
  const pct = Math.min(100, Math.max(0, actual ?? 0))
  const color = pct > 80 ? 'bg-grid-red' : pct > 60 ? 'bg-grid-yellow' : 'bg-grid-green'

  return (
    <div>
      <div className="flex justify-between text-[10px] mb-1">
        <span className="text-grid-muted">Load</span>
        <span>
          <span className="text-slate-300 font-mono font-semibold">{pct.toFixed(1)}%</span>
          {target !== undefined && target !== null && (
            <span className="ml-1.5 text-grid-accent/60 font-mono">
              → {parseFloat(target).toFixed(1)}% target
            </span>
          )}
        </span>
      </div>
      <div className="h-1.5 bg-grid-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ── Source badge ──────────────────────────────────────────────────────────────
function SourceBadge({ telemetry }) {
  // Detect data source from metadata fields or voltage range
  const voltage = telemetry?.voltage
  const isPhone = voltage !== null && voltage !== undefined && voltage < 10

  if (isPhone) {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] bg-grid-purple/10 text-grid-purple border border-grid-purple/30 rounded px-1.5 py-0.5">
        📱 Android ADB
      </span>
    )
  }
  if (voltage !== null && voltage !== undefined) {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] bg-grid-accent/10 text-grid-accent border border-grid-accent/30 rounded px-1.5 py-0.5">
        🔌 USB Sensor
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-[9px] bg-grid-muted/10 text-grid-muted border border-grid-muted/20 rounded px-1.5 py-0.5">
      ⚙ Simulated
    </span>
  )
}

// ── Phone extra info strip ────────────────────────────────────────────────────
function PhoneInfoStrip({ telemetry }) {
  // Show raw phone values when voltage is in battery range (< 10V)
  const voltage = telemetry?.voltage
  if (!voltage || voltage >= 10) return null

  const battPct  = telemetry?.load_percentage
  const temp     = telemetry?.temperature
  return (
    <div className="bg-grid-purple/5 border border-grid-purple/20 rounded-lg px-3 py-2">
      <div className="text-[9px] text-grid-purple font-semibold uppercase tracking-wider mb-1.5">
        📱 Android Phone — Real Sensor Data
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-[10px] font-mono font-bold text-grid-purple">{voltage?.toFixed(3)}V</div>
          <div className="text-[8px] text-grid-muted">Raw Batt V</div>
        </div>
        <div>
          <div className="text-[10px] font-mono font-bold text-slate-300">{temp?.toFixed(1)}°C</div>
          <div className="text-[8px] text-grid-muted">Batt Temp</div>
        </div>
        <div>
          <div className="text-[10px] font-mono font-bold text-slate-300">{battPct?.toFixed(0)}%</div>
          <div className="text-[8px] text-grid-muted">Batt Level</div>
        </div>
      </div>
    </div>
  )
}

// ── Main card ─────────────────────────────────────────────────────────────────
export default function SubstationCard({ subId, telemetry, health, loadTarget, faultReport }) {
  const status    = health?.risk_level    || 'Unknown'
  const score     = health?.health_score  ?? 0
  const isAnomaly = health?.anomaly_detected
  const cfg       = STATUS_CONFIG[status] || STATUS_CONFIG.Unknown
  const faults    = faultReport?.faults_detected || []
  const t         = telemetry || {}

  // Detect if this is raw phone voltage (not yet scaled by new adb client)
  const rawVoltage = t.voltage
  const isRawPhone = rawVoltage !== null && rawVoltage !== undefined && rawVoltage < 10

  // For display: if raw phone voltage, show it as-is with label
  // If scaled (new adb client), show normally
  const displayVoltage = rawVoltage

  return (
    <div className={`rounded-xl border ${cfg.border} ${cfg.bg} p-4 flex flex-col gap-3
      transition-all duration-500
      ${status === 'Critical' ? 'glow-red'    : ''}
      ${status === 'Warning'  ? 'glow-yellow' : ''}
    `}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot} ${
              status === 'Critical' ? 'animate-blink' : ''
            }`} />
            <h3 className="text-sm font-bold text-slate-100">Substation {subId}</h3>
            <SourceBadge telemetry={t} />
          </div>
          <div className={`text-xs font-semibold mt-1 ${cfg.color}`}>{status}</div>
        </div>
        <HealthRing score={score} status={status} />
      </div>

      {/* ── Anomaly badge ───────────────────────────────────────────────── */}
      {isAnomaly && (
        <div className="flex items-center gap-1.5 bg-grid-red/10 border border-grid-red/30 rounded-lg px-2.5 py-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-grid-red animate-blink flex-shrink-0" />
          <span className="text-[10px] font-bold text-grid-red uppercase tracking-wider">
            ⚠ Anomaly Detected
          </span>
        </div>
      )}

      {/* ── Phone raw data strip ────────────────────────────────────────── */}
      <PhoneInfoStrip telemetry={t} />

      {/* ── Metrics ─────────────────────────────────────────────────────── */}
      <div className="bg-[#070b14] rounded-lg px-3 py-1.5">
        <MetricRow
          icon="⚡" label="Voltage"
          value={displayVoltage} unit="V"
          warn={isRawPhone ? undefined : 245}
          danger={isRawPhone ? undefined : 250}
          extra={isRawPhone ? 'battery' : undefined}
        />
        <MetricRow
          icon="〜" label="Current"
          value={t.current} unit="A"
          warn={18} danger={22}
          extra={isRawPhone ? 'cpu→A' : undefined}
        />
        <MetricRow
          icon="🌡" label="Temperature"
          value={t.temperature} unit="°C"
          warn={75} danger={85}
        />
        <MetricRow
          icon="∿" label="Harmonics"
          value={t.harmonic_5th} unit="%"
          warn={5} danger={8}
          extra={isRawPhone ? 'charge→H' : undefined}
        />
      </div>

      {/* ── Load bar ────────────────────────────────────────────────────── */}
      <LoadBar actual={t.load_percentage} target={loadTarget} />

      {/* ── Fault badges ────────────────────────────────────────────────── */}
      {faults.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {faults.map(f => (
            <span key={f.name}
              className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                f.severity === 'HIGH'
                  ? 'bg-grid-red/10 text-grid-red border-grid-red/30'
                  : 'bg-grid-yellow/10 text-grid-yellow border-grid-yellow/30'
              }`}>
              {f.name}
            </span>
          ))}
        </div>
      )}

      {/* ── Timestamp ───────────────────────────────────────────────────── */}
      {t.timestamp && (
        <div className="text-[9px] text-grid-muted/50 font-mono text-right">
          {new Date(t.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}
