import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Signal, Search, Briefcase,
  Activity, PlaySquare, Cpu, Settings, ChevronLeft, ChevronRight, Zap, ChevronDown, Loader2
} from 'lucide-react'
import { useStrategyStore } from '../../store/appStore'
import api from '../../api/client'

const NAV_ITEMS = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard'    },
  { to: '/signals',   icon: Signal,          label: 'Signals'      },
  { to: '/audit',     icon: Search,          label: 'AI Audit'     },
  { to: '/portfolio', icon: Briefcase,       label: 'Portfolio'    },
  { to: '/orders',    icon: Activity,        label: 'Orders'       },
  { to: '/execute',   icon: PlaySquare,      label: 'Execute'      },
  { to: '/model',     icon: Cpu,             label: 'Model'        },
  { to: '/settings',  icon: Settings,        label: 'Settings'     },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [changingTo, setChangingTo] = useState(null)
  const { strategies, setStrategies, selectedStrategyId, setSelectedStrategyId } = useStrategyStore()

  useEffect(() => {
    api.get('/model/strategies/').then(res => {
      const list = res.data.results || res.data
      setStrategies(list)
      if (list.length > 0 && !selectedStrategyId) {
        setSelectedStrategyId(list[0].id)
      }
    }).catch(err => console.error("Failed to load strategies:", err))
  }, [setStrategies, selectedStrategyId, setSelectedStrategyId])

  return (
    <aside
      className={`
        sticky top-0 h-screen flex flex-col bg-zinc-950 border-r border-zinc-800 text-white transition-all duration-300
        ${collapsed ? 'w-16' : 'w-56'}
      `}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-6 border-b border-zinc-800">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400">
          <Zap size={18} className={collapsed ? "" : "animate-pulse"} />
        </div>
        {!collapsed && (
          <div>
            <p className="font-bold text-sm tracking-wide text-zinc-100 uppercase">TradeAgent</p>
            <p className="text-[10px] text-blue-400/80 font-medium tracking-widest uppercase">Swing AI</p>
          </div>
        )}
      </div>

      {/* Strategy Selector */}
      {!collapsed && strategies && strategies.length > 0 && (
        <div className="px-4 py-4 border-b border-zinc-800/80 bg-zinc-900/20 relative">
          <div 
            className="w-full bg-zinc-900 border border-zinc-700/80 hover:border-zinc-600 text-zinc-300 font-medium text-sm rounded-xl py-2.5 pl-4 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all cursor-pointer shadow-sm relative"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            onBlur={() => setTimeout(() => setDropdownOpen(false), 200)}
            tabIndex={0}
          >
            {strategies.find(s => s.id === selectedStrategyId)?.name || 'Select Strategy'} 
            {strategies.find(s => s.id === selectedStrategyId) && ` (${strategies.find(s => s.id === selectedStrategyId).tp_target * 100}%/${(strategies.find(s => s.id === selectedStrategyId).sl_stop * 100).toFixed(0)}%)`}
            
            <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-zinc-500">
              <ChevronDown size={16} />
            </div>
          </div>
          
          {dropdownOpen && (
            <div className="absolute top-[68px] left-4 right-4 bg-zinc-900 border border-zinc-700/80 rounded-xl shadow-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-1">
              {strategies.map(s => (
                <div 
                  key={s.id} 
                  className={`flex items-center justify-between px-4 py-2.5 text-sm cursor-pointer hover:bg-zinc-800 transition-colors ${selectedStrategyId === s.id ? 'bg-blue-600/10 text-blue-400 font-semibold' : 'text-zinc-300'}`}
                  onMouseDown={(e) => {
                      e.preventDefault();
                      setChangingTo(s.id);
                      setTimeout(() => {
                        setSelectedStrategyId(s.id);
                        setDropdownOpen(false);
                        setChangingTo(null);
                      }, 400);
                    }}
                >
                  <span>{s.name} <span className="opacity-70 text-xs ml-1">({s.tp_target * 100}%/{(s.sl_stop * 100).toFixed(0)}%)</span></span>
                    {changingTo === s.id && <Loader2 size={14} className="animate-spin text-blue-400" />}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 py-6 overflow-y-auto space-y-1">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 mx-3 rounded-lg text-sm font-medium transition-all
              ${isActive
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(37,99,235,0.1)]'
                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200 border border-transparent'
              }`
            }
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center py-4 border-t border-zinc-800 text-zinc-500 hover:bg-zinc-800/50 hover:text-white transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  )
}




