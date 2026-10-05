import { cp, mkdir, mkdtemp, access } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
try {
  await access(path.join(projectRoot, '.vercel/project.json'));
} catch {
  throw new Error('Link this workspace to the existing Vercel project before deploying.');
}
const stagingParent = path.join(projectRoot, '.review/deployments');
await mkdir(stagingParent, { recursive: true });
const uploadRoot = await mkdtemp(path.join(stagingParent, 'site-'));

// Copy only build inputs. Local databases, secrets and Python caches stay out.
const sources = ['package.json', 'package-lock.json', 'vercel.json', '.vercelignore', 'api', 'scripts', '.vercel/project.json'];
for (const app of ['LandingPage', 'aggregator/frontend']) {
  for (const name of ['package.json', 'package-lock.json', 'index.html', 'vite.config.js', 'src']) {
    sources.push(`${app}/${name}`);
  }
  try {
    await access(path.join(projectRoot, app, 'public'));
    sources.push(`${app}/public`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
}
for (const relativePath of sources) {
  const destination = path.join(uploadRoot, relativePath);
  await mkdir(path.dirname(destination), { recursive: true });
  await cp(path.join(projectRoot, relativePath), destination, {
    recursive: true,
    filter: source => !/^(?:\.env(?:\..*)?|node_modules|__pycache__|\.pytest_cache)$/.test(path.basename(source)),
  });
}
console.log(`Prepared deployment: ${uploadRoot}`);
if (!process.argv.includes('--prepare-only')) {
  const result = process.platform === 'win32'
    ? spawnSync('cmd.exe', ['/d', '/s', '/c', 'npm.cmd exec --yes --package=vercel -- vercel --prod --yes'], { cwd: uploadRoot, stdio: 'inherit' })
    : spawnSync('npm', ['exec', '--yes', '--package=vercel', '--', 'vercel', '--prod', '--yes'], { cwd: uploadRoot, stdio: 'inherit' });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
}
