import { useEffect, useRef, useState } from 'react'
import { useTaskStore, useToastStore } from '../../store/appStore'
import { useNavigate } from 'react-router-dom'
import { Loader2, Check, X } from 'lucide-react'

/**
 * TaskWatcher Ã¢â‚¬â€ one per running task. Lives inside GlobalTaskMonitor (never unmounts).
 * Opens a WebSocket for live logs. If WS drops, falls back to REST polling for final status.
 */
function TaskWatcher({ taskId, label }) {
  const { appendLog, finishTask } = useTaskStore()
  const { addToast } = useToastStore()
  const wsRef = useRef(null)
  const mounted = useRef(true)
  const receivedDone = useRef(false)

  // Determine the REST endpoint to check task status based on label
  const getStatusUrl = (label) => {
    if (label?.toLowerCase().includes('audit') || label?.toLowerCase().includes('research')) {
      return `/api/research/runs/task-status/${taskId}/`
    }
    if (label?.toLowerCase().includes('execution') || label?.toLowerCase().includes('order')) {
      return `/api/execution/runs/task-status/${taskId}/`
    }
    return `/api/signals/runs/task-status/${taskId}/`
  }

  const pollRestUntilDone = () => {
    if (!mounted.current || receivedDone.current) return
    const url = getStatusUrl(label)
    let pendingCount = 0
    const existingLogs = useTaskStore.getState().tasks[taskId]?.logs?.length ?? 0

    const timer = setInterval(async () => {
      if (!mounted.current || receivedDone.current) {
        clearInterval(timer)
        return
      }
      try {
        const res = await fetch(url)
        const data = await res.json()
        const celeryStatus = data.status // PENDING, STARTED, SUCCESS, FAILURE, RETRY
        if (celeryStatus === 'SUCCESS') {
          receivedDone.current = true
          clearInterval(timer)
          finishTask(taskId, true)
          addToast({ type: 'success', title: `${label || 'Job'} Complete`, message: 'Click to view results.', duration: 7000 })
        } else if (celeryStatus === 'FAILURE') {
          receivedDone.current = true
          clearInterval(timer)
          finishTask(taskId, false)
          addToast({ type: 'error', title: `${label || 'Job'} Failed`, message: String(data.result || 'Unknown error'), duration: 8000 })
        } else if (celeryStatus === 'PENDING') {
          pendingCount++
          // PENDING after 3 checks (6s) with existing log lines = Redis was cleared, task already ran
          // PENDING after 5 checks (10s) with no logs = task was never picked up (Celery not running)
          const threshold = existingLogs > 0 ? 3 : 8
          if (pendingCount >= threshold) {
            receivedDone.current = true
            clearInterval(timer)
            // If we had log lines, task likely succeeded Ã¢â‚¬â€ mark success so page reloads
            finishTask(taskId, existingLogs > 0)
            if (existingLogs > 0) {
              addToast({ type: 'success', title: `${label || 'Job'} Complete`, message: 'Data saved. Refreshing results.', duration: 5000 })
            }
          }
        }
        // STARTED / RETRY Ã¢â€ â€™ keep polling
      } catch {
        // Network error, keep polling
      }
    }, 2000)
    // Safety timeout: if still running after 5 minutes, mark stale
    setTimeout(() => {
      if (!receivedDone.current) {
        clearInterval(timer)
        receivedDone.current = true
        finishTask(taskId, false)
      }
    }, 5 * 60 * 1000)
  }

  useEffect(() => {
    let effectActive = true
    mounted.current = true
    receivedDone.current = false
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const useAzure = localStorage.getItem(`USE_AZURE`) === `true`;
    const url = useAzure ? `ws://${import.meta.env.VITE_AZURE_IP || '20.235.242.149'}:8000/ws/tasks/${taskId}/` : `${proto}://${window.location.host}/ws/tasks/${taskId}/`;
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (e) => {
      if (!effectActive) return
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'log') {
          appendLog(taskId, data.message)
          if (data.done) {
            receivedDone.current = true
            finishTask(taskId, true)
            addToast({ type: 'success', title: `${label || 'Job'} Complete`, message: 'Click to view results.', duration: 7000 })
            ws.close()
          }
          if (data.error) {
            receivedDone.current = true
            finishTask(taskId, false)
            addToast({ type: 'error', title: `${label || 'Job'} Failed`, message: data.message, duration: 8000 })
            ws.close()
          }
        }
      } catch {}
    }

    ws.onerror = () => {
      if (!effectActive || receivedDone.current) return
      appendLog(taskId, '[WS disconnected - polling for status...]')
      pollRestUntilDone()
    }

    ws.onclose = () => {
      if (!effectActive || receivedDone.current) return
      pollRestUntilDone()
    }

    return () => {
      effectActive = false
      mounted.current = false
      ws.close()
    }
  }, [taskId])

  return null
}

