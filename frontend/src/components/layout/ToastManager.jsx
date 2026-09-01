import { useEffect } from 'react'
import { useToastStore } from '../../store/appStore'

export default function ToastManager() {
  const { toasts, removeToast } = useToastStore()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} onClose={() => removeToast(t.id)} />
      ))}
    </div>
  )
}

function Toast({ toast, onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, toast.duration || 5000)
    return () => clearTimeout(timer)
  }, [])

  const colors = {
    success: 'bg-emerald-600',
    error:   'bg-red-600',
    info:    'bg-blue-600',
    warning: 'bg-amber-500',
  }
  const bg = colors[toast.type] || colors.info

  return (
    <div className={`${bg} text-white rounded-lg shadow-lg px-4 py-3 flex items-start gap-3 max-w-sm animate-fade-in`}>
      <div className="flex-1">
        {toast.title && <p className="font-semibold text-sm">{toast.title}</p>}
        <p className="text-sm opacity-90">{toast.message}</p>
        {toast.link && (
          <a href={toast.link} className="text-xs underline opacity-80 mt-1 block">
            View result →
          </a>
        )}
      </div>
      <button onClick={onClose} className="text-white/70 hover:text-white text-lg leading-none">×</button>
    </div>
  )
}
