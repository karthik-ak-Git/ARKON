export enum AgentStatus {
  IDLE = 'idle',
  INITIALIZING = 'initializing',
  RUNNING = 'running',
  PAUSED = 'paused',
  STOPPING = 'stopping',
  SHUTDOWN = 'shutdown',
  ERROR = 'error',
}

export enum AgentType {
  BUILTIN = 'builtin',
  PLUGIN = 'plugin',
  CUSTOM = 'custom',
}

export enum AgentCapability {
  TOOLS = 'tools',
  MEMORY = 'memory',
  EVENT_HANDLING = 'event_handling',
  WORKFLOW_EXECUTION = 'workflow_execution',
  FILE_OPERATIONS = 'file_operations',
  HTTP_REQUESTS = 'http_requests',
  SHELL_EXECUTION = 'shell_execution',
  CODE_EXECUTION = 'code_execution',
  DATA_PROCESSING = 'data_processing',
  AI_INFERENCE = 'ai_inference',
}

export enum AgentPriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  CRITICAL = 3,
}

export interface AgentConfig {
  id: string
  name: string
  type: AgentType
  description?: string
  capabilities: AgentCapability[]
  priority: AgentPriority
  maxRetries: number
  timeoutMs: number
  heartbeatIntervalMs: number
  autoRestart: boolean
  metadata: Record<string, unknown>
}

export interface AgentContext {
  agentId: string
  workspaceId: string
  projectId?: string
  workflowId?: string
  taskId?: string
  environment: Record<string, unknown>
  resources: {
    memoryLimitMb: number
    cpuLimit: number
    diskLimitMb: number
  }
}

export interface AgentMessage {
  id: string
  agentId: string
  type: 'request' | 'response' | 'event' | 'error'
  payload: unknown
  timestamp: number
  correlationId?: string
}

export interface AgentResult {
  success: boolean
  data: unknown
  error?: AgentError
  metrics: AgentMetrics
}

export interface AgentError {
  code: string
  message: string
  details: unknown
  recoverable: boolean
  timestamp: number
}

export interface AgentMetrics {
  startTime: number
  endTime: number
  durationMs: number
  memoryUsedMb: number
  cpuUsedPercent: number
  retries: number
  eventsEmitted: number
}

export interface Heartbeat {
  agentId: string
  timestamp: number
  status: AgentStatus
  uptimeMs: number
  memoryUsageMb: number
  cpuUsagePercent: number
  activeTasks: number
  lastError?: string
}

export interface AgentRegistration {
  agentId: string
  name: string
  type: AgentType
  capabilities: AgentCapability[]
  version: string
  heartbeatIntervalMs: number
}

export interface RuntimeConfig {
  maxAgents: number
  defaultTimeoutMs: number
  defaultHeartbeatIntervalMs: number
  heartbeatTimeoutMs: number
  autoCleanupIntervalMs: number
  enableTelemetry: boolean
  logLevel: 'debug' | 'info' | 'warn' | 'error'
}

export interface RuntimeStats {
  totalAgents: number
  activeAgents: number
  idleAgents: number
  erroredAgents: number
  totalTasksCompleted: number
  totalTasksFailed: number
  uptimeMs: number
  memoryUsageMb: number
  cpuUsagePercent: number
}

export interface AgentLifecycleEvent {
  type: 'registered' | 'initialized' | 'started' | 'paused' | 'resumed' | 'completed' | 'cancelled' | 'error' | 'shutdown' | 'deregistered'
  agentId: string
  timestamp: number
  data?: unknown
}

export const DEFAULT_AGENT_CONFIG: AgentConfig = {
  id: '',
  name: 'unnamed',
  type: AgentType.CUSTOM,
  capabilities: [],
  priority: AgentPriority.NORMAL,
  maxRetries: 3,
  timeoutMs: 30000,
  heartbeatIntervalMs: 5000,
  autoRestart: false,
  metadata: {},
}

export const DEFAULT_RUNTIME_CONFIG: RuntimeConfig = {
  maxAgents: 100,
  defaultTimeoutMs: 30000,
  defaultHeartbeatIntervalMs: 5000,
  heartbeatTimeoutMs: 15000,
  autoCleanupIntervalMs: 60000,
  enableTelemetry: true,
  logLevel: 'info',
}

// ============================================================================
// Scheduler Types
// ============================================================================

export enum JobStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  WAITING_DEPENDENCIES = 'waiting_dependencies',
  READY = 'ready',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  RETRYING = 'retrying',
}

export enum JobPriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  CRITICAL = 3,
}

export interface ResourceRequirements {
  cpu: number
  memoryMb: number
  diskMb: number
  gpu?: number
  custom?: Record<string, number>
}

export interface ResourceAvailability {
  cpu: number
  memoryMb: number
  diskMb: number
  gpu?: number
  custom?: Record<string, number>
}

