/**
 * Step 6: Complete
 * Success screen. Final action.
 */

import type { OnboardingData } from '../../../api/types';

interface StepCompleteProps {
  data: OnboardingData;
  onComplete: () => void;
}

export function StepComplete({ data, onComplete }: StepCompleteProps) {
  return (
    <div className="flex flex-col items-center text-center">
      {/* Success icon */}
      <div className="w-16 h-16 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>

      <h2 className="text-lg font-light text-white mb-2">You're All Set</h2>
      <p className="text-sm text-white/40 max-w-sm leading-relaxed mb-6">
        ARKON is configured and ready. Your agents are waiting.
      </p>

      {/* Summary */}
      <div className="w-full max-w-sm space-y-2 mb-8">
        {data.workspace_name && (
          <div className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-lg">
            <span className="text-xs text-white/30">Workspace</span>
            <span className="text-xs text-white/60">{data.workspace_name}</span>
          </div>
        )}
        {data.providers_configured.length > 0 && (
          <div className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-lg">
            <span className="text-xs text-white/30">Providers</span>
            <span className="text-xs text-white/60">{data.providers_configured.join(', ')}</span>
          </div>
        )}
        <div className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-lg">
          <span className="text-xs text-white/30">Routing</span>
          <span className="text-xs text-white/60">{data.routing_policy}</span>
        </div>
        <div className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-lg">
          <span className="text-xs text-white/30">Thinking</span>
          <span className="text-xs text-white/60">{data.thinking_profile}</span>
        </div>
      </div>

      <button
        onClick={onComplete}
        className="px-6 py-2.5 bg-white text-[#1a1a1a] text-sm font-medium rounded-lg hover:bg-white/90 transition-colors"
      >
        Open ARKON
      </button>
    </div>
  );
}
