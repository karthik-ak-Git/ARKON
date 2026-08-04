import {
  JobConfig,
  JobState,
  JobStatus,
  JobError,
  JobResult,
  JobMetrics,
  ResourceRequirements,
} from './types.js'

export type JobHandler<TInput = unknown, TOutput = unknown> = (
  input: TInput,
  context: JobContext
) => Promise<TOutput>

export interface JobContext {
  jobId: string
  signal: AbortSignal
  resources: ResourceRequirements
  metadata: Record<string, unknown>
}

const VALID_TRANSITIONS: Record<JobStatus, JobStatus[]> = {
  [JobStatus.PENDING]: [JobStatus.QUEUED, JobStatus.CANCELLED],
  [JobStatus.QUEUED]: [JobStatus.WAITING_DEPENDENCIES, JobStatus.READY, JobStatus.RUNNING, JobStatus.CANCELLED],
  [JobStatus.WAITING_DEPENDENCIES]: [JobStatus.READY, JobStatus.CANCELLED],
  [JobStatus.READY]: [JobStatus.RUNNING, JobStatus.CANCELLED],
  [JobStatus.RUNNING]: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.PAUSED, JobStatus.CANCELLED],
  [JobStatus.PAUSED]: [JobStatus.RUNNING, JobStatus.CANCELLED],
  [JobStatus.COMPLETED]: [],
  [JobStatus.FAILED]: [JobStatus.RETRYING, JobStatus.CANCELLED],
  [JobStatus.CANCELLED]: [],
  [JobStatus.RETRYING]: [JobStatus.QUEUED, JobStatus.CANCELLED],
}

export class Job<TInput = unknown, TOutput = unknown> {
  readonly id: string
  readonly config: JobConfig
  private _state: JobState
  private _abortController: AbortController
  private _timeoutId?: ReturnType<typeof setTimeout>

  constructor(config: JobConfig) {
    this.id = config.id
    this.config = config
    this._state = {
      status: JobStatus.PENDING,
      attempts: 0,
      createdAt: Date.now(),
    }
    this._abortController = new AbortController()
  }

  get status(): JobStatus {
    return this._state.status
  }

  get state(): Readonly<JobState> {
    return { ...this._state }
  }

  get attempts(): number {
    return this._state.attempts
  }

  get createdAt(): number {
    return this._state.createdAt
  }

  get startedAt(): number | undefined {
    return this._state.startedAt
  }

  get completedAt(): number | undefined {
    return this._state.completedAt
  }

  get isTerminal(): boolean {
    return this._state.status === JobStatus.COMPLETED ||
           this._state.status === JobStatus.CANCELLED
  }

  get canRetry(): boolean {
    return this._state.status === JobStatus.FAILED &&
           this._state.attempts < this.config.maxRetries
  }

  get dependencies(): string[] {
    return [...this.config.dependencies]
  }

  get resources(): ResourceRequirements {
    return { ...this.config.resources }
  }

  get priority(): number {
    return this.config.priority
  }

  get abortSignal(): AbortSignal {
    return this._abortController.signal
  }

  private transition(to: JobStatus, data?: Partial<JobState>): void {
    const allowed = VALID_TRANSITIONS[this._state.status]
    if (!allowed.includes(to)) {
      throw new Error(
        `Invalid transition: ${this._state.status} -> ${to}`
      )
    }
    const now = Date.now()
    this._state = {
      ...this._state,
      ...data,
      status: to,
      ...(to === JobStatus.RUNNING && !this._state.startedAt ? { startedAt: now } : {}),
      ...(to === JobStatus.COMPLETED || to === JobStatus.FAILED || to === JobStatus.CANCELLED ? { completedAt: now } : {}),
      ...(to === JobStatus.PAUSED ? { pausedAt: now } : {}),
      ...(to === JobStatus.RUNNING && this._state.pausedAt ? { resumedAt: now } : {}),
    }
  }

  queue(): void {
    this.transition(JobStatus.QUEUED)
  }

  waitForDependencies(): void {
    this.transition(JobStatus.WAITING_DEPENDENCIES)
  }

  markReady(): void {
    this.transition(JobStatus.READY)
  }

  start(): void {
    this._state.attempts++
    this.transition(JobStatus.RUNNING)
    this.startTimeout()
  }

  complete(result: JobResult): void {
    this.clearTimeout()
    this.transition(JobStatus.COMPLETED, { result })
  }

  fail(error: JobError): void {
    this.clearTimeout()
    this._state.lastError = error
    this.transition(JobStatus.FAILED)
  }

  pause(): void {
    this.clearTimeout()
    this.transition(JobStatus.PAUSED)
  }

  resume(): void {
    this.transition(JobStatus.RUNNING)
    this.startTimeout()
  }

  retry(): void {
    this.transition(JobStatus.RETRYING)
  }

  queueForRetry(): void {
    this._abortController = new AbortController()
    this.transition(JobStatus.QUEUED)
  }

  cancel(): void {
    this.clearTimeout()
    this._abortController.abort()
    this.transition(JobStatus.CANCELLED)
  }

  abort(): void {
    this._abortController.abort()
  }

  canTransitionTo(status: JobStatus): boolean {
    return VALID_TRANSITIONS[this._state.status].includes(status)
  }

  private startTimeout(): void {
    this.clearTimeout()
    if (this.config.timeoutMs > 0) {
      this._timeoutId = setTimeout(() => {
        if (this._state.status === JobStatus.RUNNING) {
          this.fail({
            code: 'TIMEOUT',
            message: `Job timed out after ${this.config.timeoutMs}ms`,
            details: { timeoutMs: this.config.timeoutMs },
            recoverable: true,
            timestamp: Date.now(),
          })
        }
      }, this.config.timeoutMs)
    }
  }

  private clearTimeout(): void {
    if (this._timeoutId) {
      clearTimeout(this._timeoutId)
      this._timeoutId = undefined
    }
  }

  getMetrics(): JobMetrics {
    const startTime = this._state.startedAt ?? this._state.createdAt
    const endTime = this._state.completedAt ?? Date.now()
    return {
      startTime,
      endTime,
      durationMs: endTime - startTime,
      memoryUsedMb: 0,
      cpuUsedPercent: 0,
      attempts: this._state.attempts,
      retriesUsed: Math.max(0, this._state.attempts - 1),
    }
  }

  toJSON(): Record<string, unknown> {
    return {
      id: this.id,
      config: this.config,
      state: this._state,
    }
  }

  static fromJSON<TInput = unknown, TOutput = unknown>(
    data: Record<string, unknown>
  ): Job<TInput, TOutput> {
    const job = new Job<TInput, TOutput>(data.config as JobConfig)
    job._state = data.state as JobState
    return job
  }
}