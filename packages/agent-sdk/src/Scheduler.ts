import {
  SchedulerConfig,
  SchedulerStats,
  SchedulerEvent,
  JobConfig,
  JobStatus,
  JobPriority,
  JobError,
  DEFAULT_SCHEDULER_CONFIG,
  ResourceRequirements,
} from './types.js'
import { Job, JobHandler, JobContext, JobResult } from './Job.js'
import { ResourceMonitorImpl } from './ResourceMonitor.js'

export type SchedulerEventHandler = (event: SchedulerEvent) => void

export class Scheduler {
  private _config: SchedulerConfig
  private _jobs: Map<string, Job> = new Map()
  private _queue: Job[] = []
  private _running: Map<string, Job> = new Map()
  private _handlers: Map<string, JobHandler> = new Map()
  private _eventHandlers: SchedulerEventHandler[] = []
  private _resourceMonitor: ResourceMonitorImpl
  private _checkInterval?: ReturnType<typeof setInterval>
  private _startTime: number = Date.now()
  private _stats = {
    totalJobs: 0,
    completedJobs: 0,
    failedJobs: 0,
    cancelledJobs: 0,
    totalWaitTime: 0,
    totalExecutionTime: 0,
    jobsCompleted: 0,
  }

  constructor(config: Partial<SchedulerConfig> = {}) {
    this._config = { ...DEFAULT_SCHEDULER_CONFIG, ...config }
    this._resourceMonitor = new ResourceMonitorImpl({
      cpu: 16,
      memoryMb: 32768,
      diskMb: 1024000,
    })
  }

  get config(): Readonly<SchedulerConfig> {
    return { ...this._config }
  }

  get stats(): SchedulerStats {
    const running = this._running.size
    const queued = this._queue.length
    const paused = this._jobsByStatus(JobStatus.PAUSED).length
    return {
      totalJobs: this._stats.totalJobs,
      queuedJobs: queued,
      runningJobs: running,
      completedJobs: this._stats.completedJobs,
      failedJobs: this._stats.failedJobs,
      cancelledJobs: this._stats.cancelledJobs,
      pausedJobs: paused,
      averageWaitTimeMs: this._stats.jobsCompleted > 0
        ? this._stats.totalWaitTime / this._stats.jobsCompleted
        : 0,
      averageExecutionTimeMs: this._stats.jobsCompleted > 0
        ? this._stats.totalExecutionTime / this._stats.jobsCompleted
        : 0,
      resourceUtilization: this._resourceMonitor.getUtilization(),
      uptimeMs: Date.now() - this._startTime,
    }
  }

  // ==========================================================================
  // Job Registration
  // ==========================================================================

  registerHandler<TInput = unknown, TOutput = unknown>(
    name: string,
    handler: JobHandler<TInput, TOutput>
  ): void {
    this._handlers.set(name, handler as JobHandler)
  }

  unregisterHandler(name: string): void {
    this._handlers.delete(name)
  }

  // ==========================================================================
  // Event Handling
  // ==========================================================================

  onEvent(handler: SchedulerEventHandler): () => void {
    this._eventHandlers.push(handler)
    return () => {
      this._eventHandlers = this._eventHandlers.filter(h => h !== handler)
    }
  }

  private emit(type: SchedulerEvent['type'], jobId: string, data?: unknown): void {
    const event: SchedulerEvent = {
      type,
      jobId,
      timestamp: Date.now(),
      data,
    }
    for (const handler of this._eventHandlers) {
      try {
        handler(event)
      } catch {
        // Event handler errors should not affect scheduler
      }
    }
  }

  // ==========================================================================
  // Queue Management
  // ==========================================================================

