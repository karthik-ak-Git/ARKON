import { useState } from 'react';
import { useWorkspaces, useCreateWorkspace, useDeleteWorkspace } from '../../api/hooks';
import { useArkonStore } from '../../store/useArkonStore';
import type { Workspace } from '../../api/types';
import { FolderGit2, Blocks, Bot, MessageSquare, Clock, Trash2, Loader2, AlertCircle, WifiOff } from 'lucide-react';

export function ViewHome() {
  const { activeWorkspaceId, selectWorkspace, setActiveSidebarItem } = useArkonStore();
  const { data: workspaceList, isLoading, isError, error } = useWorkspaces();
  const createWorkspace = useCreateWorkspace();
  const deleteWorkspace = useDeleteWorkspace();

  const workspaces = workspaceList
    ? [...(workspaceList.active || []), ...(workspaceList.available || [])]
    : [];

  const handleCreateWorkspace = async () => {
    const name = `Workspace ${workspaces.length + 1}`;
    const id = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '-' + Date.now().toString(36);
    const workspace: Workspace = await createWorkspace.mutateAsync({ id, name });
    if (workspace) {
      selectWorkspace(workspace.id);
      setActiveSidebarItem('chat');
    }
  };

  const handleOpenWorkspace = (id?: string) => {
    const targetId = id || (workspaces.length > 0 ? workspaces[0].id : null);
    if (targetId) {
      selectWorkspace(targetId);
      setActiveSidebarItem('chat');
    }
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

      {/* Offline indicator */}
      {isError && (
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 text-red-600 dark:text-red-400 text-[13px] mb-4">
          <WifiOff className="w-4 h-4" />
          Backend offline — {error?.message || 'Unable to connect'}
        </div>
      )}

      <div className="flex gap-4 mt-8">
        <button
          onClick={() => handleOpenWorkspace()}
          disabled={workspaces.length === 0}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <FolderGit2 className="w-[18px] h-[18px]" strokeWidth={1.5} />
          Open Workspace
        </button>
        <button
          onClick={handleCreateWorkspace}
          disabled={createWorkspace.isPending}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10 disabled:opacity-40"
        >
          {createWorkspace.isPending ? (
            <Loader2 className="w-[18px] h-[18px] animate-spin" strokeWidth={1.5} />
          ) : (
            <Blocks className="w-[18px] h-[18px]" strokeWidth={1.5} />
          )}
          Create Workspace
        </button>
        <button
          onClick={() => setActiveSidebarItem('agents')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10"
        >
          <Bot className="w-[18px] h-[18px]" strokeWidth={1.5} />
          Spawn Agent
        </button>
      </div>

      {/* Workspace History */}
      {isLoading ? (
        <div className="mt-12 flex items-center gap-2 text-[14px] text-gray-400 dark:text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading workspaces...
        </div>
      ) : workspaces.length > 0 ? (
        <div className="mt-12 w-full max-w-2xl">
          <div className="text-[13px] font-medium tracking-wide uppercase text-gray-400 dark:text-gray-600 mb-3 border-b border-gray-200 dark:border-white/10 pb-2">
            Recent Workspaces
          </div>
          <div className="flex flex-col gap-2">
            {workspaces.map((workspace) => (
              <div
                key={workspace.id}
                onClick={() => handleOpenWorkspace(workspace.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer group border ${
                  activeWorkspaceId === workspace.id
                    ? 'border-gray-300 dark:border-white/20 bg-gray-50 dark:bg-white/5'
                    : 'border-transparent hover:border-gray-200 dark:hover:border-white/10'
                }`}
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
                  <span className={`text-[11px] px-1.5 py-0.5 rounded-full ${
                    workspace.state === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                    workspace.state === 'suspended' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                    'bg-gray-100 text-gray-500 dark:bg-white/10 dark:text-gray-400'
                  }`}>
                    {workspace.state}
                  </span>
                  <span className="text-[11px] text-gray-400 dark:text-gray-600 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(workspace.updated_at)}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteWorkspace.mutate(workspace.id);
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
      ) : !isError ? (
        <div className="mt-12 text-[14px] text-gray-400 dark:text-gray-500">
          No workspaces yet. Create one to get started.
        </div>
      ) : null}
    </div>
  );
}
