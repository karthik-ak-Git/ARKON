import { useArkonStore } from '../../store/useArkonStore';
import { useProjects, useCreateProject } from '../../api/hooks';
import { FolderGit2, Plus, Clock } from 'lucide-react';

export function ViewProjects() {
  const { activeWorkspaceId } = useArkonStore();
  const { data: projects = [], isLoading: projectsLoading, isError: projectsError } = useProjects(activeWorkspaceId);
  const createProject = useCreateProject();

  const handleAddProject = () => {
    if (!activeWorkspaceId) return;
    createProject.mutate({
      workspaceId: activeWorkspaceId,
      data: {
        name: `Project ${projects.length + 1}`,
        description: 'New project',
      },
    });
  };

  const formatTime = (timestamp: string) => {
    const now = Date.now();
    const diff = now - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-medium text-gray-900 dark:text-gray-100 tracking-tight">Projects</h1>
          <p className="text-[14px] text-gray-500 dark:text-gray-400 mt-1 font-light">Manage your workspace projects</p>
        </div>
        <button
          onClick={handleAddProject}
          disabled={!activeWorkspaceId}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[13px] font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-40"
        >
          <Plus className="w-4 h-4" strokeWidth={1.5} />
          New Project
        </button>
      </div>

      {!activeWorkspaceId ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-4">
            <FolderGit2 className="w-7 h-7 text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
          </div>
          <p className="text-[15px] text-gray-500 dark:text-gray-400 font-light">No workspace selected</p>
          <p className="text-[13px] text-gray-400 dark:text-gray-600 mt-1">Select a workspace to view projects</p>
        </div>
      ) : projectsLoading ? (
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
      ) : projectsError ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/20 flex items-center justify-center mb-4">
            <FolderGit2 className="w-7 h-7 text-red-400 dark:text-red-500" strokeWidth={1.5} />
          </div>
          <p className="text-[15px] text-red-500 dark:text-red-400 font-light">Failed to load projects</p>
          <p className="text-[13px] text-gray-400 dark:text-gray-600 mt-1">Check your backend connection</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-4">
            <FolderGit2 className="w-7 h-7 text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
          </div>
          <p className="text-[15px] text-gray-500 dark:text-gray-400 font-light">No projects yet</p>
          <p className="text-[13px] text-gray-400 dark:text-gray-600 mt-1">Create one to get started</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {projects.map((project) => (
            <div
              key={project.id}
              className="flex items-center gap-4 px-5 py-4 rounded-xl border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group"
            >
              <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/5 flex items-center justify-center shrink-0">
                <FolderGit2 className="w-5 h-5 text-gray-500 dark:text-gray-400" strokeWidth={1.5} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[14px] text-gray-900 dark:text-gray-100 font-medium">{project.name}</div>
                <div className="text-[12px] text-gray-400 dark:text-gray-500 mt-0.5">{project.description}</div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                  project.status === 'active'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-500'
                }`}>
                  {project.status}
                </span>
                <span className="text-[11px] text-gray-400 dark:text-gray-600 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTime(project.updated_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
