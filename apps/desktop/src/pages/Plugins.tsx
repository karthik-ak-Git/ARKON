import { Puzzle, Loader2 } from 'lucide-react'
import { useRuntimeAgents } from '@/api/hooks'

export function Plugins() {
  const { data: agents, isLoading } = useRuntimeAgents()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Plugins</h1>
        <p className="text-muted-foreground">Manage installed plugins and extensions</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="rounded-lg border bg-card p-12 text-center">
          <Puzzle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground">No plugins installed</p>
          <p className="text-sm text-muted-foreground/70 mt-1">Plugins will appear here when available</p>
        </div>
      )}
    </div>
  )
}
