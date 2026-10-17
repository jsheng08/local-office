// Local Office web console — SPA, fully offline (no remote fonts/CDN/UI kits).
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: false,
  devtools: { enabled: false },
  telemetry: false,
  css: ['~/assets/main.css'],
  app: {
    head: {
      title: 'Local Office',
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
    },
  },
  nitro: {
    devProxy: {
      '/api': { target: 'http://127.0.0.1:8000/api', changeOrigin: true },
    },
  },
  routeRules: {
    '/api/**': { proxy: 'http://127.0.0.1:8000/api/**' },
  },
})