export interface JobConfig {
  id: string
  name: string
  description?: string
  priority: JobPriority
  maxRetries: number
  retryDelayMs: number
  timeoutMs: number
  resources: ResourceRequirements
  dependencies: string[]
  metadata: Record<string, unknown>
}

export interface JobState {
  status: JobStatus
  attempts: number
  createdAt: number
  startedAt?: number
  completedAt?: number
  pausedAt?: number
  resumedAt?: number
  lastError?: JobError
  result?: JobResult
}

export interface JobError {
  code: string
  message: string
  details: unknown
  recoverable: boolean
  timestamp: number
}

export interface JobResult {
  success: boolean
  data: unknown
  error?: JobError
  metrics: JobMetrics
}

export interface JobMetrics {
  startTime: number
  endTime: number
  durationMs: number
  memoryUsedMb: number
  cpuUsedPercent: number
  attempts: number
  retriesUsed: number
}

export interface SchedulerConfig {
  maxConcurrentJobs: number
  maxQueueSize: number
  defaultJobTimeoutMs: number
  defaultMaxRetries: number
  defaultRetryDelayMs: number
  checkIntervalMs: number
  dependencyTimeoutMs: number
  resourceCheckIntervalMs: number
  enablePriorityScheduling: boolean
  enableDependencyResolution: boolean
  enableResourceAwareScheduling: boolean
}

export interface SchedulerStats {
  totalJobs: number
  queuedJobs: number
  runningJobs: number
  completedJobs: number
  failedJobs: number
  cancelledJobs: number
  pausedJobs: number
  averageWaitTimeMs: number
  averageExecutionTimeMs: number
  resourceUtilization: ResourceAvailability
  uptimeMs: number
}

export interface ResourceMonitor {
  getAvailability(): ResourceAvailability
  canAllocate(resources: ResourceRequirements): boolean
  allocate(jobId: string, resources: ResourceRequirements): boolean
  release(jobId: string): void
  getUtilization(): ResourceAvailability
}

export interface SchedulerEvent {
  type: 'job_queued' | 'job_started' | 'job_completed' | 'job_failed' | 'job_cancelled' | 'job_paused' | 'job_resumed' | 'job_retrying' | 'job_dependency_met' | 'job_ready' | 'resource_allocated' | 'resource_released'
  jobId: string
  timestamp: number
  data?: unknown
}

export const DEFAULT_SCHEDULER_CONFIG: SchedulerConfig = {
  maxConcurrentJobs: 10,
  maxQueueSize: 1000,
  defaultJobTimeoutMs: 60000,
  defaultMaxRetries: 3,
  defaultRetryDelayMs: 1000,
  checkIntervalMs: 100,
  dependencyTimeoutMs: 300000,
  resourceCheckIntervalMs: 1000,
  enablePriorityScheduling: true,
  enableDependencyResolution: true,
  enableResourceAwareScheduling: true,
}

// ============================================================================
// Event Bus Types
// ============================================================================

export enum EventType {
  // Agent events
  AGENT_REGISTERED = 'agent.registered',
  AGENT_INITIALIZED = 'agent.initialized',
  AGENT_STARTED = 'agent.started',
  AGENT_PAUSED = 'agent.paused',
  AGENT_RESUMED = 'agent.resumed',
  AGENT_COMPLETED = 'agent.completed',
  AGENT_CANCELLED = 'agent.cancelled',
  AGENT_ERROR = 'agent.error',
  AGENT_SHUTDOWN = 'agent.shutdown',
  AGENT_DEREGISTERED = 'agent.deregistered',
  AGENT_HEARTBEAT = 'agent.heartbeat',

  // Task events
  TASK_CREATED = 'task.created',
  TASK_STARTED = 'task.started',
  TASK_COMPLETED = 'task.completed',
  TASK_FAILED = 'task.failed',
  TASK_CANCELLED = 'task.cancelled',

  // Workflow events
  WORKFLOW_STARTED = 'workflow.started',
  WORKFLOW_COMPLETED = 'workflow.completed',
  WORKFLOW_FAILED = 'workflow.failed',
  WORKFLOW_STEP_COMPLETED = 'workflow.step.completed',

  // Plugin events
  PLUGIN_INSTALLED = 'plugin.installed',
  PLUGIN_UNINSTALLED = 'plugin.uninstalled',
  PLUGIN_LOADED = 'plugin.loaded',
  PLUGIN_UNLOADED = 'plugin.unloaded',
  PLUGIN_ERROR = 'plugin.error',

  // System events
  SYSTEM_STARTUP = 'system.startup',
  SYSTEM_SHUTDOWN = 'system.shutdown',
  SYSTEM_ERROR = 'system.error',
  SYSTEM_METRIC = 'system.metric',

