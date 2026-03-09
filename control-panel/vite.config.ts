import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/mas/',  // 修改为 /mas/ 路径
  server: {
    port: 3000,
    proxy: {
      '/api': { 
        target: 'http://localhost:12301',  // 修正：使用正确的后端端口
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      },
      '/internal': {
        target: 'http://localhost:12301',  // 修正：使用正确的后端端口
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
      },
    },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
        }
      }
    }
  }
})