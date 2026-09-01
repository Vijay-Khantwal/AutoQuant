import { useEffect, useState, useRef } from 'react'
import { PageHeader, Button, Badge, Spinner, EmptyState, Pagination } from '../components/ui'
import { ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react'
import { getResearchRuns, triggerResearch } from '../api/research'
import { useTaskStore, useStrategyStore } from '../store/appStore'

const RISK_COLORS = { high: 'red', medium: 'yellow', low: 'green' }

function DecisionCard({ d }) {
  const [expanded, setExpanded] = useState(false)
  const [tab, setTab] = useState('verdict')
  const approved = d.action === 'APPROVE'

  const fundData = d.fundamentals_json || {}
  const val = fundData.valuation || {}
  const prof = fundData.profitability_and_returns || {}
  const solv = fundData.solvency || {}
  const own = fundData.ownership || {}

  const fmt = (num) => (num !== null && num !== undefined) ? Number(num).toFixed(2) : 'N/A'

  return (
    <div className={`border rounded-xl mb-3 overflow-hidden ${approved ? 'border-emerald-700' : 'border-red-800'}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-3 bg-zinc-800 hover:bg-zinc-750 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="font-bold text-white">{d.ticker.replace('.NS', '')}</span>
          <Badge color={approved ? 'green' : 'red'}>{d.action}</Badge>
          <span className="text-xs text-zinc-400">LTP: ₹{d.ltp?.toFixed(2)}</span>
          <span className="text-xs text-zinc-400">Confidence: {(d.confidence_score * 100).toFixed(0)}%</span>
        </div>
        <div className="flex items-center gap-3">
          {d.risk_flags?.length > 0 && (
            <Badge color="yellow">{d.risk_flags.length} flag{d.risk_flags.length > 1 ? 's' : ''}</Badge>
          )}
          <button 
            className="text-zinc-400 hover:text-white px-2"
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </button>

      {expanded && (
        <div className="bg-zinc-900 border-t border-zinc-800 p-5">
          <div className="flex gap-6">
            
            <div className="flex-1 space-y-4">
              <div className="flex gap-2 border-b border-zinc-800 pb-2">
                <button onClick={() => setTab('verdict')} className={`text-xs font-semibold px-2 py-1 rounded transition-colors ${tab==='verdict' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}>AI Verdict</button>
                <button onClick={() => setTab('news')} className={`text-xs font-semibold px-2 py-1 rounded transition-colors ${tab==='news' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}>News & Sentiment</button>
                <button onClick={() => setTab('fundamentals')} className={`text-xs font-semibold px-2 py-1 rounded transition-colors ${tab==='fundamentals' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}>Fundamentals</button>
              </div>
              
              {tab === 'verdict' && (
                <div className="space-y-4 text-sm text-zinc-300">
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wide mb-1">Final Rationale</h4>
                    <p className="leading-relaxed whitespace-pre-wrap">{d.final_rationale}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wide mb-1">Suggested Allocation</h4>
                    <p className="leading-relaxed font-mono text-blue-400">₹{d.recommended_allocation_inr?.toLocaleString()}</p>
                  </div>
                </div>
              )}

              {tab === 'news' && (
                <div className="space-y-4 text-sm text-zinc-300">
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wide mb-1">News Brief</h4>
                    <p className="leading-relaxed whitespace-pre-wrap">{d.tier1_news_brief || 'No recent news found.'}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wide mb-1">Sentiment Summary</h4>
                    <p className="leading-relaxed whitespace-pre-wrap">{d.news_sentiment_summary}</p>
                  </div>
                </div>
              )}

              {tab === 'fundamentals' && (
                <div className="space-y-4 text-sm text-zinc-300">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-zinc-800/50 p-4 rounded-xl">
                    <div><p className="text-xs text-zinc-500">P/E Ratio</p><p className="font-mono text-white">{fmt(val.pe_ratio)}</p></div>
                    <div><p className="text-xs text-zinc-500">Forward P/E</p><p className="font-mono text-white">{fmt(val.forward_pe)}</p></div>
                    <div><p className="text-xs text-zinc-500">P/B Ratio</p><p className="font-mono text-white">{fmt(val.pb_ratio)}</p></div>
                    <div><p className="text-xs text-zinc-500">Profit Margin</p><p className="font-mono text-white">{fmt(prof.profit_margins_pct)}%</p></div>
                    <div><p className="text-xs text-zinc-500">ROE</p><p className="font-mono text-white">{fmt(prof.roe_pct)}%</p></div>
                    <div><p className="text-xs text-zinc-500">D/E Ratio</p><p className="font-mono text-white">{fmt(solv.debt_to_equity)}</p></div>
                    <div><p className="text-xs text-zinc-500">Promoter Hold</p><p className="font-mono text-white">{fmt(own.insider_promoter_holding_pct)}%</p></div>
                    <div><p className="text-xs text-zinc-500">Inst. Hold</p><p className="font-mono text-white">{fmt(own.institutional_holding_pct)}%</p></div>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wide mb-1">Fundamental Summary</h4>
                    <p className="leading-relaxed whitespace-pre-wrap">{d.fundamental_summary}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="w-64 shrink-0 space-y-4 border-l border-zinc-800 pl-6">
              <div>
                <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wide mb-2">Risk Flags</h4>
                {d.risk_flags?.length > 0 ? (
                  <ul className="space-y-2">
                    {d.risk_flags.map((flag, idx) => (
                      <li key={idx} className="flex gap-2 text-xs">
                        <span className={`w-1.5 h-1.5 mt-1 rounded-full shrink-0 bg-${RISK_COLORS[flag.severity]}-500`} />
                        <span className="text-zinc-300">{flag.reason}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-xs text-zinc-400">None detected.</span>
                )}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  )
}

export default function AuditDossier() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [loading, setLoading] = useState(true)
  const [runsPage, setRunsPage] = useState(1)
  const [runsTotal, setRunsTotal] = useState(0)

  const { startTask, hasRunning } = useTaskStore()
  const { selectedStrategyId } = useStrategyStore()
  const isRunning = hasRunning()

  const loadRuns = () => {
    if (!selectedStrategyId) return Promise.resolve()
    return getResearchRuns({ strategy_id: selectedStrategyId, page: runsPage }).then(r => {
      const list = r.data.results || r.data
      setRuns(list)
      setRunsTotal(r.data.count || list.length)
      if (list.length > 0) {
        if (!selectedRun || !list.find(x => x.id === selectedRun.id)) {
           setSelectedRun(list[0])
        }
      } else {
        setSelectedRun(null)
      }
    }).catch(e => console.error(e))
  }

  const selectRun = (run) => {
    setSelectedRun(run)
  }

  useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId, runsPage])

  useEffect(() => {
    if (selectedRun) {
      import('../api/research').then(module => {
        module.getRunDecisions(selectedRun.id).then(res => setDecisions(res.data))
      })
    } else {
      setDecisions([])
    }
  }, [selectedRun])

  const wasRunning = useRef(false)
  useEffect(() => {
    if (wasRunning.current && !isRunning) {
      loadRuns()
    }
    wasRunning.current = isRunning
  }, [isRunning, selectedStrategyId])

  const handleTrigger = async () => {
    if (!selectedStrategyId) return
    const { data } = await triggerResearch({ strategy_id: selectedStrategyId })
    startTask(data.task_id, 'LLM Audit Workflow', '/audit')
  }

  return (
    <div>
      <PageHeader
        title="AI Audit Dossier"
        subtitle="Deep fundamental and technical review of top signals"
        actions={
          <Button onClick={handleTrigger} disabled={isRunning}>
            {isRunning ? <><Spinner /> Running...</> : <><ShieldCheck size={16} /> Run Audit</>}
          </Button>
        }
      />

      <div className="flex gap-4">
        <div className="w-56 shrink-0">
          <p className="text-xs text-zinc-400 uppercase mb-2">Audit Runs</p>
          {runs.map(r => {
            const dateObj = new Date(r.created_at)
            return (
              <button key={r.id} onClick={() => selectRun(r)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 transition-colors
                  ${selectedRun?.id === r.id ? 'bg-blue-600 text-white' : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300'}`}>
                <p className="font-medium">{dateObj.toLocaleDateString()} <span className="text-xs text-zinc-400 ml-1">@ {dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></p>
                <p className="text-xs opacity-70">
                  {r.status === 'RUNNING' ? 'Running...' : `${r.decision_count} decisions`}
                </p>
              </button>
            )
          })}
          {runsTotal > 0 && <div className="mt-4"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}
        </div>

        <div className="flex-1">
          {loading ? <Spinner /> : !selectedRun ? <EmptyState message="Select an audit run." /> : (
            decisions.length === 0 ? (
              selectedRun.status === 'RUNNING' ? (
                <div className="py-20 flex flex-col items-center justify-center bg-zinc-900 rounded-xl border border-zinc-800">
                  <Spinner />
                  <p className="mt-4 text-sm text-blue-400 font-medium">Auditing tickers via LLM pipeline...</p>
                  <p className="mt-1 text-xs text-zinc-500">This involves multi-agent web searches.</p>
                </div>
              ) : (
                <EmptyState message="No decisions made in this run." />
              )
            ) : (
              <div>
                {decisions.map(d => <DecisionCard key={d.id} d={d} />)}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  )
}
