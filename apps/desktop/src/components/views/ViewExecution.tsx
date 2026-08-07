import { useState } from 'react';
import { useExecutionSummary, useExecutionTask, useSubmitTask, useCancelTask, usePauseTask, useResumeTask } from '../../api/hooks';
import { Activity, Play, Pause, X, Loader2, CheckCircle2, AlertCircle, RotateCcw, ChevronRight } from 'lucide-react';

const STATUS_ICONS: Record<string, typeof Activity> = {
  running: Loader2,
  completed: CheckCircle2,
  failed: AlertCircle,
  paused: Pause,
  cancelled: X,
};

export function ViewExecution() {
  const { data: summary, isLoading, isError } = useExecutionSummary();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const { data: selectedTask } = useExecutionTask(selectedTaskId || '');
  const cancelMutation = useCancelTask();
  const pauseMutation = usePauseTask();
  const resumeMutation = useResumeTask();

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Execution Monitor</h2>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-3 mb-8">
        {[
          { label: 'Total', value: summary?.total_tasks ?? 0, color: 'text-gray-900 dark:text-gray-100' },
          { label: 'Running', value: summary?.running ?? 0, color: 'text-blue-600 dark:text-blue-400' },
          { label: 'Completed', value: summary?.completed ?? 0, color: 'text-green-600 dark:text-green-400' },
          { label: 'Failed', value: summary?.failed ?? 0, color: 'text-red-600 dark:text-red-400' },
        ].map((s) => (
          <div key={s.label} className="p-3 rounded-xl border border-gray-200 dark:border-white/10">
            <p className="text-xs text-gray-400 dark:text-gray-500">{s.label}</p>
            <p className={`text-2xl font-medium ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-500">
          <Activity className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">Unable to load execution data.</p>
          <p className="text-sm mt-1">Backend may be offline.</p>
        </div>
      ) : summary && summary.total_tasks === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-500">
          <Activity className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">No tasks executed yet.</p>
          <p className="text-sm mt-1">Submit a task from the command box to get started.</p>
        </div>
      ) : summary ? (
        <div className="flex gap-4">
          {/* Summary detail */}
          <div className={`${selectedTaskId ? 'w-1/2' : 'w-full'} transition-all`}>
            <div className="space-y-2">
              <div className="p-4 rounded-xl border border-gray-200 dark:border-white/10">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Pending:</span>{' '}
                    <span className="font-medium">{summary.pending}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Cancelled:</span>{' '}
                    <span className="font-medium">{summary.cancelled}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Completed:</span>{' '}
                    <span className="font-medium">{summary.completed}</span>
                  </div>
                </div>
              </div>

              {selectedTask && (
                <div className="p-4 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.02]">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-medium">Task Detail</h3>
                    <button onClick={() => setSelectedTaskId(null)} className="text-gray-400 hover:text-gray-600 text-xs">Close</button>
                  </div>
                  <div className="space-y-3 text-sm">
                    <div><span className="text-gray-400">ID:</span> <span className="font-mono text-xs">{selectedTask.task_id}</span></div>
                    <div><span className="text-gray-400">Type:</span> {selectedTask.task_type}</div>
                    <div><span className="text-gray-400">Status:</span> <span className="font-medium">{selectedTask.status}</span></div>
                    <div><span className="text-gray-400">Agent:</span> {selectedTask.agent_id || '—'}</div>
                    {selectedTask.progress > 0 && (
                      <div>
                        <span className="text-gray-400">Progress:</span> {Math.round(selectedTask.progress * 100)}%
                        <div className="mt-1 h-1.5 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
                          <div className="h-full rounded-full bg-blue-500 transition-all" style={{ width: `${selectedTask.progress * 100}%` }} />
                        </div>
                      </div>
                    )}
                    {selectedTask.error_message && (
                      <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs">
                        {selectedTask.error_message}
                      </div>
                    )}
                    {selectedTask.output_data && (
                      <div>
                        <span className="text-gray-400">Output:</span>
                        <pre className="mt-1 p-2 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 text-xs overflow-auto max-h-40">
                          {JSON.stringify(selectedTask.output_data, null, 2)}
                        </pre>
                      </div>
                    )}
                    <div className="flex gap-2 pt-2">
                      {selectedTask.status === 'running' && (
                        <>
                          <button
                            onClick={() => pauseMutation.mutate(selectedTask.task_id)}
                            disabled={pauseMutation.isPending}
                            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20"
                          >
                            <Pause className="w-3 h-3" /> Pause
                          </button>
                          <button
                            onClick={() => cancelMutation.mutate({ taskId: selectedTask.task_id })}
                            disabled={cancelMutation.isPending}
                            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                          >
                            <X className="w-3 h-3" /> Cancel
                          </button>
                        </>
                      )}
                      {selectedTask.status === 'paused' && (
                        <button
                          onClick={() => resumeMutation.mutate(selectedTask.task_id)}
                          disabled={resumeMutation.isPending}
                          className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
                        >
                          <Play className="w-3 h-3" /> Resume
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
