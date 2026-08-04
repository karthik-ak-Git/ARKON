import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { AgentRegistry, AgentRegistryInterface } from '@arkon/agent-sdk'
import { Agent, AgentConfig, AgentContext, AgentStatus, AgentType, AgentCapability, AgentPriority } from '@arkon/agent-sdk'

class TestAgent extends Agent {
  async execute() {
    return { success: true, data: {}, metrics: this.metrics }
  }
}

describe('AgentRegistry', () => {
  let registry: AgentRegistry

  beforeEach(() => {
    registry = new AgentRegistry()
  })

  afterEach(async () => {
    registry.clear()
  })

  describe('register', () => {
    it('should register an agent', () => {
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
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      expect(registry.getAgentCount()).toBe(1)
    })

    it('should throw when registering duplicate agent', () => {
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
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      expect(() => registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })).toThrow(/already registered/)
    })
  })

  describe('unregister', () => {
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
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      const result = registry.unregister('agent-1')
      expect(result).toBe(true)
      expect(registry.getAgentCount()).toBe(0)
    })

    it('should return false for non-existent agent', () => {
      expect(registry.unregister('non-existent')).toBe(false)
    })
  })

  describe('getAgent', () => {
    it('should retrieve a registered agent', () => {
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
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      expect(registry.getAgent('agent-1')).toBe(agent)
    })

    it('should return undefined for non-existent agent', () => {
      expect(registry.getAgent('non-existent')).toBeUndefined()
    })
  })

  describe('listAgents', () => {
    it('should list all registered agents', () => {
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
        type: AgentType.PLUGIN,
        capabilities: [AgentCapability.MEMORY],
        priority: AgentPriority.HIGH,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const context1: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const context2: AgentContext = {
        agentId: 'agent-2',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent1 = new TestAgent(config1, context1)
      const agent2 = new TestAgent(config2, context2)
      registry.register(agent1, {
        agentId: 'agent-1',
        name: 'Agent 1',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      registry.register(agent2, {
        agentId: 'agent-2',
        name: 'Agent 2',
        type: AgentType.PLUGIN,
        capabilities: [AgentCapability.MEMORY],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      expect(registry.listAgents().length).toBe(2)
    })
  })

  describe('listAgentsByStatus', () => {
    it('should filter agents by status', () => {
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
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      const idleAgents = registry.listAgentsByStatus(AgentStatus.IDLE)
      expect(idleAgents.length).toBe(1)
    })
  })

  describe('listAgentsByType', () => {
    it('should filter agents by type', () => {
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
        type: AgentType.PLUGIN,
        capabilities: [AgentCapability.MEMORY],
        priority: AgentPriority.HIGH,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const context1: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const context2: AgentContext = {
        agentId: 'agent-2',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent1 = new TestAgent(config1, context1)
      const agent2 = new TestAgent(config2, context2)
      registry.register(agent1, {
        agentId: 'agent-1',
        name: 'Agent 1',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      registry.register(agent2, {
        agentId: 'agent-2',
        name: 'Agent 2',
        type: AgentType.PLUGIN,
        capabilities: [AgentCapability.MEMORY],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      expect(registry.listAgentsByType(AgentType.CUSTOM).length).toBe(1)
      expect(registry.listAgentsByType(AgentType.PLUGIN).length).toBe(1)
    })
  })

  describe('findAgentByName', () => {
    it('should find agent by name', () => {
      const config: AgentConfig = {
        id: 'agent-1',
        name: 'My Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        priority: AgentPriority.NORMAL,
        maxRetries: 3,
        timeoutMs: 30000,
        heartbeatIntervalMs: 5000,
        autoRestart: false,
        metadata: {},
      }
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'My Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      expect(registry.findAgentByName('My Agent')).toBe(agent)
      expect(registry.findAgentByName('Nonexistent')).toBeUndefined()
    })
  })

  describe('clear', () => {
    it('should clear all agents', () => {
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
      const context: AgentContext = {
        agentId: 'agent-1',
        workspaceId: 'workspace-1',
        environment: {},
        resources: { memoryLimitMb: 512, cpuLimit: 1, diskLimitMb: 1024 },
      }
      const agent = new TestAgent(config, context)
      registry.register(agent, {
        agentId: 'agent-1',
        name: 'Test Agent',
        type: AgentType.CUSTOM,
        capabilities: [AgentCapability.TOOLS],
        version: '0.1.0',
        heartbeatIntervalMs: 5000,
      })
      registry.clear()
      expect(registry.getAgentCount()).toBe(0)
    })
  })
})