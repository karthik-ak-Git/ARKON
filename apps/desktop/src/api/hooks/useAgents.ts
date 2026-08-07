import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentsApi } from '../index';
import type { CreateAgent, UpdateAgent } from '../index';

export function useAgents(workspaceId: string | null) {
  return useQuery({
    queryKey: ['agents', workspaceId],
    queryFn: () => agentsApi.list(workspaceId!),
    enabled: !!workspaceId,
    staleTime: 30_000,
  });
}

export function useAgent(workspaceId: string | null, agentId: string | null) {
  return useQuery({
    queryKey: ['agents', workspaceId, agentId],
    queryFn: () => agentsApi.get(workspaceId!, agentId!),
    enabled: !!workspaceId && !!agentId,
  });
}

export function useCreateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workspaceId, data }: { workspaceId: string; data: CreateAgent }) =>
      agentsApi.create(workspaceId, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['agents', variables.workspaceId] });
    },
  });
}

export function useUpdateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      workspaceId,
      agentId,
      data,
    }: {
      workspaceId: string;
      agentId: string;
      data: UpdateAgent;
    }) => agentsApi.update(workspaceId, agentId, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['agents', variables.workspaceId] });
    },
  });
}

export function useDeleteAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workspaceId, agentId }: { workspaceId: string; agentId: string }) =>
      agentsApi.delete(workspaceId, agentId),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['agents', variables.workspaceId] });
    },
  });
}
