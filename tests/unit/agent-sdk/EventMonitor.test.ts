import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { EventMonitor } from '../../../packages/agent-sdk/src/EventMonitor.js'
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

describe('EventMonitor', () => {
  let monitor: EventMonitor

  beforeEach(() => {
    monitor = new EventMonitor()
  })

  afterEach(() => {
    monitor.stopCollection()
  })

  describe('Construction', () => {
    it('should create an EventMonitor with default config', () => {
      expect(monitor).toBeDefined()
      expect(monitor.config.enabled).toBe(true)
      expect(monitor.config.enableAlerts).toBe(true)
    })

    it('should accept custom config', () => {
      const customMonitor = new EventMonitor({
        metricsInterval: 10000,
        enableAlerts: false,
      })
      expect(customMonitor.config.metricsInterval).toBe(10000)
      expect(customMonitor.config.enableAlerts).toBe(false)
    })
  })

  describe('Event Tracking', () => {
    it('should track events', () => {
      monitor.trackEvent(createEvent())
      monitor.trackEvent(createEvent())

      const stats = monitor.getStats()
      expect(stats.totalEventsTracked).toBe(2)
    })

    it('should track delivery times', () => {
      monitor.trackDeliveryTime(10)
      monitor.trackDeliveryTime(20)
      monitor.trackDeliveryTime(30)

      const metrics = monitor.collectMetrics()
      expect(metrics.averageDeliveryTimeMs).toBe(20)
    })

    it('should track errors', () => {
      monitor.trackEvent(createEvent())
      monitor.trackError()

      const stats = monitor.getStats()
      expect(stats.totalErrors).toBe(1)
    })

    it('should track dead letters', () => {
      monitor.trackDeadLetters(5)
      const metrics = monitor.collectMetrics()
      expect(metrics.deadLetterCount).toBe(5)
    })

    it('should track active subscriptions', () => {
      monitor.trackActiveSubscriptions(10)
      const metrics = monitor.collectMetrics()
      expect(metrics.activeSubscriptions).toBe(10)
    })
  })

  describe('Metrics Collection', () => {
    it('should collect metrics', () => {
      monitor.trackEvent(createEvent())
      const metrics = monitor.collectMetrics()

      expect(metrics).toBeDefined()
      expect(metrics.timestamp).toBeDefined()
      expect(typeof metrics.eventsPerSecond).toBe('number')
      expect(typeof metrics.averageDeliveryTimeMs).toBe('number')
      expect(typeof metrics.errorRate).toBe('number')
    })

    it('should store metrics history', () => {
      monitor.collectMetrics()
      monitor.collectMetrics()

      expect(monitor.metricsHistory).toHaveLength(2)
    })

    it('should limit metrics history', () => {
      // Create a monitor with a small limit
      for (let i = 0; i < 1100; i++) {
        monitor.collectMetrics()
      }

      expect(monitor.metricsHistory.length).toBeLessThanOrEqual(1000)
    })

    it('should calculate events per second', () => {
      // Track multiple events
      for (let i = 0; i < 100; i++) {
        monitor.trackEvent(createEvent())
      }

      const metrics = monitor.collectMetrics()
      expect(metrics.eventsPerSecond).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Alerts', () => {
    it('should generate alerts when thresholds exceeded', () => {
      const alertMonitor = new EventMonitor({
        enableAlerts: true,
        alertThresholds: {
          eventsPerSecond: 0.5,
          deliveryTimeMs: 10,
          errorRate: 0.01,
          deadLetterCount: 5,
        },
      })

      // Track many events to exceed threshold
      for (let i = 0; i < 100; i++) {
        alertMonitor.trackEvent(createEvent())
      }

      alertMonitor.collectMetrics()
      const alerts = alertMonitor.alerts
      expect(alerts.length).toBeGreaterThan(0)
    })

    it('should not duplicate recent alerts', () => {
      const alertMonitor = new EventMonitor({
        enableAlerts: true,
        alertThresholds: {
          eventsPerSecond: 0.5,
          deliveryTimeMs: 0,
          errorRate: 0,
          deadLetterCount: 0,
        },
      })

      // Track events to exceed threshold
      for (let i = 0; i < 10; i++) {
        alertMonitor.trackEvent(createEvent())
      }

      alertMonitor.collectMetrics()
      alertMonitor.collectMetrics()

      // Should not create duplicate alert within 60 seconds
      const alerts = alertMonitor.alerts
      const alertsByType = alerts.filter(a => a.metric === 'eventsPerSecond')
      expect(alertsByType.length).toBe(1)
    })

    it('should clear alerts', () => {
      const alertMonitor = new EventMonitor({
        enableAlerts: true,
        alertThresholds: {
          eventsPerSecond: 0.5,
          deliveryTimeMs: 0,
          errorRate: 0,
          deadLetterCount: 0,
        },
      })

      // Track events to exceed threshold
      for (let i = 0; i < 10; i++) {
        alertMonitor.trackEvent(createEvent())
      }

      alertMonitor.collectMetrics()
      expect(alertMonitor.alerts.length).toBeGreaterThan(0)

      alertMonitor.clearAlerts()
      expect(alertMonitor.alerts).toHaveLength(0)
    })
  })

  describe('Callbacks', () => {
    it('should register and call alert handlers', () => {
      const alertHandler = vi.fn()

      const alertMonitor = new EventMonitor({
        enableAlerts: true,
        alertThresholds: {
          eventsPerSecond: 0.5,
          deliveryTimeMs: 0,
          errorRate: 0,
          deadLetterCount: 0,
        },
      })

      alertMonitor.onAlert(alertHandler)
      // Track events to exceed threshold
      for (let i = 0; i < 10; i++) {
        alertMonitor.trackEvent(createEvent())
      }
      alertMonitor.collectMetrics()
      expect(alertHandler).toHaveBeenCalled()
    })

    it('should register and call metrics handlers', () => {
      const metricsHandler = vi.fn()
      monitor.onMetrics(metricsHandler)

      monitor.collectMetrics()
      expect(metricsHandler).toHaveBeenCalled()
    })

    it('should unregister handlers', () => {
      const metricsHandler = vi.fn()
      const unsub = monitor.onMetrics(metricsHandler)

      monitor.collectMetrics()
      expect(metricsHandler).toHaveBeenCalledTimes(1)

      unsub()
      monitor.collectMetrics()
      expect(metricsHandler).toHaveBeenCalledTimes(1)
    })
  })

  describe('Lifecycle', () => {
    it('should start and stop collection', () => {
      monitor.startCollection(100)
      expect(() => monitor.stopCollection()).not.toThrow()
    })
  })

  describe('Query', () => {
    it('should get recent metrics', () => {
      monitor.collectMetrics()
      monitor.collectMetrics()
      monitor.collectMetrics()

      const recent = monitor.getRecentMetrics(2)
      expect(recent).toHaveLength(2)
    })

    it('should get recent alerts', () => {
      const alertMonitor = new EventMonitor({
        enableAlerts: true,
        alertThresholds: {
          eventsPerSecond: 0.5,
          deliveryTimeMs: 0,
          errorRate: 0,
          deadLetterCount: 0,
        },
      })

      // Track events to exceed threshold
      for (let i = 0; i < 10; i++) {
        alertMonitor.trackEvent(createEvent())
      }

      alertMonitor.collectMetrics()
      const alerts = alertMonitor.getRecentAlerts(10)
      expect(alerts.length).toBeGreaterThan(0)
    })

    it('should get alerts by type', () => {
      const alertMonitor = new EventMonitor({
        enableAlerts: true,
        alertThresholds: {
          eventsPerSecond: 0,
          deliveryTimeMs: 0,
          errorRate: 0,
          deadLetterCount: 0,
        },
      })

      alertMonitor.collectMetrics()
      const warningAlerts = alertMonitor.getAlertsByType('warning')
      expect(Array.isArray(warningAlerts)).toBe(true)
    })

    it('should get latest metrics', () => {
      monitor.collectMetrics()
      const latest = monitor.getLatestMetrics()
      expect(latest).toBeDefined()
    })
  })

  describe('Management', () => {
    it('should clear metrics', () => {
      monitor.trackEvent(createEvent())
      monitor.trackDeliveryTime(10)
      monitor.collectMetrics()

      monitor.clearMetrics()
      expect(monitor.metricsHistory).toHaveLength(0)
    })
  })

  describe('Stats', () => {
    it('should return accurate stats', () => {
      monitor.trackEvent(createEvent())
      monitor.trackError()
      monitor.collectMetrics()

      const stats = monitor.getStats()
      expect(stats.totalEventsTracked).toBe(1)
      expect(stats.totalErrors).toBe(1)
      expect(stats.metricsCollected).toBe(1)
    })
  })
})