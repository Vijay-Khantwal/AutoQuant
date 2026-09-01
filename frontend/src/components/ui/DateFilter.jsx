import { useEffect } from 'react'
import { Calendar, X, ChevronLeft, ChevronRight } from 'lucide-react'
import { useDateStore } from '../../store/appStore'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'

export function DateFilter() {
  const { startDate, endDate, isSingleDay, setDateRange, toggleSingleDay } = useDateStore()

  useEffect(() => {
    if (isSingleDay && startDate !== endDate) {
      setDateRange(startDate, startDate)
    }
  }, [isSingleDay, startDate, endDate, setDateRange])

  const parseDate = (dStr) => {
    if (!dStr) return null
    const [y, m, d] = dStr.split('-')
    return new Date(y, m - 1, d)
  }

  const formatDate = (dateObj) => {
    if (!dateObj) return ''
    const d = new Date(dateObj)
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const setPreset = (daysBack) => {
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - daysBack)
    
    const fEnd = formatDate(end)
    const fStart = formatDate(start)
    
    toggleSingleDay(daysBack === 0)
    setDateRange(fStart, daysBack === 0 ? fStart : fEnd)
  }

  const glideDays = (offset) => {
    if (!startDate) return
    const start = parseDate(startDate)
    start.setDate(start.getDate() + offset)
    const newStart = formatDate(start)
    
    let newEnd = endDate
    if (endDate && !isSingleDay) {
      const end = parseDate(endDate)
      end.setDate(end.getDate() + offset)
      newEnd = formatDate(end)
    } else {
      newEnd = newStart
    }
    
    setDateRange(newStart, newEnd)
  }

  const clear = () => {
    toggleSingleDay(false)
    setDateRange('', '')
  }

  return (
    <div className="flex flex-wrap items-center gap-3 bg-zinc-900/50 p-2 rounded-lg border border-zinc-800">
      <div className="flex items-center gap-2 text-zinc-400">
        <Calendar size={16} />
        <span className="text-xs font-medium uppercase tracking-wider hidden sm:inline">Date</span>
      </div>
      
      {isSingleDay && (
        <div className="flex items-center gap-1 border-l border-zinc-800 pl-2">
          <button onClick={() => glideDays(-1)} className="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors" title="Previous Day">
            <ChevronLeft size={16} />
          </button>
          <button onClick={() => glideDays(1)} className="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors mr-1" title="Next Day">
            <ChevronRight size={16} />
          </button>
        </div>
      )}
      
      <div className="flex items-center gap-2 datepicker-dark">
        <DatePicker
          selected={parseDate(startDate)}
          onChange={(date) => setDateRange(formatDate(date), isSingleDay ? formatDate(date) : endDate)}
          dateFormat="yyyy-MM-dd"
          placeholderText={isSingleDay ? "Select Date" : "Start Date"}
          className="bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500 transition-colors w-28 cursor-pointer text-center"
        />
        
        {!isSingleDay && <span className="text-zinc-600">-</span>}
        
        {!isSingleDay && (
          <DatePicker
            selected={parseDate(endDate)}
            onChange={(date) => setDateRange(startDate, formatDate(date))}
            dateFormat="yyyy-MM-dd"
            placeholderText="End Date"
            minDate={parseDate(startDate)}
            className="bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500 transition-colors w-28 cursor-pointer text-center"
          />
        )}
      </div>

      <div className="flex items-center gap-2 border-l border-zinc-800 pl-3">
        <label className="flex items-center gap-2 cursor-pointer text-sm text-zinc-300">
          <input 
            type="checkbox" 
            checked={isSingleDay} 
            onChange={(e) => toggleSingleDay(e.target.checked)}
            className="accent-emerald-500"
          />
          Single Day
        </label>
      </div>

      <div className="flex items-center gap-1 border-l border-zinc-800 pl-3 hidden md:flex">
        <button onClick={() => setPreset(0)} className="px-2 py-1 text-xs rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors">Today</button>
        <button onClick={() => setPreset(7)} className="px-2 py-1 text-xs rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors">7d</button>
      </div>

      {(startDate || endDate) && (
        <button onClick={clear} className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded bg-zinc-800 text-zinc-400 hover:text-red-400 hover:bg-red-950/30 transition-colors ml-auto border border-zinc-700/50">
          <X size={14} /> Clear Filter
        </button>
      )}
      
      <style>{`
        .datepicker-dark .react-datepicker {
          background-color: #18181b;
          border: 1px solid #27272a;
          color: #e4e4e7;
          font-family: inherit;
        }
        .datepicker-dark .react-datepicker__header {
          background-color: #09090b;
          border-bottom: 1px solid #27272a;
        }
        .datepicker-dark .react-datepicker__current-month, 
        .datepicker-dark .react-datepicker-time__header, 
        .datepicker-dark .react-datepicker-year-header {
          color: #e4e4e7;
        }
        .datepicker-dark .react-datepicker__day-name, 
        .datepicker-dark .react-datepicker__day, 
        .datepicker-dark .react-datepicker__time-name {
          color: #a1a1aa;
        }
        .datepicker-dark .react-datepicker__day:hover, 
        .datepicker-dark .react-datepicker__month-text:hover, 
        .datepicker-dark .react-datepicker__quarter-text:hover, 
        .datepicker-dark .react-datepicker__year-text:hover {
          background-color: #27272a;
        }
        .datepicker-dark .react-datepicker__day--selected, 
        .datepicker-dark .react-datepicker__day--in-selecting-range, 
        .datepicker-dark .react-datepicker__day--in-range, 
        .datepicker-dark .react-datepicker__month-text--selected, 
        .datepicker-dark .react-datepicker__month-text--in-selecting-range, 
        .datepicker-dark .react-datepicker__month-text--in-range, 
        .datepicker-dark .react-datepicker__quarter-text--selected, 
        .datepicker-dark .react-datepicker__quarter-text--in-selecting-range, 
        .datepicker-dark .react-datepicker__quarter-text--in-range, 
        .datepicker-dark .react-datepicker__year-text--selected, 
        .datepicker-dark .react-datepicker__year-text--in-selecting-range, 
        .datepicker-dark .react-datepicker__year-text--in-range {
          background-color: #10b981;
          color: #fff;
        }
        .datepicker-dark .react-datepicker__day--keyboard-selected, 
        .datepicker-dark .react-datepicker__month-text--keyboard-selected, 
        .datepicker-dark .react-datepicker__quarter-text--keyboard-selected, 
        .datepicker-dark .react-datepicker__year-text--keyboard-selected {
          background-color: #059669;
          color: #fff;
        }
        .datepicker-dark .react-datepicker-popper[data-placement^=bottom] .react-datepicker__triangle::before, 
        .datepicker-dark .react-datepicker-popper[data-placement^=bottom] .react-datepicker__triangle::after {
          border-bottom-color: #27272a;
        }
        .datepicker-dark .react-datepicker-popper[data-placement^=bottom] .react-datepicker__triangle::after {
          border-bottom-color: #09090b;
        }
      `}</style>
    </div>
  )
}
