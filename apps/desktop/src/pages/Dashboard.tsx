import { 
  FolderKanban, 
  GitBranch, 
  Bot, 
  Activity, 
  Puzzle, 
  Settings,
  Plus,
  Search,
  Filter
} from 'lucide-react'
import { cn } from '@/lib/utils'

const stats = [
  { label: 'Projects', value: '12', icon: FolderKanban, color: 'text-blue-500' },
  { label: 'Workflows', value: '48', icon: GitBranch, color: 'text-purple-500' },
  { label: 'Active Agents', value: '7', icon: Bot, color: 'text-green-500' },
  { label: 'Tasks Completed', value: '1,234', icon: Activity, color: 'text-orange-500' },
]

const recentActivity = [
  { id: 1, type: 'project', action: 'Created', target: 'Video Editing Pipeline', time: '2 min ago' },
  { id: 2, type: 'workflow', action: 'Started', target: 'Data Processing Flow', time: '15 min ago' },
  { id: 3, type: 'agent', action: 'Spawned', target: 'Research Agent #3', time: '1 hour ago' },
  { id: 4, type: 'task', action: 'Completed', target: 'Render video segments', time: '2 hours ago' },
  { id: 5, type: 'plugin', action: 'Installed', target: 'Video Editor Plugin v2.1', time: '3 hours ago' },
]

export function Dashboard() {
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
        {stats.map((stat) => (
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
            <h2 className="text-lg font-semibold">Recent Activity</h2>
          </div>
          <div className="divide-y">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="p-4 hover:bg-accent/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn('p-2 rounded-full', 
                      activity.type === 'project' && 'bg-blue-100 text-blue-600',
                      activity.type === 'workflow' && 'bg-purple-100 text-purple-600',
                      activity.type === 'agent' && 'bg-green-100 text-green-600',
                      activity.type === 'task' && 'bg-orange-100 text-orange-600',
                      activity.type === 'plugin' && 'bg-gray-100 text-gray-600'
                    )}>
                      {activity.type === 'project' && <FolderKanban className="h-4 w-4" />}
                      {activity.type === 'workflow' && <GitBranch className="h-4 w-4" />}
                      {activity.type === 'agent' && <Bot className="h-4 w-4" />}
                      {activity.type === 'task' && <Activity className="h-4 w-4" />}
                      {activity.type === 'plugin' && <Puzzle className="h-4 w-4" />}
                    </div>
                    <div>
                      <p className="font-medium">{activity.action} {activity.target}</p>
                      <p className="text-sm text-muted-foreground">{activity.time}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { name: 'Create Project', icon: FolderKanban, href: '/projects' },
              { name: 'Build Workflow', icon: GitBranch, href: '/workflows' },
              { name: 'Spawn Agent', icon: Bot, href: '/agents' },
              { name: 'Install Plugin', icon: Puzzle, href: '/plugins' },
            ].map((action) => (
              <a key={action.name} href={action.href} className="flex items-center gap-3 p-4 rounded-lg border hover:bg-accent/50 transition-colors">
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