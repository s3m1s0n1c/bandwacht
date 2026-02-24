import { LogOut, Menu, Wifi, WifiOff } from 'lucide-react'
import { UI } from '../../utils/strings'
import type { Page } from '../../types'

interface HeaderProps {
  currentPage: Page
  isConnected: boolean
  onMenuToggle: () => void
  onLogout: () => void
}

const pageTitles: Record<Page, string> = {
  dashboard: UI.nav_dashboard,
  config: UI.nav_config,
  history: UI.nav_history,
}

export default function Header({ currentPage, isConnected, onMenuToggle, onLogout }: HeaderProps) {
  return (
    <header className="h-14 bg-sdr-surface border-b border-sdr-border flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="lg:hidden text-sdr-muted hover:text-sdr-text transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h2 className="text-lg font-semibold">{pageTitles[currentPage]}</h2>
      </div>

      <div className="flex items-center gap-3">
        {isConnected ? (
          <div className="flex items-center gap-1.5 text-sdr-green text-xs">
            <Wifi className="w-3.5 h-3.5" />
            <span>{UI.dash_connected}</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-sdr-muted text-xs">
            <WifiOff className="w-3.5 h-3.5" />
            <span>{UI.dash_disconnected}</span>
          </div>
        )}
        <button
          onClick={onLogout}
          className="text-sdr-muted hover:text-sdr-red transition-colors"
          title={UI.auth_logout}
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
