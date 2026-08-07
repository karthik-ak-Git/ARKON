# Frontend

React 19 + TypeScript + Vite 6 + Tailwind CSS 4

## Setup

```bash
cd apps/desktop
npm install
```

## Running

```bash
npm run dev          # Vite dev server on :5173
npm run dev:tauri    # Tauri dev with hot reload
```

## Structure

- `src/main.tsx` — entry point with bootstrap and error boundary
- `src/App.tsx` — root component with backend status monitoring
- `src/api/` — API client, hooks, types, WebSocket provider
- `src/components/` — UI components (layout, views, ui)
- `src/lib/` — utilities, config, crash handler, Tauri IPC bridge
- `src/store/` — Zustand state management

## Key Components

| Component | Purpose |
|-----------|---------|
| `CommandBox` | Command parser and task submission |
| `MainWorkspace` | Dynamic view router |
| `Sidebar` | Navigation with execution and resource monitoring |
| `BackendStatusBanner` | Connection status indicator |

## Building

```bash
npm run build        # Vite production build
npm run build:tauri  # Full Tauri release build
npm run lint         # TypeScript type check
```
