import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const cesiumBaseUrl = '/visual-tour/cesiumStatic'

export default defineConfig({
  base: '/visual-tour/',
  plugins: [
    react(),
  ],
  define: {
    CESIUM_BASE_URL: JSON.stringify(cesiumBaseUrl),
  },
})
