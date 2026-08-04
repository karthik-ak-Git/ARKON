import {
  Event,
  EventType,
  EventHandler,
  EventSubscription,
  EventBusConfig,
  EventBusStats,
  EventFilter,
  EventMetadata,
  DEFAULT_EVENT_BUS_CONFIG,
} from './types.js'

export type EventBusEventHandler = (stats: EventBusStats) => void

export class EventBus {
  private _config: EventBusConfig
  private _subscriptions: Map<string, EventSubscription> = new Map()
  private _eventQueue: Event[] = []
  private _deadLetterQueue: Event[] = []
  private _eventHistory: Event[] = []
  private _stats: EventBusStats
  private _startTime: number = Date.now()
  private _metricsHandler?: EventBusEventHandler
  private _metricsInterval?: ReturnType<typeof setInterval>
  private _publishTimestamps: number[] = []

  constructor(config: Partial<EventBusConfig> = {}) {
    this._config = { ...DEFAULT_EVENT_BUS_CONFIG, ...config }
    this._stats = {
      totalPublished: 0,
      totalDelivered: 0,
      totalFailed: 0,
      totalRetried: 0,
      activeSubscriptions: 0,
      eventsPerSecond: 0,
      averageDeliveryTimeMs: 0,
      deadLetterCount: 0,
      uptimeMs: 0,
    }
  }

  get config(): Readonly<EventBusConfig> {
    return { ...this._config }
  }

  get stats(): EventBusStats {
    this.updateStats()
    return { ...this._stats }
  }

  // ==========================================================================
  // Subscription Management
  // ==========================================================================

  subscribe<TPayload = unknown>(
    eventType: EventType | '*',
    handler: EventHandler<TPayload>,
    options: { filter?: EventFilter; priority?: number; once?: boolean } = {}
  ): string {
    if (this._subscriptions.size >= this._config.maxSubscribers) {
      throw new Error('Maximum subscribers reached')
    }

    const id = this.generateId()
    const subscription: EventSubscription = {
      id,
      eventType: eventType as EventType | '*',
      handler: handler as EventHandler,
      filter: options.filter,
      priority: options.priority ?? 0,
      once: options.once ?? false,
      active: true,
      createdAt: Date.now(),
    }

    this._subscriptions.set(id, subscription)
    this._stats.activeSubscriptions = this._subscriptions.size
    return id
  }

  unsubscribe(subscriptionId: string): boolean {
    const subscription = this._subscriptions.get(subscriptionId)
    if (!subscription) {
      return false
    }
    subscription.active = false
    this._subscriptions.delete(subscriptionId)
    this._stats.activeSubscriptions = this._subscriptions.size
    return true
  }

  unsubscribeAll(eventType?: EventType): number {
    let count = 0
    for (const [id, subscription] of this._subscriptions) {
      if (!eventType || subscription.eventType === eventType || subscription.eventType === '*') {
        subscription.active = false
        this._subscriptions.delete(id)
        count++
      }
    }
    this._stats.activeSubscriptions = this._subscriptions.size
    return count
  }

  // ==========================================================================
  // Publishing
  // ==========================================================================

  publish<TPayload = unknown>(
    type: EventType,
    payload: TPayload,
    metadata: Partial<EventMetadata> = {}
  ): Event<TPayload> {
    const event: Event<TPayload> = {
      id: this.generateId(),
      type,
      payload,
      metadata: {
        source: metadata.source ?? 'unknown',
        version: metadata.version ?? this._config.defaultEventVersion,
        correlationId: metadata.correlationId,
        causationId: metadata.causationId,
        userId: metadata.userId,
        sessionId: metadata.sessionId,
        traceId: metadata.traceId,
        spanId: metadata.spanId,
      },
      timestamp: Date.now(),
    }

    this.trackPublishRate()
    this._stats.totalPublished++
    this._eventHistory.push(event)

    if (this._config.enablePersistence) {
      this.addToHistory(event)
    }

    this.deliverEvent(event as Event)
    return event
  }

  async publishAsync<TPayload = unknown>(
    type: EventType,
    payload: TPayload,
    metadata: Partial<EventMetadata> = {}
  ): Promise<Event<TPayload>> {
    const event: Event<TPayload> = {
      id: this.generateId(),
      type,
      payload,
      metadata: {
        source: metadata.source ?? 'unknown',
        version: metadata.version ?? this._config.defaultEventVersion,
        correlationId: metadata.correlationId,
        causationId: metadata.causationId,
        userId: metadata.userId,
        sessionId: metadata.sessionId,
        traceId: metadata.traceId,
        spanId: metadata.spanId,
      },
      timestamp: Date.now(),
    }

    this.trackPublishRate()
    this._stats.totalPublished++
    this._eventHistory.push(event)

    if (this._config.enablePersistence) {
      this.addToHistory(event)
    }

    await this.deliverEventAsync(event as Event)
    return event
  }

