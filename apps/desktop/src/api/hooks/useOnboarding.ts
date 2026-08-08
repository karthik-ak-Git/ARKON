import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { onboardingApi } from '../onboarding';
import type { OnboardingData } from '../types';

export function useOnboardingStatus() {
  return useQuery({
    queryKey: ['onboarding', 'status'],
    queryFn: () => onboardingApi.getStatus(),
    staleTime: Infinity,
    retry: false,
  });
}

export function useCompleteOnboarding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data?: OnboardingData) => onboardingApi.complete(data),
    onSuccess: (_result, variables) => {
      qc.setQueryData(['onboarding', 'status'], {
        completed: true,
        current_step: 7,
        data: variables ?? {},
      });
    },
  });
}

export function useUpdateOnboardingStep() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ step, data }: { step: number; data?: OnboardingData }) =>
      onboardingApi.updateStep(step, data),
    onSuccess: (status) => {
      qc.setQueryData(['onboarding', 'status'], status);
    },
  });
}

export function useResetOnboarding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => onboardingApi.reset(),
    onSuccess: (status) => {
      qc.setQueryData(['onboarding', 'status'], status);
    },
  });
}
