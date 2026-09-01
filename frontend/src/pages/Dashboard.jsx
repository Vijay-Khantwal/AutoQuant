import { useEffect, useState } from 'react'
import { DateFilter, KpiCard, Card, CardHeader, CardBody, Badge, Spinner, EmptyState, PageHeader } from '../components/ui'
import { getPortfolioSummary } from '../api/portfolio'
import { getSignalRuns } from '../api/signals'
import { getResearchRuns } from '../api/research'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { useStrategyStore, useDateStore } from '../store/appStore'
import { useWebSocket } from '../hooks/useWebSocket'


export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [signalRuns, setSignalRuns] = useState([])
  const [researchRuns, setResearchRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  
  const { strategies, selectedStrategyId } = useStrategyStore()
  const { startDate, endDate } = useDateStore()
  const [selectedStrats, setSelectedStrats] = useState([]) // empty = ALL

  useEffect(() => {
    if (selectedStrategyId) {
      setSelectedStrats([selectedStrategyId])
    }
  }, [selectedStrategyId])


  

  useWebSocket('/ws/portfolio/', (msg) => {
    if (msg?.action === 'refresh') fetchDashboard(true)
  })

  const fetchDashboard = async (isRefresh = false) => {
    isRefresh = isRefresh || summary !== null;
    if (!isRefresh) setLoading(true)
    else setRefreshing(true)
    
    try {
            const params = selectedStrats.length > 0 ? { strategy_ids: selectedStrats.join(',') } : {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const [s, sr, rr] = await Promise.all([
        getPortfolioSummary(params),
        getSignalRuns(),
        getResearchRuns(),
      ])
      setSummary(s.data)
      setSignalRuns(sr.data.results || sr.data)
      setResearchRuns(rr.data.results || rr.data)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [selectedStrats, startDate, endDate])

  if (loading && !summary) return <Spinner />

  const pnlColor = (v) => v >= 0 ? 'text-emerald-400' : 'text-red-400'

  const toggleStrat = (id) => {
    if (selectedStrats.includes(id)) setSelectedStrats(selectedStrats.filter(i => i !== id))
    else setSelectedStrats([...selectedStrats, id])
  }

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Real-time overview of your trading agent" />
      <div className="mb-6"><DateFilter /></div>

      {/* Strategy Multi-Select Filter */}
      {strategies && strategies.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6 bg-zinc-900/50 p-3 rounded-xl border border-zinc-800/80 w-max">
          <span className="text-sm font-semibold text-zinc-400 flex items-center mr-2">Filter Strategies:</span>
          <button 
            onClick={() => setSelectedStrats([])}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${selectedStrats.length === 0 ? 'bg-blue-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'}`}
          >
            ALL
          </button>
          {strategies.map(s => (
            <button 
              key={s.id}
              onClick={() => toggleStrat(s.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${selectedStrats.includes(s.id) ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'}`}
            >
              {s.name}
            </button>
          ))}
        </div>
      )}

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
        <KpiCard
          label="Open Positions"
          value={summary?.total_open_positions ?? '--'}
          sub={`${summary?.total_closed_trades ?? 0} closed`}
        />
        <Card className="p-4 flex flex-col justify-center">
          <p className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Unrealized P&L</p>
          <p className={`text-xl font-bold ${pnlColor(summary?.total_unrealized_pnl ?? 0)}`}>
            ₹{(summary?.total_unrealized_pnl ?? 0).toFixed(0)}
          </p>
          <p className="text-[10px] text-zinc-500 mt-1">
            Net: ₹{((summary?.total_unrealized_pnl || 0) - (summary?.total_unrealized_fees || 0)).toFixed(0)} (Est. Fees: ₹{summary?.total_unrealized_fees?.toFixed(0) || 0})
          </p>
        </Card>
        <Card className="p-4 flex flex-col justify-center border-blue-900/50 bg-blue-950/20">
          <p className="text-[11px] font-bold text-blue-300 uppercase tracking-wider mb-1">Virtual P&L (AI)</p>
          <p className={`text-xl font-bold ${pnlColor(summary?.total_virtual_pnl ?? 0)}`}>
            ₹{(summary?.total_virtual_pnl ?? 0).toFixed(0)}
          </p>
          <p className="text-[10px] text-blue-400/60 mt-1">
            Net: ₹{((summary?.total_virtual_pnl || 0) - (summary?.total_virtual_fees || 0)).toFixed(0)} (Est. Fees: ₹{summary?.total_virtual_fees?.toFixed(0) || 0})
          </p>
        </Card>
        <KpiCard
          label="Realized P&L"
          value={`₹${(summary?.total_realized_pnl ?? 0).toFixed(0)}`}
          color={pnlColor(summary?.total_realized_pnl ?? 0)}
        />
        <KpiCard
          label="Win Rate"
          value={`${summary?.win_rate_pct ?? 0}%`}
          sub={`${summary?.win_count ?? 0}W / ${summary?.loss_count ?? 0}L`}
          color="text-blue-400"
        />
        <KpiCard
          label="Avg Hold Days"
          value={`${summary?.avg_hold_days?.toFixed(1) ?? 0.0}`}
          color="text-zinc-200"
        />
      </div>

      {/* Equity Curve */}
      {summary?.equity_curve?.length > 0 && (
        <Card className="mb-6">
          <CardHeader title="Equity Curve (Realized P&L)" subtitle="Daily realized net P&L (Zerodha fees)" />
          <CardBody>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary.equity_curve}>
                  <defs>
                    <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#52525b" fontSize={12} tickMargin={10} />
                  <YAxis stroke="#52525b" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px' }}
                    itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                  />
                  <Area type="monotone" dataKey="realized_pnl" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorPnl)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Bottom Grid: Recent Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Recent Signal Runs" />
          <div className="divide-y divide-zinc-800/50">
            {signalRuns.length === 0 ? <EmptyState message="No signal runs yet" /> : signalRuns.slice(0, 5).map(r => (
              <div key={r.id} className="flex justify-between items-center p-4 hover:bg-zinc-800/20 transition-colors">
                <div>
                  <p className="text-sm font-semibold text-zinc-200">{r.strategy_name}</p>
                  <p className="text-xs text-zinc-500">{new Date(r.created_at).toLocaleString()}</p>
                </div>
                <Badge variant={r.status==='SUCCESS'?'success':r.status==='FAILED'?'danger':'warning'}>{r.status}</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Recent AI Audits" />
          <div className="divide-y divide-zinc-800/50">
            {researchRuns.length === 0 ? <EmptyState message="No audits yet" /> : researchRuns.slice(0, 5).map(r => (
              <div key={r.id} className="flex justify-between items-center p-4 hover:bg-zinc-800/20 transition-colors">
                <div>
                  <p className="text-sm font-semibold text-zinc-200">{r.strategy_name}</p>
                  <p className="text-xs text-zinc-500">{new Date(r.created_at).toLocaleString()}</p>
                </div>
                <Badge variant={r.status==='SUCCESS'?'success':r.status==='FAILED'?'danger':'warning'}>{r.status}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}


