import { Bot, Loader2, Play, Pause, Trash2 } from 'lucide-react'
import { useRuntimeAgents, useStartAgent, useCancelRuntimeAgent, useDeleteRuntimeAgent } from '@/api/hooks'

export function Agents() {
  const { data: agentList, isLoading } = useRuntimeAgents()
  const startAgent = useStartAgent()
  const cancelAgent = useCancelRuntimeAgent()
  const deleteAgent = useDeleteRuntimeAgent()
  const agents = agentList?.agents ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Agents</h1>
        <p className="text-muted-foreground">Configure and monitor AI agents</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : agents.length === 0 ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <Bot className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground">No agents running</p>
          <p className="text-sm text-muted-foreground/70 mt-1">Spawn an agent to get started</p>
        </div>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => (
            <div key={agent.agent_id} className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-full ${agent.status === 'running' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
                  <Bot className="h-4 w-4" />
                </div>
                <div>
                  <p className="font-medium">{agent.agent_type}</p>
                  <p className="text-sm text-muted-foreground">{agent.status}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {agent.status !== 'running' && (
                  <button
                    onClick={() => startAgent.mutate(agent.agent_id)}
                    disabled={startAgent.isPending}
                    className="p-2 rounded-md text-muted-foreground hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                  >
                    <Play className="h-4 w-4" />
                  </button>
                )}
                {agent.status === 'running' && (
                  <button
                    onClick={() => cancelAgent.mutate(agent.agent_id)}
                    disabled={cancelAgent.isPending}
                    className="p-2 rounded-md text-muted-foreground hover:text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 transition-colors"
                  >
                    <Pause className="h-4 w-4" />
                  </button>
                )}
                <button
                  onClick={() => deleteAgent.mutate(agent.agent_id)}
                  disabled={deleteAgent.isPending}
                  className="p-2 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
