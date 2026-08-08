import { useState, useEffect, useCallback, useRef } from 'react';
import { useOnboardingStatus } from './useOnboarding';
import { workspacesApi } from '../workspaces';
import { aiApi } from '../index';
import type { OnboardingData } from '../types';

export interface UserSession {
  userId: string;
  email?: string;
  name?: string;
  workspaceId?: string;
  providers: string[];
  isValid: boolean;
}

const SESSION_KEY = 'arkon_user_session';

function getSessionKey(): string {
  return SESSION_KEY;
}

export function saveUserSession(session: Omit<UserSession, 'isValid'>): void {
  try {
    localStorage.setItem(getSessionKey(), JSON.stringify(session));
  } catch {
    // Ignore localStorage errors
  }
}

export function loadUserSession(): Omit<UserSession, 'isValid'> | null {
  try {
    const raw = localStorage.getItem(getSessionKey());
    if (raw) {
      return JSON.parse(raw) as Omit<UserSession, 'isValid'>;
    }
  } catch {
    // Ignore localStorage errors
  }
  return null;
}

export function clearUserSession(): void {
  try {
    localStorage.removeItem(getSessionKey());
  } catch {
    // Ignore localStorage errors
  }
}

export function useUserSession() {
  const { data: onboarding, isLoading: onboardingLoading } = useOnboardingStatus();
  const [session, setSession] = useState<UserSession | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  
  // Refs to prevent validation loops
  const validationInProgress = useRef(false);
  const lastValidatedOnboarding = useRef<string | null>(null);

  // Initialize session from localStorage on mount (once)
  useEffect(() => {
    const saved = loadUserSession();
    if (saved) {
      setSession({ ...saved, isValid: false });
    }
  }, []);

  // Validate session against backend when onboarding loads
  const validateSession = useCallback(async () => {
    // Prevent concurrent validations
    if (validationInProgress.current) return;
    
    // Create a stable key for the current onboarding state
    const onboardingKey = onboarding ? `${onboarding.completed}:${onboarding.current_step}:${JSON.stringify(onboarding.data)}` : 'none';
    if (lastValidatedOnboarding.current === onboardingKey) return;
    
    if (!onboarding?.completed || !onboarding.data) {
      setSession(prev => prev ? { ...prev, isValid: false } : null);
      return;
    }

    validationInProgress.current = true;
    lastValidatedOnboarding.current = onboardingKey;
    setIsValidating(true);

    try {
      const saved = loadUserSession();
      if (!saved) {
        // No saved session, but onboarding is complete - create one
        const newSession: Omit<UserSession, 'isValid'> = {
          userId: onboarding.data.user_id || `user_${Date.now()}`,
          email: onboarding.data.user_email ?? undefined,
          name: onboarding.data.user_name ?? undefined,
          workspaceId: onboarding.data.workspace_name ?? undefined,
          providers: onboarding.data.providers_configured || [],
        };
        saveUserSession(newSession);
        setSession({ ...newSession, isValid: true });
        return;
      }

      // Validate saved session against current onboarding state
      // Verify workspace exists
      let workspaceValid = false;
      if (saved.workspaceId) {
        try {
          const ws = await workspacesApi.get(saved.workspaceId);
          workspaceValid = !!ws;
        } catch {
          workspaceValid = false;
        }
      }

      // Verify at least one provider is still registered
      let providersValid = false;
      if (saved.providers.length > 0) {
        try {
          const { providers } = await aiApi.listProviders();
          const registeredIds = providers.map(p => p.provider_id);
          providersValid = saved.providers.some(p => registeredIds.includes(p));
        } catch {
          providersValid = false;
        }
      }

      const isValid = (workspaceValid || !saved.workspaceId) && (providersValid || saved.providers.length === 0);
      
      setSession({
        ...saved,
        workspaceId: workspaceValid ? saved.workspaceId : undefined,
        providers: saved.providers,
        isValid,
      });
    } catch {
      setSession(prev => prev ? { ...prev, isValid: false } : null);
    } finally {
      setIsValidating(false);
      validationInProgress.current = false;
    }
  }, [onboarding]);

  // Single validation effect - no duplicate in useAutoLogin
  useEffect(() => {
    if (!onboardingLoading) {
      validateSession();
    }
  }, [onboarding, onboardingLoading, validateSession]);

  // Update session when onboarding completes
  const updateSession = useCallback((data: Partial<OnboardingData>) => {
    setSession(prev => {
      if (!prev) return null;
      const updated: Omit<UserSession, 'isValid'> = {
        userId: data.user_id ?? prev.userId,
        email: data.user_email ?? prev.email,
        name: data.user_name ?? prev.name,
        workspaceId: data.workspace_name ?? prev.workspaceId,
        providers: data.providers_configured ?? prev.providers,
      };
      // Convert null to undefined for optional string fields
      const sanitized = {
        ...updated,
        email: updated.email ?? undefined,
        name: updated.name ?? undefined,
        workspaceId: updated.workspaceId ?? undefined,
      };
      saveUserSession(sanitized);
      return { ...sanitized, isValid: prev.isValid };
    });
  }, []);

  const login = useCallback((userData: Omit<UserSession, 'isValid'>) => {
    saveUserSession(userData);
    setSession({ ...userData, isValid: true });
  }, []);

  const logout = useCallback(() => {
    clearUserSession();
    setSession(null);
  }, []);

  return {
    session,
    isLoading: onboardingLoading || isValidating,
    isLoggedIn: session?.isValid === true,
    validateSession,
    updateSession,
    login,
    logout,
  };
}

export function useAutoLogin() {
  const { session, isLoading, isLoggedIn, login } = useUserSession();

  // Auto-login: just expose the state, don't trigger validation
  // useUserSession handles validation internally
  
  return { session, isLoading, isLoggedIn, login };
}