import { apiGet, apiPost, apiPut, apiDelete, API_BASE } from './client';
import type { OnboardingStatus, OnboardingData } from './types';

function onboardingGet<T>(path: string): Promise<T> {
  return apiGet<T>(path, API_BASE);
}

function onboardingPost<T>(path: string, body?: unknown): Promise<T> {
  return apiPost<T>(path, body, API_BASE);
}

function onboardingPut<T>(path: string, body?: unknown): Promise<T> {
  return apiPut<T>(path, body, API_BASE);
}

function onboardingDelete<T>(path: string): Promise<T> {
  return apiDelete<T>(path, API_BASE);
}

export const onboardingApi = {
  getStatus(): Promise<OnboardingStatus> {
    return onboardingGet<OnboardingStatus>('/onboarding/status');
  },

  complete(data?: OnboardingData): Promise<OnboardingStatus> {
    return onboardingPost<OnboardingStatus>('/onboarding/complete', data ? { data } : undefined);
  },

  updateStep(step: number, data?: OnboardingData): Promise<OnboardingStatus> {
    return onboardingPut<OnboardingStatus>(`/onboarding/step/${step}`, data);
  },

  reset(): Promise<OnboardingStatus> {
    return onboardingDelete<OnboardingStatus>('/onboarding/reset');
  },
};
