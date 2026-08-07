import { useCapabilities, useAgentRegistry } from '../../api/hooks';
import { Layers, Loader2, Box } from 'lucide-react';

export function ViewCapabilities() {
  const { data: capabilities, isLoading: capLoading } = useCapabilities();
  const { data: registry, isLoading: regLoading } = useAgentRegistry();

  const capEntries = capabilities ? Object.entries(capabilities.capabilities || {}) : [];
  const agents = registry?.agents || [];
  const isLoading = capLoading || regLoading;

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Capabilities</h2>
      </div>

      <div className="mb-8">
        <p className="text-sm text-gray-400 dark:text-gray-500 font-light">
          Available agent capabilities and the registry of agent types that implement them.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Capabilities Grid */}
          <section>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">All Capabilities</h3>
            {capEntries.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500 border border-dashed border-gray-200 dark:border-white/10 rounded-xl">
                <Layers className="w-10 h-10 mb-3 opacity-50" strokeWidth={1} />
                <p className="text-sm font-light">No capabilities registered.</p>
                <p className="text-xs mt-1">Capabilities are discovered when agents are spawned.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {capEntries.map(([capability, agentIds]) => (
                  <div key={capability} className="p-4 rounded-xl border border-gray-200 dark:border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Layers className="w-4 h-4 text-gray-500" />
                      <p className="text-sm font-medium">{capability}</p>
                    </div>
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      {(agentIds as string[]).length} agent(s) implement this
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Agent Registry */}
          <section>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Agent Registry</h3>
            {agents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500 border border-dashed border-gray-200 dark:border-white/10 rounded-xl">
                <Box className="w-10 h-10 mb-3 opacity-50" strokeWidth={1} />
                <p className="text-sm font-light">No agent types registered.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {agents.map((entry) => (
                  <div key={entry.agent_type} className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-white/10">
                    <div>
                      <p className="text-sm font-medium">{entry.agent_type}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{entry.description}</p>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {entry.capabilities.map((cap) => (
                        <span key={cap} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-white/5 text-gray-500">{cap}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
