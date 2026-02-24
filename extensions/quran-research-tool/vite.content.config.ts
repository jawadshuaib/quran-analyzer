import { defineConfig } from 'vite'
import { resolve } from 'path'
import { copyFileSync } from 'fs'

export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: false, // Don't wipe the main build output
    lib: {
      entry: resolve(__dirname, 'src/content/content.ts'),
      name: 'QRTContent',
      formats: ['iife'],
      fileName: () => 'content.js',
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
  plugins: [
    {
      name: 'copy-content-css',
      writeBundle() {
        copyFileSync(
          resolve(__dirname, 'src/content/content.css'),
          resolve(__dirname, 'dist/content.css'),
        )
      },
    },
  ],
})