  // Scheduler events
  JOB_QUEUED = 'job.queued',
  JOB_STARTED = 'job.started',
  JOB_COMPLETED = 'job.completed',
  JOB_FAILED = 'job.failed',
  JOB_CANCELLED = 'job.cancelled',
  JOB_PAUSED = 'job.paused',
  JOB_RESUMED = 'job.resumed',
  JOB_RETRYING = 'job.retrying',

  // Custom events
  CUSTOM = 'custom',
}

export interface EventMetadata {
  source: string
  version: number
  correlationId?: string
  causationId?: string
  userId?: string
  sessionId?: string
  traceId?: string
  spanId?: string
}

export interface Event<TPayload = unknown> {
  id: string
  type: EventType
  payload: TPayload
  metadata: EventMetadata
  timestamp: number
}

export interface TypedEvent<TPayload, TType extends EventType = EventType> {
  type: TType
  payload: TPayload
}

export interface VersionedEvent<TPayload> extends Event<TPayload> {
  metadata: EventMetadata & {
    version: number
    schemaVersion: number
  }
}

export interface EventFilter {
  types?: EventType[]
  source?: string
  fromTimestamp?: number
  toTimestamp?: number
  correlationId?: string
  metadata?: Record<string, unknown>
}

export interface EventSubscription {
  id: string
  eventType: EventType | '*'
  handler: EventHandler
  filter?: EventFilter
  priority: number
  once: boolean
  active: boolean
  createdAt: number
}

export type EventHandler<TPayload = unknown> = (event: Event<TPayload>) => void | Promise<void>

export interface EventBusConfig {
  maxSubscribers: number
  maxEventsPerSecond: number
  enablePersistence: boolean
  enableTracing: boolean
  enableReplay: boolean
  enableVersioning: boolean
  defaultEventVersion: number
  eventTTL: number
  enableDeadLetterQueue: boolean
  deadLetterMaxSize: number
}

export interface EventBusStats {
  totalPublished: number
  totalDelivered: number
  totalFailed: number
  totalRetried: number
  activeSubscriptions: number
  eventsPerSecond: number
  averageDeliveryTimeMs: number
  deadLetterCount: number
  uptimeMs: number
}

export interface EventStoreConfig {
  maxSize: number
  enablePersistence: boolean
  persistencePath: string
  enableCompression: boolean
  enableEncryption: boolean
  encryptionKey?: string
}

export interface EventStoreEntry {
  event: Event
  storedAt: number
  accessedAt: number
  accessCount: number
}

export interface EventTracerConfig {
  enabled: boolean
  sampleRate: number
  maxTraceSize: number
  includePayload: boolean
  includeMetadata: boolean
}

export interface EventTrace {
  eventId: string
  eventType: EventType
  timestamp: number
  source: string
  correlationId?: string
  causationId?: string
  parentTraceId?: string
  traceId: string
  spanId: string
  duration?: number
  status: 'pending' | 'success' | 'error'
  error?: string
  metadata: Record<string, unknown>
}

export interface EventMonitorConfig {
  enabled: boolean
  metricsInterval: number
  enableAlerts: boolean
  alertThresholds: {
    eventsPerSecond: number
    deliveryTimeMs: number
    errorRate: number
    deadLetterCount: number
  }
}

export interface EventMonitorMetrics {
  timestamp: number
  eventsPerSecond: number
  averageDeliveryTimeMs: number
  errorRate: number
  deadLetterCount: number
  activeSubscriptions: number
  memoryUsageMb: number
}

export interface EventMonitorAlert {
  id: string
  type: 'warning' | 'critical'
  metric: string
  value: number
  threshold: number
  message: string
  timestamp: number
}

export const DEFAULT_EVENT_BUS_CONFIG: EventBusConfig = {
  maxSubscribers: 1000,
  maxEventsPerSecond: 10000,
  enablePersistence: true,
  enableTracing: true,
  enableReplay: true,
  enableVersioning: true,
  defaultEventVersion: 1,
  eventTTL: 86400000,
  enableDeadLetterQueue: true,
  deadLetterMaxSize: 1000,
}

export const DEFAULT_EVENT_STORE_CONFIG: EventStoreConfig = {
  maxSize: 100000,
  enablePersistence: true,
  persistencePath: './events',
  enableCompression: false,
  enableEncryption: false,
}

export const DEFAULT_EVENT_TRACER_CONFIG: EventTracerConfig = {
  enabled: true,
  sampleRate: 1.0,
  maxTraceSize: 10000,
  includePayload: true,
  includeMetadata: true,
}

export const DEFAULT_EVENT_MONITOR_CONFIG: EventMonitorConfig = {
  enabled: true,
  metricsInterval: 5000,
  enableAlerts: true,
  alertThresholds: {
    eventsPerSecond: 5000,
    deliveryTimeMs: 100,
    errorRate: 0.01,
    deadLetterCount: 100,
  },
}