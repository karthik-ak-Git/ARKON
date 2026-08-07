import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  GitBranch,
  Bot,
  Activity,
  Puzzle,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Workflows', href: '/workflows', icon: GitBranch },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Plugins', href: '/plugins', icon: Puzzle },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-card transition-all duration-200',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex h-16 items-center justify-between px-4 border-b">
        {!collapsed && <h1 className="text-xl font-bold text-primary">ARKON</h1>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md hover:bg-accent transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-1 overflow-y-auto" aria-label="Main navigation">
        {navigation.map((item) => {
          const isActive =
            location.pathname === item.href ||
            (item.href !== '/' && location.pathname.startsWith(item.href))

          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive: active }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  active
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  collapsed && 'justify-center'
                )
              }
              title={collapsed ? item.name : undefined}
              aria-current={isActive ? 'page' : undefined}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          )
        })}
      </nav>

      <div className="p-2 border-t">
        {!collapsed && <div className="text-xs text-muted-foreground text-center">v1.0.0</div>}
      </div>
    </aside>
  )
}
