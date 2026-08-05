import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { Agent, Project, Plugin, Workflow, EventMessage, Workspace } from '../types';

export type SidebarItem = 'home' | 'projects' | 'agents' | 'workflows' | 'plugins' | 'chat' | 'settings';

interface ArkonState {
  // App State
  activeSidebarItem: SidebarItem;
  setActiveSidebarItem: (item: SidebarItem) => void;
  
  isWorkspaceOpen: boolean;
  setWorkspaceOpen: (isOpen: boolean) => void;

  // Domain State
  projects: Project[];
  agents: Agent[];
  plugins: Plugin[];
  workflows: Workflow[];
  events: EventMessage[];
  
  // Workspace / Chat History
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  addWorkspace: (name: string) => void;
  setActiveWorkspace: (id: string) => void;
  deleteWorkspace: (id: string) => void;
  
  addProject: (project: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>) => void;
  addAgent: (agent: Omit<Agent, 'id' | 'createdAt' | 'cpuUsage' | 'memoryUsage'>) => void;
  addEvent: (event: Omit<EventMessage, 'id' | 'timestamp'>) => void;
  
  updateAgentStatus: (id: string, status: Agent['status']) => void;
  updateAgentMetrics: (id: string, cpuUsage: number, memoryUsage: number) => void;
}

export const useArkonStore = create<ArkonState>((set) => ({
  activeSidebarItem: 'home',
  setActiveSidebarItem: (item) => set({ activeSidebarItem: item }),
  
  isWorkspaceOpen: false,
  setWorkspaceOpen: (isOpen) => set({ isWorkspaceOpen: isOpen }),
  
  // Empty states
  projects: [],
  agents: [],
  plugins: [],
  workflows: [],
  events: [],
  
  // Workspace / Chat History
  workspaces: [],
  activeWorkspaceId: null,
  addWorkspace: (name) => set((state) => {
    const newWorkspace: Workspace = {
      id: uuidv4(),
      name,
      lastMessage: 'New conversation',
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    return {
      workspaces: [newWorkspace, ...state.workspaces],
      activeWorkspaceId: newWorkspace.id,
    };
  }),
  setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),
  deleteWorkspace: (id) => set((state) => ({
    workspaces: state.workspaces.filter((w) => w.id !== id),
    activeWorkspaceId: state.activeWorkspaceId === id ? null : state.activeWorkspaceId,
  })),
  
  addProject: (project) => set((state) => ({
    projects: [...state.projects, { ...project, id: uuidv4(), createdAt: Date.now(), updatedAt: Date.now() }]
  })),
  
  addAgent: (agent) => set((state) => ({
    agents: [...state.agents, { ...agent, id: uuidv4(), createdAt: Date.now(), cpuUsage: 0, memoryUsage: 0 }]
  })),
  
  addEvent: (event) => set((state) => ({
    events: [{ ...event, id: uuidv4(), timestamp: Date.now() }, ...state.events].slice(0, 100)
  })),
  
  updateAgentStatus: (id, status) => set((state) => ({
    agents: state.agents.map(a => a.id === id ? { ...a, status } : a)
  })),
  
  updateAgentMetrics: (id, cpuUsage, memoryUsage) => set((state) => ({
    agents: state.agents.map(a => a.id === id ? { ...a, cpuUsage, memoryUsage } : a)
  }))
}));
