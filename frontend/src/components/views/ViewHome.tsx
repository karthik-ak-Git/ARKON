import React from 'react';
import { useArkonStore } from '../../store/useArkonStore';
import { FolderGit2, Blocks, Bot } from 'lucide-react';

export function ViewHome() {
  const { addWorkspace, setActiveSidebarItem, workspaces, setActiveWorkspace } = useArkonStore();

  const handleCreateWorkspace = () => {
    const name = `Workspace ${workspaces.length + 1}`;
    addWorkspace(name);
    setActiveSidebarItem('chat');
  };

  const handleOpenWorkspace = () => {
    if (workspaces.length > 0) {
      setActiveWorkspace(workspaces[0].id);
    }
    setActiveSidebarItem('chat');
  };

  return (
    <div className="flex flex-col items-center justify-center pt-[10vh] animate-in fade-in zoom-in-95 duration-500 ease-out">
      <div className="mb-6 flex flex-col items-center">
        <div className="w-16 h-16 rounded-2xl bg-black dark:bg-white text-white dark:text-black flex items-center justify-center mb-6 shadow-sm">
          <span className="text-2xl font-bold tracking-tighter">A</span>
        </div>
        <h1 className="text-3xl font-medium tracking-tight text-gray-900 dark:text-gray-100 mb-2">Welcome to ARKON</h1>
        <p className="text-gray-500 dark:text-gray-400 text-center font-light text-[15px]">AI Agent Operating Platform</p>
      </div>

      <div className="flex gap-4 mt-8">
        <button onClick={handleOpenWorkspace} className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-white/10">
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
    </div>
  );
}
