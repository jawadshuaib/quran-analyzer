import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Honour an assigned PORT (used by managed preview servers); fall back to
    // 4000 for a plain `npm run dev`.
    port: Number(process.env.PORT) || 4000,
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
})
