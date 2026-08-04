import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { EventBus } from '../../../packages/agent-sdk/src/EventBus.js'
import { EventStore } from '../../../packages/agent-sdk/src/EventStore.js'
import { EventTracer } from '../../../packages/agent-sdk/src/EventTracer.js'
import { EventMonitor } from '../../../packages/agent-sdk/src/EventMonitor.js'
import { EventType, Event } from '../../../packages/agent-sdk/src/types.js'

describe('Event System Integration', () => {
  let bus: EventBus
  let store: EventStore
  let tracer: EventTracer
  let monitor: EventMonitor

  beforeEach(() => {
    bus = new EventBus()
    store = new EventStore()
    tracer = new EventTracer()
    monitor = new EventMonitor()
  })

  afterEach(async () => {
    monitor.stopCollection()
    await bus.shutdown()
  })

  describe('EventBus + EventStore', () => {
    it('should store events from bus to store', () => {
      // Subscribe to events and store them
      bus.subscribe('*', (event: Event) => {
        store.store(event)
      })

      bus.publish(EventType.AGENT_STARTED, { agentId: 'agent-1' })
      bus.publish(EventType.AGENT_COMPLETED, { agentId: 'agent-1' })

      expect(store.size).toBe(2)
      expect(store.getByType(EventType.AGENT_STARTED)).toHaveLength(1)
      expect(store.getByType(EventType.AGENT_COMPLETED)).toHaveLength(1)
    })

    it('should replay events from store', () => {
      // Store some events manually
      store.store({
        id: 'evt-1',
        type: EventType.AGENT_STARTED,
        payload: { agentId: 'agent-1' },
        metadata: { source: 'test', version: 1 },
        timestamp: Date.now() - 2000,
      })
      store.store({
        id: 'evt-2',
        type: EventType.AGENT_COMPLETED,
        payload: { agentId: 'agent-1' },
        metadata: { source: 'test', version: 1 },
        timestamp: Date.now() - 1000,
      })

      const handler = vi.fn()
      bus.subscribe('*', handler)

      // Replay from store
      const events = store.query({ types: [EventType.AGENT_STARTED] })
      for (const event of events) {
        bus.publish(event.type, event.payload, event.metadata)
      }

      expect(handler).toHaveBeenCalledTimes(1)
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({ type: EventType.AGENT_STARTED })
      )
    })
  })

  describe('EventBus + EventTracer', () => {
    it('should trace events through bus', () => {
      bus.subscribe('*', (event: Event) => {
        tracer.startTrace(event)
      })

      const event = bus.publish(EventType.AGENT_STARTED, { agentId: 'agent-1' })
      const trace = tracer.getTrace(event.id)

      expect(trace).toBeDefined()
      expect(trace?.eventId).toBe(event.id)
      expect(trace?.status).toBe('pending')
    })

    it('should trace event chains', () => {
      // Start root trace
      const rootEvent = bus.publish(EventType.WORKFLOW_STARTED, { workflowId: 'wf-1' })
      tracer.startTrace(rootEvent)

      // Create child spans
      const step1Event = bus.publish(EventType.WORKFLOW_STEP_COMPLETED, {
        workflowId: 'wf-1',
        step: 1,
      })
      tracer.createSpan(tracer.getTrace(rootEvent.id)!.traceId, step1Event)

      // Complete traces
      tracer.completeTrace(rootEvent.id, 'success')
      tracer.completeTrace(step1Event.id, 'success')

      const rootTrace = tracer.getTrace(rootEvent.id)
      const childTrace = tracer.getTrace(step1Event.id)

      expect(rootTrace?.status).toBe('success')
      expect(childTrace?.status).toBe('success')
      expect(childTrace?.parentTraceId).toBe(rootTrace?.spanId)
    })
  })

  describe('EventBus + EventMonitor', () => {
    it('should monitor event flow', () => {
      bus.subscribe('*', (event: Event) => {
        monitor.trackEvent(event)
        monitor.trackActiveSubscriptions(bus.stats.activeSubscriptions)
      })

      // Publish events
      for (let i = 0; i < 10; i++) {
        bus.publish(EventType.AGENT_STARTED, { agentId: `agent-${i}` })
      }

      const metrics = monitor.collectMetrics()
      expect(metrics.activeSubscriptions).toBeGreaterThanOrEqual(0)
    })

    it('should track delivery times', () => {
      const deliveryTimes: number[] = []

      bus.subscribe('*', (event: Event) => {
        const start = Date.now()
        // Simulate processing
        const duration = Math.random() * 50
        const elapsed = Date.now() - start + duration
        deliveryTimes.push(elapsed)
        monitor.trackDeliveryTime(elapsed)
      })

      for (let i = 0; i < 5; i++) {
        bus.publish(EventType.AGENT_STARTED, { agentId: `agent-${i}` })
      }

      const metrics = monitor.collectMetrics()
      expect(metrics.averageDeliveryTimeMs).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Full Pipeline', () => {
    it('should handle complete event lifecycle', () => {
      const receivedEvents: Event[] = []

      // Setup monitoring
      bus.subscribe('*', (event: Event) => {
        receivedEvents.push(event)
        store.store(event)
        tracer.startTrace(event)
        monitor.trackEvent(event)
      })

      // Simulate workflow execution
      const correlationId = bus.createCorrelationId()

      const workflowEvent = bus.publish(EventType.WORKFLOW_STARTED, {
        workflowId: 'wf-1',
      }, { correlationId, source: 'workflow-engine' })

      tracer.startTrace(workflowEvent)

      // Step 1
      const step1Event = bus.publish(EventType.WORKFLOW_STEP_COMPLETED, {
        workflowId: 'wf-1',
        step: 1,
      }, { correlationId, source: 'step-executor' })

      tracer.createSpan(
        tracer.getTrace(workflowEvent.id)!.traceId,
        step1Event
      )
      tracer.completeTrace(step1Event.id, 'success')

      // Step 2
      const step2Event = bus.publish(EventType.WORKFLOW_STEP_COMPLETED, {
        workflowId: 'wf-1',
        step: 2,
      }, { correlationId, source: 'step-executor' })

      tracer.createSpan(
        tracer.getTrace(workflowEvent.id)!.traceId,
        step2Event
      )
      tracer.completeTrace(step2Event.id, 'success')

      // Complete workflow
      tracer.completeTrace(workflowEvent.id, 'success')

      const completionEvent = bus.publish(EventType.WORKFLOW_COMPLETED, {
        workflowId: 'wf-1',
        success: true,
      }, { correlationId, source: 'workflow-engine' })

      // Verify all systems captured the events
      expect(receivedEvents).toHaveLength(4)
      expect(store.size).toBe(4)
      expect(tracer.size).toBe(4)

      // Verify store queries
      const workflowEvents = store.getByCorrelationId(correlationId)
      expect(workflowEvents).toHaveLength(4)

      // Verify tracer
      const rootTrace = tracer.getTrace(workflowEvent.id)
      expect(rootTrace?.status).toBe('success')

      // Verify monitor
      const metrics = monitor.collectMetrics()
      expect(metrics.eventsPerSecond).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Error Handling', () => {
    it('should handle errors in handlers gracefully', () => {
      const failingHandler = vi.fn().mockImplementation(() => {
        throw new Error('Handler failed')
      })
      const successHandler = vi.fn()

      bus.subscribe(EventType.AGENT_STARTED, failingHandler)
      bus.subscribe(EventType.AGENT_STARTED, successHandler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })

      // Both handlers should be called
      expect(failingHandler).toHaveBeenCalledTimes(1)
      expect(successHandler).toHaveBeenCalledTimes(1)

      // Failed event should be in dead letter queue
      expect(bus.getDeadLetters()).toHaveLength(1)
    })

    it('should track errors in monitor', () => {
      monitor.trackError()
      monitor.trackError()

      const stats = monitor.getStats()
      expect(stats.totalErrors).toBe(2)
    })
  })

  describe('Performance', () => {
    it('should handle high throughput', () => {
      const eventCount = 1000
      const handler = vi.fn()
      bus.subscribe('*', handler)

      const start = Date.now()
      for (let i = 0; i < eventCount; i++) {
        bus.publish(EventType.AGENT_STARTED, { agentId: `agent-${i}` })
      }
      const duration = Date.now() - start

      expect(handler).toHaveBeenCalledTimes(eventCount)
      expect(duration).toBeLessThan(5000) // Should complete within 5 seconds
    })
  })
})