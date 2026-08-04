import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Runtime, RuntimeInterface } from '@arkon/agent-sdk'
import { Agent, AgentConfig, AgentContext, AgentStatus, AgentType, AgentCapability, AgentPriority } from '@arkon/agent-sdk'

class TestAgent extends Agent {
  async execute() {
    return { success: true, data: {}, metrics: this.metrics }
  }
}

class TestRuntime extends Runtime {
  protected _createAgent(config: AgentConfig, context: AgentContext): Agent {
    return new TestAgent(config, context)
  }
}

describe('Runtime', () => {
  let runtime: TestRuntime

  beforeEach(() => {
    runtime = new TestRuntime()
  })

  afterEach(async () => {
    await runtime.shutdownAll()
  })

  describe('registerAgent', () => {
    it('should register an agent', async () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const agent = await runtime.registerAgent(config)
      expect(agent.config.id).toBe('agent-1')
      expect(agent.status).toBe(AgentStatus.INITIALIZING)
    })

    it('should throw when max agents reached', async () => {
      const limitedRuntime = new TestRuntime({ maxAgents: 1 })
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Agent 1',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await limitedRuntime.registerAgent(config)
      const config2: AgentConfig = {
        id: 'agent-2',
        name: 'Agent 2',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await expect(limitedRuntime.registerAgent(config2)).rejects.toThrow(/maximum agent capacity/)
      await limitedRuntime.shutdownAll()
    })

    it('should auto-generate agent ID if not provided', async () => {
      const config: AgentConfig = {
        id: '',
        name: 'Auto ID Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const agent = await runtime.registerAgent(config)
      expect(agent.config.id).not.toBe('')
      expect(agent.config.id.startsWith('agent_')).toBe(true)
    })
  })

  describe('unregisterAgent', () => {
    it('should unregister an agent', async () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config)
      const result = await runtime.unregisterAgent('agent-1')
      expect(result).toBe(true)
    })

    it('should return false for non-existent agent', async () => {
      const result = await runtime.unregisterAgent('non-existent')
      expect(result).toBe(false)
    })
  })

  describe('getAgent', () => {
    it('should retrieve a registered agent', async () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config)
      const agent = runtime.getAgent('agent-1')
      expect(agent).toBeDefined()
      expect(agent!.config.id).toBe('agent-1')
    })

    it('should return undefined for non-existent agent', () => {
      expect(runtime.getAgent('non-existent')).toBeUndefined()
    })
  })

  describe('listAgents', () => {
    it('should list all registered agents', async () => {
      const config1: AgentConfig = {
        id: 'agent-1',
        name: 'Agent 1',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const config2: AgentConfig = {
        id: 'agent-2',
        name: 'Agent 2',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.MEMORY],
        priority: AgentPriority.HIGH,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config1)
      await runtime.registerAgent(config2)
      const agents = runtime.listAgents()
      expect(agents.length).toBe(2)
    })
  })

  describe('terminate', () => {
    it('should terminate an agent', async () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config)
      const result = await runtime.terminate('agent-1')
      expect(result).toBe(true)
    })
  })

  describe('getStats', () => {
    it('should return runtime statistics', async () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config)
      const stats = runtime.getStats()
      expect(stats.totalAgents).toBe(1)
      expect(stats.activeAgents).toBeGreaterThanOrEqual(0)
      expect(stats.uptimeMs).toBeGreaterThanOrEqual(0)
    })
  })

  describe('getHeartbeats', () => {
    it('should return heartbeats map', async () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config)
      const heartbeats = runtime.getHeartbeats()
      expect(heartbeats.size).toBeGreaterThanOrEqual(0)
    })
  })

  describe('shutdownAll', () => {
    it('should shutdown all registered agents', async () => {
      const config1: AgentConfig = {
        id: 'agent-1',
        name: 'Agent 1',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const config2: AgentConfig = {
        id: 'agent-2',
        name: 'Agent 2',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      await runtime.registerAgent(config1)
      await runtime.registerAgent(config2)
      await runtime.shutdownAll()
      expect(runtime.listAgents().length).toBe(0)
    })
  })
})