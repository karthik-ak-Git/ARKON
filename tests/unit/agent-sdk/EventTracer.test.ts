import { describe, it, expect, beforeEach } from 'vitest'
import { EventTracer } from '../../../packages/agent-sdk/src/EventTracer.js'
import { Event, EventType } from '../../../packages/agent-sdk/src/types.js'

function createEvent(overrides: Partial<Event> = {}): Event {
  return {
    id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    type: EventType.AGENT_STARTED,
    payload: { agentId: 'test-agent' },
    metadata: {
      source: 'test-source',
      version: 1,
    },
    timestamp: Date.now(),
    ...overrides,
  }
}

describe('EventTracer', () => {
  let tracer: EventTracer

  beforeEach(() => {
    tracer = new EventTracer()
  })

  describe('Construction', () => {
    it('should create an EventTracer with default config', () => {
      expect(tracer).toBeDefined()
      expect(tracer.config.enabled).toBe(true)
      expect(tracer.config.sampleRate).toBe(1.0)
    })

    it('should accept custom config', () => {
      const customTracer = new EventTracer({ sampleRate: 0.5 })
      expect(customTracer.config.sampleRate).toBe(0.5)
    })
  })

  describe('Tracing', () => {
    it('should start a trace', () => {
      const event = createEvent()
      const trace = tracer.startTrace(event)
      expect(trace).toBeDefined()
      expect(trace.eventId).toBe(event.id)
      expect(trace.eventType).toBe(EventType.AGENT_STARTED)
      expect(trace.traceId).toBeDefined()
      expect(trace.spanId).toBeDefined()
      expect(trace.status).toBe('pending')
    })

    it('should complete a trace', () => {
      const event = createEvent()
      tracer.startTrace(event)

      tracer.completeTrace(event.id, 'success')
      const trace = tracer.getTrace(event.id)
      expect(trace?.status).toBe('success')
      expect(trace?.duration).toBeDefined()
    })

    it('should fail a trace with error', () => {
      const event = createEvent()
      tracer.startTrace(event)

      tracer.failTrace(event.id, 'Something went wrong')
      const trace = tracer.getTrace(event.id)
      expect(trace?.status).toBe('error')
      expect(trace?.error).toBe('Something went wrong')
    })

    it('should return noop trace when disabled', () => {
      const disabledTracer = new EventTracer({ enabled: false })
      const event = createEvent()
      const trace = disabledTracer.startTrace(event)
      expect(trace.traceId).toBe('')
      expect(trace.spanId).toBe('')
    })
  })

  describe('Span Management', () => {
    it('should create a child span', () => {
      const parentEvent = createEvent()
      tracer.startTrace(parentEvent)

      const childEvent = createEvent()
      const childTrace = tracer.createSpan(
        tracer.getTrace(parentEvent.id)!.traceId,
        childEvent
      )

      expect(childTrace.parentTraceId).toBeDefined()
      expect(childTrace.traceId).toBe(tracer.getTrace(parentEvent.id)!.traceId)
    })

    it('should get child traces', () => {
      const parentEvent = createEvent()
      const parentTrace = tracer.startTrace(parentEvent)

      const child1 = createEvent()
      const child2 = createEvent()
      tracer.createSpan(parentTrace.traceId, child1)
      tracer.createSpan(parentTrace.traceId, child2)

      const children = tracer.getChildTraces(parentTrace.traceId)
      expect(children).toHaveLength(2)
    })
  })

  describe('Retrieval', () => {
    it('should get trace by event ID', () => {
      const event = createEvent()
      tracer.startTrace(event)

      const trace = tracer.getTrace(event.id)
      expect(trace).toBeDefined()
      expect(trace?.eventId).toBe(event.id)
    })

    it('should get traces by trace ID', () => {
      const event1 = createEvent()
      const event2 = createEvent()
      tracer.startTrace(event1)
      tracer.startTrace(event2)

      const trace1 = tracer.getTrace(event1.id)!
      const traces = tracer.getTraceByTraceId(trace1.traceId)
      expect(traces.length).toBeGreaterThanOrEqual(1)
    })

    it('should get trace by span ID', () => {
      const event = createEvent()
      const trace = tracer.startTrace(event)

      const retrieved = tracer.getTraceBySpanId(trace.spanId)
      expect(retrieved).toBeDefined()
      expect(retrieved?.eventId).toBe(event.id)
    })

    it('should return undefined for non-existent trace', () => {
      expect(tracer.getTrace('non-existent')).toBeUndefined()
    })
  })

  describe('Query', () => {
    it('should query traces by status', () => {
      const event1 = createEvent()
      const event2 = createEvent()
      tracer.startTrace(event1)
      tracer.startTrace(event2)
      tracer.completeTrace(event1.id, 'success')

      const successTraces = tracer.query({ status: 'success' })
      expect(successTraces).toHaveLength(1)
      expect(successTraces[0].eventId).toBe(event1.id)
    })

    it('should query traces by event type', () => {
      const event1 = createEvent({ type: EventType.AGENT_STARTED })
      const event2 = createEvent({ type: EventType.AGENT_COMPLETED })
      tracer.startTrace(event1)
      tracer.startTrace(event2)

      const startedTraces = tracer.query({ eventType: EventType.AGENT_STARTED })
      expect(startedTraces).toHaveLength(1)
    })

    it('should query traces by source', () => {
      const event1 = createEvent({ metadata: { source: 'source-a', version: 1 } })
      const event2 = createEvent({ metadata: { source: 'source-b', version: 1 } })
      tracer.startTrace(event1)
      tracer.startTrace(event2)

      const sourceATraces = tracer.query({ source: 'source-a' })
      expect(sourceATraces).toHaveLength(1)
    })

    it('should query traces with limit', () => {
      for (let i = 0; i < 10; i++) {
        tracer.startTrace(createEvent())
      }

      const limitedTraces = tracer.query({ limit: 5 })
      expect(limitedTraces).toHaveLength(5)
    })
  })

  describe('Stats', () => {
    it('should return accurate stats', () => {
      const event1 = createEvent()
      const event2 = createEvent()
      const event3 = createEvent()
      tracer.startTrace(event1)
      tracer.startTrace(event2)
      tracer.startTrace(event3)
      tracer.completeTrace(event1.id, 'success')
      tracer.failTrace(event2.id, 'Failed')

      const stats = tracer.getStats()
      expect(stats.totalTraces).toBe(3)
      expect(stats.successTraces).toBe(1)
      expect(stats.errorTraces).toBe(1)
      expect(stats.pendingTraces).toBe(1)
    })

    it('should calculate average duration', () => {
      const event1 = createEvent()
      const event2 = createEvent()
      tracer.startTrace(event1)
      tracer.startTrace(event2)
      tracer.completeTrace(event1.id, 'success')
      tracer.completeTrace(event2.id, 'success')

      const stats = tracer.getStats()
      expect(stats.averageDurationMs).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Management', () => {
    it('should clear all traces', () => {
      tracer.startTrace(createEvent())
      tracer.startTrace(createEvent())
      expect(tracer.size).toBe(2)

      tracer.clear()
      expect(tracer.size).toBe(0)
    })

    it('should delete a trace', () => {
      const event = createEvent()
      tracer.startTrace(event)
      expect(tracer.size).toBe(1)

      const deleted = tracer.delete(event.id)
      expect(deleted).toBe(true)
      expect(tracer.size).toBe(0)
    })

    it('should return false for non-existent trace', () => {
      expect(tracer.delete('non-existent')).toBe(false)
    })
  })

  describe('Export', () => {
    it('should export all traces', () => {
      tracer.startTrace(createEvent())
      tracer.startTrace(createEvent())

      const traces = tracer.traces
      expect(traces).toHaveLength(2)
    })

    it('should export traces by trace ID', () => {
      const event = createEvent()
      tracer.startTrace(event)
      const traceId = tracer.getTrace(event.id)!.traceId

      const traces = tracer.tracesByTraceId(traceId)
      expect(traces).toHaveLength(1)
    })
  })
})