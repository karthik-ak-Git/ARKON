import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@arkon/shared': path.resolve(__dirname, '../../packages/shared/src'),
      '@arkon/agent-sdk': path.resolve(__dirname, '../../packages/agent-sdk/src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    watch: {
      ignored: ['**/src-tauri/**', '**/dist/**'],
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
