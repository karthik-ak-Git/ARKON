/**
 * WebSocketProvider — connects to runtime + execution WebSockets
 * and invalidates React Query caches on real-time events.
 */

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getRuntimeWs, getExecutionWs } from './websocket';
import type { RuntimeWSEvent, ExecutionWSEvent } from './types';

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const runtimeWs = getRuntimeWs();
    const executionWs = getExecutionWs();

    // Subscribe to runtime events
    const unsubRuntime = runtimeWs.subscribe((event) => {
      const e = event as RuntimeWSEvent;
      switch (e.type) {
        case 'agent_spawned':
        case 'agent_state_changed':
        case 'agent_removed':
        case 'agent_task_completed':
          // Invalidate runtime agent list + registry
          queryClient.invalidateQueries({ queryKey: ['runtime', 'agents'] });
          queryClient.invalidateQueries({ queryKey: ['runtime', 'registry'] });
          queryClient.invalidateQueries({ queryKey: ['runtime', 'resources'] });
          break;
        case 'agent_task_output':
          // Invalidate task detail if task ID present
          if (e.task_id) {
            queryClient.invalidateQueries({ queryKey: ['execution', 'task', e.task_id] });
          }
          break;
      }
    });

    // Subscribe to execution events
    const unsubExecution = executionWs.subscribe((event) => {
      const e = event as ExecutionWSEvent;
      switch (e.type) {
        case 'task_started':
        case 'task_progress':
        case 'task_completed':
        case 'task_failed':
        case 'task_output':
          // Invalidate execution summary + task detail
          queryClient.invalidateQueries({ queryKey: ['execution', 'summary'] });
          if (e.task_id) {
            queryClient.invalidateQueries({ queryKey: ['execution', 'task', e.task_id] });
          }
          break;
      }
    });

    // Connect
    runtimeWs.connect();
    executionWs.connect();

    return () => {
      unsubRuntime();
      unsubExecution();
      runtimeWs.disconnect();
      executionWs.disconnect();
    };
  }, [queryClient]);

  return <>{children}</>;
}
