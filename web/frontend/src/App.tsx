import { useCallback, useEffect, useState } from 'react'
import { getToken, setToken, clearToken, setOnAuthError } from './api/client'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './components/LoginPage'
import Dashboard from './components/dashboard/Dashboard'
import ConfigPage from './components/config/ConfigPage'
import HistoryPage from './components/history/HistoryPage'
import type { Page } from './types'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [token, setTokenState] = useState<string | null>(getToken)

  const handleLogout = useCallback(() => {
    clearToken()
    setTokenState(null)
  }, [])

  useEffect(() => {
    setOnAuthError(handleLogout)
  }, [handleLogout])

  const handleLogin = useCallback((newToken: string) => {
    setToken(newToken)
    setTokenState(newToken)
  }, [])

  if (!token) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <AppLayout currentPage={page} onNavigate={setPage} onLogout={handleLogout}>
      {page === 'dashboard' && <Dashboard />}
      {page === 'config' && <ConfigPage />}
      {page === 'history' && <HistoryPage />}
    </AppLayout>
  )
}
