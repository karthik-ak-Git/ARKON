/**
 * All ARKON backend types. Single source of truth.
 * Mirror of backend/app/schemas/schemas.py
 */

// =============================================================================
// Health
// =============================================================================

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

// =============================================================================
// Workspaces
// =============================================================================

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  state: string;
  path: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceList {
  active: Workspace[];
  available: Workspace[];
}

export interface CreateWorkspace {
  id: string;
  name: string;
  description?: string;
  path?: string;
  tags?: string[];
}

export interface UpdateWorkspace {
  name?: string;
  description?: string;
  tags?: string[];
}

export interface WorkspaceSnapshot {
  id: string;
  name: string;
  workspace_id: string;
  created_at: number;
  status: string;
}

// =============================================================================
// Projects
// =============================================================================

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateProject {
  name: string;
  description?: string;
}

export interface UpdateProject {
  name?: string;
  description?: string;
  status?: string;
}

// =============================================================================
// Agents (DB)
// =============================================================================

export interface Agent {
  id: string;
  workspace_id: string;
  name: string;
  agent_type: string;
  status: string;
  capabilities: string[] | null;
  config: Record<string, unknown> | null;
  last_heartbeat: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateAgent {
  name: string;
  agent_type?: string;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

export interface UpdateAgent {
  name?: string;
  status?: string;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

// =============================================================================
// Runtime Agents (live)
// =============================================================================

export interface RuntimeAgent {
  agent_id: string;
  agent_type: string;
  status: string;
  state: string;
  capabilities: string[];
  created_at: string;
  last_heartbeat: string | null;
}

export interface RuntimeAgentList {
  agents: RuntimeAgent[];
  count: number;
}

export interface AgentRegistryEntry {
  agent_type: string;
  class_name: string;
  capabilities: string[];
  description: string;
}

export interface AgentRegistry {
  agents: AgentRegistryEntry[];
  count: number;
}

export interface CapabilityList {
  capabilities: Record<string, string[]>;
  count: number;
}

export interface ResourceUsage {
  cpu_percent: number;
  ram_percent: number;
  ram_used_mb: number;
  ram_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  active_agents: number;
  max_agents: number;
}

// =============================================================================
// Execution
// =============================================================================

export interface ExecutionTask {
  task_id: string;
  agent_id: string | null;
  task_type: string;
  status: string;
  priority: number;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  progress: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface SubmitTaskRequest {
  task_type: string;
  agent_id?: string;
  priority?: number;
  input_data?: Record<string, unknown>;
}

export interface SubmitTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface ExecutionSummary {
  total_tasks: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
}

// =============================================================================
// AI Gateway
// =============================================================================

export interface AIProviderInfo {
  provider_id: string;
  provider_type: string;
  display_name: string;
  enabled: boolean;
  has_api_key: boolean;
  status: string;
  default_model: string;
}

export interface AIProviderCreate {
  provider_id: string;
  provider_type: string;
  display_name?: string;
  enabled?: boolean;
  api_key?: string;
  base_url?: string;
  default_model?: string;
  timeout?: number;
}

export interface AIProviderUpdate {
  api_key?: string;
  base_url?: string;
  default_model?: string;
  timeout?: number;
  enabled?: boolean;
}

export interface AIHealthResponse {
  provider_id: string;
  status: string;
  latency_ms: number;
  error: string;
}

export interface AIModelInfo {
  model_id: string;
  name: string;
  provider_id: string;
  context_window: number;
  max_output: number;
  is_free: boolean;
}

export interface AIChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AIChatRequest {
  messages: AIChatMessage[];
  model?: string;
  provider_id?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface AIChatResponse {
  content: string;
  model: string;
  provider_id: string;
  finish_reason: string;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}

export interface AIRoutingDecision {
  provider_id: string;
  model: string;
  policy: string;
  reason: string;
}

// =============================================================================
// Onboarding
// =============================================================================

export interface OnboardingData {
  workspace_name: string | null;
  workspace_description: string | null;
  providers_configured: string[];
  routing_policy: string;
  thinking_profile: string;
  // User session info
  user_id: string | null;
  user_email: string | null;
  user_name: string | null;
}

export interface OnboardingStatus {
  completed: boolean;
  current_step: number;
  data: OnboardingData;
}

// =============================================================================
// WebSocket Events
// =============================================================================

export interface WSEvent {
  type: string;
  [key: string]: unknown;
}

export interface RuntimeWSEvent extends WSEvent {
  agent_id?: string;
  event_type?: string;
  timestamp?: string;
}

export interface ExecutionWSEvent extends WSEvent {
  task_id?: string;
  status?: string;
  progress?: number;
}
