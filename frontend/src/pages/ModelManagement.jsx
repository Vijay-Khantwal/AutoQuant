import { useEffect, useState, useRef } from 'react'
import { PageHeader, Card, CardHeader, CardBody, Button, Badge, Spinner, EmptyState, LogViewer, Pagination } from '../components/ui'
import { Cpu } from 'lucide-react'
import { getModelRuns, triggerRetrain, createStrategy } from '../api/model'
import { useTaskStore, useStrategyStore, useToastStore } from '../store/appStore'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../api/client'

export default function ModelManagement() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [loading, setLoading] = useState(true)
  const [runsPage, setRunsPage] = useState(1)
  const [runsTotal, setRunsTotal] = useState(0)

  const [newStratName, setNewStratName] = useState('')
  const [newStratTP, setNewStratTP] = useState('0.06')
  const [newStratSL, setNewStratSL] = useState('-0.03')
  const [newStratHold, setNewStratHold] = useState('15')
  const [creating, setCreating] = useState(false)

  const { startTask, hasRunning } = useTaskStore()
  const { strategies, setStrategies, selectedStrategyId, setSelectedStrategyId } = useStrategyStore()
  const { addToast } = useToastStore()
  const isRunning = hasRunning()

  const loadRuns = () => {
    if (!selectedStrategyId) return Promise.resolve()
    return getModelRuns({ strategy_id: selectedStrategyId, page: runsPage }).then(r => {
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
    })
  }

  useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId, runsPage])

  const wasRunning = useRef(false)
  useEffect(() => {
    if (wasRunning.current && !isRunning) {
      loadRuns()
    }
    wasRunning.current = isRunning
  }, [isRunning, selectedStrategyId])

  const handleRetrain = async () => {
    if (!selectedStrategyId) return
    const { data } = await triggerRetrain({ strategy_id: selectedStrategyId })
    startTask(data.task_id, 'Model Retraining', '/model')
  }

  const handleCreateStrategy = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      const payload = {
        name: newStratName,
        tp_target: parseFloat(newStratTP),
        sl_stop: parseFloat(newStratSL),
        hold_days: parseInt(newStratHold, 10),
        is_active: true
      }
      const res = await createStrategy(payload)
      const stratList = await api.get('/model/strategies/')
      setStrategies(stratList.data.results || stratList.data)
      setSelectedStrategyId(res.data.id)
      setNewStratName('')
      addToast({ type: 'success', title: 'Strategy Created', message: 'Ready to train model!' })
    } catch(err) {
      addToast({ type: 'error', title: 'Error', message: 'Could not create strategy' })
    }
    setCreating(false)
  }

  return (
    <div>
      <PageHeader
        title="Model Management"
        subtitle="Manage strategy profiles and re-train LightGBM models"
        actions={
          <Button onClick={handleRetrain} disabled={isRunning || !selectedStrategyId}>
            {isRunning ? <><Spinner /> Running...</> : <><Cpu size={16} className="mr-2 inline" /> Retrain Model</>}
          </Button>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Column */}
        <div className="space-y-6 xl:col-span-1">
          {/* Create Strategy Form */}
          <Card>
            <CardHeader title="Create New Strategy" subtitle="Add a new Target/SL combo to train" />
            <CardBody>
              <form onSubmit={handleCreateStrategy} className="space-y-3 text-sm">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Strategy Name</label>
                  <input required value={newStratName} onChange={e=>setNewStratName(e.target.value)} type="text" placeholder="e.g. Aggressive 6/3" className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-white outline-none focus:border-blue-500" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Take Profit (Decimal)</label>
                    <input required value={newStratTP} onChange={e=>setNewStratTP(e.target.value)} type="number" step="0.01" className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-white outline-none focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Stop Loss (Decimal)</label>
                    <input required value={newStratSL} onChange={e=>setNewStratSL(e.target.value)} type="number" step="0.01" className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-white outline-none focus:border-blue-500" />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Hold Days</label>
                  <input required value={newStratHold} onChange={e=>setNewStratHold(e.target.value)} type="number" className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-white outline-none focus:border-blue-500" />
                </div>
                <Button type="submit" className="w-full justify-center" disabled={creating}>
                  {creating ? 'Creating...' : '+ Add Strategy'}
                </Button>
              </form>
              {runsTotal > 0 && <div className="p-4 border-t border-gray-800"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Training Runs" />
            <CardBody className="p-0">
              <div className="max-h-[400px] overflow-y-auto p-4 space-y-2">
                {loading ? <Spinner /> : runs.length === 0 ? <EmptyState message="No model runs for this strategy." /> : runs.map(r => {
                  const d = new Date(r.created_at)
                  return (
                    <div key={r.id} onClick={() => setSelectedRun(r)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${selectedRun?.id === r.id ? 'bg-blue-600/10 border-blue-500/50' : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'}`}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-medium text-sm text-gray-200">Run #{r.id}</span>
                        <Badge color={r.status === 'SUCCESS' ? 'green' : r.status === 'FAILED' ? 'red' : 'blue'}>{r.status}</Badge>
                      </div>
                      <p className="text-xs text-gray-400">{d.toLocaleDateString()} {d.toLocaleTimeString()}</p>
                    </div>
                  )
                })}
              </div>
              {runsTotal > 0 && <div className="p-4 border-t border-gray-800"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}
            </CardBody>
          </Card>
        </div>

        {/* Right Column */}
        <div className="xl:col-span-2 space-y-6">
          {selectedRun ? (
            <>
              {selectedRun.status === 'RUNNING' && <LogViewer taskId={selectedRun.celery_task_id} />}
              
              {selectedRun.status === 'SUCCESS' && selectedRun.fold_summary && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  {selectedRun.fold_summary.map(f => (
                    <Card key={f.fold} className="p-4 bg-gray-800/30">
                      <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">Fold {f.fold}</p>
                      <div className="flex justify-between items-end">
                        <div>
                          <p className="text-2xl font-bold text-white">{f.precision.toFixed(1)}%</p>
                          <p className="text-xs text-gray-400">Precision</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-blue-400 font-medium">+{f.edge > 0 ? f.edge.toFixed(1) : 0}%</p>
                          <p className="text-xs text-gray-500">Edge over {f.base_rate.toFixed(1)}%</p>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}

              {selectedRun.feature_importances && Object.keys(selectedRun.feature_importances).length > 0 && (
                <Card>
                  <CardHeader title="Feature Importance" subtitle="Top most predictive technical indicators" />
                  <CardBody>
                    <div className="h-80 w-full mt-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart 
                          data={Object.entries(selectedRun.feature_importances)
                            .map(([feature, importance]) => ({ feature, importance }))
                            .sort((a, b) => b.importance - a.importance)
                            .slice(0, 20)} 
                          layout="vertical" 
                          margin={{ top: 0, right: 0, left: 40, bottom: 0 }}
                        >
                          <XAxis type="number" hide />
                          <YAxis dataKey="feature" type="category" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                          <Tooltip
                            cursor={{ fill: '#374151', opacity: 0.4 }}
                            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                          />
                          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                            {Object.entries(selectedRun.feature_importances)
                              .sort(([, a], [, b]) => b - a)
                              .slice(0, 20)
                              .map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={index < 5 ? '#3b82f6' : '#4b5563'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardBody>
                </Card>
              )}
            </>
          ) : (
            <Card className="h-full min-h-[400px] flex items-center justify-center">
              <EmptyState message={runs.length > 0 ? "Select a run to view details" : "Create a strategy and click Retrain Model"} />
            </Card>
          )}
        </div>

      </div>
    </div>
  )
}
