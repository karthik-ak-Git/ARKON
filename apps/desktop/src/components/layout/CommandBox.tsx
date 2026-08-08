import { useState, useRef, useEffect } from 'react';
import { Paperclip, Zap } from 'lucide-react';

export function CommandBox() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (!input.trim()) return;
    setInput('');
  };

  return (
    <div className="relative w-full">
      <div className="flex items-start gap-3 p-4 rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 shadow-sm">
        <button className="mt-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
          <Paperclip className="w-[18px] h-[18px]" strokeWidth={1.5} />
        </button>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="What would you like ARKON to orchestrate?"
          className="flex-1 bg-transparent text-[15px] text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none focus:outline-none min-h-[24px] max-h-[150px] leading-relaxed font-light"
          rows={1}
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim()}
          className="mt-1 w-8 h-8 rounded-lg bg-gray-900 dark:bg-white text-white dark:text-gray-900 flex items-center justify-center hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Zap className="w-4 h-4" strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
}
