// Explicit local copy only. Never uploads; never modifies source or overwrites a directory.
import { mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { readPublication } from './publication.mjs';
const [source,output]=process.argv.slice(2);
if(!source||!output)throw new Error('Usage: node prepare-publication.mjs <already-published-export-folder> <NEW-local-assignments-folder>');
const files=readPublication(resolve(source)),destination=resolve(output);
if(existsSync(destination))throw new Error('Output already exists. Choose a new local directory; existing files are never overwritten.');
mkdirSync(destination,{recursive:true});
// Unit bytes first; manifest last. Both editions consume the identical files.
for(const [name,bytes] of [...files].sort(([a],[b])=>a==='manifest.json'?1:b==='manifest.json'?-1:a.localeCompare(b)))writeFileSync(resolve(destination,name),bytes,{flag:'wx'});
console.log(`Prepared ${files.size-1} explicitly published units in ${destination}. No upload performed.`);
