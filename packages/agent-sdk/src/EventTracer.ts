import {
  Event,
  EventType,
  EventTracerConfig,
  EventTrace,
  DEFAULT_EVENT_TRACER_CONFIG,
} from './types.js'

export class EventTracer {
  private _config: EventTracerConfig
  private _traces: Map<string, EventTrace> = new Map()
  private _traceIndex: Map<string, Set<string>> = new Map()
  private _spanIndex: Map<string, Set<string>> = new Map()

  constructor(config: Partial<EventTracerConfig> = {}) {
    this._config = { ...DEFAULT_EVENT_TRACER_CONFIG, ...config }
  }

  get config(): Readonly<EventTracerConfig> {
    return { ...this._config }
  }

  get size(): number {
    return this._traces.size
  }

  // ==========================================================================
  // Tracing
  // ==========================================================================

  startTrace(event: Event): EventTrace {
    if (!this._config.enabled) {
      return this.createNoopTrace(event)
    }

    if (Math.random() > this._config.sampleRate) {
      return this.createNoopTrace(event)
    }

    const traceId = event.metadata.traceId || this.generateTraceId()
    const spanId = this.generateSpanId()

    const trace: EventTrace = {
      eventId: event.id,
      eventType: event.type,
      timestamp: event.timestamp,
      source: event.metadata.source,
      correlationId: event.metadata.correlationId,
      causationId: event.metadata.causationId,
      parentTraceId: event.metadata.spanId,
      traceId,
      spanId,
      status: 'pending',
      metadata: this._config.includeMetadata ? event.metadata : {},
    }

    this._traces.set(event.id, trace)
    this.updateIndexes(trace)

    return trace
  }

  completeTrace(eventId: string, status: 'success' | 'error', error?: string): void {
    const trace = this._traces.get(eventId)
    if (!trace) return

    trace.status = status
    trace.duration = Date.now() - trace.timestamp
    if (error) {
      trace.error = error
    }
  }

  failTrace(eventId: string, error: string): void {
    this.completeTrace(eventId, 'error', error)
  }

  // ==========================================================================
  // Span Management
  // ==========================================================================

  createSpan(
    parentTraceId: string,
    event: Event
  ): EventTrace {
    if (!this._config.enabled) {
      return this.createNoopTrace(event)
    }

    const trace = this._traces.get(event.id)
    if (trace) {
      return trace
    }

    const spanId = this.generateSpanId()

    const newTrace: EventTrace = {
      eventId: event.id,
      eventType: event.type,
      timestamp: event.timestamp,
      source: event.metadata.source,
      correlationId: event.metadata.correlationId,
      causationId: event.metadata.causationId,
      parentTraceId,
      traceId: parentTraceId,
      spanId,
      status: 'pending',
      metadata: this._config.includeMetadata ? event.metadata : {},
    }

    this._traces.set(event.id, newTrace)
    this.updateIndexes(newTrace)

    return newTrace
  }

  // ==========================================================================
  // Retrieval
  // ==========================================================================

  getTrace(eventId: string): EventTrace | undefined {
    return this._traces.get(eventId)
  }

  getTraceByTraceId(traceId: string): EventTrace[] {
    const ids = this._traceIndex.get(traceId)
    if (!ids) return []

    return [...ids]
      .map(id => this._traces.get(id))
      .filter((t): t is EventTrace => t !== undefined)
  }

  getTraceBySpanId(spanId: string): EventTrace | undefined {
    const ids = this._spanIndex.get(spanId)
    if (!ids || ids.size === 0) return undefined

    const firstId = [...ids][0]
    return this._traces.get(firstId)
  }

  getChildTraces(parentTraceId: string): EventTrace[] {
    const children: EventTrace[] = []
    for (const trace of this._traces.values()) {
      if (trace.parentTraceId === parentTraceId) {
        children.push(trace)
      }
    }
    return children.sort((a, b) => a.timestamp - b.timestamp)
  }

  getTraceTree(traceId: string): EventTrace | undefined {
    const traces = this.getTraceByTraceId(traceId)
    if (traces.length === 0) return undefined

    const root = traces.find(t => !t.parentTraceId) || traces[0]
    return this.buildTree(root, traces)
  }

  private buildTree(root: EventTrace, allTraces: EventTrace[]): EventTrace {
    const children = allTraces.filter(t => t.parentTraceId === root.spanId)
    return {
      ...root,
      metadata: {
        ...root.metadata,
        children: children.map(c => this.buildTree(c, allTraces)),
      },
    }
  }

  // ==========================================================================
  // Query
  // ==========================================================================

