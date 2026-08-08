/**
 * Step 0: Welcome
 * Brand introduction. No inputs.
 */

interface StepWelcomeProps {
  onNext: () => void;
}

export function StepWelcome({ onNext }: StepWelcomeProps) {
  return (
    <div className="flex flex-col items-center text-center">
      {/* Logo / Brand */}
      <div className="mb-8">
        <img
          src="/arkon-logo.png"
          alt="ARKON"
          className="w-48 h-auto mx-auto mb-6"
        />
        <h1 className="text-2xl font-light text-white mb-3">Welcome to ARKON</h1>
        <p className="text-sm text-white/40 max-w-sm leading-relaxed">
          AI Agent Operating Platform. Let's configure your environment in a few steps.
        </p>
      </div>

      <button
        onClick={onNext}
        className="px-6 py-2.5 bg-white text-[#1a1a1a] text-sm font-medium rounded-lg hover:bg-white/90 transition-colors"
      >
        Get Started
      </button>
    </div>
  );
}
