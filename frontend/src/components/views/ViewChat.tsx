import React, { useState, useRef, useEffect } from 'react';
import { useArkonStore } from '../../store/useArkonStore';
import { MessageSquare, Send, User, Bot } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export function ViewChat() {
  const { activeWorkspaceId, workspaces } = useArkonStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I received your message: "${userMessage.content}". This is a placeholder response. Connect your AI agent to enable real responses.`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }, 500);
  };

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center pt-[10vh] animate-in fade-in zoom-in-95 duration-500 ease-out">
        <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-6">
          <MessageSquare className="w-8 h-8 text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
        </div>
        <h2 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">No Workspace Selected</h2>
        <p className="text-gray-500 dark:text-gray-400 text-center font-light text-[14px]">
          Select a workspace from the sidebar or create a new one.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-300">
      {/* Header */}
      <div className="pb-4 mb-4 border-b border-gray-200 dark:border-white/5">
        <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">{activeWorkspace.name}</h2>
        <p className="text-[13px] text-gray-400 dark:text-gray-500">Workspace chat</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto pb-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-12 h-12 rounded-xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-4">
              <MessageSquare className="w-6 h-6 text-gray-400" strokeWidth={1.5} />
            </div>
            <p className="text-[14px] text-gray-400 dark:text-gray-500">Start a conversation</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-gray-900 dark:bg-white flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-white dark:text-gray-900" strokeWidth={1.5} />
                </div>
              )}
              <div className={`max-w-[70%] px-4 py-2.5 rounded-2xl text-[14px] leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-br-md'
                  : 'bg-gray-100 dark:bg-white/5 text-gray-900 dark:text-gray-100 rounded-bl-md'
              }`}>
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-gray-200 dark:bg-white/10 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-gray-600 dark:text-gray-300" strokeWidth={1.5} />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="pt-4 border-t border-gray-200 dark:border-white/5">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-[14px] text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-white/20"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="w-10 h-10 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 flex items-center justify-center hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-40"
          >
            <Send className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </div>
  );
}
