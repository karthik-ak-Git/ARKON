/**
 * API Client for ARKON Backend.
 * 
 * This is the ONLY place the frontend communicates with the backend.
 * All business logic lives in Python. This is a thin HTTP client.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// =============================================================================
// Types (mirror backend schemas)
// =============================================================================

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  settings: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  workspace_id: string;
  name: string;
  agent_type: string;
  status: string;
  capabilities: string[] | null;
  config: Record<string, unknown> | null;
  last_heartbeat: string | null;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  workflow_id: string | null;
  agent_id: string | null;
  name: string;
  status: string;
  priority: number;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Health {
  status: string;
  version: string;
  environment: string;
  database: string;
  redis: string;
}

// =============================================================================
// Request types
// =============================================================================

export interface CreateWorkspace {
  name: string;
  description?: string;
}

export interface UpdateWorkspace {
  name?: string;
  description?: string;
  settings?: Record<string, unknown>;
}

export interface CreateProject {
  name: string;
  description?: string;
}

export interface UpdateProject {
  name?: string;
  description?: string;
  status?: string;
}

export interface CreateAgent {
  name: string;
  agent_type?: string;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

export interface UpdateAgent {
  name?: string;
  status?: string;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

// =============================================================================
// HTTP Client
// =============================================================================

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // ===========================================================================
  // Health
  // ===========================================================================

  async getHealth(): Promise<Health> {
    return this.request<Health>('GET', '/health');
  }

  // ===========================================================================
  // Workspaces
  // ===========================================================================

  async listWorkspaces(limit = 50, offset = 0): Promise<Workspace[]> {
    return this.request<Workspace[]>('GET', `/workspaces/?limit=${limit}&offset=${offset}`);
  }

  async getWorkspace(id: string): Promise<Workspace> {
    return this.request<Workspace>('GET', `/workspaces/${id}`);
  }

  async createWorkspace(data: CreateWorkspace): Promise<Workspace> {
    return this.request<Workspace>('POST', '/workspaces/', data);
  }

  async updateWorkspace(id: string, data: UpdateWorkspace): Promise<Workspace> {
    return this.request<Workspace>('PATCH', `/workspaces/${id}`, data);
  }

  async deleteWorkspace(id: string): Promise<void> {
    return this.request<void>('DELETE', `/workspaces/${id}`);
  }

  // ===========================================================================
  // Projects
  // ===========================================================================

  async listProjects(workspaceId: string, limit = 50, offset = 0): Promise<Project[]> {
    return this.request<Project[]>(
      'GET',
      `/workspaces/${workspaceId}/projects/?limit=${limit}&offset=${offset}`,
    );
  }

  async getProject(workspaceId: string, projectId: string): Promise<Project> {
    return this.request<Project>('GET', `/workspaces/${workspaceId}/projects/${projectId}`);
  }

  async createProject(workspaceId: string, data: CreateProject): Promise<Project> {
    return this.request<Project>('POST', `/workspaces/${workspaceId}/projects/`, data);
  }

  async updateProject(
    workspaceId: string,
    projectId: string,
    data: UpdateProject,
  ): Promise<Project> {
    return this.request<Project>(
      'PATCH',
      `/workspaces/${workspaceId}/projects/${projectId}`,
      data,
    );
  }

  async deleteProject(workspaceId: string, projectId: string): Promise<void> {
    return this.request<void>('DELETE', `/workspaces/${workspaceId}/projects/${projectId}`);
  }

  // ===========================================================================
  // Agents
  // ===========================================================================

  async listAgents(workspaceId: string, limit = 50, offset = 0): Promise<Agent[]> {
    return this.request<Agent[]>(
      'GET',
      `/workspaces/${workspaceId}/agents/?limit=${limit}&offset=${offset}`,
    );
  }

  async getAgent(workspaceId: string, agentId: string): Promise<Agent> {
    return this.request<Agent>('GET', `/workspaces/${workspaceId}/agents/${agentId}`);
  }

  async createAgent(workspaceId: string, data: CreateAgent): Promise<Agent> {
    return this.request<Agent>('POST', `/workspaces/${workspaceId}/agents/`, data);
  }

  async updateAgent(
    workspaceId: string,
    agentId: string,
    data: UpdateAgent,
  ): Promise<Agent> {
    return this.request<Agent>(
      'PATCH',
      `/workspaces/${workspaceId}/agents/${agentId}`,
      data,
    );
  }

  async deleteAgent(workspaceId: string, agentId: string): Promise<void> {
    return this.request<void>('DELETE', `/workspaces/${workspaceId}/agents/${agentId}`);
  }
}

// =============================================================================
// Singleton
// =============================================================================

export const api = new ApiClient(API_BASE);
