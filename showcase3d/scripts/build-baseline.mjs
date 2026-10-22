// Test-only frozen P0 rendering, never included in the presentation bundle.
import {build} from 'esbuild';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const output=root+'../test-results/3d-p1/p0-runtime';
await mkdir(output,{recursive:true});
const result=await build({entryPoints:[root+'tests/fixtures/p0/src/main.js'],bundle:true,minify:true,format:'esm',target:['chrome120','edge120'],outdir:output,entryNames:'app-[hash]',metafile:true,legalComments:'eof',charset:'utf8'});
const paths=Object.keys(result.metafile.outputs),name=s=>s.split('/').at(-1);
const js=name(paths.find(p=>p.endsWith('.js'))),css=name(paths.find(p=>p.endsWith('.css')));
await writeFile(output+'/index.html',(await readFile(root+'tests/fixtures/p0/index.html','utf8')).replace('__SCRIPT__','./'+js).replace('__STYLE__','./'+css));
await writeFile(output+'/LICENSES.txt',await readFile(root+'node_modules/three/LICENSE','utf8'));
console.log('Frozen P0 baseline built under test-results/3d-p1/p0-runtime');
