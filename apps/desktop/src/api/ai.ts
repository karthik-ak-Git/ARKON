import { apiGet, apiPost, apiPut, apiPatch, apiDelete, AI_BASE } from './client';
import type {
  AIProviderInfo,
  AIProviderCreate,
  AIProviderUpdate,
  AIHealthResponse,
  AIModelInfo,
  AIChatRequest,
  AIChatResponse,
  AIRoutingDecision,
} from './types';

function aiGet<T>(path: string): Promise<T> {
  return apiGet<T>(path, AI_BASE);
}

function aiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiPost<T>(path, body, AI_BASE);
}

function aiPut<T>(path: string, body?: unknown): Promise<T> {
  return apiPut<T>(path, body, AI_BASE);
}

function aiPatch<T>(path: string, body?: unknown): Promise<T> {
  return apiPatch<T>(path, body, AI_BASE);
}

function aiDelete<T>(path: string): Promise<T> {
  return apiDelete<T>(path, AI_BASE);
}

export const aiApi = {
  // Providers
  listProviders(): Promise<{ providers: AIProviderInfo[] }> {
    return aiGet<{ providers: AIProviderInfo[] }>('/providers');
  },

  registerProvider(data: AIProviderCreate): Promise<AIProviderInfo> {
    return aiPost<AIProviderInfo>('/providers', data);
  },

  updateProvider(providerId: string, data: AIProviderUpdate): Promise<AIProviderInfo> {
    return aiPut<AIProviderInfo>(`/providers/${providerId}`, data);
  },

  enableProvider(providerId: string): Promise<{ provider_id: string; enabled: boolean }> {
    return aiPatch<{ provider_id: string; enabled: boolean }>(`/providers/${providerId}/enable`);
  },

  disableProvider(providerId: string): Promise<{ provider_id: string; enabled: boolean }> {
    return aiPatch<{ provider_id: string; enabled: boolean }>(`/providers/${providerId}/disable`);
  },

  deleteProvider(providerId: string): Promise<{ provider_id: string; removed: boolean }> {
    return aiDelete<{ provider_id: string; removed: boolean }>(`/providers/${providerId}`);
  },

  // Health
  getProviderHealth(providerId: string): Promise<AIHealthResponse> {
    return aiGet<AIHealthResponse>(`/providers/${providerId}/health`);
  },

  getAllProvidersHealth(): Promise<Record<string, AIHealthResponse>> {
    return aiGet<Record<string, AIHealthResponse>>('/providers/health');
  },

  detectLocalProviders(): Promise<{ detected: string[] }> {
    return aiPost<{ detected: string[] }>('/providers/detect-local');
  },

  // Models
  listModels(providerId?: string): Promise<{ models: AIModelInfo[] }> {
    const params = providerId ? `?provider_id=${providerId}` : '';
    return aiGet<{ models: AIModelInfo[] }>(`/models${params}`);
  },

  // Chat
  chat(data: AIChatRequest): Promise<AIChatResponse> {
    return aiPost<AIChatResponse>('/chat', data);
  },

  // Routing
  getRoutingPolicy(): Promise<AIRoutingDecision> {
    return aiGet<AIRoutingDecision>('/routing');
  },

  setRoutingPolicy(data: { policy: string; manual_provider_id?: string }): Promise<AIRoutingDecision> {
    return aiPut<AIRoutingDecision>('/routing', data);
  },
};
