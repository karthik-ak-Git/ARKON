/**
 * Step 3: Routing
 * Smart routing policy selection.
 */

import type { OnboardingData } from '../../../api/types';
import type { UseMutationResult } from '@tanstack/react-query';

interface StepRoutingProps {
  data: OnboardingData;
  onUpdate: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
  setRouting: UseMutationResult<unknown, unknown, { policy: string; manual_provider_id?: string }>;
}

const POLICIES = [
  {
    id: 'local_first',
    name: 'Local First',
    description: 'Use local models (Ollama, LM Studio) when available, fall back to cloud.',
    icon: '🏠',
  },
  {
    id: 'cloud_first',
    name: 'Cloud First',
    description: 'Prefer cloud providers (OpenAI, Anthropic) for best quality.',
    icon: '☁️',
  },
  {
    id: 'cheapest',
    name: 'Cheapest',
    description: 'Route to the most cost-effective provider for each request.',
    icon: '💰',
  },
  {
    id: 'fastest',
    name: 'Fastest',
    description: 'Route to the provider with lowest latency.',
    icon: '⚡',
  },
  {
    id: 'manual',
    name: 'Manual',
    description: 'Always use a specific provider you choose.',
    icon: '🎯',
  },
];

export function StepRouting({ data, onUpdate, onNext, onBack, setRouting }: StepRoutingProps) {
  const selected = data.routing_policy;

  const handleSelect = async (policyId: string) => {
    onUpdate({ routing_policy: policyId });
    try {
      await setRouting.mutateAsync({ policy: policyId });
    } catch {
      // Continue even if API call fails — routing is in-memory
    }
    onNext();
  };

  return (
    <div>
      <h2 className="text-lg font-light text-white mb-1">Smart Routing</h2>
      <p className="text-sm text-white/40 mb-6">Choose how requests are routed to your providers.</p>

      <div className="space-y-2">
        {POLICIES.map(policy => (
          <button
            key={policy.id}
            onClick={() => handleSelect(policy.id)}
            className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
              selected === policy.id
                ? 'bg-white/10 border border-white/20'
                : 'bg-white/5 border border-white/5 hover:bg-white/8'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">{policy.icon}</span>
              <div>
                <span className="block text-sm text-white font-medium">{policy.name}</span>
                <span className="block text-xs text-white/30 mt-0.5">{policy.description}</span>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button onClick={onBack} className="px-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors">
          Back
        </button>
        <button
          onClick={() => handleSelect(selected)}
          disabled={setRouting.isPending}
          className="px-5 py-2 bg-white text-[#1a1a1a] text-sm font-medium rounded-lg hover:bg-white/90 transition-colors disabled:opacity-50"
        >
          {setRouting.isPending ? 'Saving...' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
