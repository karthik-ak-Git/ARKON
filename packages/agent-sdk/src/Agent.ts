import {
  AgentConfig,
  AgentContext,
  AgentResult,
  AgentStatus,
  Heartbeat,
  AgentError,
  AgentMetrics,
  AgentLifecycleEvent,
} from './types.js'

export abstract class Agent {
  public readonly config: AgentConfig
  public readonly context: AgentContext
  protected _status: AgentStatus = AgentStatus.IDLE
  protected _heartbeatInterval: ReturnType<typeof setInterval> | null = null
  protected _startedAt: number = 0
  protected _metrics: AgentMetrics = {
    startTime: 0,
    endTime: 0,
    durationMs: 0,
    memoryUsedMb: 0,
    cpuUsedPercent: 0,
    retries: 0,
    eventsEmitted: 0,
  }
  protected _lastError: AgentError | null = null
  protected _listeners: Map<string, Set<(event: AgentLifecycleEvent) => void>> = new Map()

  constructor(config: AgentConfig, context: AgentContext) {
    this.config = { ...config }
    this.context = context
  }

  get status(): AgentStatus {
    return this._status
  }

  get metrics(): Readonly<AgentMetrics> {
    return { ...this._metrics }
  }

  get lastError(): AgentError | null {
    return this._lastError ? { ...this._lastError } : null
  }

  get uptimeMs(): number {
    if (this._startedAt === 0) return 0
    return Date.now() - this._startedAt
  }

  async initialize(): Promise<void> {
    this._setStatus(AgentStatus.INITIALIZING)
    this._metrics.startTime = Date.now()
    this._startedAt = Date.now()
    this._emitEvent({ type: 'initialized', agentId: this.config.id, timestamp: Date.now() })
  }

  abstract execute(): Promise<AgentResult>

  async pause(): Promise<void> {
    if (this._status !== AgentStatus.RUNNING) {
      throw new Error(`Cannot pause agent in ${this._status} state`)
    }
    this._setStatus(AgentStatus.PAUSED)
    this._emitEvent({ type: 'paused', agentId: this.config.id, timestamp: Date.now() })
  }

  async resume(): Promise<void> {
    if (this._status !== AgentStatus.PAUSED) {
      throw new Error(`Cannot resume agent in ${this._status} state`)
    }
    this._setStatus(AgentStatus.RUNNING)
    this._emitEvent({ type: 'resumed', agentId: this.config.id, timestamp: Date.now() })
  }

  async cancel(): Promise<void> {
    if (this._status === AgentStatus.SHUTDOWN || this._status === AgentStatus.STOPPING) {
      return
    }
    this._setStatus(AgentStatus.STOPPING)
    this._emitEvent({ type: 'cancelled', agentId: this.config.id, timestamp: Date.now() })
  }

  async shutdown(): Promise<void> {
    this._setStatus(AgentStatus.SHUTDOWN)
    this._stopHeartbeat()
    this._metrics.endTime = Date.now()
    this._metrics.durationMs = this._metrics.endTime - this._metrics.startTime
    this._emitEvent({ type: 'shutdown', agentId: this.config.id, timestamp: Date.now() })
  }

  status(): AgentStatus {
    return this._status
  }

  async heartbeat(): Promise<Heartbeat> {
    return {
      agentId: this.config.id,
      timestamp: Date.now(),
      status: this._status,
      uptimeMs: this.uptimeMs,
      memoryUsageMb: this._metrics.memoryUsedMb,
      cpuUsagePercent: this._metrics.cpuUsedPercent,
      activeTasks: this._status === AgentStatus.RUNNING ? 1 : 0,
      lastError: this._lastError?.message,
    }
  }

  on(event: string, listener: (event: AgentLifecycleEvent) => void): () => void {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set())
    }
    this._listeners.get(event)!.add(listener)
    return () => {
      this._listeners.get(event)?.delete(listener)
    }
  }

  protected _setStatus(status: AgentStatus): void {
    this._status = status
  }

  protected _emitEvent(event: AgentLifecycleEvent): void {
    const listeners = this._listeners.get(event.type)
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(event)
        } catch {
        }
      })
    }
    const wildcard = this._listeners.get('*')
    if (wildcard) {
      wildcard.forEach((listener) => {
        try {
          listener(event)
        } catch {
        }
      })
    }
  }

  protected _stopHeartbeat(): void {
    if (this._heartbeatInterval !== null) {
      clearInterval(this._heartbeatInterval)
      this._heartbeatInterval = null
    }
  }

  protected _startHeartbeat(): void {
    if (this._heartbeatInterval !== null) {
      clearInterval(this._heartbeatInterval)
    }
    this._heartbeatInterval = setInterval(async () => {
      try {
        await this.heartbeat()
      } catch {
      }
    }, this.config.heartbeatIntervalMs)
  }

  protected _recordError(error: AgentError): void {
    this._lastError = error
    this._emitEvent({ type: 'error', agentId: this.config.id, timestamp: Date.now(), data: error })
  }
}