function FloatingJobsPanel() {
  const { tasks, clearFinished, clearTask, clearAll } = useTaskStore()
  const [open, setOpen] = useState(false)
  const [expandedTask, setExpandedTask] = useState(null)

  const allTasks = Object.entries(tasks).reverse() // Show newest first
  const running = allTasks.filter(([, t]) => t.status === 'RUNNING')
  const finished = allTasks.filter(([, t]) => t.status !== 'RUNNING')

  if (allTasks.length === 0) return null

  const statusIcon = (s) => {
    if (s === 'RUNNING') return <Loader2 size={14} className="animate-spin" />
    if (s === 'SUCCESS') return <Check size={14} />
    return <X size={14} />
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 font-sans">
      {/* Pill trigger */}
      <button
        onClick={() => setOpen(!open)}
        className={`w-full flex items-center justify-between px-5 py-3 rounded-2xl shadow-xl border backdrop-blur-md transition-all
          ${running.length > 0
            ? 'bg-blue-900/40 border-blue-500/50 text-blue-100 hover:bg-blue-900/60 shadow-blue-900/20'
            : 'bg-zinc-800/80 border-zinc-700 text-zinc-300 hover:bg-zinc-700/80'}`}
      >
        <span className="flex items-center gap-3 font-semibold tracking-wide text-sm">
          {running.length > 0 ? (
            <>
              <div className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </div>
              {running.length} JOB{running.length > 1 ? 'S' : ''} RUNNING
            </>
          ) : (
            <>
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              {finished.length} JOB{finished.length > 1 ? 'S' : ''} DONE
            </>
          )}
        </span>
        <span className="text-xs font-bold opacity-50">{open ? 'HIDE' : 'SHOW'}</span>
      </button>

      {/* Expanded panel */}
      {open && (
        <div className="mt-3 bg-zinc-900/95 backdrop-blur-xl border border-zinc-700/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[500px] animate-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-950/50">
            <span className="text-xs font-bold text-zinc-400 tracking-wider">ACTIVITY LOG</span>
            <div className="flex gap-4">
              {running.length > 0 && (
                <button onClick={clearAll} className="text-xs font-bold text-red-500 hover:text-red-400 transition-colors">
                  Force Clear
                </button>
              )}
              {finished.length > 0 && (
                <button onClick={clearFinished} className="text-xs font-medium text-zinc-500 hover:text-white transition-colors">
                  Clear Done
                </button>
              )}
            </div>
          </div>

          {/* Task list */}
          <div className="overflow-y-auto custom-scrollbar flex-1 p-2 space-y-1">
            {allTasks.map(([id, task]) => (
              <div key={id} className={`rounded-xl border transition-all overflow-hidden
                ${task.status === 'RUNNING' ? 'border-blue-900/50 bg-blue-950/20' : 
                  task.status === 'SUCCESS' ? 'border-zinc-800 bg-zinc-800/20 hover:bg-zinc-800/40' : 
                  'border-red-900/30 bg-red-950/10'}`}>
                
                <div
                  className="flex items-center gap-3 px-4 py-3 cursor-pointer"
                  onClick={() => setExpandedTask(expandedTask === id ? null : id)}
                >
                  <div className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold
                    ${task.status === 'RUNNING' ? 'bg-blue-900 text-blue-400 animate-spin-slow' : 
                      task.status === 'SUCCESS' ? 'bg-emerald-900/50 text-emerald-400' : 'bg-red-900/50 text-red-400'}`}>
                    {statusIcon(task.status)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-zinc-200 truncate">{task.label}</p>
                    <p className="text-xs text-zinc-500 mt-0.5 flex items-center gap-2">
                      {task.status === 'RUNNING' ? 'Processing...' : task.status === 'SUCCESS' ? 'Completed' : 'Failed'}
                      <span className="opacity-50">&bull;</span>
                      {task.logs.length} lines
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    {task.link && task.status === 'SUCCESS' && (
                      <a href={task.link} onClick={e => e.stopPropagation()} className="text-xs font-bold text-blue-400 hover:text-blue-300">
                        OPEN
                      </a>
                    )}
                    {task.status !== 'RUNNING' && (
                      <button onClick={e => { e.stopPropagation(); clearTask(id) }} className="text-zinc-500 hover:text-white"><X size={16} /></button>
                    )}
                  </div>
                </div>

                {/* Log viewer */}
                {expandedTask === id && task.logs.length > 0 && (
                  <div className="bg-black/50 p-4 max-h-48 overflow-y-auto font-mono text-[10px] sm:text-xs leading-relaxed space-y-1">
                    {task.logs.map((line, i) => {
                      const isError = line.toLowerCase().includes('error') || line.toLowerCase().includes('fail')
                      const isSuccess = line === 'DONE' || line.includes('SUCCESS')
                      return (
                        <div key={i} className={`${isError ? 'text-red-400 font-medium' : isSuccess ? 'text-emerald-400 font-bold' : 'text-zinc-400'}`}>
                          {line}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * GlobalTaskMonitor Ã¢â‚¬â€ renders a TaskWatcher for every RUNNING task.
 * Lives at the App root level so it never unmounts on navigation.
 */
export default function GlobalTaskMonitor() {
  const tasks = useTaskStore((s) => s.tasks)
  const runningEntries = Object.entries(tasks).filter(([, t]) => t.status === 'RUNNING')

  return (
    <>
      {runningEntries.map(([id, t]) => (
        <TaskWatcher key={id} taskId={id} label={t.label} />
      ))}
      <FloatingJobsPanel />
    </>
  )
}

