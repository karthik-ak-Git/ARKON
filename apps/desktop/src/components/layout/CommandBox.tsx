import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, ArrowUp, Zap, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useArkonStore } from '../../store/useArkonStore';
import { useSubmitTask } from '../../api/hooks';

export function CommandBox() {
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const { setActiveSidebarItem, activeWorkspaceId } = useArkonStore();
  const submitMutation = useSubmitTask();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const handleSubmit = async () => {
    const text = inputValue.trim();
    if (!text || submitMutation.isPending) return;

    setInputValue('');

    // Parse command intent
    const lower = text.toLowerCase();

    if (lower.startsWith('/chat ') || lower.startsWith('chat ')) {
      setActiveSidebarItem('chat');
      return;
    }

    if (lower.startsWith('/project ') || lower.startsWith('create project ')) {
      setActiveSidebarItem('projects');
      return;
    }

    if (lower.startsWith('/agent ') || lower.startsWith('spawn agent ') || lower.startsWith('create agent ')) {
      setActiveSidebarItem('agents');
      return;
    }

    if (lower.startsWith('/execute ') || lower.startsWith('run ') || lower.startsWith('execute ')) {
      // Submit task to execution engine
      const taskDescription = text.replace(/^\/?(execute|run)\s+/i, '');
      try {
        await submitMutation.mutateAsync({
          task_type: 'general',
          input_data: { description: taskDescription, workspace_id: activeWorkspaceId },
        });
        setActiveSidebarItem('execution');
      } catch {
        setActiveSidebarItem('execution');
      }
      return;
    }

    // Default: submit as general task
    try {
      await submitMutation.mutateAsync({
        task_type: 'general',
        input_data: { description: text, workspace_id: activeWorkspaceId },
      });
      setActiveSidebarItem('execution');
    } catch {
      setActiveSidebarItem('execution');
    }
  };

  return (
    <div 
      className={cn(
        "w-full flex flex-col bg-white dark:bg-[#1C1C1C] rounded-2xl border transition-all duration-300 shadow-sm",
        isFocused 
          ? "border-gray-300 dark:border-white/20 shadow-md ring-4 ring-gray-100 dark:ring-white/5" 
          : "border-gray-200 dark:border-white/10"
      )}
    >
      <div className="flex px-4 pt-3 pb-2 min-h-[60px] items-center">
        <textarea
          ref={textareaRef}
          placeholder="What would you like ARKON to orchestrate? (e.g. /chat, /execute, /project, /agent)"
          className="flex-1 bg-transparent border-none outline-none resize-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 font-sans text-[15px] max-h-[200px] py-1"
          rows={1}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
      </div>
      
      <div className="flex items-center justify-between px-3 pb-3 pt-1">
        <div className="flex items-center gap-1 text-gray-400 dark:text-gray-500">
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="Attach file or folder">
            <Paperclip className="w-[18px] h-[18px]" strokeWidth={2} />
          </button>
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="Quick actions">
            <Zap className="w-[18px] h-[18px]" strokeWidth={2} />
          </button>
        </div>
        
        <button 
          onClick={handleSubmit}
          disabled={!inputValue.trim() || submitMutation.isPending}
          className={cn(
            "p-2 rounded-xl transition-all duration-200",
            inputValue.trim() && !submitMutation.isPending
              ? "bg-black dark:bg-white text-white dark:text-black hover:opacity-80" 
              : "bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed"
          )}
        >
          {submitMutation.isPending ? (
            <Loader2 className="w-[18px] h-[18px] animate-spin" strokeWidth={2.5} />
          ) : (
            <ArrowUp className="w-[18px] h-[18px]" strokeWidth={2.5} />
          )}
        </button>
      </div>
    </div>
  );
}
