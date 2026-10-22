import test from 'node:test';
import assert from 'node:assert/strict';
import { generateMap } from '../src/maze/generate.js';
import { createAttempt, pauseAttempt, interact } from '../src/gameplay/attempt.js';
import { setMapOpen, consumeMapAllowance, MAP_ALLOWANCE_MS } from '../src/gameplay/navigation.js';
import { mapCamera, projectMap, mapMarkers, MAP_ZOOMS } from '../src/scene/map2d.js';
import { terminalPose } from '../src/maze/layout.js';
import { liteToThree } from '../src/gameplay/coordinates.js';

test('full map has one cumulative 30-second allowance, independent of openings and pause', () => {
  const a=createAttempt(generateMap(13,9,1)); const vehicle={...a.vehicle};
  assert.equal(a.map.remainingMs,MAP_ALLOWANCE_MS); assert.equal(setMapOpen(a,true),true);
  consumeMapAllowance(a,4321,true);setMapOpen(a,false);consumeMapAllowance(a,90000,true);
  assert.equal(a.map.remainingMs,25679);
  setMapOpen(a,true);consumeMapAllowance(a,1000,true);pauseAttempt(a);
  assert.equal(a.map.remainingMs,24679);assert.deepEqual(a.vehicle,vehicle);
  consumeMapAllowance(a,100000,false);assert.equal(a.map.remainingMs,24679);
  consumeMapAllowance(a,50000,true);assert.equal(a.map.remainingMs,0);assert.equal(a.map.open,false);
  assert.equal(setMapOpen(a,true),false);assert.deepEqual(a.vehicle,vehicle);
});
test('invalid or hidden elapsed time cannot consume/refill the allowance', () => {
  const a=createAttempt(generateMap(13,9,1));setMapOpen(a,true);
  for(const elapsed of [-1,NaN,Infinity,-Infinity,0])consumeMapAllowance(a,elapsed,true);
  consumeMapAllowance(a,999999,false);assert.equal(a.map.remainingMs,30000);
  consumeMapAllowance(a,1.25,true);assert.equal(a.map.remainingMs,29998.75);
});
test('only a new attempt restores budget; dialogs/finished state prevent opening', () => {
  const map=generateMap(13,9,1),a=createAttempt(map);setMapOpen(a,true);consumeMapAllowance(a,12345,true);
  setMapOpen(a,false);a.interaction={id:'Q1'};assert.equal(setMapOpen(a,true),false);
  a.interaction=null;a.finished=true;assert.equal(setMapOpen(a,true),false);
  assert.equal(a.map.remainingMs,17655);assert.deepEqual(createAttempt(map).map,{open:false,remainingMs:30000});
});
for(const [w,h] of [[25,19],[21,15],[17,13],[13,9]])test(`${w}x${h}: authoritative markers/terminal anchors, camera/zoom and local-map bounds`,()=>{
  for(const seed of [0,1,20264049,4294967295]){
    const map=generateMap(w,h,seed),a=createAttempt(map),markers=mapMarkers(a);
    assert.equal(markers.length,6);assert.equal(new Set(markers.map(m=>m.id)).size,6);
    a.checkpoints.forEach((c,i)=>{
      assert.deepEqual(markers[i].position,c.position);assert.deepEqual(liteToThree(markers[i].position),c.world);
      const terminal=terminalPose(map,c.logical);
      assert.ok(Math.abs(terminal.x-terminal.dx*1.25-c.world.x)<1e-12);
      assert.ok(Math.abs(terminal.z-terminal.dz*1.25-c.world.z)<1e-12);
    });
    for(const [width,height] of [[1280,540],[1366,510],[1920,820]])for(const zoom of MAP_ZOOMS){
      const p={x:map.driveRoad.w*7,y:map.driveRoad.h*7};
      const c=mapCamera(map,p,width,height,zoom),projected=projectMap(c,p);
      assert.equal(projected.x,width/2);assert.equal(projected.y,height/2);
      assert.ok(width/c.scale<c.worldWidth*.5);assert.ok(height/c.scale<c.worldHeight*.5);
      const step=projectMap(c,{x:p.x+14,y:p.y+14});assert.ok(Math.abs((step.x-projected.x)-(step.y-projected.y))<1e-9);
      const full=mapCamera(map,p,width,height,zoom,true),origin=projectMap(full,{x:0,y:0}),end=projectMap(full,{x:full.worldWidth,y:full.worldHeight});
      assert.ok(origin.x>=47 && origin.y>=89 && end.x<=width-47 && end.y<=height-89);
      const edge=projectMap(mapCamera(map,a.vehicle,width,height,zoom),a.vehicle);assert.ok(edge.x>=0&&edge.y>=0);
    }
  }
});
test('2D marker state is derived from shared activation and cannot duplicate or reveal questions',()=>{
  const map=generateMap(13,9,20264049),a=createAttempt(map);
  const before=mapMarkers(a);assert.equal(before[0].completed,false);assert.equal(before[5].unlocked,false);
  // Unit fixture positioning only; accepted browser routes use real keyboard driving.
  a.vehicle={...a.vehicle,...a.checkpoints[0].position};assert.equal(interact(map,a).status,'activated');
  const after=mapMarkers(a);assert.equal(after[0].completed,true);assert.equal(after.length,6);
  assert.equal(a.activations,1);assert.equal(interact(map,a).status,'inactive');
  a.completed.fill(true);assert.equal(mapMarkers(a)[5].unlocked,true);
  assert.ok(!JSON.stringify(after).includes('correctOption'));
  after[0].position.x=999;assert.notEqual(a.checkpoints[0].position.x,999);
});
