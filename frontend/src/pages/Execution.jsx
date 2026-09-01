import React, { useEffect, useState, useRef } from 'react'
import { PageHeader, Card, Button, Badge, Spinner, EmptyState, Pagination } from '../components/ui'
import { Zap } from 'lucide-react'
import { getResearchRuns } from '../api/research'
import { triggerExecution } from '../api/execution'
import { useTaskStore, useStrategyStore } from '../store/appStore'

export default function Execution() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [selected, setSelected] = useState({})  // { [decisionId]: bool }
  const [loading, setLoading] = useState(true)
  const [runsPage, setRunsPage] = useState(1)
  const [runsTotal, setRunsTotal] = useState(0)

  const { startTask, hasRunningByType } = useTaskStore()
  const { selectedStrategyId } = useStrategyStore()
  const isRunning = hasRunningByType('Execution')

  const loadRuns = async (currentSelectedId) => {
    if (!selectedStrategyId) return Promise.resolve()
    try {
      const r = await getResearchRuns({ strategy_id: selectedStrategyId, page: runsPage })
      const list = r.data.results || r.data
      setRuns(list)
      setRunsTotal(r.data.count || list.length)
      if (list.length > 0) {
        const newSelected = currentSelectedId ? list.find(x => x.id === currentSelectedId) : list[0]
        if (newSelected) {
          setSelectedRun(newSelected)
          if (!currentSelectedId) {
            const approvedIds = {}
            newSelected.decisions?.filter(d => d.action === 'APPROVE').forEach(d => { approvedIds[d.id] = true })
            setSelected(approvedIds)
          }
        }
      } else {
        setSelectedRun(null)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadRuns() }, [selectedStrategyId, runsPage])

  const wasRunning = useRef(false)
  useEffect(() => {
    if (wasRunning.current && !isRunning) {
      loadRuns(selectedRun?.id)
    }
    wasRunning.current = isRunning
  }, [isRunning, selectedStrategyId])

  const toggleAll = () => {
    const approved = selectedRun.decisions?.filter(d => d.action === 'APPROVE') || []
    if (Object.keys(selected).length === approved.length) {
      setSelected({})
    } else {
      const all = {}
      approved.forEach(d => { all[d.id] = true })
      setSelected(all)
    }
  }

  const handleExecute = async () => {
    if (!selectedStrategyId) return
    const ids = Object.keys(selected).filter(k => selected[k])
    if (ids.length === 0) return
    const { data } = await triggerExecution({ decision_ids: ids, research_run_id: selectedRun.id })
    startTask(data.task_id, 'Trade Execution Job', '/orders')
  }

  return (
    <div>
      <PageHeader
        title="Execution Center"
        subtitle="Review and execute audited trades via Dhan Sandbox"
      />

      <div className="flex gap-4">
        <div className="w-64 shrink-0">
          <p className="text-xs text-gray-400 uppercase mb-2">Audited Runs</p>
          {runs.map(r => {
            const dateObj = new Date(r.created_at)
            const approvedCount = r.decisions?.filter(d => d.action === 'APPROVE').length || 0
            return (
              <button key={r.id} onClick={() => {
                setSelectedRun(r)
                const defaultSel = {}
                r.decisions?.filter(d => d.action === 'APPROVE').forEach(d => { defaultSel[d.id] = true })
                setSelected(defaultSel)
              }}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 transition-colors
                  ${selectedRun?.id === r.id ? 'bg-blue-600 text-white' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}>
                <p className="font-medium">{dateObj.toLocaleDateString()} <span className="text-xs text-gray-400 ml-1">@ {dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></p>
                <div className="flex justify-between items-center mt-1">
                  <p className="text-xs opacity-70">{r.status}</p>
                  <Badge color="green">{approvedCount} Approved</Badge>
                </div>
              </button>
            )
          })}
          {runsTotal > 0 && <div className="mt-4"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}
        </div>

        <div className="flex-1">
          {loading ? <Spinner /> : !selectedRun ? <EmptyState message="Select a research run to view decisions." /> : (
            <Card>
              <div className="flex items-center justify-between p-4 border-b border-gray-800">
                <div>
                  <h3 className="font-semibold text-white">Approve Execution</h3>
                  <p className="text-xs text-gray-400">Deselect any trades you wish to skip.</p>
                </div>
                <div className="flex gap-3">
                  <Button variant="secondary" onClick={toggleAll}>Toggle All</Button>
                  <Button onClick={handleExecute} disabled={isRunning || Object.values(selected).filter(Boolean).length === 0}>
                    {isRunning ? 'Executing...' : <><Zap size={16} /> Execute {Object.values(selected).filter(Boolean).length} Trades</>}
                  </Button>
                </div>
              </div>
              <div className="overflow-x-auto custom-scrollbar pb-2">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-800 bg-gray-900/50">
                      <th className="px-4 py-3 w-10"></th>
                      <th className="px-4 py-3">Ticker</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Confidence</th>
                      <th className="px-4 py-3">LTP</th>
                      <th className="px-4 py-3">Suggested Alloc</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRun.decisions?.map(d => {
                      const isApproved = d.action === 'APPROVE'
                      return (
                        <tr key={d.id} className={`border-b border-gray-800 ${isApproved ? 'hover:bg-gray-800/50' : 'opacity-50'}`}>
                          <td className="px-4 py-3 text-center">
                            <input 
                              type="checkbox" 
                              checked={!!selected[d.id]} 
                              onChange={(e) => setSelected({ ...selected, [d.id]: e.target.checked })}
                              className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-3 font-medium text-white">{d.ticker.replace('.NS', '')}</td>
                          <td className="px-4 py-3"><Badge color={isApproved ? 'green' : 'red'}>{d.action}</Badge></td>
                          <td className="px-4 py-3 text-gray-300">{(d.confidence_score * 100).toFixed(0)}%</td>
                          <td className="px-4 py-3 text-gray-300">₹{d.ltp?.toFixed(2)}</td>
                          <td className="px-4 py-3 text-gray-300">₹{d.recommended_allocation_inr?.toFixed(0) || '15000'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

