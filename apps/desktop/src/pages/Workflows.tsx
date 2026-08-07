import { GitBranch, Loader2 } from 'lucide-react'
import { useRuntimeAgents } from '@/api/hooks'

export function Workflows() {
  const { data: agentList, isLoading } = useRuntimeAgents()
  const agents = agentList?.agents ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Workflows</h1>
        <p className="text-muted-foreground">Manage and monitor your workflows</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : agents.length === 0 ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <GitBranch className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground">No workflows yet</p>
          <p className="text-sm text-muted-foreground/70 mt-1">Workflows will appear here when agents are running</p>
        </div>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => (
            <div key={agent.agent_id} className="p-4 rounded-lg border bg-card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${agent.status === 'running' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
                    <GitBranch className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">{agent.agent_type}</p>
                    <p className="text-sm text-muted-foreground">{agent.status}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
