import { apiGet, apiPost, apiPatch, apiDelete } from './client';
import type { Agent, CreateAgent, UpdateAgent } from './types';

export const agentsApi = {
  list(workspaceId: string, limit = 50, offset = 0): Promise<Agent[]> {
    return apiGet<Agent[]>(`/workspaces/${workspaceId}/agents/?limit=${limit}&offset=${offset}`);
  },

  get(workspaceId: string, agentId: string): Promise<Agent> {
    return apiGet<Agent>(`/workspaces/${workspaceId}/agents/${agentId}`);
  },

  create(workspaceId: string, data: CreateAgent): Promise<Agent> {
    return apiPost<Agent>(`/workspaces/${workspaceId}/agents/`, data);
  },

  update(workspaceId: string, agentId: string, data: UpdateAgent): Promise<Agent> {
    return apiPatch<Agent>(`/workspaces/${workspaceId}/agents/${agentId}`, data);
  },

  delete(workspaceId: string, agentId: string): Promise<void> {
    return apiDelete<void>(`/workspaces/${workspaceId}/agents/${agentId}`);
  },
};
