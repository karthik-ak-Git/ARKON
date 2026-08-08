/**
 * Step 2: Providers
 * Configure at least one AI provider (OpenAI, Anthropic, Ollama, etc.)
 */

import { useState } from 'react';
import type { OnboardingData } from '../../../api/types';
import type { UseMutationResult } from '@tanstack/react-query';

interface StepProvidersProps {
  data: OnboardingData;
  onUpdate: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
  registerProvider: UseMutationResult<unknown, unknown, {
    provider_id: string;
    provider_type: string;
    display_name?: string;
    api_key?: string;
    enabled?: boolean;
  }>;
}

const PRESETS = [
  { id: 'openai', type: 'cloud', name: 'OpenAI', placeholder: 'sk-...' },
  { id: 'anthropic', type: 'cloud', name: 'Anthropic', placeholder: 'sk-ant-...' },
  { id: 'ollama', type: 'local', name: 'Ollama (Local)', placeholder: '' },
  { id: 'lmstudio', type: 'local', name: 'LM Studio (Local)', placeholder: '' },
  { id: 'groq', type: 'cloud', name: 'Groq', placeholder: 'gsk_...' },
  { id: 'together', type: 'cloud', name: 'Together AI', placeholder: '' },
];

export function StepProviders({ data, onUpdate, onNext, onBack, registerProvider }: StepProvidersProps) {
  const [selected, setSelected] = useState<string>(data.providers_configured[0] ?? '');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const selectedPreset = PRESETS.find(p => p.id === selected);
  const isLocal = selectedPreset?.type === 'local';

  const handleAdd = async () => {
    if (!selected) {
      setError('Select a provider');
      return;
    }
    if (!isLocal && !apiKey.trim()) {
      setError('API key is required for cloud providers');
      return;
    }

    setError('');
    try {
      await registerProvider.mutateAsync({
        provider_id: selected,
        provider_type: isLocal ? 'local' : 'cloud',
        display_name: selectedPreset?.name,
        api_key: isLocal ? undefined : apiKey.trim(),
        enabled: true,
      });
      setSuccess(true);
      onUpdate({ providers_configured: [...new Set([...data.providers_configured, selected])] });
    } catch {
      setError('Failed to register provider');
    }
  };

  return (
    <div>
      <h2 className="text-lg font-light text-white mb-1">Add an AI Provider</h2>
      <p className="text-sm text-white/40 mb-6">Connect at least one provider to power your agents.</p>

      <div className="space-y-4">
        {/* Provider grid */}
        <div className="grid grid-cols-2 gap-2">
          {PRESETS.map(preset => (
            <button
              key={preset.id}
              onClick={() => { setSelected(preset.id); setError(''); setSuccess(false); }}
              className={`px-3 py-2.5 rounded-lg text-left text-sm transition-colors ${
                selected === preset.id
                  ? 'bg-white/10 border border-white/20 text-white'
                  : 'bg-white/5 border border-white/5 text-white/50 hover:bg-white/8 hover:text-white/70'
              }`}
            >
              <span className="block font-medium">{preset.name}</span>
              <span className="block text-xs text-white/30 mt-0.5">{preset.type === 'local' ? 'No API key' : 'Cloud'}</span>
            </button>
          ))}
        </div>

        {/* API key input */}
        {selected && !isLocal && (
          <div>
            <label className="block text-xs text-white/30 uppercase tracking-wider mb-1.5">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => { setApiKey(e.target.value); setError(''); }}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-white/20 transition-colors"
              placeholder={selectedPreset?.placeholder}
              autoFocus
            />
          </div>
        )}

        {selected && isLocal && (
          <div className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg">
            <p className="text-xs text-white/40">
              Ollama runs locally. Make sure it's running on <span className="text-white/60">localhost:11434</span> before continuing.
            </p>
          </div>
        )}

        {error && <p className="text-xs text-red-400">{error}</p>}
        {success && <p className="text-xs text-green-400">Provider registered</p>}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button onClick={onBack} className="px-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors">
          Back
        </button>
        <div className="flex items-center gap-3">
          <button
            onClick={onNext}
            className="px-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors"
          >
            Skip
          </button>
          <button
            onClick={handleAdd}
            disabled={registerProvider.isPending || !selected}
            className="px-5 py-2 bg-white text-[#1a1a1a] text-sm font-medium rounded-lg hover:bg-white/90 transition-colors disabled:opacity-50"
          >
            {registerProvider.isPending ? 'Adding...' : 'Add & Continue'}
          </button>
        </div>
      </div>
    </div>
  );
}
