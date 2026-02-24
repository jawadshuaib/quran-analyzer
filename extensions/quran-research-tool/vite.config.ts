import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'
import { copyFileSync, mkdirSync, existsSync, readdirSync } from 'fs'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: 'copy-extension-assets',
      writeBundle() {
        const dist = resolve(__dirname, 'dist')
        const pub = resolve(__dirname, 'public')

        // Copy manifest.json
        copyFileSync(resolve(pub, 'manifest.json'), resolve(dist, 'manifest.json'))

        // Copy icons
        const iconsDir = resolve(pub, 'icons')
        const distIcons = resolve(dist, 'icons')
        if (existsSync(iconsDir)) {
          if (!existsSync(distIcons)) mkdirSync(distIcons, { recursive: true })
          for (const f of readdirSync(iconsDir)) {
            copyFileSync(resolve(iconsDir, f), resolve(distIcons, f))
          }
        }
      },
    },
  ],
  base: './',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'popup.html'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]',
      },
    },
  },
})
