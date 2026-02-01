import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/Control/',
  server: {
    port: 3000,
    proxy: {
      '/api': { 
        target: 'https://localhost:8000',  // 改为https
        changeOrigin: true,
        secure: false  // 允许不安全的HTTPS连接
      },
    },
  },
})