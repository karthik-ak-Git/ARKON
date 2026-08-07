import { FolderKanban, Plus, Trash2, Loader2 } from 'lucide-react'
import { useWorkspaces, useCreateWorkspace, useDeleteWorkspace } from '@/api/hooks'
import { useState } from 'react'

export function Projects() {
  const { data: workspaces, isLoading } = useWorkspaces()
  const createWorkspace = useCreateWorkspace()
  const deleteWorkspace = useDeleteWorkspace()
  const [newName, setNewName] = useState('')

  const handleCreate = async () => {
    if (!newName.trim()) return
    const slug = newName.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
    await createWorkspace.mutateAsync({ id: slug, name: newName.trim() })
    setNewName('')
  }

  const allWorkspaces = [...(workspaces?.active ?? []), ...(workspaces?.available ?? [])]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">Manage your workspaces and projects</p>
        </div>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="New workspace name..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          className="flex-1 h-9 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          onClick={handleCreate}
          disabled={createWorkspace.isPending || !newName.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {createWorkspace.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Create
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : allWorkspaces.length === 0 ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <FolderKanban className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground">No workspaces yet</p>
          <p className="text-sm text-muted-foreground/70 mt-1">Create one above to get started</p>
        </div>
      ) : (
        <div className="space-y-2">
          {allWorkspaces.map((ws) => (
            <div key={ws.id} className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                  <FolderKanban className="h-4 w-4" />
                </div>
                <div>
                  <p className="font-medium">{ws.name}</p>
                  <p className="text-sm text-muted-foreground">{ws.state}</p>
                </div>
              </div>
              <button
                onClick={() => deleteWorkspace.mutate(ws.id)}
                disabled={deleteWorkspace.isPending}
                className="p-2 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
