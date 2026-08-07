import { useResourceUsage } from '../../api/hooks';
import { Cpu, HardDrive, Loader2, Server, Activity } from 'lucide-react';

export function ViewResources() {
  const { data: resources, isLoading, isError } = useResourceUsage();

  return (
    <div className="flex flex-col w-full h-full animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-medium tracking-tight">Resources</h2>
      </div>

      <div className="mb-8">
        <p className="text-sm text-gray-400 dark:text-gray-500 font-light">
          System resource usage and runtime agent capacity.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-500">
          <Server className="w-12 h-12 mb-4 opacity-50" strokeWidth={1} />
          <p className="font-light">Unable to load resource data.</p>
          <p className="text-sm mt-1">Backend may be offline.</p>
        </div>
      ) : resources ? (
        <div className="space-y-6">
          {/* CPU */}
          <div className="p-4 rounded-xl border border-gray-200 dark:border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium">CPU</span>
            </div>
            <div className="h-3 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-500 transition-all"
                style={{ width: `${resources.cpu_percent}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">{resources.cpu_percent.toFixed(1)}%</p>
          </div>

          {/* RAM */}
          <div className="p-4 rounded-xl border border-gray-200 dark:border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <HardDrive className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium">Memory</span>
            </div>
            <div className="h-3 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-purple-500 transition-all"
                style={{ width: `${resources.ram_percent}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {resources.ram_used_mb.toFixed(0)} / {resources.ram_total_mb.toFixed(0)} MB ({resources.ram_percent.toFixed(1)}%)
            </p>
          </div>

          {/* Disk */}
          <div className="p-4 rounded-xl border border-gray-200 dark:border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <HardDrive className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium">Disk</span>
            </div>
            <div className="h-3 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-green-500 transition-all"
                style={{ width: `${resources.disk_percent}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {resources.disk_used_gb.toFixed(1)} / {resources.disk_total_gb.toFixed(1)} GB ({resources.disk_percent.toFixed(1)}%)
            </p>
          </div>

          {/* Agents */}
          <div className="p-4 rounded-xl border border-gray-200 dark:border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium">Runtime Agents</span>
            </div>
            <div className="h-3 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-orange-500 transition-all"
                style={{ width: `${resources.max_agents > 0 ? (resources.active_agents / resources.max_agents) * 100 : 0}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {resources.active_agents} / {resources.max_agents} active
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
