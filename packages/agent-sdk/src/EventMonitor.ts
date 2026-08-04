import {
  Event,
  EventType,
  EventMonitorConfig,
  EventMonitorMetrics,
  EventMonitorAlert,
  DEFAULT_EVENT_MONITOR_CONFIG,
} from './types.js'

export type EventMonitorAlertHandler = (alert: EventMonitorAlert) => void
export type EventMonitorMetricsHandler = (metrics: EventMonitorMetrics) => void

export class EventMonitor {
  private _config: EventMonitorConfig
  private _metricsHistory: EventMonitorMetrics[] = []
  private _alerts: EventMonitorAlert[] = []
  private _eventTimestamps: number[] = []
  private _deliveryTimes: number[] = []
  private _errorCount: number = 0
  private _totalEvents: number = 0
  private _deadLetterCount: number = 0
  private _activeSubscriptions: number = 0
  private _intervalId?: ReturnType<typeof setInterval>
  private _alertHandlers: EventMonitorAlertHandler[] = []
  private _metricsHandlers: EventMonitorMetricsHandler[] = []

  constructor(config: Partial<EventMonitorConfig> = {}) {
    this._config = { ...DEFAULT_EVENT_MONITOR_CONFIG, ...config }
  }

  get config(): Readonly<EventMonitorConfig> {
    return { ...this._config }
  }

  get metricsHistory(): ReadonlyArray<EventMonitorMetrics> {
    return [...this._metricsHistory]
  }

  get alerts(): ReadonlyArray<EventMonitorAlert> {
    return [...this._alerts]
  }

  // ==========================================================================
  // Event Tracking
  // ==========================================================================

  trackEvent(event: Event): void {
    this._eventTimestamps.push(event.timestamp)
    this._totalEvents++

    // Clean old timestamps (keep last 10 seconds)
    const cutoff = Date.now() - 10000
    this._eventTimestamps = this._eventTimestamps.filter(t => t > cutoff)
  }

  trackDeliveryTime(ms: number): void {
    this._deliveryTimes.push(ms)
    // Keep last 1000 entries
    if (this._deliveryTimes.length > 1000) {
      this._deliveryTimes = this._deliveryTimes.slice(-1000)
    }
  }

  trackError(): void {
    this._errorCount++
  }

  trackDeadLetters(count: number): void {
    this._deadLetterCount = count
  }

  trackActiveSubscriptions(count: number): void {
    this._activeSubscriptions = count
  }

  // ==========================================================================
  // Metrics Collection
  // ==========================================================================

  collectMetrics(): EventMonitorMetrics {
    const now = Date.now()

    // Events per second (last 10 seconds)
    const recentTimestamps = this._eventTimestamps.filter(t => t > now - 10000)
    const eventsPerSecond = recentTimestamps.length / 10

    // Average delivery time
    const averageDeliveryTimeMs = this._deliveryTimes.length > 0
      ? this._deliveryTimes.reduce((a, b) => a + b, 0) / this._deliveryTimes.length
      : 0

    // Error rate
    const errorRate = this._totalEvents > 0
      ? this._errorCount / this._totalEvents
      : 0

    const metrics: EventMonitorMetrics = {
      timestamp: now,
      eventsPerSecond: Math.round(eventsPerSecond * 100) / 100,
      averageDeliveryTimeMs: Math.round(averageDeliveryTimeMs * 100) / 100,
      errorRate: Math.round(errorRate * 10000) / 10000,
      deadLetterCount: this._deadLetterCount,
      activeSubscriptions: this._activeSubscriptions,
      memoryUsageMb: this.getMemoryUsageMb(),
    }

    this._metricsHistory.push(metrics)

    // Keep last 1000 metrics
    if (this._metricsHistory.length > 1000) {
      this._metricsHistory = this._metricsHistory.slice(-1000)
    }

    // Check thresholds and generate alerts
    if (this._config.enableAlerts) {
      this.checkThresholds(metrics)
    }

    // Notify metrics handlers
    for (const handler of this._metricsHandlers) {
      try {
        handler(metrics)
      } catch {
        // Handler errors should not affect monitoring
      }
    }

    return metrics
  }

  // ==========================================================================
  // Alert Management
  // ==========================================================================

  private checkThresholds(metrics: EventMonitorMetrics): void {
    const { alertThresholds } = this._config

    if (metrics.eventsPerSecond > alertThresholds.eventsPerSecond) {
      this.createAlert(
        'warning',
        'eventsPerSecond',
        metrics.eventsPerSecond,
        alertThresholds.eventsPerSecond,
        `Events per second (${metrics.eventsPerSecond}) exceeded threshold (${alertThresholds.eventsPerSecond})`
      )
    }

    if (metrics.averageDeliveryTimeMs > alertThresholds.deliveryTimeMs) {
      this.createAlert(
        'warning',
        'deliveryTimeMs',
        metrics.averageDeliveryTimeMs,
        alertThresholds.deliveryTimeMs,
        `Average delivery time (${metrics.averageDeliveryTimeMs}ms) exceeded threshold (${alertThresholds.deliveryTimeMs}ms)`
      )
    }

    if (metrics.errorRate > alertThresholds.errorRate) {
      this.createAlert(
        'critical',
        'errorRate',
        metrics.errorRate,
        alertThresholds.errorRate,
        `Error rate (${metrics.errorRate}) exceeded threshold (${alertThresholds.errorRate})`
      )
    }

    if (metrics.deadLetterCount > alertThresholds.deadLetterCount) {
      this.createAlert(
        'critical',
        'deadLetterCount',
        metrics.deadLetterCount,
        alertThresholds.deadLetterCount,
        `Dead letter count (${metrics.deadLetterCount}) exceeded threshold (${alertThresholds.deadLetterCount})`
      )
    }
  }

