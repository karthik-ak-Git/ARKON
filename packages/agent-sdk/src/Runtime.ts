import { Agent } from './Agent.js'
import { AgentRegistry, AgentRegistryInterface } from './AgentRegistry.js'
import {
  AgentConfig,
  AgentContext,
  AgentResult,
  AgentStatus,
  AgentLifecycleEvent,
  RuntimeConfig,
  RuntimeStats,
  Heartbeat,
  DEFAULT_RUNTIME_CONFIG,
} from './types.js'

export interface RuntimeInterface {
  registerAgent(config: AgentConfig, context?: Partial<AgentContext>): Promise<Agent>
  unregisterAgent(agentId: string): boolean
  getAgent(agentId: string): Agent | undefined
  listAgents(): Agent[]
  spawn(config: AgentConfig, context?: Partial<AgentContext>): Promise<Agent>
  terminate(agentId: string): Promise<boolean>
  getStats(): RuntimeStats
  getHeartbeats(): Map<string, Heartbeat>
  shutdownAll(): Promise<void>
  getRegistry(): AgentRegistryInterface
}

export class Runtime implements RuntimeInterface {
  private readonly _registry: AgentRegistry
  private readonly _config: RuntimeConfig
  private readonly _heartbeats: Map<string, Heartbeat> = new Map()
  private readonly _heartbeatTimers: Map<string, ReturnType<typeof setInterval>> = new Map()
  private readonly _cleanupTimer: ReturnType<typeof setInterval> | null = null
  private readonly _startedAt: number
  private _totalTasksCompleted: number = 0
  private _totalTasksFailed: number = 0

  constructor(config?: Partial<RuntimeConfig>) {
    this._config = { ...DEFAULT_RUNTIME_CONFIG, ...config }
    this._registry = new AgentRegistry()
    this._startedAt = Date.now()
    this._startCleanup()
  }

  get registry(): AgentRegistryInterface {
    return this._registry
  }

  async registerAgent(config: AgentConfig, context?: Partial<AgentContext>): Promise<Agent> {
    if (this._registry.getAgentCount() >= this._config.maxAgents) {
      throw new Error(`Runtime has reached maximum agent capacity (${this._config.maxAgents})`)
    }

    if (!config.id) {
      config = { ...config, id: this._generateId() }
    }

    const fullContext: AgentContext = {
      agentId: config.id,
      workspaceId: context?.workspaceId ?? 'default',
      projectId: context?.projectId,
      workflowId: context?.workflowId,
      taskId: context?.taskId,
      environment: context?.environment ?? {},
      resources: context?.resources ?? {
        memoryLimitMb: 512,
        cpuLimit: 1,
        diskLimitMb: 1024,
      },
    }

    const agent = this._createAgent(config, fullContext)
    const registration: AgentConfig = { ...config }

    this._registry.register(agent, {
      agentId: config.id,
      name: config.name,
      type: config.type,
      capabilities: config.capabilities,
      version: '0.1.0',
      heartbeatIntervalMs: config.heartbeatIntervalMs,
    })

    await agent.initialize()

    this._startHeartbeat(config.id, config.heartbeatIntervalMs)

    this._emitLifecycleEvent({
      type: 'registered',
      agentId: config.id,
      timestamp: Date.now(),
    })

    return agent
  }

  async unregisterAgent(agentId: string): Promise<boolean> {
    const agent = this._registry.getAgent(agentId)
    if (!agent) {
      return false
    }

    this._stopHeartbeat(agentId)
    this._registry.unregister(agentId)

    this._emitLifecycleEvent({
      type: 'deregistered',
      agentId,
      timestamp: Date.now(),
    })

    return true
  }

  getAgent(agentId: string): Agent | undefined {
    return this._registry.getAgent(agentId)
  }

  listAgents(): Agent[] {
    return this._registry.listAgents()
  }

  async spawn(config: AgentConfig, context?: Partial<AgentContext>): Promise<Agent> {
    const agent = await this.registerAgent(config, context)
    await agent.initialize()
    return agent
  }

  async terminate(agentId: string): Promise<boolean> {
    const agent = this._registry.getAgent(agentId)
    if (!agent) {
      return false
    }

    this._stopHeartbeat(agentId)
    await agent.cancel()
    await agent.shutdown()
    this._registry.unregister(agentId)

    this._emitLifecycleEvent({
      type: 'shutdown',
      agentId,
      timestamp: Date.now(),
    })

    return true
  }

  getStats(): RuntimeStats {
    const agents = this._registry.listAgents()
    const now = Date.now()

    return {
      totalAgents: agents.length,
      activeAgents: agents.filter((a) => a.status === AgentStatus.RUNNING).length,
      idleAgents: agents.filter((a) => a.status === AgentStatus.IDLE).length,
      erroredAgents: agents.filter((a) => a.status === AgentStatus.ERROR).length,
      totalTasksCompleted: this._totalTasksCompleted,
      totalTasksFailed: this._totalTasksFailed,
      uptimeMs: now - this._startedAt,
      memoryUsageMb: this._estimateMemoryUsage(),
      cpuUsagePercent: this._estimateCpuUsage(),
    }
  }

  getHeartbeats(): Map<string, Heartbeat> {
    return new Map(this._heartbeats)
  }

  async shutdownAll(): Promise<void> {
    const agents = this._registry.listAgents()
    for (const agent of agents) {
      await this.terminate(agent.config.id)
    }
    this._stopCleanup()
  }

  protected _createAgent(config: AgentConfig, context: AgentContext): Agent {
    throw new Error('Runtime._createAgent must be overridden by a subclass')
  }

  private _startHeartbeat(agentId: string, intervalMs: number): void {
    this._stopHeartbeat(agentId)
    const timer = setInterval(async () => {
      try {
        const agent = this._registry.getAgent(agentId)
        if (agent) {
          const heartbeat = await agent.heartbeat()
          this._heartbeats.set(agentId, heartbeat)
        }
      } catch {
      }
    }, intervalMs)
    this._heartbeatTimers.set(agentId, timer)
  }

  private _stopHeartbeat(agentId: string): void {
    const timer = this._heartbeatTimers.get(agentId)
    if (timer !== undefined) {
      clearInterval(timer)
      this._heartbeatTimers.delete(agentId)
    }
    this._heartbeats.delete(agentId)
  }

  private _startCleanup(): void {
    this._cleanupTimer = setInterval(async () => {
      await this._cleanupStaleHeartbeats()
    }, this._config.autoCleanupIntervalMs)
  }

  private _stopCleanup(): void {
    if (this._cleanupTimer !== null) {
      clearInterval(this._cleanupTimer)
      this._cleanupTimer = null
    }
  }

  private async _cleanupStaleHeartbeats(): Promise<void> {
    const now = Date.now()
    for (const [agentId, heartbeat] of this._heartbeats.entries()) {
      if (now - heartbeat.timestamp > this._config.heartbeatTimeoutMs) {
        await this.terminate(agentId)
        this._heartbeats.delete(agentId)
      }
    }
  }

  private _emitLifecycleEvent(event: AgentLifecycleEvent): void {
    if (this._config.enableTelemetry) {
    }
  }

  private _estimateMemoryUsage(): number {
    const agents = this._registry.listAgents()
    return agents.reduce((sum, agent) => sum + agent.metrics.memoryUsedMb, 0)
  }

  private _estimateCpuUsage(): number {
    const agents = this._registry.listAgents()
    if (agents.length === 0) return 0
    return agents.reduce((sum, agent) => sum + agent.metrics.cpuUsedPercent, 0) / agents.length
  }

  private _generateId(): string {
    return `agent_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
  }
}