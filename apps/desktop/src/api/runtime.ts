import { apiGet, apiPost, apiDelete, RUNTIME_BASE } from './client';
import type {
  RuntimeAgent,
  RuntimeAgentList,
  AgentRegistry,
  CapabilityList,
  ResourceUsage,
} from './types';

export const runtimeApi = {
  // Agents
  listAgents(): Promise<RuntimeAgentList> {
    return apiGet<RuntimeAgentList>('/agents', RUNTIME_BASE);
  },

  getAgent(agentId: string): Promise<RuntimeAgent> {
    return apiGet<RuntimeAgent>(`/agents/${agentId}`, RUNTIME_BASE);
  },

  spawnAgent(data: {
    agent_type: string;
    name?: string;
    capabilities?: string[];
    config?: Record<string, unknown>;
  }): Promise<RuntimeAgent> {
    return apiPost<RuntimeAgent>('/agents', data, RUNTIME_BASE);
  },

  deleteAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiDelete<{ status: string; agent_id: string }>(`/agents/${agentId}`, RUNTIME_BASE);
  },

  startAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/agents/${agentId}/start`, undefined, RUNTIME_BASE);
  },

  pauseAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/agents/${agentId}/pause`, undefined, RUNTIME_BASE);
  },

  resumeAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/agents/${agentId}/resume`, undefined, RUNTIME_BASE);
  },

  cancelAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/agents/${agentId}/cancel`, undefined, RUNTIME_BASE);
  },

  getAgentHealth(agentId: string): Promise<Record<string, unknown>> {
    return apiGet<Record<string, unknown>>(`/agents/${agentId}/health`, RUNTIME_BASE);
  },

  getAgentHeartbeat(agentId: string): Promise<Record<string, unknown>> {
    return apiGet<Record<string, unknown>>(`/agents/${agentId}/heartbeat`, RUNTIME_BASE);
  },

  sendHeartbeat(agentId: string, data: { status?: string; metrics?: Record<string, unknown> }): Promise<Record<string, unknown>> {
    return apiPost<Record<string, unknown>>(`/agents/${agentId}/heartbeat`, data, RUNTIME_BASE);
  },

  executeTask(agentId: string, data: { task_type: string; input_data?: Record<string, unknown> }): Promise<{ agent_id: string; result: unknown }> {
    return apiPost<{ agent_id: string; result: unknown }>(`/agents/${agentId}/execute`, data, RUNTIME_BASE);
  },

  getAgentState(agentId: string): Promise<{ agent_id: string; state: string }> {
    return apiGet<{ agent_id: string; state: string }>(`/agents/${agentId}/state`, RUNTIME_BASE);
  },

  // Registry
  getRegistry(): Promise<AgentRegistry> {
    return apiGet<AgentRegistry>('/registry', RUNTIME_BASE);
  },

  getRegistryEntry(agentType: string): Promise<Record<string, unknown>> {
    return apiGet<Record<string, unknown>>(`/registry/${agentType}`, RUNTIME_BASE);
  },

  // Capabilities
  getCapabilities(): Promise<CapabilityList> {
    return apiGet<CapabilityList>('/capabilities', RUNTIME_BASE);
  },

  findAgentsByCapability(capability: string): Promise<{ capability: string; agents: string[] }> {
    return apiGet<{ capability: string; agents: string[] }>(`/capabilities/${capability}`, RUNTIME_BASE);
  },

  // Resources
  getResources(): Promise<ResourceUsage> {
    return apiGet<ResourceUsage>('/resources', RUNTIME_BASE);
  },
};
