/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { ClaudeLayout } from './components/layout/ClaudeLayout';
import { ConnectionManager } from './components/system/ConnectionManager';
import { WebSocketProvider } from './api/WebSocketProvider';
import { OnboardingWizard } from './components/onboarding/OnboardingWizard';
import { useOnboardingStatus } from './api/hooks/useOnboarding';
import { useConnection } from './components/system/ConnectionManager';

function AppContent() {
  const { isOnline } = useConnection();
  const { data: onboarding, isLoading } = useOnboardingStatus();

  // Backend not yet connected — ConnectionManager handles splash/error
  if (!isOnline) {
    return <ClaudeLayout />;
  }

  // Loading onboarding status — show minimal splash
  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1a1a1a]">
        <div className="h-6 w-6 animate-spin rounded-full border border-white/20 border-t-white" />
      </div>
    );
  }

  // Onboarding not complete — show wizard
  if (onboarding && !onboarding.completed) {
    return <OnboardingWizard onComplete={() => window.location.reload()} />;
  }

  // Normal app
  return (
    <WebSocketProvider>
      <ClaudeLayout />
    </WebSocketProvider>
  );
}

export default function App() {
  return (
    <ConnectionManager>
      <AppContent />
    </ConnectionManager>
  );
}
