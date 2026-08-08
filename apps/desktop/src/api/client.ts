/**
 * Base HTTP client. All API modules use this.
 */

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const AI_BASE = import.meta.env.VITE_AI_URL || 'http://localhost:8000/ai';
export const RUNTIME_BASE = import.meta.env.VITE_RUNTIME_URL || 'http://localhost:8000/api/runtime';
export const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  base: string = API_BASE,
): Promise<T> {
  const url = `${base}${path}`;
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
    throw new ApiError(response.status, error.detail || `API error: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export function apiGet<T>(path: string, base?: string): Promise<T> {
  return request<T>('GET', path, undefined, base);
}

export function apiPost<T>(path: string, body?: unknown, base?: string): Promise<T> {
  return request<T>('POST', path, body, base);
}

export function apiPatch<T>(path: string, body?: unknown, base?: string): Promise<T> {
  return request<T>('PATCH', path, body, base);
}

export function apiPut<T>(path: string, body?: unknown, base?: string): Promise<T> {
  return request<T>('PUT', path, body, base);
}

export function apiDelete<T>(path: string, base?: string): Promise<T> {
  return request<T>('DELETE', path, undefined, base);
}
