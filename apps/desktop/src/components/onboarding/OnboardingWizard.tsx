/**
 * Onboarding Wizard
 *
 * First-run experience: Welcome → Workspace → Providers → Routing → Thinking → Verify → Complete
 * Integrates with existing backend AI Gateway + Workspace APIs.
 */

import { useState, useCallback } from 'react';
import { useCreateWorkspace } from '../../api/hooks/useWorkspaces';
import { useRegisterAIProvider, useSetAIRoutingPolicy, useAIProviderHealth } from '../../api/hooks/useAI';
import { useCompleteOnboarding } from '../../api/hooks/useOnboarding';
import type { OnboardingData } from '../../api/types';
import { StepWelcome } from './steps/StepWelcome';
import { StepWorkspace } from './steps/StepWorkspace';
import { StepProviders } from './steps/StepProviders';
import { StepRouting } from './steps/StepRouting';
import { StepThinking } from './steps/StepThinking';
import { StepVerify } from './steps/StepVerify';
import { StepComplete } from './steps/StepComplete';

const TOTAL_STEPS = 7;

interface OnboardingWizardProps {
  onComplete: () => void;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    workspace_name: null,
    workspace_description: null,
    providers_configured: [],
    routing_policy: 'local_first',
    thinking_profile: 'balanced',
  });

  const createWorkspace = useCreateWorkspace();
  const registerProvider = useRegisterAIProvider();
  const providerHealth = useAIProviderHealth();
  const setRouting = useSetAIRoutingPolicy();
  const completeOnboarding = useCompleteOnboarding();

  const updateData = useCallback((partial: Partial<OnboardingData>) => {
    setData(prev => ({ ...prev, ...partial }));
  }, []);

  const goNext = useCallback(() => {
    setStep(prev => Math.min(prev + 1, TOTAL_STEPS - 1));
  }, []);

  const goBack = useCallback(() => {
    setStep(prev => Math.max(prev - 1, 0));
  }, []);

  const handleComplete = useCallback(async () => {
    await completeOnboarding.mutateAsync(data);
    onComplete();
  }, [completeOnboarding, data, onComplete]);

  const renderStep = () => {
    switch (step) {
      case 0:
        return <StepWelcome onNext={goNext} />;
      case 1:
        return (
          <StepWorkspace
            data={data}
            onUpdate={updateData}
            onNext={goNext}
            onBack={goBack}
            createWorkspace={createWorkspace}
          />
        );
      case 2:
        return (
          <StepProviders
            data={data}
            onUpdate={updateData}
            onNext={goNext}
            onBack={goBack}
            registerProvider={registerProvider}
            providerHealth={providerHealth}
          />
        );
      case 3:
        return (
          <StepRouting
            data={data}
            onUpdate={updateData}
            onNext={goNext}
            onBack={goBack}
            setRouting={setRouting}
          />
        );
      case 4:
        return (
          <StepThinking
            data={data}
            onUpdate={updateData}
            onNext={goNext}
            onBack={goBack}
          />
        );
      case 5:
        return (
          <StepVerify
            data={data}
            onNext={goNext}
            onBack={goBack}
            providerHealth={providerHealth}
          />
        );
      case 6:
        return (
          <StepComplete
            data={data}
            onComplete={handleComplete}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1a1a1a]">
      <div className="w-full max-w-lg mx-auto px-6">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/30 uppercase tracking-wider">Setup</span>
            <span className="text-xs text-white/30">{step + 1} / {TOTAL_STEPS}</span>
          </div>
          <div className="h-1 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-white/20 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${((step + 1) / TOTAL_STEPS) * 100}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        {renderStep()}
      </div>
    </div>
  );
}
