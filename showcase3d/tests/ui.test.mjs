import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { toolFlags, toolPolicy, playerUrl } from '../src/ui/modes.js';
import { sha256 } from '../scripts/export-maze.mjs';

test('tools require explicit opt-in and leaving tools retains the deployment path and unrelated URL fields', () => {
  const url='https://example.test/~course/maze/index.html?unit=S01&presenter=1&debug=1&testClock=1#view';
  assert.deepEqual(toolFlags(url),{presenter:true,debug:true});
  assert.equal(playerUrl(url).href,'https://example.test/~course/maze/index.html?unit=S01&testClock=1#view');
  for(const query of ['', '?presenter=0&debug=0','?presenter=true&debug=true','?presenter=&debug='])
    assert.deepEqual(toolFlags('https://example.test/maze/'+query),{presenter:false,debug:false});
});
test('every presenter/debug combination is disabled by the educational state independently of the URL', () => {
  for(const presenter of [false,true])for(const debug of [false,true]){
    const flags={presenter,debug};
    assert.deepEqual(toolPolicy(flags,false),flags);
    assert.deepEqual(toolPolicy(flags,true),{presenter:false,debug:false});
  }
});
test('approved P2 graphics, lighting, camera, car, physics, generation and assignment components remain byte-identical', () => {
  const base=JSON.parse(readFileSync(new URL('./fixtures/p2-preservation.json',import.meta.url)));
  assert.equal(base.baseline,'8a9061f0128813700b6a2ca179358b8c27e56447');
  for(const [name,hash] of Object.entries(base.files))assert.equal(sha256(readFileSync(new URL('../'+name,import.meta.url))),hash,name);
  const main=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
  assert.equal(sha256(main.slice(main.indexOf('function configureLighting()'),main.indexOf('function rebuild()'))),base.main_sections.lighting);
  assert.equal(sha256(main.slice(main.indexOf('  renderer = new THREE.WebGLRenderer'),main.indexOf('  map2d = new Map2D'))),base.main_sections.renderer_camera);
});
