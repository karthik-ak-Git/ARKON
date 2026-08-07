import { apiGet } from './client';
import type { HealthResponse } from './types';

// Health endpoint is at root /health, not under /api/v1
const HEALTH_BASE = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';

export const healthApi = {
  check(): Promise<HealthResponse> {
    return apiGet<HealthResponse>('/health', HEALTH_BASE);
  },
};
