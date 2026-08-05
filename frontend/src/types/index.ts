export type AgentStatus = 'idle' | 'running' | 'paused' | 'error' | 'terminated';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: AgentStatus;
  pluginId: string;
  createdAt: number;
  cpuUsage: number;
  memoryUsage: number;
  currentTask?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: number;
  updatedAt: number;
  status: 'active' | 'archived';
}

export interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  status: 'installed' | 'active' | 'disabled';
  capabilities: string[];
}

export interface Workflow {
  id: string;
  projectId: string;
  name: string;
  status: 'draft' | 'running' | 'completed' | 'failed';
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowNode {
  id: string;
  type: string;
  data: any;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface EventMessage {
  id: string;
  timestamp: number;
  source: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  data?: any;
}

export interface Workspace {
  id: string;
  name: string;
  lastMessage: string;
  createdAt: number;
  updatedAt: number;
}

export type ViewType = 'dashboard' | 'projects' | 'agents' | 'workflows' | 'plugins' | 'settings';
