import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { cn } from '@/lib/utils'

export function Layout() {
  const location = useLocation()
  
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className={cn('flex-1 overflow-auto p-4 md:p-6', location.pathname === '/' && 'pt-0')}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}