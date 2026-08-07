import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../index';
import type { CreateProject, UpdateProject } from '../index';

export function useProjects(workspaceId: string | null) {
  return useQuery({
    queryKey: ['projects', workspaceId],
    queryFn: () => projectsApi.list(workspaceId!),
    enabled: !!workspaceId,
    staleTime: 30_000,
  });
}

export function useProject(workspaceId: string | null, projectId: string | null) {
  return useQuery({
    queryKey: ['projects', workspaceId, projectId],
    queryFn: () => projectsApi.get(workspaceId!, projectId!),
    enabled: !!workspaceId && !!projectId,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workspaceId, data }: { workspaceId: string; data: CreateProject }) =>
      projectsApi.create(workspaceId, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['projects', variables.workspaceId] });
    },
  });
}

export function useUpdateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      workspaceId,
      projectId,
      data,
    }: {
      workspaceId: string;
      projectId: string;
      data: UpdateProject;
    }) => projectsApi.update(workspaceId, projectId, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['projects', variables.workspaceId] });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workspaceId, projectId }: { workspaceId: string; projectId: string }) =>
      projectsApi.delete(workspaceId, projectId),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['projects', variables.workspaceId] });
    },
  });
}
