import { defineConfig } from 'vite'

export default defineConfig({
  // без плагина React: JSX компилирует esbuild, импорт React в каждом файле не нужен
  esbuild: { jsx: 'automatic' },
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})
