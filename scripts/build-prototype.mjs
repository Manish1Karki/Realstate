import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, relative } from 'node:path';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, 'dist');
if (relative(root, output) !== 'dist') throw new Error('Unexpected build directory');
const npmCLI = process.env.npm_execpath;
if (!npmCLI) throw new Error('Run this build using npm run build');

function build(directory, args) {
  const result = spawnSync(process.execPath, [npmCLI, 'run', 'build', '--', ...args], {
    cwd: resolve(root, directory), stdio: 'inherit', windowsHide: true,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}

// Compile the user-facing prototype only. VisualTour is a separate project.
build('LandingPage', ['--outDir', '../dist', '--emptyOutDir']);
build('aggregator/frontend', ['--base', '/aggregator/', '--outDir', '../../dist/aggregator', '--emptyOutDir']);
