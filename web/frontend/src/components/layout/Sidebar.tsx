import { Radio, Settings, BookOpen, Activity } from 'lucide-react'
import { UI } from '../../utils/strings'
import type { Page } from '../../types'

interface SidebarProps {
  currentPage: Page
  onNavigate: (page: Page) => void
}

const navItems: { page: Page; label: string; icon: typeof Radio }[] = [
  { page: 'dashboard', label: UI.nav_dashboard, icon: Activity },
  { page: 'config', label: UI.nav_config, icon: Settings },
  { page: 'history', label: UI.nav_history, icon: BookOpen },
]

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <aside className="w-60 bg-sdr-surface border-r border-sdr-border flex flex-col shrink-0">
      {/* Logo */}
      <div className="p-4 border-b border-sdr-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sdr-cyan/10 flex items-center justify-center">
            <Radio className="w-5 h-5 text-sdr-cyan" />
          </div>
          <div>
            <h1 className="text-base font-bold text-sdr-text">{UI.app_title}</h1>
            <p className="text-xs text-sdr-muted">{UI.app_subtitle}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ page, label, icon: Icon }) => (
          <button
            key={page}
            onClick={() => onNavigate(page)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              currentPage === page
                ? 'bg-sdr-cyan/10 text-sdr-cyan'
                : 'text-sdr-muted hover:text-sdr-text hover:bg-sdr-border/30'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-sdr-border">
        <p className="text-xs text-sdr-muted">BandWacht v0.1.0</p>
        <p className="text-xs text-sdr-muted">73 de OE8YML</p>
      </div>
    </aside>
  )
}
