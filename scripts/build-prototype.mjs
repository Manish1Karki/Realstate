import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, relative } from 'node:path';
import { rmSync } from 'node:fs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const obsoleteDashboard = resolve(root, 'public', 'aggregator');
if (relative(root, obsoleteDashboard).replaceAll('\\', '/') !== 'public/aggregator') throw new Error('Unexpected dashboard directory');
// Remove assets left by older builds so they cannot be published again.
rmSync(obsoleteDashboard, { recursive: true, force: true });
const npmCLI = process.env.npm_execpath;
if (!npmCLI) throw new Error('Run this build using npm run build');
const tour = spawnSync(process.execPath, [npmCLI, '--prefix', 'VisualTour', 'run', 'build', '--', '--outDir', '../public/visual-tour', '--emptyOutDir'], { cwd: root, stdio: 'inherit', windowsHide: true });
if (tour.error) throw tour.error;
if (tour.status !== 0) process.exit(tour.status || 1);
const next = spawnSync(process.execPath, [npmCLI, 'run', 'build:next'], { cwd: root, stdio: 'inherit', windowsHide: true });
if (next.error) throw next.error;
if (next.status !== 0) process.exit(next.status || 1);
