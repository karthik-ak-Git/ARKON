import React from 'react';
import { useArkonStore } from '../../store/useArkonStore';
import { FolderGit2 } from 'lucide-react';

export function ViewProjects() {
  const { projects } = useArkonStore();

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Projects</h2>
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-20 text-gray-400 dark:text-gray-500">
          <FolderGit2 className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">No projects available.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map(p => (
            <div key={p.id} className="p-4 rounded-xl border border-gray-200 dark:border-white/10">{p.name}</div>
          ))}
        </div>
      )}
    </div>
  );
}
