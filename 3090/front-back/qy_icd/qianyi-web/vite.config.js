import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: ``,
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 8008,
    strictPort: true,
    watch: {
      usePolling: true,
      interval: 100, // 100~300 可调，越大越省CPU但刷新慢
    },
    // origin: 'http://127.0.0.1:8008',
    //origin: 'http://127.0.0.1:8008',

    // hmr: {
    //  protocol: 'ws',
    //   host: '127.0.0.1', // 使用通配符以适配远程开发
    // },
    proxy: {
      '/diag': {
        target: 'http://127.0.0.1:5511', // 诊断编码模型
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/diag/, ''),
      },
      '/sur': {
        target: 'http://127.0.0.1:6000', // 手术编码模型
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/sur/, ''),
      },
      '/api': {
        target: 'http://127.0.0.1:8088', // 后端接口
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ocr': {
        target: 'http://127.0.0.1:5050', // OCR服务地址
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ocr/, ''),
        timeout: 1200000, // 2分钟超时
      },
    },
  },
})
