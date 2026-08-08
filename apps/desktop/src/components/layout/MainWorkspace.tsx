import { useArkonStore } from '../../store/useArkonStore';
import { CommandBox } from './CommandBox';
import { ViewHome } from '../views/ViewHome';
import { ViewChat } from '../views/ViewChat';
import { ViewProjects } from '../views/ViewProjects';
import { ViewAgents } from '../views/ViewAgents';
import { ViewWorkflows } from '../views/ViewWorkflows';

export function MainWorkspace() {
  const { activeSidebarItem } = useArkonStore();

  const renderContent = () => {
    switch (activeSidebarItem) {
      case 'home':
        return <ViewHome />;
      case 'chat':
        return <ViewChat />;
      case 'projects':
        return <ViewProjects />;
      case 'agents':
        return <ViewAgents />;
      case 'workflows':
        return <ViewWorkflows />;
      case 'plugins':
        return <div className="text-gray-500 font-light mt-20 text-center">No plugins installed.</div>;
      case 'settings':
        return <div className="text-gray-500 font-light mt-20 text-center">Settings</div>;
      default:
        return <ViewHome />;
    }
  };

  return (
    <div className="flex-1 h-full flex flex-col relative overflow-hidden">
      <div className="flex-1 overflow-y-auto w-full flex justify-center pb-32">
        <div className={`w-full ${activeSidebarItem === 'chat' ? 'max-w-3xl' : 'max-w-4xl'} px-8 flex flex-col ${activeSidebarItem === 'chat' ? 'pt-8 h-full' : 'pt-[15vh]'}`}>
          {renderContent()}
        </div>
      </div>
      
      {/* Command Box fixed at bottom center of the workspace */}
      {activeSidebarItem !== 'chat' && (
        <div className="w-full flex justify-center pb-8 pt-6 px-8 bg-gradient-to-t from-white via-white dark:from-[#0D0D0D] dark:via-[#0D0D0D] to-transparent absolute bottom-0 z-10 pointer-events-none">
          <div className="w-full max-w-3xl pointer-events-auto">
            <CommandBox />
          </div>
        </div>
      )}
    </div>
  );
}