  submit<TInput = unknown, TOutput = unknown>(
    config: JobConfig,
    handler?: JobHandler<TInput, TOutput>
  ): Job<TInput, TOutput> {
    if (this._jobs.has(config.id)) {
      throw new Error(`Job ${config.id} already exists`)
    }

    if (this._queue.length >= this._config.maxQueueSize) {
      throw new Error('Queue is full')
    }

    const job = new Job<TInput, TOutput>(config)
    this._jobs.set(config.id, job as Job)
    this._stats.totalJobs++

    if (handler) {
      this._handlers.set(config.id, handler as JobHandler)
    }

    job.queue()

    if (this._config.enableDependencyResolution && config.dependencies.length > 0) {
      const depsMet = this.checkDependencies(config.dependencies)
      if (!depsMet) {
        job.waitForDependencies()
      } else {
        this.enqueueJob(job)
      }
    } else {
      this.enqueueJob(job)
    }

    this.emit('job_queued', config.id)
    return job
  }

  private enqueueJob(job: Job): void {
    this._queue.push(job)
    if (this._config.enablePriorityScheduling) {
      this.sortQueue()
    }
  }

  private sortQueue(): void {
    this._queue.sort((a, b) => {
      if (b.priority !== a.priority) {
        return b.priority - a.priority
      }
      return a.createdAt - b.createdAt
    })
  }

  private checkDependencies(dependencies: string[]): boolean {
    return dependencies.every(depId => {
      const dep = this._jobs.get(depId)
      return dep && dep.status === JobStatus.COMPLETED
    })
  }

  // ==========================================================================
  // Job Execution
  // ==========================================================================

  private async processQueue(): Promise<void> {
    while (this._running.size < this._config.maxConcurrentJobs && this._queue.length > 0) {
      const job = this._queue[0]
      if (!job) break

      if (this._config.enableResourceAwareScheduling) {
        if (!this._resourceMonitor.canAllocate(job.resources)) {
          break
        }
        this._resourceMonitor.allocate(job.id, job.resources)
        this.emit('resource_allocated', job.id, job.resources)
      }

      this._queue.shift()
      this._running.set(job.id, job)

      const waitTime = Date.now() - job.createdAt
      this._stats.totalWaitTime += waitTime

      this.executeJob(job)
    }
  }

  private async executeJob(job: Job): Promise<void> {
    const handlerName = job.config.name
    const handler = this._handlers.get(handlerName) || this._handlers.get(job.id)

    if (!handler) {
      job.fail({
        code: 'NO_HANDLER',
        message: `No handler registered for job ${job.id}`,
        details: { jobId: job.id, name: handlerName },
        recoverable: false,
        timestamp: Date.now(),
      })
      this.emit('job_failed', job.id, job.state.lastError)
      this._running.delete(job.id)
      this._stats.failedJobs++
      if (this._config.enableResourceAwareScheduling) {
        this._resourceMonitor.release(job.id)
        this.emit('resource_released', job.id)
      }
      return
    }

    job.start()
    this.emit('job_started', job.id)
    const startTime = Date.now()

    try {
      const context: JobContext = {
        jobId: job.id,
        signal: job.abortSignal,
        resources: job.resources,
        metadata: job.config.metadata,
      }

      const result = await handler(job.config.metadata, context)
      const jobResult: JobResult = {
        success: true,
        data: result,
        metrics: {
          startTime,
          endTime: Date.now(),
          durationMs: Date.now() - startTime,
          memoryUsedMb: 0,
          cpuUsedPercent: 0,
          attempts: job.attempts,
          retriesUsed: job.attempts - 1,
        },
      }

      job.complete(jobResult)
      this.emit('job_completed', job.id, jobResult)
      this._stats.completedJobs++
      this._stats.totalExecutionTime += Date.now() - startTime
    } catch (error) {
      const jobError: JobError = {
        code: 'EXECUTION_ERROR',
        message: error instanceof Error ? error.message : String(error),
        details: error,
        recoverable: true,
        timestamp: Date.now(),
      }
      job.fail(jobError)
      this.emit('job_failed', job.id, jobError)
      this._stats.failedJobs++

      if (job.canRetry) {
        this.scheduleRetry(job)
      }
    } finally {
      this._running.delete(job.id)
      if (this._config.enableResourceAwareScheduling) {
        this._resourceMonitor.release(job.id)
        this.emit('resource_released', job.id)
      }
      this.checkDependentJobs(job.id)
    }
  }

