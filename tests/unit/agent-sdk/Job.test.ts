import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Job, JobHandler, JobContext } from '../../src/Job.js'
import { JobConfig, JobStatus, JobPriority, JobError } from '../../src/types.js'

function createJobConfig(overrides: Partial<JobConfig> = {}): JobConfig {
  return {
    id: `job-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: 'test-handler',
    priority: JobPriority.NORMAL,
    maxRetries: 3,
    retryDelayMs: 100,
    timeoutMs: 5000,
    resources: { cpu: 1, memoryMb: 256, diskMb: 100 },
    dependencies: [],
    metadata: {},
    ...overrides,
  }
}

describe('Job', () => {
  let job: Job

  beforeEach(() => {
    job = new Job(createJobConfig({ id: 'test-job-1' }))
  })

  describe('initialization', () => {
    it('should create a job with pending status', () => {
      expect(job.status).toBe(JobStatus.PENDING)
      expect(job.id).toBe('test-job-1')
      expect(job.attempts).toBe(0)
      expect(job.isTerminal).toBe(false)
      expect(job.canRetry).toBe(false)
    })

    it('should have correct initial state', () => {
      const state = job.state
      expect(state.status).toBe(JobStatus.PENDING)
      expect(state.attempts).toBe(0)
      expect(state.createdAt).toBeGreaterThan(0)
      expect(state.startedAt).toBeUndefined()
      expect(state.completedAt).toBeUndefined()
    })

    it('should expose config values', () => {
      expect(job.dependencies).toEqual([])
      expect(job.resources).toEqual({ cpu: 1, memoryMb: 256, diskMb: 100 })
      expect(job.priority).toBe(JobPriority.NORMAL)
    })
  })

  describe('state transitions', () => {
    it('should transition from PENDING to QUEUED', () => {
      job.queue()
      expect(job.status).toBe(JobStatus.QUEUED)
    })

    it('should transition from PENDING to CANCELLED', () => {
      job.cancel()
      expect(job.status).toBe(JobStatus.CANCELLED)
      expect(job.isTerminal).toBe(true)
    })

    it('should transition from QUEUED to WAITING_DEPENDENCIES', () => {
      job.queue()
      job.waitForDependencies()
      expect(job.status).toBe(JobStatus.WAITING_DEPENDENCIES)
    })

    it('should transition from QUEUED to READY', () => {
      job.queue()
      job.markReady()
      expect(job.status).toBe(JobStatus.READY)
    })

    it('should transition from QUEUED to RUNNING', () => {
      job.queue()
      job.start()
      expect(job.status).toBe(JobStatus.RUNNING)
      expect(job.attempts).toBe(1)
    })

    it('should transition from READY to RUNNING', () => {
      job.queue()
      job.markReady()
      job.start()
      expect(job.status).toBe(JobStatus.RUNNING)
    })

    it('should transition from RUNNING to COMPLETED', () => {
      job.queue()
      job.start()
      job.complete({ success: true, data: null, metrics: { startTime: 0, endTime: 0, durationMs: 0, memoryUsedMb: 0, cpuUsedPercent: 0, attempts: 1, retriesUsed: 0 } })
      expect(job.status).toBe(JobStatus.COMPLETED)
      expect(job.isTerminal).toBe(true)
    })

    it('should transition from RUNNING to FAILED', () => {
      job.queue()
      job.start()
      job.fail({ code: 'ERROR', message: 'test', details: {}, recoverable: true, timestamp: Date.now() })
      expect(job.status).toBe(JobStatus.FAILED)
    })

    it('should transition from RUNNING to PAUSED', () => {
      job.queue()
      job.start()
      job.pause()
      expect(job.status).toBe(JobStatus.PAUSED)
    })

    it('should transition from PAUSED to RUNNING', () => {
      job.queue()
      job.start()
      job.pause()
      job.resume()
      expect(job.status).toBe(JobStatus.RUNNING)
    })

    it('should transition from FAILED to RETRYING', () => {
      job.queue()
      job.start()
      job.fail({ code: 'ERROR', message: 'test', details: {}, recoverable: true, timestamp: Date.now() })
      job.retry()
      expect(job.status).toBe(JobStatus.RETRYING)
    })

    it('should transition from RETRYING to QUEUED', () => {
      job.queue()
      job.start()
      job.fail({ code: 'ERROR', message: 'test', details: {}, recoverable: true, timestamp: Date.now() })
      job.retry()
      job.queueForRetry()
      expect(job.status).toBe(JobStatus.QUEUED)
    })

    it('should throw on invalid transitions', () => {
      job.queue()
      expect(() => job.queue()).toThrow('Invalid transition')
    })
  })

  describe('timeout handling', () => {
    it('should fail job on timeout', async () => {
      vi.useFakeTimers()
      const config = createJobConfig({ id: 'timeout-job', timeoutMs: 100 })
      const timeoutJob = new Job(config)
      timeoutJob.queue()
      timeoutJob.start()

      vi.advanceTimersByTime(100)

      expect(timeoutJob.status).toBe(JobStatus.FAILED)
      expect(timeoutJob.state.lastError?.code).toBe('TIMEOUT')
      vi.useRealTimers()
    })

    it('should not timeout if timeoutMs is 0', async () => {
      vi.useFakeTimers()
      const config = createJobConfig({ id: 'no-timeout-job', timeoutMs: 0 })
      const noTimeoutJob = new Job(config)
      noTimeoutJob.queue()
      noTimeoutJob.start()

      vi.advanceTimersByTime(10000)

      expect(noTimeoutJob.status).toBe(JobStatus.RUNNING)
      vi.useRealTimers()
    })
  })

  describe('abort signal', () => {
    it('should abort job on cancel', () => {
      job.queue()
      job.start()
      const signal = job.abortSignal
      expect(signal.aborted).toBe(false)
      job.cancel()
      expect(signal.aborted).toBe(true)
    })

    it('should abort job via abort method', () => {
      job.queue()
      job.start()
      job.abort()
      expect(job.abortSignal.aborted).toBe(true)
    })
  })

  describe('retry logic', () => {
    it('should allow retry when failed and attempts < maxRetries', () => {
      job.queue()
      job.start()
      job.fail({ code: 'ERROR', message: 'test', details: {}, recoverable: true, timestamp: Date.now() })
      expect(job.canRetry).toBe(true)
    })

    it('should not allow retry when attempts >= maxRetries', () => {
      const config = createJobConfig({ maxRetries: 1 })
      const limitedJob = new Job(config)
      limitedJob.queue()
      limitedJob.start()
      limitedJob.fail({ code: 'ERROR', message: 'test', details: {}, recoverable: true, timestamp: Date.now() })
      expect(limitedJob.canRetry).toBe(false)
    })

    it('should not allow retry when not failed', () => {
      expect(job.canRetry).toBe(false)
    })

    it('should reset abort controller on queueForRetry', () => {
      job.queue()
      job.start()
      job.abort()
      expect(job.abortSignal.aborted).toBe(true)
      job.queueForRetry()
      expect(job.abortSignal.aborted).toBe(false)
    })
  })

  describe('canTransitionTo', () => {
    it('should return true for valid transitions', () => {
      expect(job.canTransitionTo(JobStatus.QUEUED)).toBe(true)
      expect(job.canTransitionTo(JobStatus.CANCELLED)).toBe(true)
    })

    it('should return false for invalid transitions', () => {
      expect(job.canTransitionTo(JobStatus.RUNNING)).toBe(false)
      expect(job.canTransitionTo(JobStatus.COMPLETED)).toBe(false)
    })
  })

  describe('metrics', () => {
    it('should return metrics', () => {
      const metrics = job.getMetrics()
      expect(metrics).toHaveProperty('startTime')
      expect(metrics).toHaveProperty('endTime')
      expect(metrics).toHaveProperty('durationMs')
      expect(metrics).toHaveProperty('attempts')
      expect(metrics).toHaveProperty('retriesUsed')
      expect(metrics.attempts).toBe(0)
      expect(metrics.retriesUsed).toBe(0)
    })
  })

  describe('serialization', () => {
    it('should serialize to JSON', () => {
      const json = job.toJSON()
      expect(json).toHaveProperty('id')
      expect(json).toHaveProperty('config')
      expect(json).toHaveProperty('state')
    })

    it('should deserialize from JSON', () => {
      const json = job.toJSON()
      const restored = Job.fromJSON(json as Record<string, unknown>)
      expect(restored.id).toBe(job.id)
      expect(restored.status).toBe(job.status)
    })
  })
})