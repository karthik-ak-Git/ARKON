import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Projects } from '@/pages/Projects'
import { Workflows } from '@/pages/Workflows'
import { Agents } from '@/pages/Agents'
import { Monitoring } from '@/pages/Monitoring'
import { Plugins } from '@/pages/Plugins'
import { Settings } from '@/pages/Settings'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="workflows" element={<Workflows />} />
        <Route path="agents" element={<Agents />} />
        <Route path="monitoring" element={<Monitoring />} />
        <Route path="plugins" element={<Plugins />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
