import { apiGet, apiPost } from './client';
import type { ExecutionTask, SubmitTaskRequest, SubmitTaskResponse, ExecutionSummary } from './types';

export const executionApi = {
  submitTask(data: SubmitTaskRequest): Promise<SubmitTaskResponse> {
    return apiPost<SubmitTaskResponse>('/execution/tasks', data);
  },

  getTaskStatus(taskId: string): Promise<ExecutionTask> {
    return apiGet<ExecutionTask>(`/execution/tasks/${taskId}`);
  },

  getTaskResult(taskId: string): Promise<ExecutionTask> {
    return apiGet<ExecutionTask>(`/execution/tasks/${taskId}/result`);
  },

  cancelTask(taskId: string, reason?: string): Promise<{ task_id: string; cancelled: boolean; reason: string }> {
    return apiPost<{ task_id: string; cancelled: boolean; reason: string }>(
      `/execution/tasks/${taskId}/cancel`,
      { reason: reason || 'User cancelled' },
    );
  },

  pauseTask(taskId: string): Promise<{ task_id: string; paused: boolean }> {
    return apiPost<{ task_id: string; paused: boolean }>(`/execution/tasks/${taskId}/pause`);
  },

  resumeTask(taskId: string): Promise<{ task_id: string; resumed: boolean }> {
    return apiPost<{ task_id: string; resumed: boolean }>(`/execution/tasks/${taskId}/resume`);
  },

  getSummary(): Promise<ExecutionSummary> {
    return apiGet<ExecutionSummary>('/execution/summary');
  },
};
