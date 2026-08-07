import { Activity, Loader2 } from 'lucide-react'
import { useExecutionSummary, useExecutionTask } from '@/api/hooks'
import { useState } from 'react'

export function Monitoring() {
  const { data: summary, isLoading, isError } = useExecutionSummary()
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const { data: selectedTask } = useExecutionTask(selectedTaskId)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Monitoring</h1>
        <p className="text-muted-foreground">Monitor task execution and system health</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : isError ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground">Unable to load execution data</p>
          <p className="text-sm text-muted-foreground/70 mt-1">Backend may be offline</p>
        </div>
      ) : summary && summary.total_tasks === 0 ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground">No tasks executed yet</p>
          <p className="text-sm text-muted-foreground/70 mt-1">Submit a task to see execution data</p>
        </div>
      ) : summary ? (
        <div className="space-y-4">
          <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
            {[
              { label: 'Total', value: summary.total_tasks },
              { label: 'Running', value: summary.running },
              { label: 'Completed', value: summary.completed },
              { label: 'Failed', value: summary.failed },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg border bg-card p-4">
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="text-2xl font-bold">{stat.value}</p>
              </div>
            ))}
          </div>

          {selectedTask && (
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium">Task Detail</h3>
                <button onClick={() => setSelectedTaskId(null)} className="text-sm text-muted-foreground hover:text-foreground">
                  Close
                </button>
              </div>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground">ID:</span>{' '}
                  <span className="font-mono text-xs">{selectedTask.task_id}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span> {selectedTask.status}
                </div>
                <div>
                  <span className="text-muted-foreground">Agent:</span> {selectedTask.agent_id || '—'}
                </div>
                {selectedTask.error_message && (
                  <div className="p-2 rounded bg-destructive/10 text-destructive text-xs">
                    {selectedTask.error_message}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
