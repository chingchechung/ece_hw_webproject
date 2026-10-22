import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, cpSync, symlinkSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { readPublication } from '../scripts/publication.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
function publication(dir){
  mkdirSync(dir,{recursive:true});
  const unit=readFileSync(new URL('../../tests/fixtures/v2/S02.json',import.meta.url));
  writeFileSync(join(dir,'S02.json'),unit);
  writeFileSync(join(dir,'manifest.json'),JSON.stringify({schemaVersion:1,units:[{unitId:'S02',title:'TEST ONLY',file:'S02.json'}]},null,2));
  return unit;
}
test('publication allowlist preserves exact bytes and refuses missing, invalid, symlink or unlisted files',()=>{
  const temp=mkdtempSync(join(tmpdir(),'emi-publication-'));
  try{
    const bytes=publication(temp);assert.deepEqual(readPublication(temp).get('S02.json'),bytes);
    writeFileSync(join(temp,'S03.json'),'private draft fixture');assert.throws(()=>readPublication(temp),/Unlisted/);rmSync(join(temp,'S03.json'));
    writeFileSync(join(temp,'S02.json'),'bad JSON');assert.throws(()=>readPublication(temp));
    rmSync(join(temp,'S02.json'));assert.throws(()=>readPublication(temp));
    symlinkSync(new URL('../../tests/fixtures/v2/S02.json',import.meta.url),join(temp,'S02.json'));assert.throws(()=>readPublication(temp),/regular file/);
  }finally{rmSync(temp,{recursive:true,force:true});}
});
test('explicit local preparation copies only validated exports and never overwrites the destination',()=>{
  const temp=mkdtempSync(join(tmpdir(),'emi-prepare-'));
  try{
    const source=join(temp,'published'),output=join(temp,'new-assignments'),bytes=publication(source);
    execFileSync(process.execPath,[join(root,'scripts/prepare-publication.mjs'),source,output]);
    assert.deepEqual(readFileSync(join(output,'S02.json')),bytes);assert.equal(readPublication(output).size,2);
    assert.throws(()=>execFileSync(process.execPath,[join(root,'scripts/prepare-publication.mjs'),source,output],{stdio:'pipe'}));
    assert.deepEqual(readFileSync(join(source,'S02.json')),bytes);
  }finally{rmSync(temp,{recursive:true,force:true});}
});
test('isolated graphics rebuild retains published files byte-for-byte and fails before deleting runtime on invalid publication',()=>{
  const temp=mkdtempSync(join(tmpdir(),'emi-rebuild-')),app=join(temp,'showcase3d');
  try{
    mkdirSync(app);for(const name of ['src','scripts','public'])cpSync(join(root,name),join(app,name),{recursive:true});
    for(const name of ['package.json','index.html'])cpSync(join(root,name),join(app,name));
    symlinkSync(join(root,'node_modules'),join(app,'node_modules'),'dir');
    const student=join(temp,'student/js');mkdirSync(student,{recursive:true});
    for(const name of ['game.js','assignment-rules.js','assignment-validator.js'])cpSync(new URL(`../../student/js/${name}`,import.meta.url),join(student,name));
    const directory=join(app,'dist/assignments'),bytes=publication(directory),manifest=readFileSync(join(directory,'manifest.json'));
    const build=()=>execFileSync(process.execPath,[join(app,'scripts/build.mjs')],{cwd:app,stdio:'pipe'});
    build();build();assert.deepEqual(readFileSync(join(directory,'S02.json')),bytes);assert.deepEqual(readFileSync(join(directory,'manifest.json')),manifest);
    for(const name of ['Start-Showcase.cmd','launch.ps1','serve.py','README.md','THIRD_PARTY.md'])cpSync(join(root,name),join(app,name));
    // Packaging must not sweep arbitrary files from the public runtime root.
    writeFileSync(join(app,'dist/ignored-draft.json'),'TEST ONLY — not an approved publication');
    execFileSync('python',[join(app,'scripts/package.py')],{stdio:'pipe'});
    const archive=join(temp,'test-results/3d-p2/showcase3d-p2-static.zip');
    const contents=JSON.parse(execFileSync('python',['-c',"import json,sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); print(json.dumps({'names':z.namelist(),'unit':z.read('showcase3d/dist/assignments/S02.json').decode()}))",archive],{encoding:'utf8'}));
    assert.equal(contents.names.length,12);assert.ok(!contents.names.some(name=>name.includes('ignored-draft')));assert.equal(contents.unit,bytes.toString());
    const html=readFileSync(join(app,'dist/index.html'));writeFileSync(join(directory,'manifest.json'),'broken');assert.throws(build);
    assert.deepEqual(readFileSync(join(app,'dist/index.html')),html);assert.deepEqual(readFileSync(join(directory,'S02.json')),bytes);
  }finally{rmSync(temp,{recursive:true,force:true});}
});
