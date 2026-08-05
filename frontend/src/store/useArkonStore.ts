/**
 * ARKON Store - Thin Client.
 * 
 * This store manages UI state only.
 * All domain state comes from the backend via the API client.
 * No business logic. No execution. No fake data.
 */

import { create } from 'zustand';
import { api, Workspace, Project, Agent } from '../lib/api';

export type SidebarItem = 'home' | 'projects' | 'agents' | 'workflows' | 'plugins' | 'chat' | 'settings';

interface ArkonState {
  // UI State
  activeSidebarItem: SidebarItem;
  setActiveSidebarItem: (item: SidebarItem) => void;
  isWorkspaceOpen: boolean;
  setWorkspaceOpen: (isOpen: boolean) => void;

  // Domain State (from backend)
  workspaces: Workspace[];
  projects: Project[];
  agents: Agent[];
  activeWorkspaceId: string | null;

  // Loading states
  isLoadingWorkspaces: boolean;
  isLoadingProjects: boolean;
  isLoadingAgents: boolean;
  error: string | null;

  // Workspace actions
  fetchWorkspaces: () => Promise<void>;
  createWorkspace: (name: string, description?: string) => Promise<Workspace | null>;
  selectWorkspace: (id: string) => void;
  deleteWorkspace: (id: string) => Promise<void>;

  // Project actions
  fetchProjects: (workspaceId: string) => Promise<void>;
  createProject: (workspaceId: string, name: string, description?: string) => Promise<Project | null>;
  deleteProject: (workspaceId: string, projectId: string) => Promise<void>;

  // Agent actions
  fetchAgents: (workspaceId: string) => Promise<void>;
  createAgent: (workspaceId: string, name: string, agentType?: string) => Promise<Agent | null>;
  deleteAgent: (workspaceId: string, agentId: string) => Promise<void>;

  // Clear
  clearError: () => void;
}

export const useArkonStore = create<ArkonState>((set, get) => ({
  // UI State
  activeSidebarItem: 'home',
  setActiveSidebarItem: (item) => set({ activeSidebarItem: item }),
  isWorkspaceOpen: false,
  setWorkspaceOpen: (isOpen) => set({ isWorkspaceOpen: isOpen }),

  // Domain State
  workspaces: [],
  projects: [],
  agents: [],
  activeWorkspaceId: null,

  // Loading
  isLoadingWorkspaces: false,
  isLoadingProjects: false,
  isLoadingAgents: false,
  error: null,

  // Workspace actions
  fetchWorkspaces: async () => {
    set({ isLoadingWorkspaces: true, error: null });
    try {
      const workspaces = await api.listWorkspaces();
      set({ workspaces, isLoadingWorkspaces: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoadingWorkspaces: false });
    }
  },

  createWorkspace: async (name, description) => {
    set({ error: null });
    try {
      const workspace = await api.createWorkspace({ name, description });
      set((state) => ({
        workspaces: [workspace, ...state.workspaces],
        activeWorkspaceId: workspace.id,
      }));
      return workspace;
    } catch (err) {
      set({ error: (err as Error).message });
      return null;
    }
  },

  selectWorkspace: (id) => {
    set({ activeWorkspaceId: id });
  },

  deleteWorkspace: async (id) => {
    set({ error: null });
    try {
      await api.deleteWorkspace(id);
      set((state) => ({
        workspaces: state.workspaces.filter((w) => w.id !== id),
        activeWorkspaceId: state.activeWorkspaceId === id ? null : state.activeWorkspaceId,
      }));
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  // Project actions
  fetchProjects: async (workspaceId) => {
    set({ isLoadingProjects: true, error: null });
    try {
      const projects = await api.listProjects(workspaceId);
      set({ projects, isLoadingProjects: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoadingProjects: false });
    }
  },

  createProject: async (workspaceId, name, description) => {
    set({ error: null });
    try {
      const project = await api.createProject(workspaceId, { name, description });
      set((state) => ({
        projects: [project, ...state.projects],
      }));
      return project;
    } catch (err) {
      set({ error: (err as Error).message });
      return null;
    }
  },

  deleteProject: async (workspaceId, projectId) => {
    set({ error: null });
    try {
      await api.deleteProject(workspaceId, projectId);
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== projectId),
      }));
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  // Agent actions
  fetchAgents: async (workspaceId) => {
    set({ isLoadingAgents: true, error: null });
    try {
      const agents = await api.listAgents(workspaceId);
      set({ agents, isLoadingAgents: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoadingAgents: false });
    }
  },

  createAgent: async (workspaceId, name, agentType) => {
    set({ error: null });
    try {
      const agent = await api.createAgent(workspaceId, { name, agent_type: agentType });
      set((state) => ({
        agents: [agent, ...state.agents],
      }));
      return agent;
    } catch (err) {
      set({ error: (err as Error).message });
      return null;
    }
  },

  deleteAgent: async (workspaceId, agentId) => {
    set({ error: null });
    try {
      await api.deleteAgent(workspaceId, agentId);
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== agentId),
      }));
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  // Clear
  clearError: () => set({ error: null }),
}));
