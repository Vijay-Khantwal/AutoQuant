import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useToastStore = create((set) => ({
  toasts: [],
  addToast: (toast) =>
    set((s) => ({ toasts: [...s.toasts, { id: Date.now(), ...toast }] })),
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

export const useTaskStore = create(
  persist(
    (set, get) => ({
      tasks: {},

      startTask: (taskId, label, link = null) =>
        set((s) => ({
          tasks: {
            ...s.tasks,
            [taskId]: {
              label,
              status: 'RUNNING',
              logs: [],
              startedAt: Date.now(),
              link,
            },
          },
        })),

      appendLog: (taskId, line) =>
        set((s) => {
          const t = s.tasks[taskId]
          if (!t) return s
          return {
            tasks: {
              ...s.tasks,
              [taskId]: { ...t, logs: [...t.logs, line] },
            },
          }
        }),

      finishTask: (taskId, success) =>
        set((s) => {
          const t = s.tasks[taskId]
          if (!t) return s
          return {
            tasks: {
              ...s.tasks,
              [taskId]: { ...t, status: success ? 'SUCCESS' : 'FAILED' },
            },
          }
        }),

      clearTask: (taskId) =>
        set((s) => {
          const next = { ...s.tasks }
          delete next[taskId]
          return { tasks: next }
        }),

      clearFinished: () =>
        set((s) => {
          const next = {}
          Object.entries(s.tasks).forEach(([id, t]) => {
            if (t.status === 'RUNNING') next[id] = t
          })
          return { tasks: next }
        }),

      clearAll: () => set({ tasks: {} }),

      runningTasks: () =>
        Object.entries(get().tasks).filter(([, t]) => t.status === 'RUNNING'),
      hasRunning: () =>
        Object.values(get().tasks).some((t) => t.status === 'RUNNING'),
      hasRunningByType: (keyword) =>
        Object.values(get().tasks).some(
          (t) => t.status === 'RUNNING' && t.label?.toLowerCase().includes(keyword.toLowerCase())
        ),
    }),
    {
      name: 'trade-agent-tasks',
      partialize: (s) => ({ tasks: s.tasks }),
    }
  )
)

export const useStrategyStore = create(
  persist(
    (set) => ({
      strategies: [],
      selectedStrategyId: null,
      setStrategies: (strategies) => set({ strategies }),
      setSelectedStrategyId: (id) => set({ selectedStrategyId: id }),
    }),
    {
      name: 'trade-agent-strategies',
    }
  )
)


export const useDateStore = create((set) => ({
  startDate: '',
  endDate: '',
  isSingleDay: false,
  setDateRange: (start, end) => set({ startDate: start, endDate: end }),
  toggleSingleDay: (isSingle) => set({ isSingleDay: isSingle })
}))
