import { useRuntimeAgents, useSpawnAgent } from '../../api/hooks';
import { Bot, Plus, Cpu, MemoryStick } from 'lucide-react';

export function ViewAgents() {
  const { data: runtimeData, isLoading: agentsLoading, isError: agentsError } = useRuntimeAgents();
  const spawnAgent = useSpawnAgent();

  const agents = runtimeData?.agents ?? [];

  const handleSpawnAgent = () => {
    spawnAgent.mutate({
      agent_type: 'general',
      name: `Agent ${agents.length + 1}`,
    });
  };

  return (
    <div className="animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-medium text-gray-900 dark:text-gray-100 tracking-tight">Agents</h1>
          <p className="text-[14px] text-gray-500 dark:text-gray-400 mt-1 font-light">Monitor and manage your AI agents</p>
        </div>
        <button
          onClick={handleSpawnAgent}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[13px] font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
        >
          <Plus className="w-4 h-4" strokeWidth={1.5} />
          Spawn Agent
        </button>
      </div>

      {agentsLoading ? (
        <div className="flex flex-col gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-4 rounded-xl border border-gray-200 dark:border-white/10">
              <div className="w-10 h-10 rounded-lg bg-gray-200 dark:bg-white/10 animate-pulse" />
              <div className="flex-1 space-y-2">
                <div className="h-3 w-40 rounded bg-gray-200 dark:bg-white/10 animate-pulse" />
                <div className="h-2 w-24 rounded bg-gray-200 dark:bg-white/10 animate-pulse" />
              </div>
              <div className="h-5 w-16 rounded-full bg-gray-200 dark:bg-white/10 animate-pulse" />
            </div>
          ))}
        </div>
      ) : agentsError ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/20 flex items-center justify-center mb-4">
            <Bot className="w-7 h-7 text-red-400 dark:text-red-500" strokeWidth={1.5} />
          </div>
          <p className="text-[15px] text-red-500 dark:text-red-400 font-light">Failed to load agents</p>
          <p className="text-[13px] text-gray-400 dark:text-gray-600 mt-1">Check your backend connection</p>
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-4">
            <Bot className="w-7 h-7 text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
          </div>
          <p className="text-[15px] text-gray-500 dark:text-gray-400 font-light">No agents running</p>
          <p className="text-[13px] text-gray-400 dark:text-gray-600 mt-1">Spawn an agent to get started</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {agents.map((agent) => (
            <div
              key={agent.agent_id}
              className="flex items-center gap-4 px-5 py-4 rounded-xl border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/5 flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5 text-gray-500 dark:text-gray-400" strokeWidth={1.5} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[14px] text-gray-900 dark:text-gray-100 font-medium">
                  {agent.agent_id.length > 12 ? agent.agent_id.substring(0, 12) + '…' : agent.agent_id}
                </div>
                <div className="text-[12px] text-gray-400 dark:text-gray-500 mt-0.5">{agent.agent_type}</div>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <div className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-gray-400" strokeWidth={1.5} />
                  <span className="text-[11px] text-gray-500 dark:text-gray-400">—</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <MemoryStick className="w-3.5 h-3.5 text-gray-400" strokeWidth={1.5} />
                  <span className="text-[11px] text-gray-500 dark:text-gray-400">—</span>
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                  agent.status === 'running'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : agent.status === 'error'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-500'
                }`}>
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
