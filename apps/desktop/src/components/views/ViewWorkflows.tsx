import { useRuntimeAgents, useCapabilities, useAgentRegistry } from '../../api/hooks';
import { GitMerge, Loader2, Bot, Layers, Box } from 'lucide-react';

export function ViewWorkflows() {
  const { data: runtimeData, isLoading: rtLoading, isError: rtError } = useRuntimeAgents();
  const { data: capabilities, isLoading: capLoading } = useCapabilities();
  const { data: registry, isLoading: regLoading } = useAgentRegistry();

  const agents = runtimeData?.agents || [];
  const isLoading = rtLoading || capLoading || regLoading;
  const capEntries = capabilities ? Object.entries(capabilities.capabilities || {}) : [];

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Workflows</h2>
      </div>

      <div className="mb-8">
        <p className="text-sm text-gray-400 dark:text-gray-500 font-light">
          Workflow orchestration powered by runtime agents and capabilities.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : rtError ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-500">
          <GitMerge className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">Unable to load workflow data.</p>
          <p className="text-sm mt-1">Backend may be offline.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Active Agents */}
          <section>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Active Agents</h3>
            {agents.length === 0 ? (
              <div className="text-center py-10 text-gray-400 dark:text-gray-500 border border-dashed border-gray-200 dark:border-white/10 rounded-xl">
                <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-light">No agents running.</p>
                <p className="text-xs mt-1">Spawn an agent to start a workflow.</p>
              </div>
            ) : (
              <div className="grid gap-3">
                {agents.map((a) => (
                  <div key={a.agent_id} className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-white/10">
                    <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-white/5 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-gray-500" strokeWidth={1.5} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{a.agent_id}</p>
                      <p className="text-xs text-gray-400">{a.agent_type} — {a.state}</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      a.state === 'running' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      a.state === 'idle' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                      'bg-gray-100 text-gray-500 dark:bg-white/10 dark:text-gray-400'
                    }`}>{a.state}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Agent Registry */}
          {registry && registry.agents && registry.agents.length > 0 && (
            <section>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Agent Registry</h3>
              <div className="grid gap-2">
                {registry.agents.map((entry) => (
                  <div key={entry.agent_type} className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-white/10">
                    <Box className="w-4 h-4 text-gray-400 shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{entry.agent_type}</p>
                      <p className="text-xs text-gray-400">{entry.description}</p>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {entry.capabilities.map((cap) => (
                        <span key={cap} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-white/5 text-gray-500">{cap}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Capabilities */}
          {capEntries.length > 0 && (
            <section>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Capabilities</h3>
              <div className="grid grid-cols-2 gap-3">
                {capEntries.map(([capability, agentIds]) => (
                  <div key={capability} className="p-3 rounded-xl border border-gray-200 dark:border-white/10">
                    <div className="flex items-center gap-2 mb-1">
                      <Layers className="w-3.5 h-3.5 text-gray-400" />
                      <p className="text-sm font-medium">{capability}</p>
                    </div>
                    <p className="text-xs text-gray-400">{(agentIds as string[]).length} agent(s) available</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Empty state when nothing at all */}
          {agents.length === 0 && capEntries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400 dark:text-gray-500">
              <GitMerge className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
              <p className="font-light">No workflow activity yet.</p>
              <p className="text-sm mt-1">Spawn agents and assign capabilities to build workflows.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
