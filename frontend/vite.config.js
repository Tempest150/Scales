import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5010', // Proxy API requests to the Flask backend responsible for the backend logic of the application
        changeOrigin: true
      }
    }
  }
})