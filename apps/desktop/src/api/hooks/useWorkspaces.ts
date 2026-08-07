import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workspacesApi } from '../index';
import type { CreateWorkspace, UpdateWorkspace, WorkspaceList } from '../index';

export function useWorkspaces() {
  return useQuery({
    queryKey: ['workspaces'],
    queryFn: (): Promise<WorkspaceList> => workspacesApi.list(),
    staleTime: 30_000,
  });
}

export function useWorkspace(id: string | null) {
  return useQuery({
    queryKey: ['workspaces', id],
    queryFn: () => workspacesApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateWorkspace) => workspacesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }),
  });
}

export function useUpdateWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateWorkspace }) =>
      workspacesApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }),
  });
}

export function useDeleteWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workspacesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }),
  });
}

export function useOpenWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workspacesApi.open(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }),
  });
}

export function useCloseWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workspacesApi.close(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }),
  });
}
