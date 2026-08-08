/**
 * Step 4: Thinking Profile
 * Select reasoning depth for the AI agents.
 */

import type { OnboardingData } from '../../../api/types';

interface StepThinkingProps {
  data: OnboardingData;
  onUpdate: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
}

const PROFILES = [
  {
    id: 'fast',
    name: 'Fast',
    description: 'Quick responses, minimal reasoning. Best for simple tasks.',
    detail: 'Lower latency, less token usage',
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Good balance of speed and reasoning depth.',
    detail: 'Recommended for most users',
  },
  {
    id: 'deep',
    name: 'Deep',
    description: 'Thorough reasoning. Best for complex problems.',
    detail: 'Higher latency, more token usage',
  },
];

export function StepThinking({ data, onUpdate, onNext, onBack }: StepThinkingProps) {
  const selected = data.thinking_profile;

  const handleSelect = (profileId: string) => {
    onUpdate({ thinking_profile: profileId });
    onNext();
  };

  return (
    <div>
      <h2 className="text-lg font-light text-white mb-1">Thinking Profile</h2>
      <p className="text-sm text-white/40 mb-6">Set the reasoning depth for your AI agents.</p>

      <div className="space-y-2">
        {PROFILES.map(profile => (
          <button
            key={profile.id}
            onClick={() => handleSelect(profile.id)}
            className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
              selected === profile.id
                ? 'bg-white/10 border border-white/20'
                : 'bg-white/5 border border-white/5 hover:bg-white/8'
            }`}
          >
            <span className="block text-sm text-white font-medium">{profile.name}</span>
            <span className="block text-xs text-white/30 mt-0.5">{profile.description}</span>
            <span className="block text-xs text-white/20 mt-1">{profile.detail}</span>
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button onClick={onBack} className="px-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors">
          Back
        </button>
        <button
          onClick={() => handleSelect(selected)}
          className="px-5 py-2 bg-white text-[#1a1a1a] text-sm font-medium rounded-lg hover:bg-white/90 transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
