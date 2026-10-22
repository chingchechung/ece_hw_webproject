import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { AssignmentValidator as V, AssignmentRules } from '../src/assignments/validator.js';
import original from '../../student/js/assignment-validator.js';
import { PublishedAssignments } from '../src/assignments/loader.js';
import { generatorSource } from '../scripts/export-maze.mjs';
import { generateMap } from '../src/maze/generate.js';
import { generateLayout } from '../src/maze/lite-generated.js';
import { createAttempt, interact, answerQuestion, attemptSize } from '../src/gameplay/attempt.js';
const fixture=name=>JSON.parse(readFileSync(new URL(`../../tests/fixtures/${name}`,import.meta.url)));
const clone=value=>JSON.parse(JSON.stringify(value));
const browser=vm.createContext({});
for(const name of ['assignment-rules.js','assignment-validator.js'])vm.runInContext(readFileSync(new URL(`../../student/js/${name}`,import.meta.url),'utf8'),browser);
const B=browser.AssignmentValidator;
test('adapter uses the actual Lite validator/rules; v1/v2 normalizers, validation and answer outcomes match browser UMD',()=>{
  assert.equal(V,original);assert.equal(typeof AssignmentRules.youtubeUrl,'string');
  for(const name of ['S01.json','S02.json','v2/S01.json','v2/S02.json']){
    const base=fixture(name),file=`${base.unitId}.json`;
    const cases=[base,null,{}, {...base,schemaVersion:3}, {...base,unknown:'no'}, {...base,unitId:'S13'}, {...base,googleFormUrl:'javascript:alert(1)'}];
    for(const mutate of [q=>q.options.pop(),q=>q.options.push('extra'),q=>q.id='Q02',q=>q.questionVideoUrl='https://youtu.be/XXXXXXXXXXX',q=>q.options[0]=' ',q=>q.correctOptions=[],q=>q.correctOptions=['A','A'],q=>q.correctOptions=['D'],q=>q.correctOption='A']){
      const data=clone(base);mutate(data.questions[0]);cases.push(data);
    }
    for(const data of cases){assert.deepEqual(V.validateUnit(data,file),clone(B.validateUnit(data,file)));assert.deepEqual(V.normalizeUnit(data),clone(B.normalizeUnit(data)));}
    for(const q of base.questions)for(const selected of ['A','B','C','D','a','AB',['A','B'],null,3])assert.equal(V.acceptsAnswer(q,selected),B.acceptsAnswer(q,selected));
    const padded=clone(base);padded.title=`  ${padded.title}  `;padded.questions[0].options[0]=' trim me ';
    assert.deepEqual(V.normalizeUnit(padded),clone(B.normalizeUnit(padded)));
  }
});
test('manifest validation/normalization parity covers empty, duplicate, unlisted-id and remote/path filenames',()=>{
  const base=fixture('manifest.json');
  for(const value of [base,{schemaVersion:1,units:[]},null,{...base,schemaVersion:2}, {...base,units:[base.units[0],base.units[0]]},
    {schemaVersion:1,units:[{unitId:'S13',title:'Test',file:'S13.json'}]},
    ...['../S01.json','https://example.test/S01.json','S02.json'].map(file=>({schemaVersion:1,units:[{unitId:'S01',title:' test ',file}]}))]){
    assert.deepEqual(V.validateManifest(value),clone(B.validateManifest(value)));assert.deepEqual(V.normalizeManifest(value),clone(B.normalizeManifest(value)));
  }
});
for(const [w,h] of [[25,19],[21,15],[17,13],[13,9]])test(`${w}x${h}: exact authoritative generator output for four/five stations and five seeds`,()=>{
  for(const count of [4,5])for(const seed of [0,1,29,20264049,4294967295]){
    const math=Object.create(Math);math.random=()=>0;
    const context=vm.createContext({Date:{now:()=>seed},Math:math,MAX_QUESTS:count,seedCounter:0,TILE:28,DRIVE_TILE:14});
    vm.runInContext(generatorSource()+`\nvar result=generateMaze(${w},${h});buildDriveRoad(result);result.driveRoad.bits=Array.from(result.driveRoad.bits);`,context);
    const actual=generateLayout(w,h,seed,count);assert.deepEqual(actual,clone(context.result));assert.equal(actual.stations.length,count);
    assert.equal(new Set(actual.stations.map(s=>`${s.x},${s.y}`)).size,count);
  }
});
test('educational E opens without completion; any accepted single label passes exactly once, with no phantom checkpoint',()=>{
  for(const name of ['S01.json','v2/S02.json']){
    const unit=fixture(name),map=generateMap(13,9,20264049,unit.questions.length),a=createAttempt(map,unit);
    assert.equal(a.completed.length,unit.questions.length);assert.deepEqual(a.checkpoints.map(c=>c.id),unit.questions.map(q=>q.id));
    a.vehicle={...a.vehicle,...a.checkpoints[0].position};assert.equal(interact(map,a).status,'question');assert.equal(a.activations,0);
    a.interaction=null;assert.equal(a.completed[0],false);assert.equal(interact(map,a).status,'question');
    assert.equal(answerQuestion(a,unit,['A','B']).status,'invalid');assert.equal(a.failures,0);
    const label=unit.questions[0].correctOptions?.at(-1)??unit.questions[0].correctOption;
    assert.equal(answerQuestion(a,unit,label).status,'correct');assert.equal(a.activations,1);assert.equal(a.completed[0],true);
    assert.equal(answerQuestion(a,unit,label).status,'inactive');a.interaction=null;assert.notEqual(interact(map,a).status,'question');
    a.vehicle={...a.vehicle,...a.exit.position};assert.equal(interact(map,a).status,'locked');
  }
});
test('wrong answers use original size progression and fresh shared attempts; restarting returns to full size',()=>{
  const unit=fixture('S01.json');
  for(let failures=0;failures<6;failures++){
    const size=attemptSize(failures),map=generateMap(...size,100+failures,4),a=createAttempt(map,unit,failures);
    a.completed[1]=true;a.map.remainingMs=1;a.vehicle={...a.vehicle,...a.checkpoints[0].position};interact(map,a);
    const wrong=answerQuestion(a,unit,'D');assert.equal(wrong.status,'wrong');assert.equal(wrong.failures,failures+1);
    assert.deepEqual(wrong.size,[[21,15],[17,13],[13,9]][Math.min(failures,2)]);
    const next=createAttempt(generateMap(...wrong.size,200+failures,4),unit,wrong.failures);
    assert.deepEqual(next.completed,[false,false,false,false]);assert.equal(next.map.remainingMs,30000);assert.equal(next.unitId,unit.unitId);assert.equal(next.vehicle.distance,0);
  }
  assert.deepEqual(attemptSize(0),[25,19]);
});
test('allowlist loader resolves static nested paths, no-store, exact v2 arrays and refuses unlisted requests',async()=>{
  const unit=fixture('v2/S02.json'),calls=[];
  const fetcher=async(url,options)=>{calls.push({url:String(url),options});return {ok:true,json:async()=>String(url).endsWith('manifest.json')?{schemaVersion:1,units:[{unitId:'S02',title:'Test',file:'S02.json'}]}:unit};};
  const loader=new PublishedAssignments('https://example.test/~course/3d/assignments/',fetcher);
  await loader.refresh();const loaded=await loader.load('S02');assert.deepEqual(loaded.questions[1].correctOptions,['B','C']);
  assert.equal(calls[1].url,'https://example.test/~course/3d/assignments/S02.json');assert.equal(calls[0].options.cache,'no-store');
  await assert.rejects(loader.load('S01'),/not listed/);assert.equal(calls.length,2);
});
test('loader rejects malformed/missing/unsupported data and clears invalid refreshed allowlists',async()=>{
  const cases=[{ok:false,status:404}, {ok:true,json:async()=>{throw new SyntaxError('bad')}}, {ok:true,json:async()=>({schemaVersion:99,units:[]})}];
  for(const response of cases){const l=new PublishedAssignments('https://example.test/a/',async()=>response);await assert.rejects(l.refresh());assert.deepEqual(l.units,[]);}
  const l=new PublishedAssignments('https://example.test/a/',async url=>({ok:true,json:async()=>String(url).endsWith('manifest.json')?fixture('manifest.json'):{schemaVersion:55}}));
  await l.refresh();await assert.rejects(l.load('S01'),/schemaVersion/);
});
test('cancelled and superseded responses cannot commit, even if a fetcher ignores abort',async()=>{
  let resolve;let delayed=false;
  const loader=new PublishedAssignments('https://example.test/a/',async url=>{
    if(delayed)return new Promise(r=>{resolve=r;});
    return {ok:true,json:async()=>fixture('manifest.json')};
  });
  await loader.refresh();delayed=true;const pending=loader.load('S01');loader.cancel();resolve({ok:true,json:async()=>fixture('S01.json')});assert.equal(await pending,null);
  delayed=true;const stale=loader.refresh();delayed=false;await loader.refresh();resolve({ok:true,json:async()=>({schemaVersion:1,units:[]})});assert.equal(await stale,null);assert.equal(loader.units.length,2);
});
