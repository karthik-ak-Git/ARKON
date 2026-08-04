import { describe, it, expect, beforeEach } from 'vitest'
import { EventStore } from '../../../packages/agent-sdk/src/EventStore.js'
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

describe('EventStore', () => {
  let store: EventStore

  beforeEach(() => {
    store = new EventStore()
  })

  describe('Construction', () => {
    it('should create an EventStore with default config', () => {
      expect(store).toBeDefined()
      expect(store.config.maxSize).toBe(100000)
    })

    it('should accept custom config', () => {
      const customStore = new EventStore({ maxSize: 500 })
      expect(customStore.config.maxSize).toBe(500)
    })
  })

  describe('Storage', () => {
    it('should store an event', () => {
      const event = createEvent()
      const entry = store.store(event)
      expect(entry).toBeDefined()
      expect(entry.event.id).toBe(event.id)
      expect(entry.storedAt).toBeDefined()
      expect(entry.accessCount).toBe(0)
    })

    it('should track store size', () => {
      expect(store.size).toBe(0)
      store.store(createEvent())
      expect(store.size).toBe(1)
      store.store(createEvent())
      expect(store.size).toBe(2)
    })

    it('should enforce max size with eviction', () => {
      const smallStore = new EventStore({ maxSize: 3 })
      smallStore.store(createEvent({ timestamp: 100 }))
      smallStore.store(createEvent({ timestamp: 200 }))
      smallStore.store(createEvent({ timestamp: 300 }))

      smallStore.store(createEvent({ timestamp: 400 }))
      expect(smallStore.size).toBe(3)
    })
  })

  describe('Retrieval', () => {
    it('should get event by ID', () => {
      const event = createEvent()
      store.store(event)
      const retrieved = store.get(event.id)
      expect(retrieved).toBeDefined()
      expect(retrieved?.id).toBe(event.id)
    })

    it('should increment access count on get', () => {
      const event = createEvent()
      store.store(event)
      store.get(event.id)
      store.get(event.id)
      const entry = store.getEntry(event.id)
      expect(entry?.accessCount).toBe(2)
    })

    it('should return undefined for non-existent event', () => {
      expect(store.get('non-existent')).toBeUndefined()
    })

    it('should get entry details', () => {
      const event = createEvent()
      store.store(event)
      const entry = store.getEntry(event.id)
      expect(entry).toBeDefined()
      expect(entry?.storedAt).toBeDefined()
      expect(entry?.accessedAt).toBeDefined()
    })
  })

  describe('Query', () => {
    it('should query all events', () => {
      store.store(createEvent())
      store.store(createEvent())
      store.store(createEvent())

      const results = store.query()
      expect(results).toHaveLength(3)
    })

    it('should query by type', () => {
      store.store(createEvent({ type: EventType.AGENT_STARTED }))
      store.store(createEvent({ type: EventType.AGENT_STARTED }))
      store.store(createEvent({ type: EventType.AGENT_COMPLETED }))

      const results = store.query({ types: [EventType.AGENT_STARTED] })
      expect(results).toHaveLength(2)
    })

    it('should query by source', () => {
      store.store(createEvent({ metadata: { source: 'source-a', version: 1 } }))
      store.store(createEvent({ metadata: { source: 'source-b', version: 1 } }))
      store.store(createEvent({ metadata: { source: 'source-a', version: 1 } }))

      const results = store.query({ source: 'source-a' })
      expect(results).toHaveLength(2)
    })

    it('should query by timestamp range', () => {
      store.store(createEvent({ timestamp: 1000 }))
      store.store(createEvent({ timestamp: 2000 }))
      store.store(createEvent({ timestamp: 3000 }))

      const results = store.query({ fromTimestamp: 1500, toTimestamp: 2500 })
      expect(results).toHaveLength(1)
    })

    it('should query by correlationId', () => {
      store.store(createEvent({ metadata: { source: 'test', version: 1, correlationId: 'corr-1' } }))
      store.store(createEvent({ metadata: { source: 'test', version: 1, correlationId: 'corr-2' } }))
      store.store(createEvent({ metadata: { source: 'test', version: 1, correlationId: 'corr-1' } }))

      const results = store.query({ correlationId: 'corr-1' })
      expect(results).toHaveLength(2)
    })

    it('should combine multiple filters', () => {
      store.store(createEvent({
        type: EventType.AGENT_STARTED,
        metadata: { source: 'source-a', version: 1 },
        timestamp: 1000,
      }))
      store.store(createEvent({
        type: EventType.AGENT_STARTED,
        metadata: { source: 'source-b', version: 1 },
        timestamp: 2000,
      }))
      store.store(createEvent({
        type: EventType.AGENT_COMPLETED,
        metadata: { source: 'source-a', version: 1 },
        timestamp: 1000,
      }))

      const results = store.query({
        types: [EventType.AGENT_STARTED],
        source: 'source-a',
      })
      expect(results).toHaveLength(1)
    })
  })

  describe('Index-based Queries', () => {
    it('should get events by type', () => {
      store.store(createEvent({ type: EventType.AGENT_STARTED }))
      store.store(createEvent({ type: EventType.AGENT_COMPLETED }))
      store.store(createEvent({ type: EventType.AGENT_STARTED }))

      const results = store.getByType(EventType.AGENT_STARTED)
      expect(results).toHaveLength(2)
    })

    it('should get events by source', () => {
      store.store(createEvent({ metadata: { source: 'source-a', version: 1 } }))
      store.store(createEvent({ metadata: { source: 'source-b', version: 1 } }))
      store.store(createEvent({ metadata: { source: 'source-a', version: 1 } }))

      const results = store.getBySource('source-a')
      expect(results).toHaveLength(2)
    })

    it('should get events by correlationId', () => {
      store.store(createEvent({ metadata: { source: 'test', version: 1, correlationId: 'corr-1' } }))
      store.store(createEvent({ metadata: { source: 'test', version: 1, correlationId: 'corr-2' } }))

      const results = store.getByCorrelationId('corr-1')
      expect(results).toHaveLength(1)
    })

    it('should get recent events', () => {
      for (let i = 0; i < 10; i++) {
        store.store(createEvent({ timestamp: i * 1000 }))
      }

      const recent = store.getRecent(3)
      expect(recent).toHaveLength(3)
    })
  })

  describe('Deletion', () => {
    it('should delete an event', () => {
      const event = createEvent()
      store.store(event)
      expect(store.size).toBe(1)

      const deleted = store.delete(event.id)
      expect(deleted).toBe(true)
      expect(store.size).toBe(0)
    })

    it('should return false for non-existent event', () => {
      expect(store.delete('non-existent')).toBe(false)
    })

    it('should update indexes on delete', () => {
      const event = createEvent({ type: EventType.AGENT_STARTED })
      store.store(event)

      expect(store.getByType(EventType.AGENT_STARTED)).toHaveLength(1)
      store.delete(event.id)
      expect(store.getByType(EventType.AGENT_STARTED)).toHaveLength(0)
    })
  })

  describe('Clear', () => {
    it('should clear all events', () => {
      store.store(createEvent())
      store.store(createEvent())
      expect(store.size).toBe(2)

      store.clear()
      expect(store.size).toBe(0)
    })

    it('should clear all indexes', () => {
      store.store(createEvent({ type: EventType.AGENT_STARTED }))
      store.store(createEvent({ metadata: { source: 'source-a', version: 1 } }))

      store.clear()
      expect(store.getByType(EventType.AGENT_STARTED)).toHaveLength(0)
      expect(store.getBySource('source-a')).toHaveLength(0)
    })
  })

  describe('Stats', () => {
    it('should return accurate stats', () => {
      store.store(createEvent({ type: EventType.AGENT_STARTED }))
      store.store(createEvent({ type: EventType.AGENT_COMPLETED }))
      store.store(createEvent({ type: EventType.AGENT_STARTED }))

      const stats = store.getStats()
      expect(stats.totalEvents).toBe(3)
      expect(stats.typeCounts[EventType.AGENT_STARTED]).toBe(2)
      expect(stats.typeCounts[EventType.AGENT_COMPLETED]).toBe(1)
    })

    it('should track oldest and newest events', () => {
      store.store(createEvent({ timestamp: 1000 }))
      store.store(createEvent({ timestamp: 3000 }))

      const stats = store.getStats()
      expect(stats.oldestEvent).toBe(1000)
      expect(stats.newestEvent).toBe(3000)
    })
  })

  describe('Serialization', () => {
    it('should serialize to JSON', () => {
      store.store(createEvent())
      const json = store.toJSON()
      expect(json).toBeDefined()
      expect(Array.isArray(json.events)).toBe(true)
      expect((json.events as Event[]).length).toBe(1)
    })

    it('should restore from JSON', () => {
      const event = createEvent()
      store.store(event)

      const json = store.toJSON()
      const restored = EventStore.fromJSON(json as Record<string, unknown>)
      expect(restored.size).toBe(1)
      expect(restored.get(event.id)).toBeDefined()
    })
  })
})