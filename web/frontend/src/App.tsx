import { useState } from 'react'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './components/dashboard/Dashboard'
import ConfigPage from './components/config/ConfigPage'
import HistoryPage from './components/history/HistoryPage'
import type { Page } from './types'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')

  return (
    <AppLayout currentPage={page} onNavigate={setPage}>
      {page === 'dashboard' && <Dashboard />}
      {page === 'config' && <ConfigPage />}
      {page === 'history' && <HistoryPage />}
    </AppLayout>
  )
}
