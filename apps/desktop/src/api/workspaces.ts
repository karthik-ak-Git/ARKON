import { apiGet, apiPost, apiPatch, apiDelete } from './client';
import type { Workspace, WorkspaceList, CreateWorkspace, UpdateWorkspace, WorkspaceSnapshot } from './types';

export const workspacesApi = {
  list(limit = 50, offset = 0): Promise<WorkspaceList> {
    return apiGet<WorkspaceList>(`/workspaces/?limit=${limit}&offset=${offset}`);
  },

  get(id: string): Promise<Workspace> {
    return apiGet<Workspace>(`/workspaces/${id}`);
  },

  create(data: CreateWorkspace): Promise<Workspace> {
    return apiPost<Workspace>('/workspaces/', data);
  },

  update(id: string, data: UpdateWorkspace): Promise<Workspace> {
    return apiPatch<Workspace>(`/workspaces/${id}`, data);
  },

  delete(id: string): Promise<void> {
    return apiDelete<void>(`/workspaces/${id}`);
  },

  open(id: string): Promise<Workspace> {
    return apiPost<Workspace>(`/workspaces/${id}/open`);
  },

  close(id: string): Promise<{ status: string; workspace_id: string }> {
    return apiPost<{ status: string; workspace_id: string }>(`/workspaces/${id}/close`);
  },

  suspend(id: string, reason?: string): Promise<{ status: string; workspace_id: string }> {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    return apiPost<{ status: string; workspace_id: string }>(`/workspaces/${id}/suspend${params}`);
  },

  resume(id: string): Promise<{ status: string; workspace_id: string }> {
    return apiPost<{ status: string; workspace_id: string }>(`/workspaces/${id}/resume`);
  },

  createSnapshot(id: string, name?: string): Promise<WorkspaceSnapshot> {
    return apiPost<WorkspaceSnapshot>(`/workspaces/${id}/snapshots`, { name });
  },

  restoreSnapshot(id: string, snapshotId: string): Promise<{ status: string; workspace_id: string; snapshot_id: string }> {
    return apiPost<{ status: string; workspace_id: string; snapshot_id: string }>(
      `/workspaces/${id}/snapshots/${snapshotId}/restore`,
    );
  },
};
