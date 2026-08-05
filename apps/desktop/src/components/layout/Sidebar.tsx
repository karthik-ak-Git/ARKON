import React from 'react';
import { useArkonStore, SidebarItem } from '../../store/useArkonStore';
import { cn } from '../../lib/utils';
import { Home, FolderGit2, Bot, GitMerge, Blocks, Settings, MessageSquare } from 'lucide-react';

export function Sidebar() {
  const { activeSidebarItem, setActiveSidebarItem } = useArkonStore();

  const topItems: { id: SidebarItem; icon: React.ElementType; label: string }[] = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'projects', icon: FolderGit2, label: 'Projects' },
    { id: 'agents', icon: Bot, label: 'Agents' },
    { id: 'workflows', icon: GitMerge, label: 'Workflows' },
    { id: 'plugins', icon: Blocks, label: 'Plugins' },
  ];

  return (
    <div className="w-[60px] h-full flex flex-col items-center py-4 border-r border-gray-200 dark:border-white/5 shrink-0 z-10 bg-transparent">
      <div className="flex flex-col items-center gap-3 w-full flex-1">
        {topItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveSidebarItem(item.id)}
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
  );
}
