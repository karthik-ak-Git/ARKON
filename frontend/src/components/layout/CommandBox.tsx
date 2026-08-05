import React, { useState } from 'react';
import { Paperclip, ArrowUp, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';

export function CommandBox() {
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState('');

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
          placeholder="What would you like ARKON to orchestrate?"
          className="flex-1 bg-transparent border-none outline-none resize-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 font-sans text-[15px] max-h-[200px] py-1"
          rows={1}
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            // Auto resize logic could go here
          }}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
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
          className={cn(
            "p-2 rounded-xl transition-all duration-200",
            inputValue.trim() 
              ? "bg-black dark:bg-white text-white dark:text-black hover:opacity-80" 
              : "bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed"
          )}
        >
          <ArrowUp className="w-[18px] h-[18px]" strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}
