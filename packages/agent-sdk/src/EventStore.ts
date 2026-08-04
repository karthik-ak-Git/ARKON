import {
  Event,
  EventType,
  EventStoreConfig,
  EventStoreEntry,
  EventFilter,
  DEFAULT_EVENT_STORE_CONFIG,
} from './types.js'

export class EventStore {
  private _config: EventStoreConfig
  private _store: Map<string, EventStoreEntry> = new Map()
  private _indexByType: Map<EventType, Set<string>> = new Map()
  private _indexBySource: Map<string, Set<string>> = new Map()
  private _indexByTimestamp: Array<{ id: string; timestamp: number }> = []
  private _totalAccessCount: number = 0

  constructor(config: Partial<EventStoreConfig> = {}) {
    this._config = { ...DEFAULT_EVENT_STORE_CONFIG, ...config }
  }

  get config(): Readonly<EventStoreConfig> {
    return { ...this._config }
  }

  get size(): number {
    return this._store.size
  }

  // ==========================================================================
  // Storage
  // ==========================================================================

  store(event: Event): EventStoreEntry {
    if (this._store.size >= this._config.maxSize) {
      this.evictOldest()
    }

    const entry: EventStoreEntry = {
      event,
      storedAt: Date.now(),
      accessedAt: Date.now(),
      accessCount: 0,
    }

    this._store.set(event.id, entry)
    this.updateIndexes(event)
    return entry
  }

  private updateIndexes(event: Event): void {
    // Index by type
    if (!this._indexByType.has(event.type)) {
      this._indexByType.set(event.type, new Set())
    }
    this._indexByType.get(event.type)!.add(event.id)

    // Index by source
    const source = event.metadata.source
    if (!this._indexBySource.has(source)) {
      this._indexBySource.set(source, new Set())
    }
    this._indexBySource.get(source)!.add(event.id)

    // Index by timestamp (keep sorted)
    this._indexByTimestamp.push({ id: event.id, timestamp: event.timestamp })
    this._indexByTimestamp.sort((a, b) => a.timestamp - b.timestamp)
  }

  private evictOldest(): void {
    if (this._indexByTimestamp.length === 0) return

    const oldest = this._indexByTimestamp.shift()!
    const entry = this._store.get(oldest.id)
    if (entry) {
      this.removeFromIndexes(entry.event)
      this._store.delete(oldest.id)
    }
  }

  private removeFromIndexes(event: Event): void {
    const typeIndex = this._indexByType.get(event.type)
    if (typeIndex) {
      typeIndex.delete(event.id)
      if (typeIndex.size === 0) {
        this._indexByType.delete(event.type)
      }
    }

    const sourceIndex = this._indexBySource.get(event.metadata.source)
    if (sourceIndex) {
      sourceIndex.delete(event.id)
      if (sourceIndex.size === 0) {
        this._indexBySource.delete(event.metadata.source)
      }
    }

    this._indexByTimestamp = this._indexByTimestamp.filter(i => i.id !== event.id)
  }

  // ==========================================================================
  // Retrieval
  // ==========================================================================

  get(eventId: string): Event | undefined {
    const entry = this._store.get(eventId)
    if (!entry) return undefined

    entry.accessedAt = Date.now()
    entry.accessCount++
    this._totalAccessCount++

    return entry.event
  }

  getEntry(eventId: string): EventStoreEntry | undefined {
    return this._store.get(eventId)
  }

  query(filter: EventFilter = {}): Event[] {
    let candidateIds: Set<string> | undefined

    // Start with type filter if specified
    if (filter.types && filter.types.length > 0) {
      candidateIds = new Set<string>()
      for (const type of filter.types) {
        const ids = this._indexByType.get(type)
        if (ids) {
          for (const id of ids) {
            candidateIds.add(id)
          }
        }
      }
    }

    // Intersect with source filter if specified
    if (filter.source) {
      const sourceIds = this._indexBySource.get(filter.source)
      if (candidateIds) {
        candidateIds = new Set(
          [...candidateIds].filter(id => sourceIds?.has(id))
        )
      } else {
        candidateIds = sourceIds ? new Set(sourceIds) : new Set()
      }
    }

    // Get all events if no filters specified
    if (!candidateIds) {
      candidateIds = new Set(this._store.keys())
    }

    // Apply remaining filters
    const results: Event[] = []
    for (const id of candidateIds) {
      const entry = this._store.get(id)
      if (!entry) continue

      const event = entry.event

      if (filter.fromTimestamp && event.timestamp < filter.fromTimestamp) continue
      if (filter.toTimestamp && event.timestamp > filter.toTimestamp) continue
      if (filter.correlationId && event.metadata.correlationId !== filter.correlationId) continue

      entry.accessedAt = Date.now()
      entry.accessCount++
      this._totalAccessCount++

      results.push(event)
    }

    return results.sort((a, b) => a.timestamp - b.timestamp)
  }

  getByType(type: EventType): Event[] {
    const ids = this._indexByType.get(type)
    if (!ids) return []

    return [...ids]
      .map(id => this.get(id))
      .filter((e): e is Event => e !== undefined)
  }

  getBySource(source: string): Event[] {
    const ids = this._indexBySource.get(source)
    if (!ids) return []

    return [...ids]
      .map(id => this.get(id))
      .filter((e): e is Event => e !== undefined)
  }

  getByCorrelationId(correlationId: string): Event[] {
    return this.query({ correlationId })
  }

  getRecent(count: number): Event[] {
    return this._indexByTimestamp
      .slice(-count)
      .map(i => this.get(i.id))
      .filter((e): e is Event => e !== undefined)
  }

  // ==========================================================================
  // Management
  // ==========================================================================

  delete(eventId: string): boolean {
    const entry = this._store.get(eventId)
    if (!entry) return false

    this.removeFromIndexes(entry.event)
    this._store.delete(eventId)
    return true
  }

  clear(): void {
    this._store.clear()
    this._indexByType.clear()
    this._indexBySource.clear()
    this._indexByTimestamp = []
    this._totalAccessCount = 0
  }

  // ==========================================================================
  // Stats
  // ==========================================================================

  getStats(): {
    totalEvents: number
    totalAccessCount: number
    typeCounts: Record<string, number>
    sourceCounts: Record<string, number>
    oldestEvent?: number
    newestEvent?: number
  } {
    const typeCounts: Record<string, number> = {}
    for (const [type, ids] of this._indexByType) {
      typeCounts[type] = ids.size
    }

    const sourceCounts: Record<string, number> = {}
    for (const [source, ids] of this._indexBySource) {
      sourceCounts[source] = ids.size
    }

    const timestamps = this._indexByTimestamp

    return {
      totalEvents: this._store.size,
      totalAccessCount: this._totalAccessCount,
      typeCounts,
      sourceCounts,
      oldestEvent: timestamps.length > 0 ? timestamps[0].timestamp : undefined,
      newestEvent: timestamps.length > 0 ? timestamps[timestamps.length - 1].timestamp : undefined,
    }
  }

  // ==========================================================================
  // Serialization
  // ==========================================================================

  toJSON(): Record<string, unknown> {
    return {
      config: this._config,
      events: Array.from(this._store.values()).map(entry => entry.event),
      stats: this.getStats(),
    }
  }

  static fromJSON(data: Record<string, unknown>): EventStore {
    const store = new EventStore(data.config as Partial<EventStoreConfig>)
    const events = data.events as Event[]
    for (const event of events) {
      store.store(event)
    }
    return store
  }
}