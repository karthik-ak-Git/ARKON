import React, { useState } from 'react';
import { useArkonStore, SidebarItem } from '../../store/useArkonStore';
import { cn } from '../../lib/utils';
import { Home, FolderGit2, Bot, GitMerge, Blocks, Settings, MessageSquare, Plus, Trash2, Clock } from 'lucide-react';

export function Sidebar() {
  const { activeSidebarItem, setActiveSidebarItem, workspaces, addWorkspace, deleteWorkspace, activeWorkspaceId, setActiveWorkspace } = useArkonStore();
  const [showHistory, setShowHistory] = useState(false);

  const topItems: { id: SidebarItem; icon: React.ElementType; label: string }[] = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'projects', icon: FolderGit2, label: 'Projects' },
    { id: 'agents', icon: Bot, label: 'Agents' },
    { id: 'workflows', icon: GitMerge, label: 'Workflows' },
    { id: 'plugins', icon: Blocks, label: 'Plugins' },
  ];

  const handleChatClick = () => {
    setActiveSidebarItem('chat');
    setShowHistory(!showHistory);
  };

  const handleNewWorkspace = () => {
    const name = `Workspace ${workspaces.length + 1}`;
    addWorkspace(name);
  };

  const formatTime = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="flex h-full shrink-0 z-10 bg-transparent">
      {/* Main Sidebar Icons */}
      <div className="w-[60px] h-full flex flex-col items-center py-4 border-r border-gray-200 dark:border-white/5">
        <div className="flex flex-col items-center gap-3 w-full flex-1">
          {topItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'chat') {
                  handleChatClick();
                } else {
                  setActiveSidebarItem(item.id);
                  setShowHistory(false);
                }
              }}
              className={cn(
                "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 group relative",
                activeSidebarItem === item.id 
                  ? "bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-gray-100" 
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-50 dark:hover:bg-white/5 dark:hover:text-gray-200"
              )}
              title={item.label}
            >
              <item.icon className="w-[20px] h-[20px]" strokeWidth={1.5} />
            </button>
          ))}
        </div>

        <div className="flex flex-col items-center gap-4 w-full">
          <button
            onClick={() => setActiveSidebarItem('settings')}
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200",
              activeSidebarItem === 'settings'
                ? "bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-gray-100"
                : "text-gray-500 hover:text-gray-900 hover:bg-gray-50 dark:hover:bg-white/5 dark:hover:text-gray-200"
            )}
            title="Settings"
          >
            <Settings className="w-[20px] h-[20px]" strokeWidth={1.5} />
          </button>
        </div>
      </div>

      {/* History Panel */}
      {showHistory && (
        <div className="w-[240px] h-full border-r border-gray-200 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02] flex flex-col animate-in slide-in-from-left fade-in duration-200">
          <div className="p-3 border-b border-gray-200 dark:border-white/5">
            <button
              onClick={handleNewWorkspace}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[13px] font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Workspace
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2">
            {workspaces.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="w-8 h-8 mx-auto text-gray-300 dark:text-gray-600 mb-2" strokeWidth={1.5} />
                <p className="text-[13px] text-gray-400 dark:text-gray-500">No workspaces yet</p>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                {workspaces.map((workspace) => (
                  <button
                    key={workspace.id}
                    onClick={() => {
                      setActiveWorkspace(workspace.id);
                      setActiveSidebarItem('chat');
                    }}
                    className={cn(
                      "w-full text-left px-3 py-2.5 rounded-lg transition-colors group flex flex-col gap-0.5",
                      activeWorkspaceId === workspace.id
                        ? "bg-gray-200 dark:bg-white/10"
                        : "hover:bg-gray-100 dark:hover:bg-white/5"
                    )}
                  >
                    <span className="text-[13px] text-gray-900 dark:text-gray-100 truncate">
                      {workspace.name}
                    </span>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500 truncate">
                      {workspace.lastMessage}
                    </span>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-[10px] text-gray-400 dark:text-gray-600">
                        {formatTime(workspace.updatedAt)}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteWorkspace(workspace.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
