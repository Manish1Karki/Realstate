import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'
import process from 'node:process'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: {
    '/api': process.env.LAND_DEV_API_URL || 'http://127.0.0.1:8000',
    '/aggregator': { target: process.env.LAND_DEV_AGGREGATOR_URL || 'http://127.0.0.1:5174', ws: true },
  } },
})