  private deliverEvent(event: Event): void {
    const matchingSubscriptions = this.getMatchingSubscriptions(event)

    for (const subscription of matchingSubscriptions) {
      try {
        if (subscription.filter && !this.matchesFilter(event, subscription.filter)) {
          continue
        }

        const deliveryStart = Date.now()
        subscription.handler(event)
        const deliveryTime = Date.now() - deliveryStart

        this._stats.totalDelivered++
        this._stats.averageDeliveryTimeMs =
          (this._stats.averageDeliveryTimeMs * (this._stats.totalDelivered - 1) + deliveryTime) /
          this._stats.totalDelivered

        if (subscription.once) {
          this.unsubscribe(subscription.id)
        }
      } catch (error) {
        this._stats.totalFailed++
        if (this._config.enableDeadLetterQueue) {
          this._deadLetterQueue.push(event)
          this._stats.deadLetterCount = this._deadLetterQueue.length
          if (this._deadLetterQueue.length > this._config.deadLetterMaxSize) {
            this._deadLetterQueue.shift()
          }
        }
      }
    }
  }

  private async deliverEventAsync(event: Event): Promise<void> {
    const matchingSubscriptions = this.getMatchingSubscriptions(event)
    const deliveryPromises: Promise<void>[] = []

    for (const subscription of matchingSubscriptions) {
      if (subscription.filter && !this.matchesFilter(event, subscription.filter)) {
        continue
      }

      const promise = (async () => {
        try {
          const deliveryStart = Date.now()
          await subscription.handler(event)
          const deliveryTime = Date.now() - deliveryStart

          this._stats.totalDelivered++
          this._stats.averageDeliveryTimeMs =
            (this._stats.averageDeliveryTimeMs * (this._stats.totalDelivered - 1) + deliveryTime) /
            this._stats.totalDelivered

          if (subscription.once) {
            this.unsubscribe(subscription.id)
          }
        } catch (error) {
          this._stats.totalFailed++
          if (this._config.enableDeadLetterQueue) {
            this._deadLetterQueue.push(event)
            this._stats.deadLetterCount = this._deadLetterQueue.length
          }
        }
      })()

      deliveryPromises.push(promise)
    }

    await Promise.all(deliveryPromises)
  }

  private getMatchingSubscriptions(event: Event): EventSubscription[] {
    const subscriptions: EventSubscription[] = []

    for (const subscription of this._subscriptions.values()) {
      if (!subscription.active) continue
      if (subscription.eventType === '*' || subscription.eventType === event.type) {
        subscriptions.push(subscription)
      }
    }

    return subscriptions.sort((a, b) => b.priority - a.priority)
  }

  private matchesFilter(event: Event, filter: EventFilter): boolean {
    if (filter.types && !filter.types.includes(event.type)) {
      return false
    }
    if (filter.source && event.metadata.source !== filter.source) {
      return false
    }
    if (filter.fromTimestamp && event.timestamp < filter.fromTimestamp) {
      return false
    }
    if (filter.toTimestamp && event.timestamp > filter.toTimestamp) {
      return false
    }
    if (filter.correlationId && event.metadata.correlationId !== filter.correlationId) {
      return false
    }
    return true
  }

  // ==========================================================================
  // Replay
  // ==========================================================================

  replay(options: {
    fromTimestamp?: number
    toTimestamp?: number
    types?: EventType[]
    source?: string
    correlationId?: string
  } = {}): Event[] {
    if (!this._config.enableReplay) {
      throw new Error('Replay is disabled')
    }

    let events = [...this._eventHistory]

    if (options.fromTimestamp) {
      events = events.filter(e => e.timestamp >= options.fromTimestamp!)
    }
    if (options.toTimestamp) {
      events = events.filter(e => e.timestamp <= options.toTimestamp!)
    }
    if (options.types) {
      events = events.filter(e => options.types!.includes(e.type))
    }
    if (options.source) {
      events = events.filter(e => e.metadata.source === options.source)
    }
    if (options.correlationId) {
      events = events.filter(e => e.metadata.correlationId === options.correlationId)
    }

    for (const event of events) {
      this.deliverEvent(event)
    }

    return events
  }

