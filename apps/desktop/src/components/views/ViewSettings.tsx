import { useState, useEffect } from 'react';
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
} from '../../api/hooks';
import { Settings, Plus, Trash2, Check, X, Loader2, Server, Wifi, WifiOff } from 'lucide-react';

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google', label: 'Google AI' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'lmstudio', label: 'LM Studio (Local)' },
];

const ROUTING_POLICIES = [
  { value: 'local_first', label: 'Local First', description: 'Prefer local providers, fallback to remote' },
  { value: 'remote_first', label: 'Remote First', description: 'Prefer cloud providers' },
  { value: 'cost_optimized', label: 'Cost Optimized', description: 'Choose cheapest provider' },
  { value: 'latency_optimized', label: 'Latency Optimized', description: 'Choose fastest provider' },
  { value: 'round_robin', label: 'Round Robin', description: 'Distribute across providers' },
  { value: 'manual', label: 'Manual', description: 'Use a specific provider only' },
];

export function ViewSettings() {
  const { data: providersData, isLoading: providersLoading } = useAIProviders();
  const { data: routing } = useAIRouting();
  const { data: health, isError: healthError } = useHealth();
  const registerProvider = useRegisterAIProvider();
  const enableProvider = useEnableAIProvider();
  const disableProvider = useDisableAIProvider();
  const deleteProvider = useDeleteAIProvider();
  const setRoutingPolicy = useSetAIRoutingPolicy();
  const detectLocal = useDetectLocalProviders();

  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [newProvider, setNewProvider] = useState({
    provider_id: '',
    provider_type: 'openai',
    display_name: '',
    api_key: '',
    base_url: '',
    default_model: '',
  });

  const providers = providersData?.providers || [];
  const currentPolicy = routing?.policy || 'local_first';

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (registerProvider.isError) setError(registerProvider.error?.message || 'Failed to add provider');
    if (enableProvider.isError) setError(enableProvider.error?.message || 'Failed to enable provider');
    if (disableProvider.isError) setError(disableProvider.error?.message || 'Failed to disable provider');
    if (deleteProvider.isError) setError(deleteProvider.error?.message || 'Failed to delete provider');
    if (setRoutingPolicy.isError) setError(setRoutingPolicy.error?.message || 'Failed to update routing');
  }, [registerProvider.isError, enableProvider.isError, disableProvider.isError, deleteProvider.isError, setRoutingPolicy.isError]);

  const handleAddProvider = async () => {
    if (!newProvider.provider_id || !newProvider.provider_type) {
      setError('Provider ID and type are required');
      return;
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
      });
      setSuccess(`Provider "${newProvider.provider_id}" added`);
      setIsAdding(false);
      setNewProvider({ provider_id: '', provider_type: 'openai', display_name: '', api_key: '', base_url: '', default_model: '' });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleToggleProvider = async (providerId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await enableProvider.mutateAsync(providerId);
      } else {
        await disableProvider.mutateAsync(providerId);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleDeleteProvider = async (providerId: string) => {
    if (!confirm(`Delete provider "${providerId}"?`)) return;
    try {
      await deleteProvider.mutateAsync(providerId);
      setSuccess(`Provider "${providerId}" deleted`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handlePolicyChange = async (policy: string) => {
    try {
      await setRoutingPolicy.mutateAsync({ policy });
      setSuccess('Routing policy updated');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleDetectLocal = async () => {
    try {
      const result: { detected: string[] } = await detectLocal.mutateAsync();
      if (result.detected.length > 0) {
        setSuccess(`Detected: ${result.detected.join(', ')}`);
      } else {
        setSuccess('No local providers detected');
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Settings</h2>
        <div className="flex items-center gap-2">
          {/* Backend status */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border ${
            healthError
              ? 'border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
              : 'border-green-200 dark:border-green-800 text-green-600 dark:text-green-400'
          }`}>
            {healthError ? <WifiOff className="w-3 h-3" /> : <Wifi className="w-3 h-3" />}
            {healthError ? 'Offline' : `v${health?.version || '?'}`}
          </div>
          <button
            onClick={handleDetectLocal}
            disabled={detectLocal.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors disabled:opacity-50"
          >
            {detectLocal.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Server className="w-3.5 h-3.5" />}
            Detect Local
          </button>
        </div>
      </div>

      {/* Status messages */}
      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm flex items-center gap-2">
          <X className="w-4 h-4 shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}
      {success && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 text-sm flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          {success}
        </div>
      )}

      {/* Routing Policy */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Routing Policy</h3>
        <div className="grid grid-cols-3 gap-2">
          {ROUTING_POLICIES.map((p) => (
            <button
              key={p.value}
              onClick={() => handlePolicyChange(p.value)}
              disabled={setRoutingPolicy.isPending}
              className={`p-3 rounded-xl border text-left transition-all ${
                currentPolicy === p.value
                  ? 'border-gray-900 dark:border-white bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                  : 'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20'
              }`}
            >
              <p className="text-sm font-medium">{p.label}</p>
              <p className={`text-xs mt-0.5 ${currentPolicy === p.value ? 'opacity-70' : 'text-gray-400 dark:text-gray-500'}`}>
                {p.description}
              </p>
            </button>
          ))}
        </div>
      </section>

      {/* Providers */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">AI Providers</h3>
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:opacity-90 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Provider
          </button>
        </div>

        {/* Add Provider Form */}
        {isAdding && (
          <div className="mb-4 p-4 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.02]">
            <div className="grid grid-cols-2 gap-3">
              <input
                placeholder="Provider ID (e.g., my-openai)"
                value={newProvider.provider_id}
                onChange={(e) => setNewProvider({ ...newProvider, provider_id: e.target.value })}
                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
              />
              <select
                value={newProvider.provider_type}
                onChange={(e) => setNewProvider({ ...newProvider, provider_type: e.target.value })}
                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
              >
                {PROVIDER_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              <input
                placeholder="Display name"
                value={newProvider.display_name}
                onChange={(e) => setNewProvider({ ...newProvider, display_name: e.target.value })}
                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
              />
              <input
                placeholder="API Key"
                type="password"
                value={newProvider.api_key}
                onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
              />
              <input
                placeholder="Base URL (optional)"
                value={newProvider.base_url}
                onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })}
                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
              />
              <input
                placeholder="Default model"
                value={newProvider.default_model}
                onChange={(e) => setNewProvider({ ...newProvider, default_model: e.target.value })}
                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
              />
            </div>
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={() => setIsAdding(false)}
                className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddProvider}
                disabled={registerProvider.isPending}
                className="px-3 py-1.5 text-sm rounded-lg bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {registerProvider.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin inline" /> : 'Add Provider'}
              </button>
            </div>
          </div>
        )}

        {/* Provider List */}
        {providersLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : providers.length === 0 ? (
          <div className="text-center py-12 text-gray-400 dark:text-gray-500">
            <Settings className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No providers configured.</p>
            <p className="text-xs mt-1">Add a provider to enable AI chat.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {providers.map((p) => (
              <div
                key={p.provider_id}
                className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-white/10"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${p.enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                  <div>
                    <p className="text-sm font-medium">{p.display_name || p.provider_id}</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      {p.provider_type} {p.default_model ? `• ${p.default_model}` : ''} {p.has_api_key ? '• API key set' : '• No API key'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    p.enabled ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-white/10 dark:text-gray-400'
                  }`}>{p.enabled ? 'Enabled' : 'Disabled'}</span>
                  <button
                    onClick={() => handleToggleProvider(p.provider_id, !p.enabled)}
                    disabled={enableProvider.isPending || disableProvider.isPending}
                    className={`px-2 py-1 text-xs rounded-lg border transition-colors disabled:opacity-50 ${
                      p.enabled
                        ? 'border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
                        : 'border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
                    }`}
                  >
                    {p.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDeleteProvider(p.provider_id)}
                    disabled={deleteProvider.isPending}
                    className="p-1.5 rounded-lg border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
