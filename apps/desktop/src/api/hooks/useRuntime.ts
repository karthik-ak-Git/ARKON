import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { runtimeApi } from '../index';

export function useRuntimeAgents() {
  return useQuery({
    queryKey: ['runtime', 'agents'],
    queryFn: () => runtimeApi.listAgents(),
    staleTime: 10_000,
    refetchInterval: 15_000,
  });
}

export function useRuntimeAgent(agentId: string | null) {
  return useQuery({
    queryKey: ['runtime', 'agents', agentId],
    queryFn: () => runtimeApi.getAgent(agentId!),
    enabled: !!agentId,
    refetchInterval: 10_000,
  });
}

export function useAgentRegistry() {
  return useQuery({
    queryKey: ['runtime', 'registry'],
    queryFn: () => runtimeApi.getRegistry(),
    staleTime: 60_000,
  });
}

export function useCapabilities() {
  return useQuery({
    queryKey: ['runtime', 'capabilities'],
    queryFn: () => runtimeApi.getCapabilities(),
    staleTime: 60_000,
  });
}

export function useResourceUsage() {
  return useQuery({
    queryKey: ['runtime', 'resources'],
    queryFn: () => runtimeApi.getResources(),
    staleTime: 10_000,
    refetchInterval: 10_000,
  });
}

export function useSpawnAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      agent_type: string;
      name?: string;
      capabilities?: string[];
      config?: Record<string, unknown>;
    }) => runtimeApi.spawnAgent(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runtime', 'agents'] }),
  });
}

export function useStartAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => runtimeApi.startAgent(agentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runtime', 'agents'] }),
  });
}

export function usePauseRuntimeAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => runtimeApi.pauseAgent(agentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runtime', 'agents'] }),
  });
}

export function useResumeRuntimeAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => runtimeApi.resumeAgent(agentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runtime', 'agents'] }),
  });
}

export function useCancelRuntimeAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => runtimeApi.cancelAgent(agentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runtime', 'agents'] }),
  });
}

export function useDeleteRuntimeAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => runtimeApi.deleteAgent(agentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runtime', 'agents'] }),
  });
}

export function useExecuteRuntimeTask() {
  return useMutation({
    mutationFn: ({
      agentId,
      taskType,
      inputData,
    }: {
      agentId: string;
      taskType: string;
      inputData?: Record<string, unknown>;
    }) => runtimeApi.executeTask(agentId, { task_type: taskType, input_data: inputData }),
  });
}
