import React from 'react';
import { useArkonStore } from '../../store/useArkonStore';
import { GitMerge } from 'lucide-react';

export function ViewWorkflows() {
  const { workflows } = useArkonStore();

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Workflows</h2>
      </div>

      {workflows.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-20 text-gray-400 dark:text-gray-500">
          <GitMerge className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">No workflows found.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {workflows.map(w => (
            <div key={w.id} className="p-4 rounded-xl border border-gray-200 dark:border-white/10">{w.name}</div>
          ))}
        </div>
      )}
    </div>
  );
}
