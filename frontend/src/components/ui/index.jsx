/** Reusable UI primitives */
import React from 'react';
import { Loader2, Inbox, ChevronLeft, ChevronRight, Terminal } from 'lucide-react';

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-zinc-900/50 backdrop-blur-sm rounded-2xl border border-zinc-800/80 shadow-sm ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, actions, className = '' }) {
  return (
    <div className={`flex items-start justify-between px-6 py-5 border-b border-zinc-800/80 ${className}`}>
      <div>
        <h3 className="font-semibold text-zinc-100 tracking-tight">{title}</h3>
        {subtitle && <p className="text-xs text-zinc-400 mt-1 font-medium">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-3">{actions}</div>}
    </div>
  )
}

export function CardBody({ children, className = '' }) {
  return <div className={`p-6 ${className}`}>{children}</div>
}

export function Button({ children, onClick, variant = 'primary', size = 'md', disabled = false, className = '' }) {
  const base = 'inline-flex items-center justify-center gap-2 font-semibold rounded-xl transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-zinc-950 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]'
  const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-5 py-2.5 text-sm', lg: 'px-6 py-3 text-base' }
  const variants = {
    primary:   'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/20 border border-blue-500/50 focus:ring-blue-500',
    secondary: 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 focus:ring-zinc-600',
    danger:    'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 focus:ring-red-500',
    ghost:     'bg-transparent hover:bg-zinc-800/50 text-zinc-400 hover:text-zinc-200 shadow-none',
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  )
}

export function Badge({ children, color = 'zinc' }) {
  const colorMap = {
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    red:   'bg-rose-500/10 text-rose-400 border-rose-500/20',
    yellow:'bg-amber-500/10 text-amber-400 border-amber-500/20',
    blue:  'bg-blue-500/10 text-blue-400 border-blue-500/20',
    zinc:  'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${colorMap[color] || colorMap.zinc}`}>
      {children}
    </span>
  )
}

export function KpiCard({ label, value, sub, color = 'text-zinc-100' }) {
  return (
    <Card className="p-5 flex flex-col justify-center">
      <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1">{label}</h4>
      <div className={`text-2xl font-bold tracking-tight ${color}`}>{value}</div>
      {sub && <p className="text-[11px] text-zinc-500 mt-1 font-medium">{sub}</p>}
    </Card>
  )
}

export function Spinner({ size = 24, className = 'text-blue-500' }) {
  return (
    <div className="flex justify-center items-center p-4">
      <Loader2 size={size} className={`animate-spin ${className}`} />
    </div>
  )
}

export function EmptyState({ message = 'No data yet.', icon: Icon = Inbox }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-zinc-800/50 flex items-center justify-center mb-4 border border-zinc-700/50">
        <Icon size={32} className="text-zinc-500" strokeWidth={1.5} />
      </div>
      <h3 className="text-sm font-medium text-zinc-300">{message}</h3>
    </div>
  )
}

export function LogViewer({ logs = [] }) {
  return (
    <div className="bg-[#0c0c0e] rounded-xl border border-zinc-800 p-4 font-mono text-[11px] text-zinc-300 h-[250px] overflow-y-auto leading-relaxed shadow-inner">
      {logs.map((l, i) => (
        <div key={i} className="mb-1 flex gap-3 hover:bg-zinc-800/30 px-1 rounded">
          <span className="text-zinc-600 shrink-0">{new Date(l.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          <span className={l.log_line.includes('ERROR') ? 'text-rose-400' : 'text-zinc-300'}>{l.log_line}</span>
        </div>
      ))}
      {logs.length === 0 && (
        <div className="h-full flex flex-col items-center justify-center text-zinc-600">
          <Terminal size={24} className="mb-2 opacity-50" />
          <p>Waiting for logs...</p>
        </div>
      )}
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-zinc-400 mt-1.5 font-medium">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  )
}

export function Pagination({ currentPage = 1, totalCount = 0, pageSize = 50, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  return (
    <div className="flex flex-wrap items-center justify-center sm:justify-between gap-3 px-4 py-3 border-t border-zinc-800/80 bg-zinc-900/30">
      <p className="text-xs text-zinc-500 font-medium">
        Showing <span className="text-zinc-300">{(currentPage - 1) * pageSize + 1}</span> to <span className="text-zinc-300">{Math.min(currentPage * pageSize, totalCount)}</span> of <span className="text-zinc-300">{totalCount}</span>
      </p>
      <div className="flex gap-2">
        <Button 
          variant="secondary" 
          size="sm" 
          disabled={currentPage === 1} 
          onClick={() => onPageChange(currentPage - 1)}
          className="px-2"
        >
          <ChevronLeft size={16} />
        </Button>
        <div className="flex items-center px-3 text-xs font-semibold text-zinc-400">
          Page {currentPage} of {totalPages}
        </div>
        <Button 
          variant="secondary" 
          size="sm" 
          disabled={currentPage === totalPages} 
          onClick={() => onPageChange(currentPage + 1)}
          className="px-2"
        >
          <ChevronRight size={16} />
        </Button>
      </div>
    </div>
  )
}

export { DateFilter } from './DateFilter'

