import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import Inspector from 'unplugin-vue-dev-locator/vite'
import traeBadgePlugin from 'vite-plugin-trae-solo-badge'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    build: {
      sourcemap: 'hidden',
    },
    server: {
      hmr: {
        overlay: false
      },
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000', // Django 后端地址
          changeOrigin: true,
          secure: false,
        },
        '/functions/v1': {
          target: env.VITE_SUPABASE_URL,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/functions\/v1/, '/functions/v1'), // Explicitly keep path
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        },
      },
    },
    plugins: [
      vue(),
      // Inspector(), // Temporarily disabled
      traeBadgePlugin({
        variant: 'dark',
        position: 'bottom-right',
        prodOnly: true,
        clickable: true,
        clickUrl: 'https://www.trae.ai/solo?showJoin=1',
        autoTheme: true,
        autoThemeTarget: '#app',
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'), // ✅ 定义 @ = src
      },
    },
  }
})
