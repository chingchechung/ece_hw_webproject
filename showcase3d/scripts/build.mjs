import { build } from 'esbuild';
import { mkdir, readFile, writeFile, rm, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { readPublication } from './publication.mjs';
import { fileURLToPath } from 'node:url';
import { exportMaps, runtimeGeneratorSource, sha256 } from './export-maze.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
process.chdir(root);
await mkdir('src/maze', { recursive: true });
await writeFile('src/maze/maps.json', JSON.stringify(exportMaps()) + '\n');
await writeFile('src/maze/lite-generated.js', runtimeGeneratorSource());
await mkdir('dist', { recursive: true });
// A graphics rebuild must never remove instructor-published assignments.
if (!existsSync('dist/assignments/manifest.json')) {
  await mkdir('dist/assignments',{recursive:true});
  await writeFile('dist/assignments/manifest.json',await readFile('public/assignments/manifest.json'));
}
readPublication('dist/assignments'); // Fail before touching runtime files if publication is invalid.
for(const name of await readdir('dist'))if(/^(app-.*\.(js|css)|index\.html|build-info\.json|LICENSES\.txt)$/.test(name))await rm(`dist/${name}`);
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
await writeFile('dist/build-info.json', JSON.stringify({ phase: '3D-P2.1', version: JSON.parse(await readFile('package.json','utf8')).version, three: '0.180.0',
  esbuild: '0.25.12', liteBaseline: exportMaps().baseline, files: hashes }, null, 2) + '\n');
console.log('Reproducible local bundle:', hashes);
