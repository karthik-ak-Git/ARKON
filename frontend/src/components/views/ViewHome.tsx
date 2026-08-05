import React, { useEffect } from 'react';
import { useArkonStore } from '../../store/useArkonStore';
import { FolderGit2, Blocks, Bot, MessageSquare, Clock, Trash2 } from 'lucide-react';

export function ViewHome() {
  const {
    workspaces,
    activeWorkspaceId,
    fetchWorkspaces,
    createWorkspace,
    selectWorkspace,
    deleteWorkspace,
    setActiveSidebarItem,
    isLoadingWorkspaces,
  } = useArkonStore();

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  const handleCreateWorkspace = async () => {
    const name = `Workspace ${workspaces.length + 1}`;
    const workspace = await createWorkspace(name);
    if (workspace) {
      setActiveSidebarItem('chat');
    }
  };

  const handleOpenWorkspace = (id?: string) => {
    if (id) {
      selectWorkspace(id);
    } else if (workspaces.length > 0) {
      selectWorkspace(workspaces[0].id);
    }
    setActiveSidebarItem('chat');
  };

  const formatTime = (timestamp: string) => {
    const now = Date.now();
    const then = new Date(timestamp).getTime();
    const diff = now - then;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="flex flex-col items-center pt-[8vh] animate-in fade-in zoom-in-95 duration-500 ease-out">
      <div className="mb-6 flex flex-col items-center">
        <div className="w-16 h-16 rounded-2xl bg-black dark:bg-white text-white dark:text-black flex items-center justify-center mb-6 shadow-sm">
          <span className="text-2xl font-bold tracking-tighter">A</span>
        </div>
        <h1 className="text-3xl font-medium tracking-tight text-gray-900 dark:text-gray-100 mb-2">Welcome to ARKON</h1>
        <p className="text-gray-500 dark:text-gray-400 text-center font-light text-[15px]">AI Agent Operating Platform</p>
      </div>

      <div className="flex gap-4 mt-8">
        <button onClick={() => handleOpenWorkspace()} className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10">
          <FolderGit2 className="w-[18px] h-[18px]" strokeWidth={1.5} />
          Open Workspace
        </button>
        <button onClick={handleCreateWorkspace} className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10">
          <Blocks className="w-[18px] h-[18px]" strokeWidth={1.5} />
          Create Workspace
        </button>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10">
          <Bot className="w-[18px] h-[18px]" strokeWidth={1.5} />
          Spawn Agent
        </button>
      </div>

      {/* Workspace History */}
      {workspaces.length > 0 && (
        <div className="mt-12 w-full max-w-2xl">
          <div className="text-[13px] font-medium tracking-wide uppercase text-gray-400 dark:text-gray-600 mb-3 border-b border-gray-200 dark:border-white/10 pb-2">
            Recent Workspaces
          </div>
          <div className="flex flex-col gap-2">
            {workspaces.map((workspace) => (
              <div
                key={workspace.id}
                onClick={() => handleOpenWorkspace(workspace.id)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer group border border-transparent hover:border-gray-200 dark:hover:border-white/10"
              >
                <div className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-white/5 flex items-center justify-center shrink-0">
                  <MessageSquare className="w-4 h-4 text-gray-500 dark:text-gray-400" strokeWidth={1.5} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[14px] text-gray-900 dark:text-gray-100 font-medium truncate">
                    {workspace.name}
                  </div>
                  {workspace.description && (
                    <div className="text-[12px] text-gray-400 dark:text-gray-500 truncate">
                      {workspace.description}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[11px] text-gray-400 dark:text-gray-600 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(workspace.updated_at)}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteWorkspace(workspace.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoadingWorkspaces && workspaces.length === 0 && (
        <div className="mt-12 text-[14px] text-gray-400 dark:text-gray-500">
          Loading workspaces...
        </div>
      )}

      {/* Empty state with backend error */}
      {!isLoadingWorkspaces && workspaces.length === 0 && (
        <div className="mt-12 text-[14px] text-gray-400 dark:text-gray-500">
          No workspaces yet. Create one to get started.
        </div>
      )}
    </div>
  );
}
