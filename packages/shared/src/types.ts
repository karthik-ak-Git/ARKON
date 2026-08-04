export interface Project {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive' | 'archived'
  createdAt: Date
  updatedAt: Date
}

export interface Agent {
  id: string
  projectId: string
  name: string
  type: AgentType
  status: AgentStatus
  config: Record<string, unknown>
  createdAt: Date
  updatedAt: Date
}

export type AgentType = 'video' | 'audio' | 'text' | 'image' | 'data' | 'custom'

export type AgentStatus = 'idle' | 'running' | 'paused' | 'error' | 'completed'

export interface Workflow {
  id: string
  projectId: string
  name: string
  description: string
  steps: WorkflowStep[]
  status: 'draft' | 'active' | 'completed' | 'failed'
  createdAt: Date
  updatedAt: Date
}

export interface WorkflowStep {
  id: string
  agentId: string
  action: string
  config: Record<string, unknown>
  order: number
  status: 'pending' | 'running' | 'completed' | 'failed'
}

export interface Plugin {
  id: string
  name: string
  description: string
  version: string
  author: string
  enabled: boolean
  config: Record<string, unknown>
  installedAt: Date
}

export interface Event {
  id: string
  type: string
  source: string
  payload: Record<string, unknown>
  timestamp: Date
}

export interface Metrics {
  cpu: number
  memory: number
  activeAgents: number
  completedTasks: number
  failedTasks: number
  uptime: number
}
