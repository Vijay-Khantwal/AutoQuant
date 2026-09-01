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
