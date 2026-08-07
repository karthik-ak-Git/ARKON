import { Bell, Search, User, Sun, Moon } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { useAuth } from '@/hooks/useAuth'

export function Header() {
  const { theme, toggleTheme } = useTheme()
  const { user } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between px-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <div className="relative hidden sm:block">
          <Search
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            type="search"
            placeholder="Search..."
            className="h-9 w-64 rounded-md border bg-background pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-ring"
            aria-label="Search"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-accent transition-colors"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        <button
          className="p-2 rounded-md hover:bg-accent transition-colors relative"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center">
            3
          </span>
        </button>

        <div className="w-px h-6 bg-border mx-1" />

        <div className="flex items-center gap-2">
          {user && (
            <>
              <div className="hidden sm:block text-sm text-muted-foreground">{user.name}</div>
              <button className="p-1 rounded-full hover:bg-accent transition-colors" aria-label="User menu">
                <User className="h-6 w-6" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
