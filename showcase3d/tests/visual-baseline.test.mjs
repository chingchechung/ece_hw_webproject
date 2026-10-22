import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {sha256} from '../scripts/export-maze.mjs';
test('immutable approved P0 visual source baseline and unchanged PBR/quality definitions',()=>{
  const base=new URL('./fixtures/p0/',import.meta.url),manifest=JSON.parse(readFileSync(new URL('baseline.json',base)));
  assert.equal(manifest.commit,'f685a21e391cdb0848b851e6bf2b72707c77162a');
  for(const [file,hash] of Object.entries(manifest.files))assert.equal(sha256(readFileSync(new URL(file,base))),hash,file);
  for(const file of ['src/materials/laboratory.js','src/performance/quality.js'])assert.equal(sha256(readFileSync(new URL('../'+file,import.meta.url))),manifest.files[file]);
});
test('frozen P0 comparison runtime builds separately from the deployed P1 bundle',()=>{
  execFileSync(process.execPath,['scripts/build-baseline.mjs'],{cwd:fileURLToPath(new URL('../',import.meta.url))});
});
