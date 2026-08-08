import { create } from 'zustand';

export type SidebarItem = 'home' | 'projects' | 'agents' | 'workflows' | 'plugins' | 'chat' | 'settings';

interface ArkonState {
  // UI State only
  activeSidebarItem: SidebarItem;
  setActiveSidebarItem: (item: SidebarItem) => void;

  activeWorkspaceId: string | null;
  setActiveWorkspaceId: (id: string | null) => void;

  activeAgentId: string | null;
  setActiveAgentId: (id: string | null) => void;

  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;

  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

export const useArkonStore = create<ArkonState>((set) => ({
  activeSidebarItem: 'home',
  setActiveSidebarItem: (item) => set({ activeSidebarItem: item }),

  activeWorkspaceId: null,
  setActiveWorkspaceId: (id) => set({ activeWorkspaceId: id }),

  activeAgentId: null,
  setActiveAgentId: (id) => set({ activeAgentId: id }),

  activeProjectId: null,
  setActiveProjectId: (id) => set({ activeProjectId: id }),

  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
}));
