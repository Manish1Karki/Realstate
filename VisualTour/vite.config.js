import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'

const cesiumSource = 'node_modules/cesium/Build/Cesium'
const cesiumBaseUrl = '/visual-tour/cesiumStatic'

export default defineConfig({
  base: '/visual-tour/',
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        { src: `${cesiumSource}/Workers`, dest: 'cesiumStatic' },
        { src: `${cesiumSource}/ThirdParty`, dest: 'cesiumStatic' },
        { src: `${cesiumSource}/Assets`, dest: 'cesiumStatic' },
        { src: `${cesiumSource}/Widgets`, dest: 'cesiumStatic' },
      ],
    }),
  ],
  define: {
    CESIUM_BASE_URL: JSON.stringify(cesiumBaseUrl),
  },
})
