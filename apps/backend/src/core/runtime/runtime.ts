import {
  Agent,
  AgentConfig,
  AgentContext,
  AgentResult,
  AgentStatus,
  AgentType,
  AgentCapability,
  AgentPriority,
  DEFAULT_RUNTIME_CONFIG,
  Runtime,
  RuntimeInterface,
  RuntimeStats,
  Heartbeat,
  AgentLifecycleEvent,
} from '@arkon/agent-sdk'
import { EventEmitter } from 'events'

export interface BackendAgentConfig extends AgentConfig {
  backendUrl: string
  wsUrl: string
}

export interface BackendAgentContext extends AgentContext {
  backendUrl: string
  wsUrl: string
  apiKey?: string
}

export class BackendAgent extends Agent {
  private _backendUrl: string
  private _wsUrl: string

  constructor(config: AgentConfig, context: AgentContext) {
    super(config, context)
    this._backendUrl = (context as BackendAgentContext).backendUrl ?? ''
    this._wsUrl = (context as BackendAgentContext).wsUrl ?? ''
  }

  async execute(): Promise<AgentResult> {
    this._setStatus(AgentStatus.RUNNING)
    this._metrics.startTime = Date.now()

    try {
      const result = await this._runTask()
      this._metrics.endTime = Date.now()
      this._metrics.durationMs = this._metrics.endTime - this._metrics.startTime
      this._setStatus(AgentStatus.IDLE)
      return result
    } catch (error) {
      this._metrics.endTime = Date.now()
      this._metrics.durationMs = this._metrics.endTime - this._metrics.startTime
      this._setStatus(AgentStatus.ERROR)
      this._recordError({
        code: 'EXECUTION_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
        details: error,
        recoverable: true,
        timestamp: Date.now(),
      })
      return {
        success: false,
        data: null,
        error: {
          code: 'EXECUTION_ERROR',
          message: error instanceof Error ? error.message : 'Unknown error',
          details: error,
          recoverable: true,
          timestamp: Date.now(),
        },
        metrics: this._metrics,
      }
    }
  }

  private async _runTask(): Promise<AgentResult> {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return {
      success: true,
      data: { message: 'Task completed', agentId: this.config.id },
      metrics: this._metrics,
    }
  }
}

export class BackendRuntime extends Runtime {
  private readonly _eventBus: EventEmitter
  private readonly _agents: Map<string, BackendAgent> = new Map()

  constructor(config?: Partial<typeof DEFAULT_RUNTIME_CONFIG>) {
    super(config)
    this._eventBus = new EventEmitter()
  }

  protected _createAgent(config: AgentConfig, context: AgentContext): Agent {
    const backendConfig = config as BackendAgentConfig
    const backendContext = context as BackendAgentContext
    const agent = new BackendAgent(backendConfig, backendContext)
    this._agents.set(config.id, agent)
    return agent
  }

  onAgentEvent(event: string, listener: (data: AgentLifecycleEvent) => void): () => void {
    this._eventBus.on(event, listener)
    return () => {
      this._eventBus.off(event, listener)
    }
  }

  getAgentById(agentId: string): BackendAgent | undefined {
    return this._agents.get(agentId)
  }

  getActiveAgents(): BackendAgent[] {
    return Array.from(this._agents.values()).filter(
      (agent) => agent.status === AgentStatus.RUNNING
    )
  }

  getIdleAgents(): BackendAgent[] {
    return Array.from(this._agents.values()).filter(
      (agent) => agent.status === AgentStatus.IDLE
    )
  }

  getErroredAgents(): BackendAgent[] {
    return Array.from(this._agents.values()).filter(
      (agent) => agent.status === AgentStatus.ERROR
    )
  }

  async terminateAll(): Promise<void> {
    const agents = this.listAgents()
    for (const agent of agents) {
      await this.terminate(agent.config.id)
    }
    this._agents.clear()
  }
}