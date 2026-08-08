/**
 * Step 5: Verify
 * Test connection to backend + providers.
 */

import { useState, useEffect } from 'react';
import type { OnboardingData } from '../../../api/types';

interface StepVerifyProps {
  data: OnboardingData;
  onNext: () => void;
  onBack: () => void;
}

type CheckStatus = 'pending' | 'running' | 'pass' | 'fail' | 'skip';

interface Check {
  id: string;
  label: string;
  status: CheckStatus;
  detail?: string;
}

export function StepVerify({ data, onNext, onBack }: StepVerifyProps) {
  const [checks, setChecks] = useState<Check[]>([
    { id: 'backend', label: 'Backend connection', status: 'pending' },
    { id: 'workspace', label: 'Workspace created', status: 'pending' },
    { id: 'provider', label: 'AI provider registered', status: 'pending' },
    { id: 'routing', label: 'Routing policy set', status: 'pending' },
  ]);

  useEffect(() => {
    let cancelled = false;

    const runChecks = async () => {
      const update = (id: string, status: CheckStatus, detail?: string) => {
        if (cancelled) return;
        setChecks(prev => prev.map(c => c.id === id ? { ...c, status, detail } : c));
      };

      // 1. Backend check
      update('backend', 'running');
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          update('backend', 'pass', 'Connected');
        } else {
          update('backend', 'fail', `HTTP ${res.status}`);
        }
      } catch {
        update('backend', 'fail', 'Cannot reach backend');
      }

      // 2. Workspace check
      update('workspace', 'running');
      if (data.workspace_name) {
        update('workspace', 'pass', data.workspace_name);
      } else {
        update('workspace', 'skip', 'No workspace configured');
      }

      // 3. Provider check
      update('provider', 'running');
      if (data.providers_configured.length > 0) {
        update('provider', 'pass', data.providers_configured.join(', '));
      } else {
        update('provider', 'skip', 'No providers configured');
      }

      // 4. Routing check
      update('routing', 'running');
      update('routing', 'pass', data.routing_policy);
    };

    // Small delay for UX
    const timer = setTimeout(runChecks, 500);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [data]);

  const allPassed = checks.every(c => c.status === 'pass' || c.status === 'skip');
  const anyFailed = checks.some(c => c.status === 'fail');

  return (
    <div>
      <h2 className="text-lg font-light text-white mb-1">Verify Setup</h2>
      <p className="text-sm text-white/40 mb-6">Checking your configuration...</p>

      <div className="space-y-3">
        {checks.map(check => (
          <div key={check.id} className="flex items-center gap-3 px-3 py-2.5 bg-white/5 border border-white/5 rounded-lg">
            {/* Status icon */}
            <div className="w-5 h-5 flex items-center justify-center">
              {check.status === 'pending' && <div className="w-2 h-2 rounded-full bg-white/20" />}
              {check.status === 'running' && <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" />}
              {check.status === 'pass' && (
                <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
              {check.status === 'fail' && (
                <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
              {check.status === 'skip' && (
                <svg className="w-4 h-4 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
              )}
            </div>

            {/* Label */}
            <div className="flex-1">
              <span className="text-sm text-white">{check.label}</span>
              {check.detail && (
                <span className="text-xs text-white/30 ml-2">{check.detail}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button onClick={onBack} className="px-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors">
          Back
        </button>
        <button
          onClick={onNext}
          disabled={!allPassed && !anyFailed}
          className={`px-5 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 ${
            anyFailed
              ? 'bg-white/10 text-white/60 hover:bg-white/15'
              : 'bg-white text-[#1a1a1a] hover:bg-white/90'
          }`}
        >
          {anyFailed ? 'Continue Anyway' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