  replayTo(subscriptionId: string, options: {
    fromTimestamp?: number
    toTimestamp?: number
    types?: EventType[]
  } = {}): Event[] {
    const subscription = this._subscriptions.get(subscriptionId)
    if (!subscription) {
      throw new Error(`Subscription ${subscriptionId} not found`)
    }

    let events = [...this._eventHistory]

    if (options.fromTimestamp) {
      events = events.filter(e => e.timestamp >= options.fromTimestamp!)
    }
    if (options.toTimestamp) {
      events = events.filter(e => e.timestamp <= options.toTimestamp!)
    }
    if (options.types) {
      events = events.filter(e => options.types!.includes(e.type))
    }

    for (const event of events) {
      try {
        subscription.handler(event)
      } catch {
        // Replay errors should not affect the bus
      }
    }

    return events
  }

  // ==========================================================================
  // History Management
  // ==========================================================================

  private addToHistory(event: Event): void {
    if (this._eventHistory.length > this._config.maxSubscribers * 10) {
      this._eventHistory = this._eventHistory.slice(-this._config.maxSubscribers * 5)
    }
  }

  getHistory(options: {
    limit?: number
    offset?: number
    types?: EventType[]
    source?: string
  } = {}): Event[] {
    let events = [...this._eventHistory]

    if (options.types) {
      events = events.filter(e => options.types!.includes(e.type))
    }
    if (options.source) {
      events = events.filter(e => e.metadata.source === options.source)
    }

    const offset = options.offset ?? 0
    const limit = options.limit ?? events.length

    return events.slice(offset, offset + limit)
  }

  clearHistory(): void {
    this._eventHistory = []
  }

  // ==========================================================================
  // Dead Letter Queue
  // ==========================================================================

  getDeadLetters(): Event[] {
    return [...this._deadLetterQueue]
  }

  clearDeadLetters(): void {
    this._deadLetterQueue = []
    this._stats.deadLetterCount = 0
  }

  retryDeadLetter(eventId: string): boolean {
    const index = this._deadLetterQueue.findIndex(e => e.id === eventId)
    if (index === -1) {
      return false
    }

    const event = this._deadLetterQueue.splice(index, 1)[0]
    this._stats.deadLetterCount = this._deadLetterQueue.length
    this._stats.totalRetried++
    this.deliverEvent(event)
    return true
  }

  // ==========================================================================
  // Monitoring
  // ==========================================================================

  onMetrics(handler: EventBusEventHandler): () => void {
    this._metricsHandler = handler
    return () => {
      this._metricsHandler = undefined
    }
  }

  startMetricsCollection(intervalMs: number = 5000): void {
    this.stopMetricsCollection()
    this._metricsInterval = setInterval(() => {
      this.updateStats()
      if (this._metricsHandler) {
        this._metricsHandler(this._stats)
      }
    }, intervalMs)
  }

  stopMetricsCollection(): void {
    if (this._metricsInterval) {
      clearInterval(this._metricsInterval)
      this._metricsInterval = undefined
    }
  }

  private trackPublishRate(): void {
    const now = Date.now()
    this._publishTimestamps.push(now)
    this._publishTimestamps = this._publishTimestamps.filter(t => now - t < 1000)
  }

  private updateStats(): void {
    const now = Date.now()
    this._stats.uptimeMs = now - this._startTime
    this._stats.eventsPerSecond = this._publishTimestamps.length
    this._stats.activeSubscriptions = this._subscriptions.size
    this._stats.deadLetterCount = this._deadLetterQueue.length
  }

  // ==========================================================================
  // Query
  // ==========================================================================

  getSubscriptions(eventType?: EventType): EventSubscription[] {
    const subscriptions = Array.from(this._subscriptions.values())
    if (eventType) {
      return subscriptions.filter(s => s.eventType === eventType || s.eventType === '*')
    }
    return subscriptions
  }

  getSubscription(subscriptionId: string): EventSubscription | undefined {
    return this._subscriptions.get(subscriptionId)
  }

  // ==========================================================================
  // Lifecycle
  // ==========================================================================

  async shutdown(): Promise<void> {
    this.stopMetricsCollection()
    this._subscriptions.clear()
    this._eventQueue = []
    this._stats.activeSubscriptions = 0
  }

  // ==========================================================================
  // Utilities
  // ==========================================================================

  private generateId(): string {
    return `evt-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  }

  createCorrelationId(): string {
    return `corr-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  }

  createTraceId(): string {
    return `trace-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  }
}