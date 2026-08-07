import { apiGet, apiPost, apiPatch, apiDelete } from './client';
import type { Project, CreateProject, UpdateProject } from './types';

export const projectsApi = {
  list(workspaceId: string, limit = 50, offset = 0): Promise<Project[]> {
    return apiGet<Project[]>(`/workspaces/${workspaceId}/projects/?limit=${limit}&offset=${offset}`);
  },

  get(workspaceId: string, projectId: string): Promise<Project> {
    return apiGet<Project>(`/workspaces/${workspaceId}/projects/${projectId}`);
  },

  create(workspaceId: string, data: CreateProject): Promise<Project> {
    return apiPost<Project>(`/workspaces/${workspaceId}/projects/`, data);
  },

  update(workspaceId: string, projectId: string, data: UpdateProject): Promise<Project> {
    return apiPatch<Project>(`/workspaces/${workspaceId}/projects/${projectId}`, data);
  },

  delete(workspaceId: string, projectId: string): Promise<void> {
    return apiDelete<void>(`/workspaces/${workspaceId}/projects/${projectId}`);
  },
};