  private createAlert(
    type: 'warning' | 'critical',
    metric: string,
    value: number,
    threshold: number,
    message: string
  ): void {
    // Check for duplicate alerts (same metric within last 60 seconds)
    const recentDuplicate = this._alerts.find(
      a => a.metric === metric && Date.now() - a.timestamp < 60000
    )
    if (recentDuplicate) return

    const alert: EventMonitorAlert = {
      id: `alert-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      type,
      metric,
      value,
      threshold,
      message,
      timestamp: Date.now(),
    }

    this._alerts.push(alert)

    // Keep last 100 alerts
    if (this._alerts.length > 100) {
      this._alerts = this._alerts.slice(-100)
    }

    // Notify alert handlers
    for (const handler of this._alertHandlers) {
      try {
        handler(alert)
      } catch {
        // Handler errors should not affect monitoring
      }
    }
  }

  // ==========================================================================
  // Callbacks
  // ==========================================================================

  onAlert(handler: EventMonitorAlertHandler): () => void {
    this._alertHandlers.push(handler)
    return () => {
      this._alertHandlers = this._alertHandlers.filter(h => h !== handler)
    }
  }

  onMetrics(handler: EventMonitorMetricsHandler): () => void {
    this._metricsHandlers.push(handler)
    return () => {
      this._metricsHandlers = this._metricsHandlers.filter(h => h !== handler)
    }
  }

  // ==========================================================================
  // Lifecycle
  // ==========================================================================

  startCollection(intervalMs?: number): void {
    this.stopCollection()
    const interval = intervalMs || this._config.metricsInterval
    this._intervalId = setInterval(() => {
      this.collectMetrics()
    }, interval)
  }

  stopCollection(): void {
    if (this._intervalId) {
      clearInterval(this._intervalId)
      this._intervalId = undefined
    }
  }

  // ==========================================================================
  // Query
  // ==========================================================================

  getRecentMetrics(count: number): EventMonitorMetrics[] {
    return this._metricsHistory.slice(-count)
  }

  getRecentAlerts(count: number): EventMonitorAlert[] {
    return this._alerts.slice(-count)
  }

  getAlertsByType(type: 'warning' | 'critical'): EventMonitorAlert[] {
    return this._alerts.filter(a => a.type === type)
  }

  getLatestMetrics(): EventMonitorMetrics | undefined {
    return this._metricsHistory[this._metricsHistory.length - 1]
  }

  // ==========================================================================
  // Management
  // ==========================================================================

  clearMetrics(): void {
    this._metricsHistory = []
    this._eventTimestamps = []
    this._deliveryTimes = []
    this._errorCount = 0
    this._totalEvents = 0
  }

  clearAlerts(): void {
    this._alerts = []
  }

  // ==========================================================================
  // Stats
  // ==========================================================================

  getStats(): {
    totalEventsTracked: number
    totalErrors: number
    averageEventsPerSecond: number
    averageDeliveryTimeMs: number
    totalAlerts: number
    alertsByType: Record<string, number>
    metricsCollected: number
  } {
    const totalAlerts = this._alerts.length
    const alertsByType: Record<string, number> = {}
    for (const alert of this._alerts) {
      alertsByType[alert.type] = (alertsByType[alert.type] || 0) + 1
    }

    const avgEventsPerSecond = this._metricsHistory.length > 0
      ? this._metricsHistory.reduce((sum, m) => sum + m.eventsPerSecond, 0) / this._metricsHistory.length
      : 0

    const avgDeliveryTime = this._metricsHistory.length > 0
      ? this._metricsHistory.reduce((sum, m) => sum + m.averageDeliveryTimeMs, 0) / this._metricsHistory.length
      : 0

    return {
      totalEventsTracked: this._totalEvents,
      totalErrors: this._errorCount,
      averageEventsPerSecond: Math.round(avgEventsPerSecond * 100) / 100,
      averageDeliveryTimeMs: Math.round(avgDeliveryTime * 100) / 100,
      totalAlerts,
      alertsByType,
      metricsCollected: this._metricsHistory.length,
    }
  }

  // ==========================================================================
  // Private Helpers
  // ==========================================================================

  private getMemoryUsageMb(): number {
    if (typeof process !== 'undefined' && process.memoryUsage) {
      return Math.round(process.memoryUsage().heapUsed / 1024 / 1024 * 100) / 100
    }
    return 0
  }
}