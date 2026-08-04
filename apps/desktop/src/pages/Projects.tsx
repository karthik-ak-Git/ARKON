import { Plus, Search, Filter, MoreVertical, FolderKanban, FileText, Clock, CheckCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

const projects = [
  { id: 1, name: 'Video Editing Pipeline', description: 'Automated video editing workflow', status: 'active', workflows: 5, agents: 3, updated: '2 hours ago' },
  { id: 2, name: 'Data Processing Flow', description: 'ETL pipeline for analytics', status: 'active', workflows: 3, agents: 2, updated: '1 day ago' },
  { id: 3, name: 'Research Assistant', description: 'AI-powered research automation', status: 'draft', workflows: 2, agents: 4, updated: '3 days ago' },
  { id: 4, name: 'Code Review Bot', description: 'Automated code review system', status: 'archived', workflows: 1, agents: 1, updated: '1 week ago' },
]

export function Projects() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">Manage your AI agent projects</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
          <Plus className="h-4 w-4" />
          New Project
        </button>
      </div>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input type="search" placeholder="Search projects..." className="w-full h-10 pl-10 pr-4 rounded-lg border bg-background outline-none focus:ring-2 focus:ring-ring" />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors">
          <Filter className="h-4 w-4" />
          Filters
        </button>
      </div>
      
      <div className="rounded-lg border bg-card overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Project</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Workflows</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Agents</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Last Updated</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {projects.map((project) => (
              <tr key={project.id} className="hover:bg-accent/50 transition-colors">
                <td className="px-4 py-4">
                  <div className="flex items-center gap-3">
                    <FolderKanban className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{project.name}</p>
                      <p className="text-sm text-muted-foreground">{project.description}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <span className={cn(
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    project.status === 'active' && 'bg-green-100 text-green-800',
                    project.status === 'draft' && 'bg-yellow-100 text-yellow-800',
                    project.status === 'archived' && 'bg-gray-100 text-gray-800'
                  )}>
                    {project.status}
                  </span>
                </td>
                <td className="px-4 py-4 text-sm">{project.workflows}</td>
                <td className="px-4 py-4 text-sm">{project.agents}</td>
                <td className="px-4 py-4 text-sm text-muted-foreground">{project.updated}</td>
                <td className="px-4 py-4">
                  <button className="p-1 rounded hover:bg-accent transition-colors" aria-label="More options">
                    <MoreVertical className="h-4 w-4 text-muted-foreground" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}