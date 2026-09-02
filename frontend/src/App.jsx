import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import ToastManager from './components/layout/ToastManager'
import GlobalTaskMonitor from './components/layout/GlobalTaskMonitor'
import Dashboard      from './pages/Dashboard'
import Signals        from './pages/Signals'
import AuditDossier   from './pages/AuditDossier'
import Portfolio      from './pages/Portfolio'
import Orders         from './pages/Orders'
import Execution      from './pages/Execution'
import ModelManagement from './pages/ModelManagement'
import Settings       from './pages/Settings'

import Login          from './pages/Login'
import { Navigate } from 'react-router-dom'

const EnvironmentBadge = () => {
  // Default to env var if not set in local storage
  const stored = localStorage.getItem('USE_AZURE');
  if (stored === null) {
    localStorage.setItem('USE_AZURE', (import.meta.env.VITE_BACKEND === 'AZURE').toString());
  }
  const isAzure = localStorage.getItem('USE_AZURE') === 'true';

  const toggleEnv = () => {
    localStorage.setItem('USE_AZURE', (!isAzure).toString());
    window.location.reload();
  };
  
  return (
    <div 
      onDoubleClick={toggleEnv}
      title="Double click to toggle environment"
      className={`cursor-pointer fixed top-3 left-1/2 -translate-x-1/2 z-[9999] px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest shadow-lg border backdrop-blur-sm flex items-center gap-2 ${isAzure ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'}`}>
      <span className={`w-2 h-2 rounded-full animate-pulse ${isAzure ? 'bg-blue-400' : 'bg-emerald-400'}`}></span>
      {isAzure ? 'AZURE CLOUD' : 'LOCAL TEST'}
    </div>
  )
}

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')
  if (!token) return <Navigate to="/login" replace />
  return (
    <div className="flex min-h-screen bg-gray-950 text-gray-100">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        {children}
      </main>
      <GlobalTaskMonitor />
      
      <ToastManager />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <EnvironmentBadge />
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/*" element={
          <ProtectedRoute>
            <Routes>
              <Route path="/"          element={<Dashboard />} />
              <Route path="/signals"   element={<Signals />} />
              <Route path="/audit"     element={<AuditDossier />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/orders"    element={<Orders />} />
              <Route path="/execute"   element={<Execution />} />
              <Route path="/model"     element={<ModelManagement />} />
              <Route path="/settings"  element={<Settings />} />
            </Routes>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}

