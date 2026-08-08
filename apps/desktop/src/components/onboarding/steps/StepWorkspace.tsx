/**
 * Step 1: Workspace
 * Create first workspace.
 */

import { useState } from 'react';
import { useOpenWorkspace } from '../../../api/hooks/useWorkspaces';
import type { OnboardingData } from '../../../api/types';
import type { UseMutationResult } from '@tanstack/react-query';

interface StepWorkspaceProps {
  data: OnboardingData;
  onUpdate: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
  createWorkspace: UseMutationResult<unknown, unknown, { id: string; name: string; description?: string }>;
}

export function StepWorkspace({ data, onUpdate, onNext, onBack, createWorkspace }: StepWorkspaceProps) {
  const [name, setName] = useState(data.workspace_name ?? 'My Workspace');
  const [description, setDescription] = useState(data.workspace_description ?? '');
  const [error, setError] = useState('');
  const openWorkspace = useOpenWorkspace();

  const handleNext = async () => {
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Workspace name is required');
      return;
    }

    const id = trimmed.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

    try {
      await createWorkspace.mutateAsync({
        id,
        name: trimmed,
        description: description.trim() || undefined,
      });
      onUpdate({ workspace_name: trimmed, workspace_description: description.trim() || null });
      onNext();
    } catch (err) {
      const apiError = err as { status?: number; detail?: string };
      if (apiError.status === 400 && apiError.detail?.includes('already exists')) {
        // Workspace exists on disk — try to open it
        try {
          await openWorkspace.mutateAsync(id);
          onUpdate({ workspace_name: trimmed, workspace_description: description.trim() || null });
          onNext();
          return;
        } catch {
          setError('Workspace exists but could not be opened');
        }
      }
      setError(apiError.detail || 'Failed to create workspace');
    }
  };

  return (
    <div>
      <h2 className="text-lg font-light text-white mb-1">Create a Workspace</h2>
      <p className="text-sm text-white/40 mb-6">Workspaces organize your projects and agents.</p>

      <div className="space-y-4">
        <div>
          <label className="block text-xs text-white/30 uppercase tracking-wider mb-1.5">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => { setName(e.target.value); setError(''); }}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-white/20 transition-colors"
            placeholder="My Workspace"
            autoFocus
          />
          {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
        </div>

        <div>
          <label className="block text-xs text-white/30 uppercase tracking-wider mb-1.5">Description (optional)</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-white/20 transition-colors"
            placeholder="What is this workspace for?"
          />
        </div>
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          disabled={createWorkspace.isPending}
          className="px-5 py-2 bg-white text-[#1a1a1a] text-sm font-medium rounded-lg hover:bg-white/90 transition-colors disabled:opacity-50"
        >
          {createWorkspace.isPending ? 'Creating...' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
