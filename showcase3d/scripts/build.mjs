import { build } from 'esbuild';
import { mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { exportMaps, sha256 } from './export-maze.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
process.chdir(root);
await mkdir('src/maze', { recursive: true });
await writeFile('src/maze/maps.json', JSON.stringify(exportMaps()) + '\n');
await rm('dist', { recursive: true, force: true });
await mkdir('dist', { recursive: true });
const output = await build({ entryPoints: ['src/main.js'], bundle: true, minify: true,
  format: 'esm', target: ['chrome120', 'edge120'], outdir: 'dist', entryNames: 'app-[hash]',
  legalComments: 'eof', metafile: true, charset: 'utf8' });
const files = Object.keys(output.metafile.outputs);
const js = files.find(f => f.endsWith('.js')).replace('dist/', './');
const css = files.find(f => f.endsWith('.css')).replace('dist/', './');
await writeFile('dist/index.html', (await readFile('index.html', 'utf8'))
  .replace('__SCRIPT__', js).replace('__STYLE__', css));
await writeFile('dist/LICENSES.txt', await readFile('node_modules/three/LICENSE', 'utf8'));
const hashes = {};
for (const file of [...files, 'dist/index.html', 'dist/LICENSES.txt'].sort()) {
  hashes[file.replace('dist/', '')] = sha256(await readFile(file));
}
await writeFile('dist/build-info.json', JSON.stringify({ phase: '3D-P0', three: '0.180.0',
  esbuild: '0.25.12', liteBaseline: exportMaps().baseline, files: hashes }, null, 2) + '\n');
console.log('Reproducible local bundle:', hashes);
