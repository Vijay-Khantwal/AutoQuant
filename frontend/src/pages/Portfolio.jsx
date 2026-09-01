import React, { useEffect, useState } from 'react'
import { DateFilter, PageHeader, Card, Button, Badge, Spinner, Pagination } from '../components/ui'
import { getPositions, getTrades, getPortfolioSummary, triggerMonitor } from '../api/portfolio'
import { useToastStore, useStrategyStore, useDateStore } from '../store/appStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { RefreshCw, CheckCircle, XCircle } from 'lucide-react'

const pnlColor = v => v > 0 ? 'text-emerald-400' : v < 0 ? 'text-red-400' : 'text-zinc-400'

const FEE_TABLE_BROKERS = ['zerodha', 'dhan', 'groww', 'angel']

export default function Portfolio() {
  const [positions, setPositions] = useState([])
  const [positionsCount, setPositionsCount] = useState(0)
  const [positionsPage, setPositionsPage] = useState(1)
  
  const [trades, setTrades] = useState([])
  const [tradesCount, setTradesCount] = useState(0)
  const [tradesPage, setTradesPage] = useState(1)
  
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('open')
  const [aiFilter, setAiFilter] = useState('ALL')
  const { addToast } = useToastStore()
  const { selectedStrategyId } = useStrategyStore()
  const { startDate, endDate } = useDateStore()

  

  useWebSocket('/ws/portfolio/', (msg) => {
    if (msg?.action === 'refresh') load(true)
  })

  const load = (isSilent = false) => {
    if (!selectedStrategyId) return
    if (!isSilent) setLoading(true)
    
        let params = { strategy_id: selectedStrategyId }
    if (aiFilter !== 'ALL') params.ai_filter = aiFilter
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    Promise.all([
      getPositions({ ...params, status: 'OPEN', page: positionsPage }), 
      getTrades({ ...params, page: tradesPage }), 
      getPortfolioSummary(params)
    ])
      .then(([p, t, s]) => {
        setPositions(p.data.results || p.data)
        setPositionsCount(p.data.count || (p.data.results ? p.data.results.length : p.data.length))
        
        setTrades(t.data.results || t.data)
        setTradesCount(t.data.count || (t.data.results ? t.data.results.length : t.data.length))
        
        setSummary(s.data)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [selectedStrategyId, aiFilter, positionsPage, tradesPage, startDate, endDate])

  const handleMonitor = async () => {
    await triggerMonitor()
    addToast({ type: 'info', title: 'Monitor Started', message: 'Checking TP/SL/expiry on all positions...' })
    setTimeout(load, 3000)
  }

  return (
    <div>
      <PageHeader
        title="Portfolio & P&L"
        subtitle="Open positions, closed trades, and performance"
        actions={<Button onClick={handleMonitor}><RefreshCw size={16} /> Run Monitor</Button>}
      />

      <div className="mb-4"><DateFilter /></div>
        {/* AI Decision Filter */}
      <div className="flex gap-2 mb-4 bg-zinc-900 p-2 rounded-lg border border-zinc-800 w-max">
        {['ALL', 'APPROVE', 'REJECT'].map(f => (
          <button key={f} onClick={() => {
              setAiFilter(f)
              setPositionsPage(1)
              setTradesPage(1)
            }}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors
              ${aiFilter === f ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}>
            {f === 'ALL' ? 'All AI Decisions' : f === 'APPROVE' ? 'Approved Only' : 'Rejected Only'}
          </button>
        ))}
      </div>

            {/* Summary row */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <Card className="p-4">
            <p className="text-xs text-zinc-400">Win Rate</p>
            <p className="text-xl font-bold text-blue-400">{summary.win_rate_pct}%</p>
            <p className="text-[10px] text-zinc-500 mt-1">{summary.win_count}W / {summary.loss_count}L</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-zinc-400">Realized P&L</p>
            <p className={`text-xl font-bold ${pnlColor(summary.total_realized_pnl)}`}>
              &#x20B9;{summary.total_realized_pnl.toFixed(0)}
            </p>
          </Card>
                    <Card className="p-4">
            <p className="text-xs text-zinc-400">Unrealized P&L</p>
            <p className={`text-xl font-bold ${pnlColor(summary.total_unrealized_pnl)}`}>
              &#x20B9;{summary.total_unrealized_pnl.toFixed(0)}
            </p>
            <p className="text-[10px] text-zinc-500 mt-1">
              Net: &#x20B9;{(summary.total_unrealized_pnl - (summary.total_unrealized_fees || 0)).toFixed(0)} (Fees: &#x20B9;{summary.total_unrealized_fees?.toFixed(0) || 0})
            </p>
          </Card>
          <Card className="p-4 border-blue-900/50 bg-blue-950/20">
            <p className="text-xs text-blue-300">Virtual P&L (AI)</p>
            <p className={`text-xl font-bold ${pnlColor(summary.total_virtual_pnl)}`}>
              &#x20B9;{summary.total_virtual_pnl?.toFixed(0) || 0}
            </p>
            <p className="text-[10px] text-blue-400/60 mt-1">
              Net: &#x20B9;{((summary.total_virtual_pnl || 0) - (summary.total_virtual_fees || 0)).toFixed(0)} (Fees: &#x20B9;{summary.total_virtual_fees?.toFixed(0) || 0})
            </p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-zinc-400">Avg Hold Days</p>
            <p className="text-xl font-bold text-zinc-200">{summary.avg_hold_days.toFixed(1)}</p>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 mb-4">
        <button 
          onClick={() => setTab('open')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${tab === 'open' ? 'bg-emerald-600/20 text-emerald-400' : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200'}`}
        >
          Open ({positionsCount})
        </button>
        <button 
          onClick={() => setTab('closed')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${tab === 'closed' ? 'bg-zinc-700 text-white' : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200'}`}
        >
          Closed ({tradesCount})
        </button>
      </div>

      {loading ? <Spinner /> : (
        tab === 'open' ? (
        <Card>
          <div className="overflow-x-auto custom-scrollbar pb-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-zinc-400 border-b border-zinc-700 text-left whitespace-nowrap">
                  {['Ticker','Entry \u20B9','Current \u20B9','Qty','Days / 15','TP','SL','15d Peak/Dip','Virtual Exit','Unrealized','Status'].map(h =>
                    <th key={h} className="px-4 py-3">{h}</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {positions.map(p => (
                  <tr key={p.id} className="border-b border-zinc-800 hover:bg-zinc-800/40">
                    <td className="px-4 py-3 font-medium">
                      <div className="flex items-center gap-2 whitespace-nowrap">
                        {p.ticker.replace('.NS','')}
                        <Badge color={p.ai_decision === 'APPROVE' ? 'green' : 'red'} className="whitespace-nowrap flex-shrink-0">
                          {p.ai_decision === 'APPROVE' ? <><CheckCircle size={12} /> AI: YES</> : <><XCircle size={12} /> AI: NO</>}
                        </Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3">&#x20B9;{p.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-3">&#x20B9;{p.current_price.toFixed(2)}</td>
                    <td className="px-4 py-3">{p.quantity}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 whitespace-nowrap">
                        <span>{p.days_held}/{p.max_hold_days}</span>
                        <div className="w-16 h-1.5 bg-zinc-700 rounded-full">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(100, (p.days_held / p.max_hold_days) * 100)}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-emerald-400">&#x20B9;{p.tp_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-red-400">&#x20B9;{p.sl_price.toFixed(2)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex flex-col text-[11px] font-mono font-medium opacity-80 space-y-0.5">
                        <span className="text-emerald-400">H: &#x20B9;{p.max_high_15d?.toFixed(2) || '-'}</span>
                        <span className="text-red-400">L: &#x20B9;{p.max_low_15d?.toFixed(2) || '-'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {p.threshold_hit ? (
                        <div className={`px-2 py-0.5 rounded text-[10px] font-bold w-max whitespace-nowrap ${p.threshold_hit === 'TP' ? 'bg-emerald-950 text-emerald-400 border border-emerald-900/50' : 'bg-red-950 text-red-400 border border-red-900/50'}`}>
                          {p.threshold_hit} ({(p.threshold_hit_price - p.entry_price) * p.quantity > 0 ? '+' : ''}&#x20B9;{((p.threshold_hit_price - p.entry_price) * p.quantity).toFixed(0)})
                        </div>
                      ) : (
                        <span className="text-zinc-600 text-xs italic">Pending</span>
                      )}
                    </td>
                    <td className={`px-4 py-3 font-medium whitespace-nowrap ${pnlColor(p.unrealized_pnl)}`}>
                      {p.unrealized_pnl_pct > 0 ? '+' : ''}{p.unrealized_pnl_pct.toFixed(2)}% (&#x20B9;{p.unrealized_pnl.toFixed(0)})
                    </td>
                    <td className="px-4 py-3"><Badge color="blue">OPEN</Badge></td>
                  </tr>
                ))}
                {positions.length === 0 &&
                  <tr><td colSpan={11} className="text-center py-10 text-zinc-500">No open positions</td></tr>
                }
              </tbody>
            </table>
          </div>
          <Pagination 
            currentPage={positionsPage}
            totalCount={positionsCount}
            pageSize={50}
            onPageChange={setPositionsPage}
          />
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto custom-scrollbar pb-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-zinc-400 border-b border-zinc-700 text-left whitespace-nowrap">
                  {['Ticker','Entry \u20B9','Exit \u20B9','Reason','Hold Days','Gross P&L','Zerodha Net','Dhan Net','Groww Net','Angel Net'].map(h =>
                    <th key={h} className="px-4 py-3">{h}</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {trades.map(t => (
                  <tr key={t.id} className="border-b border-zinc-800 hover:bg-zinc-800/40">
                    <td className="px-4 py-3 font-medium">
                      <div className="flex items-center gap-2 whitespace-nowrap">
                        {t.ticker?.replace('.NS','')}
                        <Badge color={t.ai_decision === 'APPROVE' ? 'green' : 'red'} className="whitespace-nowrap flex-shrink-0">
                          {t.ai_decision === 'APPROVE' ? <><CheckCircle size={12} /> AI: YES</> : <><XCircle size={12} /> AI: NO</>}
                        </Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3">&#x20B9;{t.entry_price?.toFixed(2)}</td>
                    <td className="px-4 py-3">&#x20B9;{t.exit_price.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <Badge color={t.exit_reason === 'TP' ? 'green' : t.exit_reason === 'SL' ? 'red' : 'yellow'}>
                        {t.exit_reason}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">{t.hold_days}d</td>
                    <td className={`px-4 py-3 font-medium ${pnlColor(t.gross_pnl)}`}>&#x20B9;{t.gross_pnl.toFixed(0)}</td>
                    <td className={`px-4 py-3 ${pnlColor(t.net_pnl_zerodha)}`}>&#x20B9;{t.net_pnl_zerodha.toFixed(0)}</td>
                    <td className={`px-4 py-3 ${pnlColor(t.net_pnl_dhan)}`}>&#x20B9;{t.net_pnl_dhan.toFixed(0)}</td>
                    <td className={`px-4 py-3 ${pnlColor(t.net_pnl_groww)}`}>&#x20B9;{t.net_pnl_groww.toFixed(0)}</td>
                    <td className={`px-4 py-3 ${pnlColor(t.net_pnl_angel)}`}>&#x20B9;{t.net_pnl_angel.toFixed(0)}</td>
                  </tr>
                ))}
                {trades.length === 0 &&
                  <tr><td colSpan={10} className="text-center py-10 text-zinc-500">No closed trades yet</td></tr>
                }
              </tbody>
            </table>
          </div>
          <Pagination 
            currentPage={tradesPage}
            totalCount={tradesCount}
            pageSize={50}
            onPageChange={setTradesPage}
          />
        </Card>
      )
    )}
    </div>
  )
}










