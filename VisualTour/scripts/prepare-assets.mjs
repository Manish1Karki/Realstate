import { cp, mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const source = new URL('../node_modules/cesium/Build/Cesium/', import.meta.url)
const destination = new URL('../public/cesiumStatic/', import.meta.url)
await mkdir(fileURLToPath(destination), { recursive: true })
for (const directory of ['Workers', 'ThirdParty', 'Assets', 'Widgets']) {
  await cp(fileURLToPath(new URL(directory, source)), fileURLToPath(new URL(directory, destination)), { recursive: true })
}
