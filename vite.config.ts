import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'
import Inspector from 'unplugin-vue-dev-locator/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    build: {
      sourcemap: 'hidden',
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html'),
        },
      },
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
      {
        name: 'serve-django-media',
        configureServer(server) {
          const mediaRoot = path.resolve(__dirname, 'backend/media')

          server.middlewares.use('/media', (req, res, next) => {
            const rawPath = req.url?.split('?')[0] ?? ''
            const mediaPath = path.resolve(mediaRoot, decodeURIComponent(rawPath.replace(/^\/+/, '')))

            if (!mediaPath.startsWith(mediaRoot + path.sep)) {
              res.statusCode = 403
              res.end('Forbidden')
              return
            }

            fs.stat(mediaPath, (statError, stat) => {
              if (statError || !stat.isFile()) {
                next()
                return
              }

              const extension = path.extname(mediaPath).toLowerCase()
              const contentType =
                extension === '.png' ? 'image/png'
                : extension === '.jpg' || extension === '.jpeg' ? 'image/jpeg'
                : extension === '.webp' ? 'image/webp'
                : extension === '.avif' ? 'image/avif'
                : 'application/octet-stream'

              res.setHeader('Content-Type', contentType)
              res.setHeader('Content-Length', String(stat.size))

              if (req.method === 'HEAD') {
                res.end()
                return
              }

              fs.createReadStream(mediaPath).pipe(res)
            })
          })
        },
      },
      // Inspector(), // Temporarily disabled
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'), // ✅ 定义 @ = src
      },
    },
  }
})
