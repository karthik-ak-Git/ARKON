import React from 'react';
import { useArkonStore } from '../../store/useArkonStore';
import { Bot } from 'lucide-react';

export function ViewAgents() {
  const { agents } = useArkonStore();

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Agents</h2>
      </div>

      {agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-20 text-gray-400 dark:text-gray-500">
          <Bot className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">No agents active.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {agents.map(a => (
            <div key={a.id} className="p-4 rounded-xl border border-gray-200 dark:border-white/10">{a.name}</div>
          ))}
        </div>
      )}
    </div>
  );
}
