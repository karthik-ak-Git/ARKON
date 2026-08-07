import { useProjects, useDeleteProject } from '../../api/hooks';
import { useArkonStore } from '../../store/useArkonStore';
import { FolderGit2, Loader2, Plus, Trash2 } from 'lucide-react';

export function ViewProjects() {
  const { activeWorkspaceId } = useArkonStore();
  const { data: projects, isLoading, isError } = useProjects(activeWorkspaceId);
  const deleteProject = useDeleteProject();

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Projects</h2>
        {activeWorkspaceId && (
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 border border-gray-200 dark:border-white/10 transition-colors">
            <Plus className="w-3.5 h-3.5" />
            New Project
          </button>
        )}
      </div>

      {!activeWorkspaceId ? (
        <div className="flex flex-col items-center justify-center mt-20 text-gray-400 dark:text-gray-500">
          <FolderGit2 className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">Select a workspace first.</p>
        </div>
      ) : isLoading ? (
        <div className="flex items-center justify-center mt-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center mt-20 text-red-400">
          <p className="font-light">Failed to load projects.</p>
        </div>
      ) : !projects || projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-20 text-gray-400 dark:text-gray-500">
          <FolderGit2 className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">No projects yet.</p>
          <p className="text-sm mt-1">Create a project to organize your work.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((p) => (
            <div key={p.id} className="p-4 rounded-xl border border-gray-200 dark:border-white/10 group hover:border-gray-300 dark:hover:border-white/20 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{p.name}</p>
                  {p.description && <p className="text-sm text-gray-500 mt-1">{p.description}</p>}
                </div>
                <button
                  onClick={() => activeWorkspaceId && deleteProject.mutate({ workspaceId: activeWorkspaceId, projectId: p.id })}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  p.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                  p.status === 'completed' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                  'bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-400'
                }`}>{p.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
