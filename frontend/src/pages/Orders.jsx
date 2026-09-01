import { useEffect, useState } from 'react'
import { PageHeader, Card, Button, Badge, Spinner } from '../components/ui'
import { RefreshCw } from 'lucide-react'
import { getOrders, getLiveOrders } from '../api/execution'

const statusColor = s => ({ TRANSIT: 'yellow', PENDING: 'blue', TRADED: 'green', REJECTED: 'red', ERROR: 'red', CANCELLED: 'gray' }[s] || 'gray')

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [liveOrders, setLiveOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('db')

  useEffect(() => {
    getOrders().then(r => setOrders(r.data.results || r.data)).finally(() => setLoading(false))
  }, [])

  const refreshLive = () =>
    getLiveOrders().then(r => setLiveOrders(r.data.orders || []))

  const list = tab === 'db' ? orders : liveOrders

  return (
    <div>
      <PageHeader
        title="Order History"
        subtitle="All orders placed via Dhan Sandbox"
        actions={<Button onClick={refreshLive} ><RefreshCw size={16} /> Refresh Live</Button>}
      />

      <div className="flex gap-2 mb-4">
        <button onClick={() => setTab('db')} className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${tab === 'db' ? 'bg-emerald-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>
          DB Orders ({orders.length})
        </button>
        <button onClick={() => { setTab('live'); refreshLive() }} className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${tab === 'live' ? 'bg-emerald-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>
          Live Dhan Orders ({liveOrders.length})
        </button>
      </div>

      <Card>
        {loading ? <Spinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-400 border-b border-gray-700 text-left">
                  {['Ticker', 'Type', 'Qty', 'Price ₹', 'Alloc ₹', 'Dhan ID', 'Status',
                    'Fee Zerodha', 'Fee Dhan', 'Fee Groww', 'Fee Angel', 'Time'].map(h =>
                    <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {list.map((o, i) => (
                  <tr key={o.id || i} className="border-b border-gray-800 hover:bg-gray-800/40">
                    <td className="px-4 py-3 font-medium">{(o.ticker || o.tradingSymbol || 'â€”').replace('.NS','')}</td>
                    <td className="px-4 py-3"><Badge color={o.transaction_type === 'BUY' ? 'green' : 'red'}>{o.transaction_type || o.transactionType}</Badge></td>
                    <td className="px-4 py-3">{o.quantity}</td>
                    <td className="px-4 py-3">₹{Number(o.price || o.price || 0).toFixed(2)}</td>
                    <td className="px-4 py-3">₹{Number(o.allocated_inr || 0).toFixed(0)}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{o.dhan_order_id || o.orderId || 'â€”'}</td>
                    <td className="px-4 py-3"><Badge color={statusColor(o.dhan_status || o.orderStatus)}>{o.dhan_status || o.orderStatus}</Badge></td>
                    <td className="px-4 py-3 text-gray-300">₹{Number(o.fee_zerodha || 0).toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-300">₹{Number(o.fee_dhan || 0).toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-300">₹{Number(o.fee_groww || 0).toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-300">₹{Number(o.fee_angel || 0).toFixed(2)}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{o.created_at ? new Date(o.created_at).toLocaleString('en-IN') : 'â€”'}</td>
                  </tr>
                ))}
                {list.length === 0 && <tr><td colSpan={12} className="text-center py-10 text-gray-500">No orders yet</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}


