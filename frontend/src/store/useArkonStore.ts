import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { Agent, Project, Plugin, Workflow, EventMessage } from '../types';

export type SidebarItem = 'home' | 'projects' | 'agents' | 'workflows' | 'plugins' | 'settings';

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


