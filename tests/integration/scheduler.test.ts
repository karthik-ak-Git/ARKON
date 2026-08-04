import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Scheduler } from '../../src/Scheduler.js'
import { JobHandler } from '../../src/Job.js'
import {
  JobConfig,
  JobStatus,
  JobPriority,
  SchedulerEvent,
} from '../../src/types.js'

function createJobConfig(overrides: Partial<JobConfig> = {}): JobConfig {
  return {
    id: `job-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: 'test-handler',
    priority: JobPriority.NORMAL,
    maxRetries: 3,
    retryDelayMs: 10,
    timeoutMs: 5000,
    resources: { cpu: 1, memoryMb: 256, diskMb: 100 },
    dependencies: [],
    metadata: {},
    ...overrides,
  }
}

function createHandler(result: unknown = 'done'): JobHandler {
  return vi.fn().mockResolvedValue(result)
}

function createFailingHandler(error: Error = new Error('test error')): JobHandler {
  return vi.fn().mockRejectedValue(error)
}

function createSlowHandler(ms: number, result: unknown = 'done'): JobHandler {
  return vi.fn().mockImplementation(
    () => new Promise(resolve => setTimeout(() => resolve(result), ms))
  )
}

describe('Scheduler Integration', () => {
  let scheduler: Scheduler

  beforeEach(() => {
    scheduler = new Scheduler({
      maxConcurrentJobs: 3,
      checkIntervalMs: 10,
      enablePriorityScheduling: true,
      enableDependencyResolution: true,
      enableResourceAwareScheduling: true,
    })
  })

  afterEach(async () => {
    await scheduler.shutdown()
  })

  describe('dependency chains', () => {
    it('should execute a linear dependency chain A -> B -> C', async () => {
      const executionOrder: string[] = []
      const handler = vi.fn().mockImplementation(async (metadata: Record<string, unknown>) => {
        executionOrder.push(metadata.name as string)
      })

      scheduler.registerHandler('task', handler)

      scheduler.submit(createJobConfig({ id: 'A', name: 'task', metadata: { name: 'A' } }))
      scheduler.submit(createJobConfig({ id: 'B', name: 'task', metadata: { name: 'B' }, dependencies: ['A'] }))
      scheduler.submit(createJobConfig({ id: 'C', name: 'task', metadata: { name: 'C' }, dependencies: ['B'] }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(executionOrder).toEqual(['A', 'B', 'C'])
      }, { timeout: 5000 })
    })

    it('should execute a diamond dependency A -> B, A -> C, B+C -> D', async () => {
      const executionOrder: string[] = []
      const handler = vi.fn().mockImplementation(async (metadata: Record<string, unknown>) => {
        executionOrder.push(metadata.name as string)
      })

      scheduler.registerHandler('task', handler)

      scheduler.submit(createJobConfig({ id: 'A', name: 'task', metadata: { name: 'A' } }))
      scheduler.submit(createJobConfig({ id: 'B', name: 'task', metadata: { name: 'B' }, dependencies: ['A'] }))
      scheduler.submit(createJobConfig({ id: 'C', name: 'task', metadata: { name: 'C' }, dependencies: ['A'] }))
      scheduler.submit(createJobConfig({ id: 'D', name: 'task', metadata: { name: 'D' }, dependencies: ['B', 'C'] }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(executionOrder.length).toBe(4)
      }, { timeout: 5000 })

      expect(executionOrder[0]).toBe('A')
      expect(executionOrder.slice(1, 3)).toContain('B')
      expect(executionOrder.slice(1, 3)).toContain('C')
      expect(executionOrder[3]).toBe('D')
    })
  })

  describe('failure recovery', () => {
    it('should retry failed jobs and eventually succeed', async () => {
      let attempts = 0
      const handler = vi.fn().mockImplementation(async () => {
        attempts++
        if (attempts < 3) {
          throw new Error('Not ready yet')
        }
        return 'success'
      })

      scheduler.registerHandler('flaky', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'flaky', maxRetries: 5, retryDelayMs: 10 }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalledTimes(3)
      }, { timeout: 5000 })

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.COMPLETED)
    })

    it('should fail job after max retries exhausted', async () => {
      const handler = createFailingHandler(new Error('permanent failure'))
      scheduler.registerHandler('fail', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'fail', maxRetries: 2, retryDelayMs: 10 }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalledTimes(3)
      }, { timeout: 5000 })

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.FAILED)
    })

    it('should not execute dependent job when dependency fails', async () => {
      const handler = createFailingHandler(new Error('dep failed'))
      const depHandler = createHandler()

      scheduler.registerHandler('fail', handler)
      scheduler.registerHandler('dep', depHandler)

      scheduler.submit(createJobConfig({ id: 'dep-1', name: 'fail' }))
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'dep', dependencies: ['dep-1'] }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      }, { timeout: 5000 })

      await new Promise(r => setTimeout(r, 100))

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.WAITING_DEPENDENCIES)
    })
  })

  describe('concurrent execution', () => {
    it('should respect max concurrent jobs limit', async () => {
      let runningCount = 0
      let maxRunning = 0

      const handler = vi.fn().mockImplementation(async () => {
        runningCount++
        maxRunning = Math.max(maxRunning, runningCount)
        await new Promise(r => setTimeout(r, 50))
        runningCount--
      })

      scheduler = new Scheduler({
        maxConcurrentJobs: 2,
        checkIntervalMs: 10,
        enableResourceAwareScheduling: false,
      })

      scheduler.registerHandler('task', handler)

      for (let i = 0; i < 6; i++) {
        scheduler.submit(createJobConfig({ id: `job-${i}`, name: 'task' }))
      }

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalledTimes(6)
      }, { timeout: 10000 })

      expect(maxRunning).toBeLessThanOrEqual(2)
    })
  })

  describe('priority scheduling', () => {
    it('should execute higher priority jobs first', async () => {
      const executionOrder: string[] = []

      const handler = vi.fn().mockImplementation(async (metadata: Record<string, unknown>) => {
        executionOrder.push(metadata.name as string)
      })

      scheduler = new Scheduler({
        maxConcurrentJobs: 1,
        checkIntervalMs: 10,
        enableResourceAwareScheduling: false,
      })

      scheduler.registerHandler('task', handler)

      scheduler.submit(createJobConfig({ id: 'low', name: 'task', priority: JobPriority.LOW, metadata: { name: 'low' } }))
      scheduler.submit(createJobConfig({ id: 'high', name: 'task', priority: JobPriority.HIGH, metadata: { name: 'high' } }))
      scheduler.submit(createJobConfig({ id: 'normal', name: 'task', priority: JobPriority.NORMAL, metadata: { name: 'normal' } }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(executionOrder.length).toBe(3)
      }, { timeout: 5000 })

      expect(executionOrder).toEqual(['high', 'normal', 'low'])
    })
  })

  describe('event tracking', () => {
    it('should track all job lifecycle events', async () => {
      const events: SchedulerEvent[] = []
      scheduler.onEvent(event => events.push(event))

      const handler = createHandler()
      scheduler.registerHandler('test', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'test' }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(events.some(e => e.type === 'job_completed')).toBe(true)
      }, { timeout: 5000 })

      expect(events).toContainEqual(
        expect.objectContaining({ type: 'job_queued', jobId: 'job-1' })
      )
      expect(events).toContainEqual(
        expect.objectContaining({ type: 'job_started', jobId: 'job-1' })
      )
      expect(events).toContainEqual(
        expect.objectContaining({ type: 'job_completed', jobId: 'job-1' })
      )
    })
  })

  describe('cancel during execution', () => {
    it('should cancel a running job and not complete it', async () => {
      let completed = false
      const handler = vi.fn().mockImplementation(async () => {
        await new Promise(r => setTimeout(r, 1000))
        completed = true
      })

      scheduler.registerHandler('slow', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'slow' }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      scheduler.cancel('job-1')

      await new Promise(r => setTimeout(r, 100))

      expect(completed).toBe(false)
      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.CANCELLED)
    })
  })

  describe('pause and resume during execution', () => {
    it('should pause and resume a running job', async () => {
      let resumeCalled = false
      const handler = vi.fn().mockImplementation(async () => {
        await new Promise(r => setTimeout(r, 100))
        resumeCalled = true
      })

      scheduler.registerHandler('slow', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'slow' }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      scheduler.pause('job-1')
      expect(scheduler.getJob('job-1')?.status).toBe(JobStatus.PAUSED)

      scheduler.resume('job-1')
      expect(scheduler.getJob('job-1')?.status).toBe(JobStatus.RUNNING)
    })
  })

  describe('resource constraints', () => {
    it('should queue jobs when resources are exhausted', async () => {
      scheduler = new Scheduler({
        maxConcurrentJobs: 100,
        checkIntervalMs: 10,
        enableResourceAwareScheduling: true,
      })

      const handler = createSlowHandler(200)
      scheduler.registerHandler('resource-heavy', handler)

      scheduler.submit(createJobConfig({
        id: 'big-job',
        name: 'resource-heavy',
        resources: { cpu: 100, memoryMb: 100000, diskMb: 100000 },
      }))

      scheduler.submit(createJobConfig({
        id: 'small-job',
        name: 'resource-heavy',
        resources: { cpu: 1, memoryMb: 1, diskMb: 1 },
      }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalledTimes(1)
      }, { timeout: 1000 })

      const bigJob = scheduler.getJob('big-job')
      expect(bigJob?.status).toBe(JobStatus.RUNNING)

      const smallJob = scheduler.getJob('small-job')
      expect(smallJob?.status).toBe(JobStatus.QUEUED)
    })
  })

  describe('complex workflow', () => {
    it('should handle a real-world video processing workflow', async () => {
      const steps: string[] = []

      const ingestHandler = vi.fn().mockImplementation(async () => {
        steps.push('ingest')
        return { files: ['video.mp4'] }
      })

      const transcodeHandler = vi.fn().mockImplementation(async () => {
        steps.push('transcode')
        return { transcoded: true }
      })

      const thumbnailHandler = vi.fn().mockImplementation(async () => {
        steps.push('thumbnail')
        return { thumbnails: ['thumb.jpg'] }
      })

      const uploadHandler = vi.fn().mockImplementation(async () => {
        steps.push('upload')
        return { uploaded: true }
      })

      scheduler.registerHandler('ingest', ingestHandler)
      scheduler.registerHandler('transcode', transcodeHandler)
      scheduler.registerHandler('thumbnail', thumbnailHandler)
      scheduler.registerHandler('upload', uploadHandler)

      scheduler.submit(createJobConfig({ id: 'ingest', name: 'ingest' }))
      scheduler.submit(createJobConfig({ id: 'transcode', name: 'transcode', dependencies: ['ingest'] }))
      scheduler.submit(createJobConfig({ id: 'thumbnail', name: 'thumbnail', dependencies: ['ingest'] }))
      scheduler.submit(createJobConfig({ id: 'upload', name: 'upload', dependencies: ['transcode', 'thumbnail'] }))

      scheduler.start()

      await vi.waitFor(() => {
        expect(steps.length).toBe(4)
      }, { timeout: 10000 })

      expect(steps[0]).toBe('ingest')
      expect(steps.slice(1, 3)).toContain('transcode')
      expect(steps.slice(1, 3)).toContain('thumbnail')
      expect(steps[3]).toBe('upload')
    })
  })
})