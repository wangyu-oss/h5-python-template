import vue from '@vitejs/plugin-vue'
import { VantResolver } from '@vant/auto-import-resolver'
import { fileURLToPath, URL } from 'node:url'
import { visualizer } from 'rollup-plugin-visualizer'
import Components from 'unplugin-vue-components/vite'
import { defineConfig } from 'vitest/config'
import compression from 'vite-plugin-compression'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [VantResolver()],
      dts: 'src/components.d.ts',
    }),
    compression({ algorithm: 'gzip', threshold: 1024 }),
    VitePWA({
      registerType: 'prompt',
      manifest: {
        name: 'H5 基座',
        short_name: 'H5',
        theme_color: '#1989fa',
        background_color: '#f7f8fa',
        display: 'standalone',
        start_url: '/',
      },
      workbox: { globPatterns: ['**/*.{js,css,html,svg,png,webp}'] },
    }),
    process.env.ANALYZE ? visualizer({ filename: 'stats.html', open: false }) : null,
  ].filter(Boolean),
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8010', changeOrigin: true } },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia', 'vue-i18n'],
          vant: ['vant'],
        },
      },
    },
  },
  test: { environment: 'node', include: ['src/**/*.test.ts'] },
})
