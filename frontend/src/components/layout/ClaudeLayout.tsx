import React from 'react';
import { Sidebar } from './Sidebar';
import { MainWorkspace } from './MainWorkspace';

export function ClaudeLayout() {
  return (
    <div className="dark flex h-screen w-screen bg-[#FDFDFD] dark:bg-[#0D0D0D] text-gray-900 dark:text-gray-100 font-sans overflow-hidden transition-colors duration-200">
      <Sidebar />
      <MainWorkspace />
    </div>
  );
}
