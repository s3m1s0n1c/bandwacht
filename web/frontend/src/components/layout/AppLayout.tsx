import { useCallback, useEffect, useState } from 'react'
import { health } from '../../api/client'
import Sidebar from './Sidebar'
import Header from './Header'
import type { Page } from '../../types'

interface AppLayoutProps {
  currentPage: Page
  onNavigate: (page: Page) => void
  children: React.ReactNode
}

export default function AppLayout({ currentPage, onNavigate, children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [backendConnected, setBackendConnected] = useState(false)

  const checkHealth = useCallback(async () => {
    try {
      await health()
      setBackendConnected(true)
    } catch {
      setBackendConnected(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [checkHealth])

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 lg:static lg:z-auto
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <Sidebar
          currentPage={currentPage}
          onNavigate={(page) => {
            onNavigate(page)
            setSidebarOpen(false)
          }}
        />
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          currentPage={currentPage}
          isConnected={backendConnected}
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
        />
        <main className="flex-1 overflow-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
