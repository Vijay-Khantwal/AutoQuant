import React, { useEffect, useState, useRef } from 'react'
import { PageHeader, Card, CardHeader, CardBody, Button, Badge, Spinner, EmptyState, Pagination } from '../components/ui'
import { Play, Activity, Loader2 } from 'lucide-react'
import { getSignalRuns, getRunSignals, triggerPredict } from '../api/signals'
import { useTaskStore, useStrategyStore } from '../store/appStore'

export default function Signals() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [runsPage, setRunsPage] = useState(1)
  const [runsTotal, setRunsTotal] = useState(0)
  const [signalsPage, setSignalsPage] = useState(1)
  const [signalsTotal, setSignalsTotal] = useState(0)

  const { startTask, hasRunning } = useTaskStore()
  const { selectedStrategyId } = useStrategyStore()
  const isRunning = hasRunning()

  const loadRuns = () => {
    if (!selectedStrategyId) return Promise.resolve()
    return getSignalRuns({ strategy_id: selectedStrategyId, page: runsPage }).then(r => {
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
      getRunSignals(selectedRun.id, { page: signalsPage }).then(r => {
        setSignals(r.data.results || r.data)
        setSignalsTotal(r.data.count || (r.data.results ? r.data.results.length : r.data.length))
      })
    } else {
      setSignals([])
    }
  }, [selectedRun, signalsPage])

  const wasRunning = useRef(false)
  useEffect(() => {
    if (wasRunning.current && !isRunning) {
      loadRuns()
    }
    wasRunning.current = isRunning
  }, [isRunning, selectedStrategyId])

  const handleTrigger = async () => {
    if (!selectedStrategyId) return
    const { data } = await triggerPredict({ strategy_id: selectedStrategyId })
    startTask(data.task_id, 'ML Prediction Pipeline', '/signals')
  }

  return (
    <div>
      <PageHeader
        title="Daily Signals"
        subtitle="ML-ranked Nifty 500 trade candidates"
        actions={
          <Button onClick={handleTrigger} disabled={isRunning} className="min-w-[160px]">
            {isRunning ? <><Loader2 size={16} className="animate-spin mr-1 inline" /> Running...</> : <><Play size={16} /> Run Prediction</>}
          </Button>
        }
      />

      <div className="flex gap-4">
        <div className="w-56 shrink-0">
          <p className="text-xs text-gray-400 uppercase mb-2">Prediction Runs</p>
          {runs.map(r => {
            const dateObj = new Date(r.created_at)
            const timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            return (
              <button key={r.id} onClick={() => selectRun(r)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 transition-colors
                  ${selectedRun?.id === r.id ? 'bg-blue-600 text-white' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}>
                <p className="font-medium">{r.run_date} <span className="text-xs text-gray-400 ml-1">@ {timeStr}</span></p>
                <p className="text-xs opacity-70">
                  {r.status === 'RUNNING' ? 'Running...' : `${r.signal_count} signals`}
                </p>
              </button>
            )
          })}
          {runsTotal > 0 && <div className="mt-4"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}
        </div>

        <Card className="flex-1">
          <CardHeader title={selectedRun ? `Signals - ${new Date(selectedRun.created_at).toLocaleDateString()} @ ${new Date(selectedRun.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}` : 'Select a run'} />
          {loading ? <Spinner /> : !selectedRun ? <EmptyState message="Select a prediction run." /> : (
            <CardBody className="p-0">
              {signals.length === 0 ? (
                selectedRun.status === 'RUNNING' ? (
                  <div className="py-12 flex flex-col items-center justify-center">
                    <Spinner />
                    <p className="mt-4 text-sm text-blue-400 font-medium tracking-wide">Running ML pipeline...</p>
                  </div>
                ) : (
                  <EmptyState message="No signals generated for this run." />
                )
              ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-700">
                      <th className="px-4 py-3">Rank</th>
                      <th className="px-4 py-3">Ticker</th>
                      <th className="px-4 py-3">LTP</th>
                      <th className="px-4 py-3">Win Prob</th>
                      <th className="px-4 py-3">Percentile</th>
                    </tr>
                  </thead>
                  <tbody>
                    {signals.map(s => (
                      <tr key={s.id} className="border-b border-gray-800 hover:bg-gray-750">
                        <td className="px-4 py-3 text-gray-400">#{s.rank}</td>
                        <td className="px-4 py-3 font-medium text-white">{s.ticker.replace('.NS', '')}</td>
                        <td className="px-4 py-3">₹{s.ltp.toFixed(2)}</td>
                        <td className="px-4 py-3">
                          <Badge color={s.win_probability > 0.6 ? 'green' : s.win_probability > 0.5 ? 'yellow' : 'gray'}>
                            {(s.win_probability * 100).toFixed(1)}%
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-gray-300">Top {(100 - s.percentile_rank).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {signalsTotal > 0 && <div className="p-4 border-t border-gray-800"><Pagination totalCount={signalsTotal} currentPage={signalsPage} onPageChange={setSignalsPage} /></div>}
              </div>
              )}
            </CardBody>
          )}
        </Card>
      </div>
    </div>
  )
}
