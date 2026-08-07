import { useAgents, useDeleteAgent } from '../../api/hooks';
import { useRuntimeAgents, useSpawnAgent, useStartAgent, useCancelRuntimeAgent, useDeleteRuntimeAgent } from '../../api/hooks';
import { useArkonStore } from '../../store/useArkonStore';
import { Bot, Loader2, Plus, Trash2, Play, Square, Power } from 'lucide-react';

export function ViewAgents() {
  const { activeWorkspaceId } = useArkonStore();
  const { data: dbAgents, isLoading: dbLoading, isError: dbError } = useAgents(activeWorkspaceId);
  const { data: runtimeData, isLoading: rtLoading } = useRuntimeAgents();
  const deleteAgent = useDeleteAgent();
  const spawnAgent = useSpawnAgent();
  const startAgent = useStartAgent();
  const cancelAgent = useCancelRuntimeAgent();
  const deleteRuntimeAgent = useDeleteRuntimeAgent();

  const runtimeAgents = runtimeData?.agents || [];

  const allAgents = [
    ...(dbAgents || []).map((a) => ({
      id: a.id,
      name: a.name,
      type: a.agent_type,
      status: a.status,
      source: 'db' as const,
    })),
    ...runtimeAgents.map((a) => ({
      id: a.agent_id,
      name: a.agent_id,
      type: a.agent_type,
      status: a.status,
      source: 'runtime' as const,
    })),
  ];

  const isLoading = dbLoading || rtLoading;

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Agents</h2>
        <div className="flex gap-2">
          <button
            onClick={() => spawnAgent.mutate({ agent_type: 'generic', name: `Agent-${Date.now().toString(36)}` })}
            disabled={spawnAgent.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 border border-gray-200 dark:border-white/10 transition-colors disabled:opacity-40"
          >
            {spawnAgent.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            Spawn Agent
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center mt-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : allAgents.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-20 text-gray-400 dark:text-gray-500">
          <Bot className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">No agents active.</p>
          <p className="text-sm mt-1">Spawn an agent to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {allAgents.map((a) => (
            <div key={a.id} className="p-4 rounded-xl border border-gray-200 dark:border-white/10 group hover:border-gray-300 dark:hover:border-white/20 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{a.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-500">{a.type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      a.status === 'active' || a.status === 'running' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      a.status === 'idle' || a.status === 'paused' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                      a.status === 'failed' || a.status === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-400'
                    }`}>{a.status}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-white/5 text-gray-500">{a.source}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {a.source === 'runtime' && a.status !== 'running' && (
                    <button
                      onClick={() => startAgent.mutate(a.id)}
                      className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                      title="Start"
                    >
                      <Play className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {a.source === 'runtime' && a.status === 'running' && (
                    <button
                      onClick={() => cancelAgent.mutate(a.id)}
                      className="p-1 text-gray-400 hover:text-yellow-500 transition-colors"
                      title="Cancel"
                    >
                      <Square className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (a.source === 'runtime') {
                        deleteRuntimeAgent.mutate(a.id);
                      } else if (activeWorkspaceId) {
                        deleteAgent.mutate({ workspaceId: activeWorkspaceId, agentId: a.id });
                      }
                    }}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
