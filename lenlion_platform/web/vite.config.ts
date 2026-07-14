import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../control_plane/web_dist',
    emptyOutDir: true,
    manifest: true,
  },
  server: {
    proxy: {
      '/admin': {
        target: 'http://127.0.0.1:8080',
      },
    },
  },
})
