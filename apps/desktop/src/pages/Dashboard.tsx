import { FolderKanban, GitBranch, Bot, Activity, Puzzle, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkspaces } from '@/api/hooks'
import { useHealth } from '@/api/hooks'

export function Dashboard() {
  const { data: workspaces, isLoading: wsLoading } = useWorkspaces()
  const { data: health } = useHealth()

  const workspaceCount = (workspaces?.active?.length ?? 0) + (workspaces?.available?.length ?? 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your ARKON workspace</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
          <Plus className="h-4 w-4" />
          New Project
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Workspaces', value: wsLoading ? '...' : String(workspaceCount), icon: FolderKanban, color: 'text-blue-500' },
          { label: 'Backend', value: health?.status === 'ok' ? 'Online' : 'Offline', icon: Activity, color: health?.status === 'ok' ? 'text-green-500' : 'text-red-500' },
          { label: 'Version', value: health?.version ?? '—', icon: GitBranch, color: 'text-purple-500' },
          { label: 'Environment', value: health?.environment ?? '—', icon: Bot, color: 'text-orange-500' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg border bg-card p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
              </div>
              <div className={cn('p-3 rounded-full', stat.color)}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border bg-card">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Workspaces</h2>
          </div>
          <div className="divide-y">
            {wsLoading ? (
              <div className="p-4 text-sm text-muted-foreground">Loading...</div>
            ) : (workspaces?.active?.length ?? 0) === 0 ? (
              <div className="p-4 text-sm text-muted-foreground">No workspaces yet. Create one to get started.</div>
            ) : (
              workspaces?.active?.map((ws) => (
                <div key={ws.id} className="p-4 hover:bg-accent/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                        <FolderKanban className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium">{ws.name}</p>
                        <p className="text-sm text-muted-foreground">{ws.state}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { name: 'Projects', icon: FolderKanban, href: '/projects' },
              { name: 'Workflows', icon: GitBranch, href: '/workflows' },
              { name: 'Agents', icon: Bot, href: '/agents' },
              { name: 'Plugins', icon: Puzzle, href: '/plugins' },
            ].map((action) => (
              <a
                key={action.name}
                href={action.href}
                className="flex items-center gap-3 p-4 rounded-lg border hover:bg-accent/50 transition-colors"
              >
                <action.icon className="h-5 w-5 text-muted-foreground" />
                <span className="font-medium">{action.name}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
