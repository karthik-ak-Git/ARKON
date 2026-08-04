import { Agent, AgentConfig, AgentContext, AgentRegistration, AgentStatus, AgentType, AgentCapability } from './types.js'

export interface AgentRegistryInterface {
  register(agent: Agent, config: AgentRegistration): void
  unregister(agentId: string): boolean
  getAgent(agentId: string): Agent | undefined
  listAgents(): Agent[]
  listAgentsByStatus(status: AgentStatus): Agent[]
  listAgentsByType(type: AgentType): Agent[]
  listAgentsByCapability(capability: AgentCapability): Agent[]
  getAgentCount(): number
  getActiveAgentCount(): number
  findAgentByName(name: string): Agent | undefined
  clear(): void
}

export class AgentRegistry implements AgentRegistryInterface {
  private _agents: Map<string, Agent> = new Map()
  private _registrations: Map<string, AgentRegistration> = new Map()

  register(agent: Agent, registration: AgentRegistration): void {
    if (this._agents.has(registration.agentId)) {
      throw new Error(`Agent with id '${registration.agentId}' is already registered`)
    }
    this._agents.set(registration.agentId, agent)
    this._registrations.set(registration.agentId, registration)
    agent.on('*', () => {
    })
  }

  unregister(agentId: string): boolean {
    const agent = this._agents.get(agentId)
    if (!agent) {
      return false
    }
    agent.shutdown()
    this._agents.delete(agentId)
    this._registrations.delete(agentId)
    return true
  }

  getAgent(agentId: string): Agent | undefined {
    return this._agents.get(agentId)
  }

  listAgents(): Agent[] {
    return Array.from(this._agents.values())
  }

  listAgentsByStatus(status: AgentStatus): Agent[] {
    return this.listAgents().filter((agent) => agent.status === status)
  }

  listAgentsByType(type: AgentType): Agent[] {
    return this.listAgents().filter((agent) => agent.config.type === type)
  }

  listAgentsByCapability(capability: AgentCapability): Agent[] {
    return this.listAgents().filter((agent) => agent.config.capabilities.includes(capability))
  }

  getAgentCount(): number {
    return this._agents.size
  }

  getActiveAgentCount(): number {
    return this.listAgentsByStatus(AgentStatus.RUNNING).length
  }

  findAgentByName(name: string): Agent | undefined {
    return this.listAgents().find((agent) => agent.config.name === name)
  }

  clear(): void {
    for (const agent of this._agents.values()) {
      agent.shutdown()
    }
    this._agents.clear()
    this._registrations.clear()
  }

  getRegistration(agentId: string): AgentRegistration | undefined {
    return this._registrations.get(agentId)
  }
}