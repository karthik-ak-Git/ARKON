import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Scheduler, SchedulerEventHandler } from '../../src/Scheduler.js'
import { JobHandler } from '../../src/Job.js'
import {
  JobConfig,
  JobStatus,
  JobPriority,
  SchedulerConfig,
  SchedulerEvent,
} from '../../src/types.js'

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

function createHandler(result: unknown = 'done'): JobHandler {
  return vi.fn().mockResolvedValue(result)
}

function createFailingHandler(error: Error = new Error('test error')): JobHandler {
  return vi.fn().mockRejectedValue(error)
}

function createSlowHandler(ms: number): JobHandler {
  return vi.fn().mockImplementation(
    () => new Promise(resolve => setTimeout(resolve, ms))
  )
}

describe('Scheduler', () => {
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

  describe('initialization', () => {
    it('should create scheduler with default config', () => {
      const s = new Scheduler()
      expect(s.config).toHaveProperty('maxConcurrentJobs')
      expect(s.config).toHaveProperty('maxQueueSize')
      expect(s.config).toHaveProperty('checkIntervalMs')
    })

    it('should create scheduler with custom config', () => {
      expect(scheduler.config.maxConcurrentJobs).toBe(3)
      expect(scheduler.config.enablePriorityScheduling).toBe(true)
    })

    it('should have empty stats initially', () => {
      const stats = scheduler.stats
      expect(stats.totalJobs).toBe(0)
      expect(stats.runningJobs).toBe(0)
      expect(stats.queuedJobs).toBe(0)
    })
  })

  describe('handler registration', () => {
    it('should register and unregister handlers', () => {
      const handler = createHandler()
      scheduler.registerHandler('test', handler)
      scheduler.unregisterHandler('test')
    })
  })

  describe('job submission', () => {
    it('should submit a job', () => {
      const job = scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(job.id).toBe('job-1')
      expect(job.status).toBe(JobStatus.QUEUED)
    })

    it('should reject duplicate job ids', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(() => {
        scheduler.submit(createJobConfig({ id: 'job-1' }))
      }).toThrow('already exists')
    })

    it('should register handler with job', () => {
      const handler = createHandler()
      const job = scheduler.submit(createJobConfig({ id: 'job-1' }), handler)
      expect(job).toBeDefined()
    })
  })

  describe('priority scheduling', () => {
    it('should prioritize higher priority jobs', () => {
      const lowJob = scheduler.submit(
        createJobConfig({ id: 'low', priority: JobPriority.LOW })
      )
      const highJob = scheduler.submit(
        createJobConfig({ id: 'high', priority: JobPriority.HIGH })
      )
      const normalJob = scheduler.submit(
        createJobConfig({ id: 'normal', priority: JobPriority.NORMAL })
      )

      const queue = scheduler.getQueue()
      expect(queue[0].id).toBe('high')
      expect(queue[1].id).toBe('normal')
      expect(queue[2].id).toBe('low')
    })

    it('should respect FIFO for same priority', () => {
      scheduler.submit(createJobConfig({ id: 'first', priority: JobPriority.NORMAL }))
      scheduler.submit(createJobConfig({ id: 'second', priority: JobPriority.NORMAL }))
      scheduler.submit(createJobConfig({ id: 'third', priority: JobPriority.NORMAL }))

      const queue = scheduler.getQueue()
      expect(queue[0].id).toBe('first')
      expect(queue[1].id).toBe('second')
      expect(queue[2].id).toBe('third')
    })
  })

  describe('job execution', () => {
    it('should execute a job', async () => {
      const handler = createHandler('result')
      scheduler.registerHandler('test', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'test' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.COMPLETED)
    })

    it('should execute multiple jobs concurrently', async () => {
      const executionOrder: string[] = []
      const handler1 = createHandler()
      const handler2 = createHandler()
      const handler3 = createHandler()

      handler1.mockImplementation(async () => {
        executionOrder.push('start-1')
        await new Promise(r => setTimeout(r, 10))
        executionOrder.push('end-1')
      })
      handler2.mockImplementation(async () => {
        executionOrder.push('start-2')
        await new Promise(r => setTimeout(r, 10))
        executionOrder.push('end-2')
      })
      handler3.mockImplementation(async () => {
        executionOrder.push('start-3')
        await new Promise(r => setTimeout(r, 10))
        executionOrder.push('end-3')
      })

      scheduler.registerHandler('handler-1', handler1)
      scheduler.registerHandler('handler-2', handler2)
      scheduler.registerHandler('handler-3', handler3)

      scheduler.submit(createJobConfig({ id: 'job-1', name: 'handler-1' }))
      scheduler.submit(createJobConfig({ id: 'job-2', name: 'handler-2' }))
      scheduler.submit(createJobConfig({ id: 'job-3', name: 'handler-3' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(executionOrder.length).toBe(6)
      })

      expect(executionOrder.filter(e => e.startsWith('start')).length).toBe(3)
      expect(executionOrder.filter(e => e.startsWith('end')).length).toBe(3)
    })
  })

  describe('cancel', () => {
    it('should cancel a queued job', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      scheduler.cancel('job-1')
      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.CANCELLED)
    })

    it('should cancel a running job', async () => {
      const handler = createSlowHandler(1000)
      scheduler.registerHandler('slow', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'slow' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      scheduler.cancel('job-1')
      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.CANCELLED)
    })

    it('should throw when cancelling non-existent job', () => {
      expect(() => scheduler.cancel('nonexistent')).toThrow('not found')
    })

    it('should throw when cancelling terminal job', async () => {
      const handler = createHandler()
      scheduler.registerHandler('test', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'test' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      expect(() => scheduler.cancel('job-1')).toThrow('terminal state')
    })
  })

  describe('pause and resume', () => {
    it('should pause a running job', async () => {
      const handler = createSlowHandler(1000)
      scheduler.registerHandler('slow', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'slow' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      scheduler.pause('job-1')
      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.PAUSED)
    })

    it('should resume a paused job', async () => {
      const handler = createSlowHandler(1000)
      scheduler.registerHandler('slow', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'slow' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      scheduler.pause('job-1')
      scheduler.resume('job-1')
      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.RUNNING)
    })

    it('should throw when pausing non-running job', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(() => scheduler.pause('job-1')).toThrow('not running')
    })

    it('should throw when resuming non-paused job', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(() => scheduler.resume('job-1')).toThrow('not paused')
    })
  })

  describe('retry', () => {
    it('should retry a failed job', async () => {
      const handler = createFailingHandler()
      scheduler.registerHandler('fail', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'fail', retryDelayMs: 10 }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalled()
      })

      scheduler.retry('job-1')
      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.RETRYING)
    })

    it('should throw when retrying non-retriable job', () => {
      scheduler.submit(createJobConfig({ id: 'job-1', maxRetries: 0 }))
      expect(() => scheduler.retry('job-1')).toThrow('cannot be retried')
    })
  })

  describe('dependency resolution', () => {
    it('should wait for dependencies', () => {
      scheduler.submit(createJobConfig({ id: 'dep-1' }))
      scheduler.submit(createJobConfig({ id: 'job-1', dependencies: ['dep-1'] }))

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.WAITING_DEPENDENCIES)
    })

    it('should mark job ready when dependencies complete', async () => {
      const handler = createHandler()
      scheduler.registerHandler('test', handler)

      scheduler.submit(createJobConfig({ id: 'dep-1', name: 'test' }))
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'test', dependencies: ['dep-1'] }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalledTimes(2)
      })

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.COMPLETED)
    })

    it('should handle multiple dependencies', async () => {
      const handler = createHandler()
      scheduler.registerHandler('test', handler)

      scheduler.submit(createJobConfig({ id: 'dep-1', name: 'test' }))
      scheduler.submit(createJobConfig({ id: 'dep-2', name: 'test' }))
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'test', dependencies: ['dep-1', 'dep-2'] }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(handler).toHaveBeenCalledTimes(3)
      })

      const job = scheduler.getJob('job-1')
      expect(job?.status).toBe(JobStatus.COMPLETED)
    })
  })

  describe('event handling', () => {
    it('should emit events', async () => {
      const events: SchedulerEvent[] = []
      scheduler.onEvent(event => events.push(event))

      const handler = createHandler()
      scheduler.registerHandler('test', handler)
      scheduler.submit(createJobConfig({ id: 'job-1', name: 'test' }))

      scheduler.start()
      await vi.waitFor(() => {
        expect(events.length).toBeGreaterThan(0)
      })

      expect(events.some(e => e.type === 'job_queued')).toBe(true)
      expect(events.some(e => e.type === 'job_started')).toBe(true)
      expect(events.some(e => e.type === 'job_completed')).toBe(true)
    })

    it('should unsubscribe from events', () => {
      const events: SchedulerEvent[] = []
      const unsubscribe = scheduler.onEvent(event => events.push(event))
      unsubscribe()
    })
  })

  describe('job queries', () => {
    it('should get job by id', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(scheduler.getJob('job-1')).toBeDefined()
      expect(scheduler.getJob('nonexistent')).toBeUndefined()
    })

    it('should get jobs by status', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      const queued = scheduler.getJobsByStatus(JobStatus.QUEUED)
      expect(queued.length).toBe(1)
    })

    it('should get all jobs', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      scheduler.submit(createJobConfig({ id: 'job-2' }))
      expect(scheduler.getAllJobs().length).toBe(2)
    })

    it('should get queue', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(scheduler.getQueue().length).toBe(1)
    })

    it('should get running jobs', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      expect(scheduler.getRunning().length).toBe(0)
    })
  })

  describe('resource-aware scheduling', () => {
    it('should track resource utilization', () => {
      const stats = scheduler.stats
      expect(stats.resourceUtilization).toHaveProperty('cpu')
      expect(stats.resourceUtilization).toHaveProperty('memoryMb')
    })
  })

  describe('lifecycle', () => {
    it('should start and stop scheduler', () => {
      scheduler.start()
      expect(scheduler).toBeDefined()
      scheduler.stop()
    })

    it('should shutdown gracefully', async () => {
      scheduler.start()
      await scheduler.shutdown()
      expect(scheduler.getRunning().length).toBe(0)
    })
  })

  describe('serialization', () => {
    it('should serialize scheduler to JSON', () => {
      scheduler.submit(createJobConfig({ id: 'job-1' }))
      const json = scheduler.toJSON()
      expect(json).toHaveProperty('config')
      expect(json).toHaveProperty('jobs')
      expect(json).toHaveProperty('stats')
    })
  })
})