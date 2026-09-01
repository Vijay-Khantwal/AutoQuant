import { Card, CardHeader, CardBody, PageHeader } from '../components/ui'
import { Key, Settings2, ReceiptText } from 'lucide-react'

export default function Settings() {
  const fields = [
    { label: 'TAVILY_API_KEY',    hint: 'Web search provider' },
    { label: 'NVIDIA_API_KEY',   hint: 'NVIDIA NIM — Tier 1 & Tier 2 LLMs' },
    { label: 'WORKER_MODEL',     hint: 'Tier 1 model (StepFun 3.7 Flash)' },
    { label: 'AUDITOR_MODEL',    hint: 'Tier 2 model (Nemotron 120B)' },
    { label: 'DHAN_CLIENT_ID',   hint: 'Dhan Sandbox client ID' },
    { label: 'DHAN_ACCESS_TOKEN',hint: 'Dhan JWT access token' },
  ]

  return (
    <div>
      <PageHeader title="Settings" subtitle="Configuration reference — keys are loaded from the .env file" />

      <div className="space-y-6 max-w-3xl">
        <Card>
          <CardHeader 
            title={<div className="flex items-center gap-2"><Key size={18} className="text-zinc-400" /> API Keys</div>} 
            subtitle="Edit backend/.env to change these values. Restart Django after changes." 
          />
          <CardBody className="space-y-4">
            {fields.map(f => (
              <div key={f.label}>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">{f.label}</label>
                <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                  <input
                    type="password"
                    defaultValue="••••••••••••••••"
                    disabled
                    className="flex-1 bg-zinc-950/50 border border-zinc-800/80 rounded-xl px-4 py-2.5 text-sm text-zinc-400 font-mono focus:outline-none"
                  />
                  <span className="text-xs text-zinc-500 sm:w-1/3 shrink-0">{f.hint}</span>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader 
            title={<div className="flex items-center gap-2"><Settings2 size={18} className="text-zinc-400" /> Trading Parameters</div>} 
            subtitle="These legacy values are globally defined in backend/config/settings.py" 
          />
          <CardBody>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
              {[
                ['Capital per trade', '₹15,000'],
                ['Top N candidates', '5'],
                ['Exchange', 'NSE Equity (CNC)'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-zinc-800/80 pb-3">
                  <span className="text-zinc-400 font-medium">{k}</span>
                  <span className="font-semibold text-zinc-200">{v}</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader 
            title={<div className="flex items-center gap-2"><ReceiptText size={18} className="text-zinc-400" /> Fee Profiles</div>} 
            subtitle="All profiles use identical statutory charges; only brokerage differs" 
          />
          <CardBody className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs font-semibold uppercase tracking-wider text-zinc-500 text-left border-b border-zinc-800/80">
                  <th className="pb-3 px-2">Broker</th>
                  <th className="pb-3 px-2">Brokerage</th>
                  <th className="pb-3 px-2">STT</th>
                  <th className="pb-3 px-2">GST</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['Zerodha', '₹20 or 0.03% (lower)', '0.1% sell', '18% on brokerage'],
                  ['Dhan',    '₹20 or 0.03% (lower)', '0.1% sell', '18% on brokerage'],
                  ['Groww',   '₹20 flat',              '0.1% sell', '18% on brokerage'],
                  ['Angel',   '₹20 flat',              '0.1% sell', '18% on brokerage'],
                ].map(([b, ...rest]) => (
                  <tr key={b} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 transition-colors">
                    <td className="py-3 px-2 font-medium text-zinc-200">{b}</td>
                    {rest.map((c, i) => <td key={i} className="py-3 px-2 text-zinc-400">{c}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
