import re
import os

base_dir = r"c:\Users\vkhan\OneDrive\Desktop\TradeTest\frontend\src\pages"

def edit_signals():
    path = os.path.join(base_dir, "Signals.jsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Imports
    content = content.replace(
        "import { PageHeader, Card, CardHeader, CardBody, Button, Badge, Spinner, EmptyState } from '../components/ui'",
        "import { PageHeader, Card, CardHeader, CardBody, Button, Badge, Spinner, EmptyState, Pagination } from '../components/ui'\nimport { Play, Activity } from 'lucide-react'"
    )
    
    # State
    content = content.replace(
        "  const [loading, setLoading] = useState(true)",
        "  const [loading, setLoading] = useState(true)\n  const [runsPage, setRunsPage] = useState(1)\n  const [runsTotal, setRunsTotal] = useState(0)\n  const [signalsPage, setSignalsPage] = useState(1)\n  const [signalsTotal, setSignalsTotal] = useState(0)"
    )
    
    # loadRuns
    content = content.replace(
        "getSignalRuns({ strategy_id: selectedStrategyId }).then(r => {",
        "getSignalRuns({ strategy_id: selectedStrategyId, page: runsPage }).then(r => {"
    )
    content = content.replace(
        "const list = r.data.results || r.data\n      setRuns(list)",
        "const list = r.data.results || r.data\n      setRuns(list)\n      setRunsTotal(r.data.count || list.length)"
    )
    
    # loadRuns dependencies
    content = content.replace(
        "useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId])",
        "useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId, runsPage])"
    )
    
    # getRunSignals
    content = content.replace(
        "getRunSignals(selectedRun.id).then(r => setSignals(r.data))",
        "getRunSignals(selectedRun.id, { page: signalsPage }).then(r => {\n        setSignals(r.data.results || r.data)\n        setSignalsTotal(r.data.count || (r.data.results ? r.data.results.length : r.data.length))\n      })"
    )
    
    # getRunSignals dependencies
    content = content.replace(
        "}, [selectedRun])",
        "}, [selectedRun, signalsPage])"
    )
    
    # Icons
    content = content.replace(
        "{isRunning ? 'Running...' : 'Run Prediction'}",
        "{isRunning ? <><Spinner /> Running...</> : <><Play size={16} className=\"mr-2 inline\" /> Run Prediction</>}"
    )
    
    # Pagination UI for runs
    content = content.replace(
        "</div>\n\n        <Card className=\"flex-1\">",
        "  {runsTotal > 0 && <div className=\"mt-4\"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}\n        </div>\n\n        <Card className=\"flex-1\">"
    )
    
    # Pagination UI for signals
    content = content.replace(
        "</tbody>\n                </table>\n              </div>\n              )}",
        "</tbody>\n                </table>\n                {signalsTotal > 0 && <div className=\"p-4 border-t border-gray-800\"><Pagination totalCount={signalsTotal} currentPage={signalsPage} onPageChange={setSignalsPage} /></div>}\n              </div>\n              )}"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def edit_audit():
    path = os.path.join(base_dir, "AuditDossier.jsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    content = content.replace(
        "import { PageHeader, Button, Badge, Spinner, EmptyState } from '../components/ui'",
        "import { PageHeader, Button, Badge, Spinner, EmptyState, Pagination } from '../components/ui'\nimport { ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react'"
    )
    
    content = content.replace(
        "{expanded ? '▲' : '▼'}",
        "{expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}"
    )
    
    content = content.replace(
        "const [loading, setLoading] = useState(true)",
        "const [loading, setLoading] = useState(true)\n  const [runsPage, setRunsPage] = useState(1)\n  const [runsTotal, setRunsTotal] = useState(0)"
    )
    
    content = content.replace(
        "getResearchRuns({ strategy_id: selectedStrategyId }).then(r => {",
        "getResearchRuns({ strategy_id: selectedStrategyId, page: runsPage }).then(r => {"
    )
    content = content.replace(
        "const list = r.data.results || r.data\n      setRuns(list)",
        "const list = r.data.results || r.data\n      setRuns(list)\n      setRunsTotal(r.data.count || list.length)"
    )
    
    content = content.replace(
        "useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId])",
        "useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId, runsPage])"
    )
    
    content = content.replace(
        "{isRunning ? 'Running...' : 'Run Audit'}",
        "{isRunning ? <><Spinner /> Running...</> : <><ShieldCheck size={16} className=\"mr-2 inline\" /> Run Audit</>}"
    )
    
    content = content.replace(
        "</div>\n\n        <div className=\"flex-1\">",
        "  {runsTotal > 0 && <div className=\"mt-4\"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}\n        </div>\n\n        <div className=\"flex-1\">"
    )
    
    content = content.replace("gray-", "zinc-")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def edit_execution():
    path = os.path.join(base_dir, "Execution.jsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        "import { PageHeader, Card, Button, Badge, Spinner, EmptyState } from '../components/ui'",
        "import { PageHeader, Card, Button, Badge, Spinner, EmptyState, Pagination } from '../components/ui'\nimport { Zap } from 'lucide-react'"
    )
    
    content = content.replace(
        "const [loading, setLoading] = useState(true)",
        "const [loading, setLoading] = useState(true)\n  const [runsPage, setRunsPage] = useState(1)\n  const [runsTotal, setRunsTotal] = useState(0)"
    )
    
    content = content.replace(
        "const r = await getResearchRuns({ strategy_id: selectedStrategyId })",
        "const r = await getResearchRuns({ strategy_id: selectedStrategyId, page: runsPage })"
    )
    content = content.replace(
        "const list = r.data.results || r.data\n      setRuns(list)",
        "const list = r.data.results || r.data\n      setRuns(list)\n      setRunsTotal(r.data.count || list.length)"
    )
    
    content = content.replace(
        "useEffect(() => { loadRuns() }, [selectedStrategyId])",
        "useEffect(() => { loadRuns() }, [selectedStrategyId, runsPage])"
    )
    
    content = content.replace(
        "Executing...' : `Execute ${Object.values(selected).filter(Boolean).length} Trades`}",
        "Executing...' : <><Zap size={16} className=\"mr-2 inline\" /> Execute ${Object.values(selected).filter(Boolean).length} Trades</>}"
    )
    
    content = content.replace(
        "</div>\n\n        <div className=\"flex-1\">",
        "  {runsTotal > 0 && <div className=\"mt-4\"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}\n        </div>\n\n        <div className=\"flex-1\">"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def edit_model():
    path = os.path.join(base_dir, "ModelManagement.jsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        "import { PageHeader, Card, CardHeader, CardBody, Button, Badge, Spinner, EmptyState, LogViewer } from '../components/ui'",
        "import { PageHeader, Card, CardHeader, CardBody, Button, Badge, Spinner, EmptyState, LogViewer, Pagination } from '../components/ui'\nimport { Cpu } from 'lucide-react'"
    )
    
    content = content.replace(
        "const [loading, setLoading] = useState(true)",
        "const [loading, setLoading] = useState(true)\n  const [runsPage, setRunsPage] = useState(1)\n  const [runsTotal, setRunsTotal] = useState(0)"
    )
    
    content = content.replace(
        "getModelRuns({ strategy_id: selectedStrategyId }).then(r => {",
        "getModelRuns({ strategy_id: selectedStrategyId, page: runsPage }).then(r => {"
    )
    
    content = content.replace(
        "const list = r.data.results || r.data\n      setRuns(list)",
        "const list = r.data.results || r.data\n      setRuns(list)\n      setRunsTotal(r.data.count || list.length)"
    )
    
    content = content.replace(
        "useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId])",
        "useEffect(() => { loadRuns().finally(() => setLoading(false)) }, [selectedStrategyId, runsPage])"
    )
    
    content = content.replace(
        "{isRunning ? 'Running...' : 'Retrain Model'}",
        "{isRunning ? <><Spinner /> Running...</> : <><Cpu size={16} className=\"mr-2 inline\" /> Retrain Model</>}"
    )
    
    content = content.replace(
        "</CardBody>\n          </Card>",
        "  {runsTotal > 0 && <div className=\"p-4 border-t border-gray-800\"><Pagination totalCount={runsTotal} currentPage={runsPage} onPageChange={setRunsPage} /></div>}\n            </CardBody>\n          </Card>"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

edit_signals()
edit_audit()
edit_execution()
edit_model()
