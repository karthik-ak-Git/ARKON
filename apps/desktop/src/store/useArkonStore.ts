/**
 * Zustand Store — UI STATE ONLY.
 *
 * All domain data comes from React Query hooks.
 * This store handles: navigation, selection, dialogs, theme, layout.
 */

import { create } from 'zustand';

export type SidebarItem =
  | 'home'
  | 'chat'
  | 'projects'
  | 'agents'
  | 'workflows'
  | 'execution'
  | 'resources'
  | 'plugins'
  | 'settings';

interface ArkonState {
  // Navigation
  activeSidebarItem: SidebarItem;
  setActiveSidebarItem: (item: SidebarItem) => void;

  // Workspace selection
  activeWorkspaceId: string | null;
  selectWorkspace: (id: string | null) => void;

  // Agent selection
  selectedAgentId: string | null;
  selectAgent: (id: string | null) => void;

  // Project selection
  selectedProjectId: string | null;
  selectProject: (id: string | null) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Theme
  darkMode: boolean;
  toggleDarkMode: () => void;

  // Command box
  commandBoxOpen: boolean;
  setCommandBoxOpen: (open: boolean) => void;

  // Offline state
  isOffline: boolean;
  setOffline: (offline: boolean) => void;
}

export const useArkonStore = create<ArkonState>((set) => ({
  // Navigation
  activeSidebarItem: 'home',
  setActiveSidebarItem: (item) => set({ activeSidebarItem: item }),

  // Workspace selection
  activeWorkspaceId: null,
  selectWorkspace: (id) => set({ activeWorkspaceId: id }),

  // Agent selection
  selectedAgentId: null,
  selectAgent: (id) => set({ selectedAgentId: id }),

  // Project selection
  selectedProjectId: null,
  selectProject: (id) => set({ selectedProjectId: id }),

  // Sidebar
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  // Theme
  darkMode: true,
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),

  // Command box
  commandBoxOpen: false,
  setCommandBoxOpen: (open) => set({ commandBoxOpen: open }),

  // Offline state
  isOffline: false,
  setOffline: (offline) => set({ isOffline: offline }),
}));
