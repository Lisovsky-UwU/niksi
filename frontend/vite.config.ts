import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // On Windows the native file watcher sometimes misses quick successive edits and the
    // dev server keeps serving stale <style> blocks; polling catches every change.
    watch: {
      usePolling: true,
      interval: 200,
    },
    proxy: {
      // Keeps the dev server same-origin with the backend, so the httpOnly auth
      // cookie works locally exactly as it will in prod behind Caddy.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
