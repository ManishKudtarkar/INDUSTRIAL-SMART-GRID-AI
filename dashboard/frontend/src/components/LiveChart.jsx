/**
 * LiveChart — scrolling line chart for a single metric across all substations.
 * Uses Recharts ResponsiveContainer + LineChart.
 */
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine,
} from 'recharts'

const SUB_COLORS = {
  S1: '#00d4ff',
  S2: '#ff3b5c',
  S3: '#00ff88',
  S4: '#a855f7',
  S5: '#ffb800',
}

const DEFAULT_COLORS = ['#00d4ff', '#ff3b5c', '#00ff88', '#a855f7', '#ffb800']

function getColor(subId, index) {
  return SUB_COLORS[subId] || DEFAULT_COLORS[index % DEFAULT_COLORS.length]
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-grid-card border border-grid-border rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-grid-muted mb-1 font-mono">{label}</p>
      {payload.map(p => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-300">{p.dataKey}:</span>
          <span className="font-mono font-semibold" style={{ color: p.color }}>
            {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function LiveChart({ title, data, substations, unit, dangerLine, warnLine, height = 180 }) {
  return (
    <div className="bg-grid-card border border-grid-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</h4>
        {unit && <span className="text-[10px] text-grid-muted font-mono">{unit}</span>}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" />
          <XAxis
            dataKey="time"
            tick={{ fill: '#4a5568', fontSize: 9 }}
            tickLine={false}
            axisLine={{ stroke: '#1e2d4a' }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#4a5568', fontSize: 9 }}
            tickLine={false}
            axisLine={{ stroke: '#1e2d4a' }}
            width={40}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '10px', paddingTop: '8px' }}
            formatter={(v) => <span style={{ color: '#94a3b8' }}>{v}</span>}
          />
          {dangerLine && (
            <ReferenceLine y={dangerLine} stroke="#ff3b5c" strokeDasharray="4 2"
              label={{ value: 'Danger', fill: '#ff3b5c', fontSize: 9, position: 'insideTopRight' }} />
          )}
          {warnLine && (
            <ReferenceLine y={warnLine} stroke="#ffb800" strokeDasharray="4 2"
              label={{ value: 'Warn', fill: '#ffb800', fontSize: 9, position: 'insideTopRight' }} />
          )}
          {substations.map((sub, i) => (
            <Line
              key={sub}
              type="monotone"
              dataKey={sub}
              stroke={getColor(sub, i)}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
