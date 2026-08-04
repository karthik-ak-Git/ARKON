import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { EventBus, EventBusEventHandler } from '../../../packages/agent-sdk/src/EventBus.js'
import { EventType, Event } from '../../../packages/agent-sdk/src/types.js'

describe('EventBus', () => {
  let bus: EventBus

  beforeEach(() => {
    bus = new EventBus()
  })

  afterEach(async () => {
    await bus.shutdown()
  })

  describe('Construction', () => {
    it('should create an EventBus with default config', () => {
      expect(bus).toBeDefined()
      expect(bus.config.maxSubscribers).toBe(1000)
      expect(bus.config.enableReplay).toBe(true)
      expect(bus.config.enableDeadLetterQueue).toBe(true)
    })

    it('should accept custom config', () => {
      const customBus = new EventBus({
        maxSubscribers: 100,
        enableReplay: false,
      })
      expect(customBus.config.maxSubscribers).toBe(100)
      expect(customBus.config.enableReplay).toBe(false)
    })
  })

  describe('Subscription', () => {
    it('should subscribe to an event type', () => {
      const handler = vi.fn()
      const id = bus.subscribe(EventType.AGENT_STARTED, handler)
      expect(id).toBeDefined()
      expect(typeof id).toBe('string')
    })

    it('should subscribe to all events with wildcard', () => {
      const handler = vi.fn()
      const id = bus.subscribe('*', handler)
      expect(id).toBeDefined()
    })

    it('should track active subscriptions', () => {
      expect(bus.stats.activeSubscriptions).toBe(0)
      bus.subscribe(EventType.AGENT_STARTED, vi.fn())
      expect(bus.stats.activeSubscriptions).toBe(1)
    })

    it('should enforce max subscribers limit', () => {
      const limitedBus = new EventBus({ maxSubscribers: 2 })
      limitedBus.subscribe(EventType.AGENT_STARTED, vi.fn())
      limitedBus.subscribe(EventType.AGENT_STARTED, vi.fn())
      expect(() => {
        limitedBus.subscribe(EventType.AGENT_STARTED, vi.fn())
      }).toThrow('Maximum subscribers reached')
    })
  })

  describe('Unsubscription', () => {
    it('should unsubscribe from an event', () => {
      const handler = vi.fn()
      const id = bus.subscribe(EventType.AGENT_STARTED, handler)
      expect(bus.stats.activeSubscriptions).toBe(1)

      const result = bus.unsubscribe(id)
      expect(result).toBe(true)
      expect(bus.stats.activeSubscriptions).toBe(0)
    })

    it('should return false for non-existent subscription', () => {
      const result = bus.unsubscribe('non-existent')
      expect(result).toBe(false)
    })

    it('should unsubscribe all subscriptions', () => {
      bus.subscribe(EventType.AGENT_STARTED, vi.fn())
      bus.subscribe(EventType.AGENT_COMPLETED, vi.fn())
      expect(bus.stats.activeSubscriptions).toBe(2)

      const count = bus.unsubscribeAll()
      expect(count).toBe(2)
      expect(bus.stats.activeSubscriptions).toBe(0)
    })

    it('should unsubscribe all for specific event type', () => {
      bus.subscribe(EventType.AGENT_STARTED, vi.fn())
      bus.subscribe(EventType.AGENT_STARTED, vi.fn())
      bus.subscribe(EventType.AGENT_COMPLETED, vi.fn())

      const count = bus.unsubscribeAll(EventType.AGENT_STARTED)
      expect(count).toBe(2)
      expect(bus.stats.activeSubscriptions).toBe(1)
    })
  })

  describe('Publishing', () => {
    it('should publish an event', () => {
      const event = bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(event).toBeDefined()
      expect(event.type).toBe(EventType.AGENT_STARTED)
      expect(event.payload).toEqual({ agentId: 'test' })
      expect(event.id).toBeDefined()
      expect(event.timestamp).toBeDefined()
    })

    it('should include metadata in published event', () => {
      const event = bus.publish(EventType.AGENT_STARTED, { agentId: 'test' }, {
        source: 'test-source',
        userId: 'user-1',
      })
      expect(event.metadata.source).toBe('test-source')
      expect(event.metadata.userId).toBe('user-1')
    })

    it('should track publish statistics', () => {
      expect(bus.stats.totalPublished).toBe(0)
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(bus.stats.totalPublished).toBe(1)
    })

    it('should deliver events to matching subscribers', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(handler).toHaveBeenCalledTimes(1)
      expect(handler).toHaveBeenCalledWith(expect.objectContaining({
        type: EventType.AGENT_STARTED,
        payload: { agentId: 'test' },
      }))
    })

    it('should not deliver events to non-matching subscribers', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_COMPLETED, handler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(handler).not.toHaveBeenCalled()
    })

    it('should deliver to wildcard subscribers', () => {
      const handler = vi.fn()
      bus.subscribe('*', handler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(handler).toHaveBeenCalledTimes(1)
    })

    it('should deliver to subscribers in priority order', () => {
      const callOrder: number[] = []
      bus.subscribe(EventType.AGENT_STARTED, () => callOrder.push(1), { priority: 1 })
      bus.subscribe(EventType.AGENT_STARTED, () => callOrder.push(3), { priority: 3 })
      bus.subscribe(EventType.AGENT_STARTED, () => callOrder.push(2), { priority: 2 })

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(callOrder).toEqual([3, 2, 1])
    })

    it('should remove once subscriptions after delivery', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler, { once: true })
      expect(bus.stats.activeSubscriptions).toBe(1)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(bus.stats.activeSubscriptions).toBe(0)
      expect(handler).toHaveBeenCalledTimes(1)
    })
  })

  describe('Filtering', () => {
    it('should filter events by source', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler, {
        filter: { source: 'allowed-source' },
      })

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' }, { source: 'blocked-source' })
      expect(handler).not.toHaveBeenCalled()

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' }, { source: 'allowed-source' })
      expect(handler).toHaveBeenCalledTimes(1)
    })

    it('should filter events by correlationId', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler, {
        filter: { correlationId: 'corr-123' },
      })

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' }, { correlationId: 'corr-456' })
      expect(handler).not.toHaveBeenCalled()

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' }, { correlationId: 'corr-123' })
      expect(handler).toHaveBeenCalledTimes(1)
    })
  })

  describe('Dead Letter Queue', () => {
    it('should add failed events to dead letter queue', () => {
      const failingHandler = vi.fn().mockImplementation(() => {
        throw new Error('Handler failed')
      })
      bus.subscribe(EventType.AGENT_STARTED, failingHandler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(bus.getDeadLetters()).toHaveLength(1)
      expect(bus.stats.deadLetterCount).toBe(1)
    })

    it('should retry dead letters', () => {
      const failingHandler = vi.fn()
        .mockImplementationOnce(() => { throw new Error('First attempt failed') })
        .mockImplementationOnce(() => { /* Success */ })

      bus.subscribe(EventType.AGENT_STARTED, failingHandler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(bus.getDeadLetters()).toHaveLength(1)

      const eventId = bus.getDeadLetters()[0].id
      const retried = bus.retryDeadLetter(eventId)
      expect(retried).toBe(true)
      expect(bus.getDeadLetters()).toHaveLength(0)
      expect(bus.stats.totalRetried).toBe(1)
    })

    it('should clear dead letters', () => {
      const failingHandler = vi.fn().mockImplementation(() => {
        throw new Error('Handler failed')
      })
      bus.subscribe(EventType.AGENT_STARTED, failingHandler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(bus.getDeadLetters()).toHaveLength(1)

      bus.clearDeadLetters()
      expect(bus.getDeadLetters()).toHaveLength(0)
      expect(bus.stats.deadLetterCount).toBe(0)
    })
  })

  describe('Replay', () => {
    it('should replay events', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test1' })
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test2' })
      expect(handler).toHaveBeenCalledTimes(2)

      handler.mockClear()
      bus.replay()
      expect(handler).toHaveBeenCalledTimes(2)
    })

    it('should replay with filter options', () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test1' }, { source: 'source-a' })
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test2' }, { source: 'source-b' })
      expect(handler).toHaveBeenCalledTimes(2)

      handler.mockClear()
      bus.replay({ source: 'source-a' })
      expect(handler).toHaveBeenCalledTimes(1)
    })

    it('should replay to specific subscription', () => {
      const handler1 = vi.fn()
      const handler2 = vi.fn()

      bus.subscribe(EventType.AGENT_STARTED, handler2)
      const sub1Id = bus.subscribe(EventType.AGENT_STARTED, handler1)

      bus.publish(EventType.AGENT_STARTED, { agentId: 'test1' })
      expect(handler1).toHaveBeenCalledTimes(1)
      expect(handler2).toHaveBeenCalledTimes(1)

      handler1.mockClear()
      handler2.mockClear()
      bus.replayTo(sub1Id)
      expect(handler1).toHaveBeenCalledTimes(1)
      expect(handler2).not.toHaveBeenCalled()
    })

    it('should throw if replay is disabled', () => {
      const noReplayBus = new EventBus({ enableReplay: false })
      expect(() => noReplayBus.replay()).toThrow('Replay is disabled')
    })
  })

  describe('History', () => {
    it('should track event history', () => {
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test1' })
      bus.publish(EventType.AGENT_COMPLETED, { agentId: 'test2' })

      const history = bus.getHistory()
      expect(history).toHaveLength(2)
    })

    it('should get history with limit', () => {
      for (let i = 0; i < 10; i++) {
        bus.publish(EventType.AGENT_STARTED, { agentId: `test-${i}` })
      }

      const history = bus.getHistory({ limit: 5 })
      expect(history).toHaveLength(5)
    })

    it('should filter history by type', () => {
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test1' })
      bus.publish(EventType.AGENT_COMPLETED, { agentId: 'test2' })
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test3' })

      const history = bus.getHistory({ types: [EventType.AGENT_STARTED] })
      expect(history).toHaveLength(2)
    })

    it('should clear history', () => {
      bus.publish(EventType.AGENT_STARTED, { agentId: 'test1' })
      expect(bus.getHistory()).toHaveLength(1)

      bus.clearHistory()
      expect(bus.getHistory()).toHaveLength(0)
    })
  })

  describe('Metrics', () => {
    it('should track uptime', () => {
      expect(bus.stats.uptimeMs).toBeGreaterThanOrEqual(0)
    })

    it('should track events per second', () => {
      for (let i = 0; i < 5; i++) {
        bus.publish(EventType.AGENT_STARTED, { agentId: `test-${i}` })
      }
      expect(bus.stats.eventsPerSecond).toBeGreaterThanOrEqual(0)
    })

    it('should start and stop metrics collection', () => {
      const callback: EventBusEventHandler = vi.fn()
      bus.onMetrics(callback)
      bus.startMetricsCollection(100)
      expect(() => bus.stopMetricsCollection()).not.toThrow()
    })
  })

  describe('Lifecycle', () => {
    it('should shutdown cleanly', async () => {
      bus.subscribe(EventType.AGENT_STARTED, vi.fn())
      expect(bus.stats.activeSubscriptions).toBe(1)

      await bus.shutdown()
      expect(bus.stats.activeSubscriptions).toBe(0)
    })
  })

  describe('Correlation IDs', () => {
    it('should generate unique correlation IDs', () => {
      const id1 = bus.createCorrelationId()
      const id2 = bus.createCorrelationId()
      expect(id1).not.toBe(id2)
      expect(id1).toMatch(/^corr-/)
    })

    it('should generate unique trace IDs', () => {
      const id1 = bus.createTraceId()
      const id2 = bus.createTraceId()
      expect(id1).not.toBe(id2)
      expect(id1).toMatch(/^trace-/)
    })
  })

  describe('Async Publishing', () => {
    it('should publish events asynchronously', async () => {
      const handler = vi.fn()
      bus.subscribe(EventType.AGENT_STARTED, handler)

      const event = await bus.publishAsync(EventType.AGENT_STARTED, { agentId: 'test' })
      expect(event).toBeDefined()
      expect(handler).toHaveBeenCalledTimes(1)
    })
  })
})