  query(filter: {
    traceId?: string
    eventType?: EventType
    source?: string
    status?: 'pending' | 'success' | 'error'
    fromTimestamp?: number
    toTimestamp?: number
    limit?: number
  }): EventTrace[] {
    let traces = Array.from(this._traces.values())

    if (filter.traceId) {
      traces = traces.filter(t => t.traceId === filter.traceId)
    }
    if (filter.eventType) {
      traces = traces.filter(t => t.eventType === filter.eventType)
    }
    if (filter.source) {
      traces = traces.filter(t => t.source === filter.source)
    }
    if (filter.status) {
      traces = traces.filter(t => t.status === filter.status)
    }
    if (filter.fromTimestamp) {
      traces = traces.filter(t => t.timestamp >= filter.fromTimestamp!)
    }
    if (filter.toTimestamp) {
      traces = traces.filter(t => t.timestamp <= filter.toTimestamp!)
    }

    traces.sort((a, b) => a.timestamp - b.timestamp)

    if (filter.limit) {
      traces = traces.slice(0, filter.limit)
    }

    return traces
  }

  // ==========================================================================
  // Stats
  // ==========================================================================

  getStats(): {
    totalTraces: number
    pendingTraces: number
    successTraces: number
    errorTraces: number
    averageDurationMs: number
    tracesByType: Record<string, number>
    tracesBySource: Record<string, number>
  } {
    const traces = Array.from(this._traces.values())

    const pending = traces.filter(t => t.status === 'pending')
    const success = traces.filter(t => t.status === 'success')
    const error = traces.filter(t => t.status === 'error')

    const completedTraces = traces.filter(t => t.duration !== undefined)
    const averageDurationMs = completedTraces.length > 0
      ? completedTraces.reduce((sum, t) => sum + (t.duration || 0), 0) / completedTraces.length
      : 0

    const tracesByType: Record<string, number> = {}
    const tracesBySource: Record<string, number> = {}

    for (const trace of traces) {
      tracesByType[trace.eventType] = (tracesByType[trace.eventType] || 0) + 1
      tracesBySource[trace.source] = (tracesBySource[trace.source] || 0) + 1
    }

    return {
      totalTraces: traces.length,
      pendingTraces: pending.length,
      successTraces: success.length,
      errorTraces: error.length,
      averageDurationMs,
      tracesByType,
      tracesBySource,
    }
  }

  // ==========================================================================
  // Management
  // ==========================================================================

  clear(): void {
    this._traces.clear()
    this._traceIndex.clear()
    this._spanIndex.clear()
  }

  delete(eventId: string): boolean {
    const trace = this._traces.get(eventId)
    if (!trace) return false

    this.removeFromIndexes(trace)
    this._traces.delete(eventId)
    return true
  }

  // ==========================================================================
  // Export
  // ==========================================================================

  get traces(): EventTrace[] {
    return Array.from(this._traces.values())
  }

  tracesByTraceId(traceId: string): EventTrace[] {
    return this.getTraceByTraceId(traceId)
  }

  // ==========================================================================
  // Private Helpers
  // ==========================================================================

  private updateIndexes(trace: EventTrace): void {
    // Index by traceId
    if (!this._traceIndex.has(trace.traceId)) {
      this._traceIndex.set(trace.traceId, new Set())
    }
    this._traceIndex.get(trace.traceId)!.add(trace.eventId)

    // Index by spanId
    if (!this._spanIndex.has(trace.spanId)) {
      this._spanIndex.set(trace.spanId, new Set())
    }
    this._spanIndex.get(trace.spanId)!.add(trace.eventId)
  }

  private removeFromIndexes(trace: EventTrace): void {
    const traceIds = this._traceIndex.get(trace.traceId)
    if (traceIds) {
      traceIds.delete(trace.eventId)
      if (traceIds.size === 0) {
        this._traceIndex.delete(trace.traceId)
      }
    }

    const spanIds = this._spanIndex.get(trace.spanId)
    if (spanIds) {
      spanIds.delete(trace.eventId)
      if (spanIds.size === 0) {
        this._spanIndex.delete(trace.spanId)
      }
    }
  }

  private createNoopTrace(event: Event): EventTrace {
    return {
      eventId: event.id,
      eventType: event.type,
      timestamp: event.timestamp,
      source: event.metadata.source,
      traceId: '',
      spanId: '',
      status: 'success',
      metadata: {},
    }
  }

  private generateTraceId(): string {
    return `trace-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  }

  private generateSpanId(): string {
    return `span-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  }
}