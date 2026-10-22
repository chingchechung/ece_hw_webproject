import { readFileSync, readdirSync, lstatSync } from 'node:fs';
import { join } from 'node:path';
import { AssignmentValidator as validator } from '../src/assignments/validator.js';
import { requireValid } from '../src/assignments/loader.js';

export function readPublication(directory) {
  const raw = name => {
    const path=join(directory,name);
    if(!lstatSync(path).isFile())throw new Error(`Publication requires a regular file: ${name}`);
    const bytes=readFileSync(path);return {bytes,data:JSON.parse(bytes.toString('utf8'))};
  };
  const manifest=raw('manifest.json');requireValid(validator.validateManifest(manifest.data),'manifest.json');
  const files=new Map([['manifest.json',manifest.bytes]]);
  for(const entry of validator.normalizeManifest(manifest.data).units){
    const unit=raw(entry.file);requireValid(validator.validateUnit(unit.data,entry.file),entry.file);
    files.set(entry.file,unit.bytes);
  }
  for(const name of readdirSync(directory))if(!files.has(name))throw new Error(`Unlisted file in public assignments directory: ${name}. Move it outside the public package.`);
  return files;
}
