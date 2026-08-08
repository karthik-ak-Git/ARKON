import { GitMerge, Plus } from 'lucide-react';

export function ViewWorkflows() {
  return (
    <div className="animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-medium text-gray-900 dark:text-gray-100 tracking-tight">Workflows</h1>
          <p className="text-[14px] text-gray-500 dark:text-gray-400 mt-1 font-light">Design and automate agent workflows</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[13px] font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-40" disabled>
          <Plus className="w-4 h-4" strokeWidth={1.5} />
          New Workflow
        </button>
      </div>

      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-4">
          <GitMerge className="w-7 h-7 text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
        </div>
        <p className="text-[15px] text-gray-500 dark:text-gray-400 font-light">No workflows yet</p>
        <p className="text-[13px] text-gray-400 dark:text-gray-600 mt-1">Coming soon — workflow engine is under development</p>
      </div>
    </div>
  );
}