  private scheduleRetry(job: Job): void {
    job.retry()
    this.emit('job_retrying', job.id, {
      attempt: job.attempts,
      maxRetries: job.config.maxRetries,
      delayMs: job.config.retryDelayMs,
    })

    setTimeout(() => {
      if (job.status === JobStatus.RETRYING) {
        job.queueForRetry()
        this.enqueueJob(job)
        this.emit('job_queued', job.id, { retry: true })
      }
    }, job.config.retryDelayMs)
  }

  private checkDependentJobs(completedJobId: string): void {
    if (!this._config.enableDependencyResolution) return

    for (const job of this._jobs.values()) {
      if (job.status === JobStatus.WAITING_DEPENDENCIES) {
        if (this.checkDependencies(job.dependencies)) {
          job.markReady()
          this.enqueueJob(job)
          this.emit('job_ready', job.id, { dependencies: job.dependencies })
        }
      }
    }
  }

  // ==========================================================================
  // Job Control
  // ==========================================================================

  pause(jobId: string): void {
    const job = this._getJob(jobId)
    if (job.status !== JobStatus.RUNNING) {
      throw new Error(`Job ${jobId} is not running (status: ${job.status})`)
    }
    job.pause()
    this.emit('job_paused', jobId)
  }

  resume(jobId: string): void {
    const job = this._getJob(jobId)
    if (job.status !== JobStatus.PAUSED) {
      throw new Error(`Job ${jobId} is not paused (status: ${job.status})`)
    }
    job.resume()
    this.emit('job_resumed', jobId)
  }

  cancel(jobId: string): void {
    const job = this._getJob(jobId)
    if (job.isTerminal) {
      throw new Error(`Job ${jobId} is in terminal state: ${job.status}`)
    }
    job.cancel()
    this._queue = this._queue.filter(j => j.id !== jobId)
    this._running.delete(jobId)
    this._stats.cancelledJobs++
    if (this._config.enableResourceAwareScheduling) {
      this._resourceMonitor.release(jobId)
      this.emit('resource_released', jobId)
    }
    this.emit('job_cancelled', jobId)
  }

  retry(jobId: string): void {
    const job = this._getJob(jobId)
    if (!job.canRetry) {
      throw new Error(`Job ${jobId} cannot be retried (status: ${job.status}, attempts: ${job.attempts}/${job.config.maxRetries})`)
    }
    this.scheduleRetry(job)
  }

  // ==========================================================================
  // Job Queries
  // ==========================================================================

  getJob(jobId: string): Job | undefined {
    return this._jobs.get(jobId)
  }

  private _getJob(jobId: string): Job {
    const job = this._jobs.get(jobId)
    if (!job) {
      throw new Error(`Job ${jobId} not found`)
    }
    return job
  }

  getJobState(jobId: string) {
    return this._getJob(jobId).state
  }

  getJobsByStatus(status: JobStatus): Job[] {
    return this._jobsByStatus(status)
  }

  private _jobsByStatus(status: JobStatus): Job[] {
    return Array.from(this._jobs.values()).filter(j => j.status === status)
  }

  getAllJobs(): Job[] {
    return Array.from(this._jobs.values())
  }

  getQueue(): Job[] {
    return [...this._queue]
  }

  getRunning(): Job[] {
    return Array.from(this._running.values())
  }

  // ==========================================================================
  // Lifecycle
  // ==========================================================================

  start(): void {
    if (this._checkInterval) return
    this._checkInterval = setInterval(() => {
      this.processQueue()
    }, this._config.checkIntervalMs)
    this.processQueue()
  }

  stop(): void {
    if (this._checkInterval) {
      clearInterval(this._checkInterval)
      this._checkInterval = undefined
    }
  }

  async shutdown(): Promise<void> {
    this.stop()
    for (const job of this._running.values()) {
      job.abort()
    }
    this._running.clear()
    this._queue = []
  }

  // ==========================================================================
  // Serialization
  // ==========================================================================

  toJSON(): Record<string, unknown> {
    return {
      config: this._config,
      jobs: Array.from(this._jobs.values()).map(j => j.toJSON()),
      stats: this.stats,
    }
  }
}