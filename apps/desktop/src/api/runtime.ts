import { apiGet, apiPost, apiDelete } from './client';
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
    return apiGet<RuntimeAgentList>('/runtime/agents');
  },

  getAgent(agentId: string): Promise<RuntimeAgent> {
    return apiGet<RuntimeAgent>(`/runtime/agents/${agentId}`);
  },

  spawnAgent(data: {
    agent_type: string;
    name?: string;
    capabilities?: string[];
    config?: Record<string, unknown>;
  }): Promise<RuntimeAgent> {
    return apiPost<RuntimeAgent>('/runtime/agents', data);
  },

  deleteAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiDelete<{ status: string; agent_id: string }>(`/runtime/agents/${agentId}`);
  },

  startAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/runtime/agents/${agentId}/start`);
  },

  pauseAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/runtime/agents/${agentId}/pause`);
  },

  resumeAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/runtime/agents/${agentId}/resume`);
  },

  cancelAgent(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiPost<{ status: string; agent_id: string }>(`/runtime/agents/${agentId}/cancel`);
  },

  getAgentHealth(agentId: string): Promise<Record<string, unknown>> {
    return apiGet<Record<string, unknown>>(`/runtime/agents/${agentId}/health`);
  },

  getAgentHeartbeat(agentId: string): Promise<Record<string, unknown>> {
    return apiGet<Record<string, unknown>>(`/runtime/agents/${agentId}/heartbeat`);
  },

  sendHeartbeat(agentId: string, data: { status?: string; metrics?: Record<string, unknown> }): Promise<Record<string, unknown>> {
    return apiPost<Record<string, unknown>>(`/runtime/agents/${agentId}/heartbeat`, data);
  },

  executeTask(agentId: string, data: { task_type: string; input_data?: Record<string, unknown> }): Promise<{ agent_id: string; result: unknown }> {
    return apiPost<{ agent_id: string; result: unknown }>(`/runtime/agents/${agentId}/execute`, data);
  },

  getAgentState(agentId: string): Promise<{ agent_id: string; state: string }> {
    return apiGet<{ agent_id: string; state: string }>(`/runtime/agents/${agentId}/state`);
  },

  // Registry
  getRegistry(): Promise<AgentRegistry> {
    return apiGet<AgentRegistry>('/runtime/registry');
  },

  getRegistryEntry(agentType: string): Promise<Record<string, unknown>> {
    return apiGet<Record<string, unknown>>(`/runtime/registry/${agentType}`);
  },

  // Capabilities
  getCapabilities(): Promise<CapabilityList> {
    return apiGet<CapabilityList>('/runtime/capabilities');
  },

  findAgentsByCapability(capability: string): Promise<{ capability: string; agents: string[] }> {
    return apiGet<{ capability: string; agents: string[] }>(`/runtime/capabilities/${capability}`);
  },

  // Resources
  getResources(): Promise<ResourceUsage> {
    return apiGet<ResourceUsage>('/runtime/resources');
  },
};
