import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Agent } from '@arkon/agent-sdk'
import { AgentStatus, AgentConfig, AgentContext, AgentPriority, AgentType, AgentCapability } from '@arkon/agent-sdk'

const createTestConfig = (overrides: Partial<AgentConfig> = {}): AgentConfig => ({
  id: overrides.id ?? 'test-agent-1',
  name: overrides.name ?? 'Test Agent',
  type: overrides.type ?? AgentType.CUSTOM,
  capabilities: overrides.capabilities ?? [AgentCapability.TOOLS],
  priority: overrides.priority ?? AgentPriority.NORMAL,
  maxRetries: overrides.maxRetries ?? 3,
  timeoutMs: overrides.timeoutMs ?? 30000,
  heartbeatIntervalMs: overrides.heartbeatIntervalMs ?? 5000,
  autoRestart: overrides.autoRestart ?? false,
  metadata: overrides.metadata ?? {},
})

const createTestContext = (overrides: Partial<AgentContext> = {}): AgentContext => ({
  agentId: 'test-agent-1',
  workspaceId: 'workspace-1',
  projectId: overrides.projectId,
  workflowId: overrides.workflowId,
  taskId: overrides.taskId,
  environment: overrides.environment ?? {},
  resources: {
    memoryLimitMb: 512,
    cpuLimit: 1,
    diskLimitMb: 1024,
  },
})

class TestAgent extends Agent {
  private _executeResult: any = { message: 'success' }
  private _shouldFail: boolean = false

  setExecuteResult(result: any): void {
    this._executeResult = result
  }

  setShouldFail(shouldFail: boolean): void {
    this._shouldFail = shouldFail
  }

  async execute(): Promise<any> {
    if (this._shouldFail) {
      throw new Error('Execution failed')
    }
    return {
      success: true,
      data: this._executeResult,
      metrics: this.metrics,
    }
  }
}

describe('Agent', () => {
  let agent: TestAgent
  let config: AgentConfig
  let context: AgentContext

  beforeEach(() => {
    config = createTestConfig()
    context = createTestContext()
    agent = new TestAgent(config, context)
  })

  afterEach(async () => {
    await agent.shutdown()
  })

  describe('initialization', () => {
    it('should initialize with IDLE status', () => {
      expect(agent.status).toBe(AgentStatus.IDLE)
    })

    it('should set status to INITIALIZING when initialize is called', async () => {
      await agent.initialize()
      expect(agent.status).toBe(AgentStatus.INITIALIZING)
    })

    it('should set startedAt timestamp on initialize', async () => {
      await agent.initialize()
      expect(agent.uptimeMs).toBeGreaterThanOrEqual(0)
    })
  })

  describe('execute', () => {
    it('should execute and return success result', async () => {
      await agent.initialize()
      const result = await agent.execute()
      expect(result.success).toBe(true)
      expect(result.data).toEqual({ message: 'success' })
    })

    it('should return error result when execution throws', async () => {
      agent.setShouldFail(true)
      await agent.initialize()
      const result = await agent.execute()
      expect(result.success).toBe(false)
      expect(result.error).toBeDefined()
      expect(result.error!.code).toBe('EXECUTION_ERROR')
    })
  })

  describe('pause and resume', () => {
    it('should pause when in RUNNING state', async () => {
      await agent.initialize()
      agent._setStatus(AgentStatus.RUNNING)
      await agent.pause()
      expect(agent.status).toBe(AgentStatus.PAUSED)
    })

    it('should throw when pausing in non-RUNNING state', async () => {
      await agent.initialize()
      await expect(agent.pause()).rejects.toThrow()
    })

    it('should resume when in PAUSED state', async () => {
      await agent.initialize()
      agent._setStatus(AgentStatus.PAUSED)
      await agent.resume()
      expect(agent.status).toBe(AgentStatus.RUNNING)
    })

    it('should throw when resuming in non-PAUSED state', async () => {
      await agent.initialize()
      await expect(agent.resume()).rejects.toThrow()
    })
  })

  describe('cancel', () => {
    it('should set status to STOPPING when cancel is called', async () => {
      await agent.initialize()
      agent._setStatus(AgentStatus.RUNNING)
      await agent.cancel()
      expect(agent.status).toBe(AgentStatus.STOPPING)
    })

    it('should be idempotent when already shutdown', async () => {
      await agent.initialize()
      agent._setStatus(AgentStatus.SHUTDOWN)
      await agent.cancel()
      expect(agent.status).toBe(AgentStatus.SHUTDOWN)
    })
  })

  describe('shutdown', () => {
    it('should set status to SHUTDOWN', async () => {
      await agent.initialize()
      await agent.shutdown()
      expect(agent.status).toBe(AgentStatus.SHUTDOWN)
    })

    it('should stop heartbeat on shutdown', async () => {
      await agent.initialize()
      agent._startHeartbeat()
      await agent.shutdown()
      expect(agent.status).toBe(AgentStatus.SHUTDOWN)
    })
  })

  describe('heartbeat', () => {
    it('should return heartbeat with correct agentId', async () => {
      await agent.initialize()
      const heartbeat = await agent.heartbeat()
      expect(heartbeat.agentId).toBe(config.id)
    })

    it('should return heartbeat with current status', async () => {
      await agent.initialize()
      agent._setStatus(AgentStatus.RUNNING)
      const heartbeat = await agent.heartbeat()
      expect(heartbeat.status).toBe(AgentStatus.RUNNING)
    })

    it('should include uptime in heartbeat', async () => {
      await agent.initialize()
      const heartbeat = await agent.heartbeat()
      expect(heartbeat.uptimeMs).toBeGreaterThanOrEqual(0)
    })
  })

  describe('status', () => {
    it('should return current status', () => {
      expect(agent.status()).toBe(AgentStatus.IDLE)
    })
  })

  describe('event listeners', () => {
    it('should emit lifecycle events', async () => {
      const events: string[] = []
      agent.on('*', (event) => {
        events.push(event.type)
      })
      await agent.initialize()
      expect(events).toContain('initialized')
    })

    it('should allow removing event listeners', async () => {
      const events: string[] = []
      const unsubscribe = agent.on('*', (event) => {
        events.push(event.type)
      })
      await agent.initialize()
      unsubscribe()
      agent._emitEvent({ type: 'registered', agentId: config.id, timestamp: Date.now() })
      expect(events.length).toBe(1)
    })
  })

  describe('metrics', () => {
    it('should track execution metrics', async () => {
      await agent.initialize()
      await agent.execute()
      expect(agent.metrics.durationMs).toBeGreaterThanOrEqual(0)
    })
  })
})