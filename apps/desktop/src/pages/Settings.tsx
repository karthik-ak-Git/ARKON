import { useState, useEffect } from 'react'
import {
  useAIProviders,
  useRegisterAIProvider,
  useEnableAIProvider,
  useDisableAIProvider,
  useDeleteAIProvider,
  useSetAIRoutingPolicy,
  useDetectLocalProviders,
  useAIRouting,
  useHealth,
} from '@/api/hooks'
import { Settings as SettingsIcon, Plus, Trash2, Check, X, Loader2, Wifi, WifiOff } from 'lucide-react'

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google', label: 'Google AI' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'lmstudio', label: 'LM Studio (Local)' },
]

const ROUTING_POLICIES = [
  { value: 'local_first', label: 'Local First', description: 'Prefer local providers, fallback to remote' },
  { value: 'remote_first', label: 'Remote First', description: 'Prefer cloud providers' },
  { value: 'cost_optimized', label: 'Cost Optimized', description: 'Choose cheapest provider' },
  { value: 'latency_optimized', label: 'Latency Optimized', description: 'Choose fastest provider' },
  { value: 'round_robin', label: 'Round Robin', description: 'Distribute across providers' },
  { value: 'manual', label: 'Manual', description: 'Use a specific provider only' },
]

export function Settings() {
  const { data: providersData, isLoading: providersLoading } = useAIProviders()
  const { data: routing } = useAIRouting()
  const { data: health, isError: healthError } = useHealth()
  const registerProvider = useRegisterAIProvider()
  const enableProvider = useEnableAIProvider()
  const disableProvider = useDisableAIProvider()
  const deleteProvider = useDeleteAIProvider()
  const setRoutingPolicy = useSetAIRoutingPolicy()
  const detectLocal = useDetectLocalProviders()

  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [newProvider, setNewProvider] = useState({
    provider_id: '',
    provider_type: 'openai',
    display_name: '',
    api_key: '',
    base_url: '',
    default_model: '',
  })

  const providers = providersData?.providers || []
  const currentPolicy = routing?.policy || 'local_first'

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [success])

  useEffect(() => {
    if (registerProvider.isError) setError(registerProvider.error?.message || 'Failed to add provider')
    if (enableProvider.isError) setError(enableProvider.error?.message || 'Failed to enable provider')
    if (disableProvider.isError) setError(disableProvider.error?.message || 'Failed to disable provider')
    if (deleteProvider.isError) setError(deleteProvider.error?.message || 'Failed to delete provider')
    if (setRoutingPolicy.isError) setError(setRoutingPolicy.error?.message || 'Failed to update routing')
  }, [registerProvider.isError, enableProvider.isError, disableProvider.isError, deleteProvider.isError, setRoutingPolicy.isError])

  const handleAddProvider = async () => {
    if (!newProvider.provider_id || !newProvider.provider_type) {
      setError('Provider ID and type are required')
      return
    }
    try {
      await registerProvider.mutateAsync({
        provider_id: newProvider.provider_id,
        provider_type: newProvider.provider_type,
        display_name: newProvider.display_name || newProvider.provider_id,
        api_key: newProvider.api_key || undefined,
        base_url: newProvider.base_url || undefined,
        default_model: newProvider.default_model || undefined,
        enabled: true,
      })
      setSuccess(`Provider "${newProvider.provider_id}" added`)
      setIsAdding(false)
      setNewProvider({ provider_id: '', provider_type: 'openai', display_name: '', api_key: '', base_url: '', default_model: '' })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleToggleProvider = async (providerId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await enableProvider.mutateAsync(providerId)
      } else {
        await disableProvider.mutateAsync(providerId)
      }
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleDeleteProvider = async (providerId: string) => {
    if (!confirm(`Delete provider "${providerId}"?`)) return
    try {
      await deleteProvider.mutateAsync(providerId)
      setSuccess(`Provider "${providerId}" deleted`)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handlePolicyChange = async (policy: string) => {
    try {
      await setRoutingPolicy.mutateAsync({ policy })
      setSuccess('Routing policy updated')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleDetectLocal = async () => {
    try {
      const result: { detected: string[] } = await detectLocal.mutateAsync()
      if (result.detected.length > 0) {
        setSuccess(`Detected: ${result.detected.join(', ')}`)
      } else {
        setSuccess('No local providers detected')
      }
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Configure AI providers and routing</p>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md border ${
              healthError
                ? 'border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
                : 'border-green-200 dark:border-green-800 text-green-600 dark:text-green-400'
            }`}
          >
            {healthError ? <WifiOff className="h-3 w-3" /> : <Wifi className="h-3 w-3" />}
            {healthError ? 'Offline' : `v${health?.version || '?'}`}
          </div>
          <button
            onClick={handleDetectLocal}
            disabled={detectLocal.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border hover:bg-accent transition-colors disabled:opacity-50"
          >
            {detectLocal.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <SettingsIcon className="h-3.5 w-3.5" />}
            Detect Local
          </button>
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
          <X className="h-4 w-4 shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
      {success && (
        <div className="px-4 py-3 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 text-sm flex items-center gap-2">
          <Check className="h-4 w-4" />
          {success}
        </div>
      )}

      <section>
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-3">Routing Policy</h3>
        <div className="grid grid-cols-3 gap-2">
          {ROUTING_POLICIES.map((p) => (
            <button
              key={p.value}
              onClick={() => handlePolicyChange(p.value)}
              disabled={setRoutingPolicy.isPending}
              className={`p-3 rounded-lg border text-left transition-all ${
                currentPolicy === p.value
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border hover:border-border/80'
              }`}
            >
              <p className="text-sm font-medium">{p.label}</p>
              <p className={`text-xs mt-0.5 ${currentPolicy === p.value ? 'opacity-70' : 'text-muted-foreground'}`}>
                {p.description}
              </p>
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">AI Providers</h3>
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Provider
          </button>
        </div>

        {isAdding && (
          <div className="mb-4 p-4 rounded-lg border bg-card">
            <div className="grid grid-cols-2 gap-3">
              <input
                placeholder="Provider ID (e.g., my-openai)"
                value={newProvider.provider_id}
                onChange={(e) => setNewProvider({ ...newProvider, provider_id: e.target.value })}
                className="px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-ring"
              />
              <select
                value={newProvider.provider_type}
                onChange={(e) => setNewProvider({ ...newProvider, provider_type: e.target.value })}
                className="px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-ring"
              >
                {PROVIDER_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
              <input
                placeholder="Display name"
                value={newProvider.display_name}
                onChange={(e) => setNewProvider({ ...newProvider, display_name: e.target.value })}
                className="px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-ring"
              />
              <input
                placeholder="API Key"
                type="password"
                value={newProvider.api_key}
                onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                className="px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-ring"
              />
              <input
                placeholder="Base URL (optional)"
                value={newProvider.base_url}
                onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })}
                className="px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-ring"
              />
              <input
                placeholder="Default model"
                value={newProvider.default_model}
                onChange={(e) => setNewProvider({ ...newProvider, default_model: e.target.value })}
                className="px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={() => setIsAdding(false)}
                className="px-3 py-1.5 text-sm rounded-md border hover:bg-accent transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddProvider}
                disabled={registerProvider.isPending}
                className="px-3 py-1.5 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {registerProvider.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin inline" /> : 'Add Provider'}
              </button>
            </div>
          </div>
        )}

        {providersLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : providers.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <SettingsIcon className="h-8 w-8 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No providers configured</p>
            <p className="text-xs mt-1">Add a provider to enable AI chat</p>
          </div>
        ) : (
          <div className="space-y-2">
            {providers.map((p) => (
              <div key={p.provider_id} className="flex items-center justify-between p-4 rounded-lg border bg-card">
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${p.enabled ? 'bg-green-500' : 'bg-muted-foreground/50'}`} />
                  <div>
                    <p className="text-sm font-medium">{p.display_name || p.provider_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {p.provider_type} {p.default_model ? `• ${p.default_model}` : ''}{' '}
                      {p.has_api_key ? '• API key set' : '• No API key'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      p.enabled
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {p.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <button
                    onClick={() => handleToggleProvider(p.provider_id, !p.enabled)}
                    disabled={enableProvider.isPending || disableProvider.isPending}
                    className="px-2 py-1 text-xs rounded-md border hover:bg-accent transition-colors disabled:opacity-50"
                  >
                    {p.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDeleteProvider(p.provider_id)}
                    disabled={deleteProvider.isPending}
                    className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
