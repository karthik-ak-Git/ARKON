import { Sidebar } from './Sidebar';
import { MainWorkspace } from './MainWorkspace';

export function ClaudeLayout() {
  return (
    <div className="h-screen w-full flex overflow-hidden bg-white dark:bg-[#0D0D0D]">
      <Sidebar />
      <MainWorkspace />
    </div>
  );
}
