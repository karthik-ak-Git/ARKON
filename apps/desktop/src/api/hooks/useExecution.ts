import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { executionApi } from '../index';
import type { SubmitTaskRequest } from '../index';

export function useExecutionSummary() {
  return useQuery({
    queryKey: ['execution', 'summary'],
    queryFn: () => executionApi.getSummary(),
    staleTime: 10_000,
    refetchInterval: 15_000,
  });
}

export function useExecutionTask(taskId: string | null) {
  return useQuery({
    queryKey: ['execution', 'tasks', taskId],
    queryFn: () => executionApi.getTaskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'running' || status === 'pending') return 5_000;
      return false;
    },
  });
}

export function useSubmitTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SubmitTaskRequest) => executionApi.submitTask(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['execution', 'summary'] }),
  });
}

export function useCancelTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, reason }: { taskId: string; reason?: string }) =>
      executionApi.cancelTask(taskId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['execution'] });
    },
  });
}

export function usePauseTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => executionApi.pauseTask(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['execution'] }),
  });
}

export function useResumeTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => executionApi.resumeTask(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['execution'] }),
  });
}
