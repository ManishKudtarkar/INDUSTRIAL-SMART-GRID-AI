/**
 * LoadDistribution — bar chart + stat cards for load across substations.
 */
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, LabelList } from 'recharts'

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

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="bg-[#0a0e1a] border border-grid-border rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-300 font-semibold mb-1">{d.payload.name}</p>
      <p className="font-mono font-bold" style={{ color: d.fill }}>{d.value.toFixed(1)}% load</p>
      <p className="text-grid-muted mt-0.5">{d.payload.status}</p>
    </div>
  )
}

export default function LoadDistribution({ loadDist, healthData }) {
  const entries = Object.entries(loadDist || {})
  if (!entries.length) return null

  const chartData = entries.map(([sub, load]) => ({
    name: sub,
    load: parseFloat(parseFloat(load).toFixed(1)),
    status: healthData?.[sub]?.risk_level || 'Unknown',
  }))

  // Dynamic Y-axis: max value + 15% headroom, minimum ceiling of 60
  const maxLoad = Math.max(...chartData.map(d => d.load))
  const yMax = Math.max(60, Math.ceil((maxLoad * 1.25) / 10) * 10)

  const totalLoad = chartData.reduce((s, d) => s + d.load, 0)

  return (
    <div className="bg-grid-card border border-grid-border rounded-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          ⚖️ Load Distribution
        </h4>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-grid-muted">Total:</span>
          <span className="text-[10px] font-mono font-bold text-grid-accent">{totalLoad.toFixed(1)}%</span>
          <span className="text-[10px] text-grid-muted ml-1">Auto-balanced</span>
        </div>
      </div>

      {/* Stat cards row */}
      <div className="grid gap-2 mb-4" style={{ gridTemplateColumns: `repeat(${chartData.length}, 1fr)` }}>
        {chartData.map((d, i) => {
          const color = getColor(d.name, i)
          const status = d.status
          const statusColor = status === 'Healthy' ? '#00ff88' : status === 'Warning' ? '#ffb800' : '#ff3b5c'
          return (
            <div key={d.name}
              className="rounded-lg p-3 text-center border"
              style={{ borderColor: color + '33', background: color + '0a' }}>
              <div className="text-[10px] text-slate-400 mb-1">{d.name}</div>
              <div className="text-xl font-bold font-mono leading-none" style={{ color }}>
                {d.load.toFixed(1)}
                <span className="text-xs font-normal ml-0.5">%</span>
              </div>
              <div className="text-[9px] mt-1 font-semibold" style={{ color: statusColor }}>{status}</div>
            </div>
          )
        })}
      </div>

      {/* Bar chart — Y axis scaled to actual data range */}
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData} margin={{ top: 16, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            domain={[0, yMax]}
            tick={{ fill: '#4a5568', fontSize: 9 }}
            tickLine={false}
            axisLine={false}
            width={32}
            tickFormatter={v => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#ffffff06' }} />
          <Bar dataKey="load" radius={[6, 6, 0, 0]} maxBarSize={56}>
            <LabelList
              dataKey="load"
              position="top"
              formatter={v => `${v.toFixed(1)}%`}
              style={{ fill: '#94a3b8', fontSize: 9, fontFamily: 'monospace' }}
            />
            {chartData.map((entry, i) => (
              <Cell key={entry.name} fill={getColor(entry.name, i)} fillOpacity={0.9} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
