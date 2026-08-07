import { Blocks } from 'lucide-react';

export function ViewPlugins() {
  return (
    <div className="flex flex-col items-center justify-center h-full animate-in fade-in duration-300">
      <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-6">
        <Blocks className="w-8 h-8 text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
      </div>
      <h2 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">Plugins</h2>
      <p className="text-gray-500 dark:text-gray-400 text-center font-light text-[14px] max-w-sm">
        No plugins installed. Plugin management is coming soon.
      </p>
      <p className="text-gray-400 dark:text-gray-500 text-center font-light text-[13px] mt-1">
        Backend plugin routes are not yet available.
      </p>
    </div>
  );
}
