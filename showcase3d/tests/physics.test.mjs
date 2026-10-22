import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { generatorSource, runtimeGeneratorSource, sha256 } from '../scripts/export-maze.mjs';
import { generateLayout } from '../src/maze/lite-generated.js';
import { generateMap } from '../src/maze/generate.js';
import { stepDriving, initialVehicle, canDriveStand, chooseDriveHeading } from '../src/gameplay/driving.js';
import { logicalToLite, liteToThree, liteToMeters, metersToLite, virtualSpeedToMeters } from '../src/gameplay/coordinates.js';
import { createAttempt, nearestInteraction, interact, pauseAttempt } from '../src/gameplay/attempt.js';
import { terminalPose } from '../src/maze/layout.js';
import { planRoute, path } from './control-route.mjs';

const sizes = [[25,19], [21,15], [17,13], [13,9]], seeds = [0, 1, 29, 20261022, 20264049, 4294967295];
function reference(map, vehicle) {
  const source = readFileSync(new URL('../../student/js/game.js', import.meta.url), 'utf8');
  const functions = source.slice(source.indexOf('  function driveRoadAt('), source.indexOf('  function worldCenter('))
    + source.slice(source.indexOf('  function chooseDriveHeading('), source.indexOf('  function toggleMode('))
    + source.slice(source.indexOf('  function updateDrive('), source.indexOf('  function lineVisible('));
  const c = vm.createContext({ current: { ...map, player: { x: vehicle.x, y: vehicle.y, walk: vehicle.walk } },
    DRIVE_TILE: 14, DRIVE_SCALE: 12, DRIVE_TOP_SPEED: 590, pressed: {}, driveSpeed: vehicle.speed,
    driveAngle: vehicle.heading, driveDistance: vehicle.distance, el: () => ({}), Math,
    clamp: (v,a,b) => Math.max(a,Math.min(v,b)) });
  vm.runInContext(functions, c);
  return { c, step(input, dt) { c.pressed = input; c.dt = Math.min(dt, .045); vm.runInContext('updateDrive(dt)', c);
    return { x: c.current.player.x, y: c.current.player.y, speed: c.driveSpeed, heading: c.driveAngle,
      distance: c.driveDistance, walk: c.current.player.walk, moving: c.current.player.moving }; } };
}
test('generated runtime boundary is source-identical, reproducible, static code without eval', () => {
  const source = readFileSync(new URL('../src/maze/lite-generated.js', import.meta.url), 'utf8');
  assert.equal(source, runtimeGeneratorSource()); assert.ok(!/\beval\s*\(|new Function/.test(source));
  assert.ok(source.includes(generatorSource()));
});
for (const [w,h] of sizes) test(`${w}x${h}: six seeds exactly match authoritative generator, markers, exit and roads`, () => {
  for (const seed of seeds) {
    const math = Object.create(Math); math.random = () => 0;
    const c = vm.createContext({ Date: { now: () => seed }, Math: math, MAX_QUESTS: 5, seedCounter: 0, TILE: 28, DRIVE_TILE: 14 });
    vm.runInContext(generatorSource() + `\nvar map=generateMaze(${w},${h});buildDriveRoad(map);map.driveRoad.bits=Array.from(map.driveRoad.bits);`, c);
    const expected = JSON.parse(JSON.stringify(c.map)), actual = generateLayout(w,h,seed);
    assert.deepEqual(actual, expected); assert.deepEqual(actual, generateLayout(w,h,seed));
    const attempt = createAttempt(actual);
    for (const c of [...attempt.checkpoints, attempt.exit]) {
      assert.deepEqual(c.position, logicalToLite(c.logical)); assert.deepEqual(c.world, liteToThree(c.position));
      assert.ok(canDriveStand(actual,c.position.x,c.position.y));
    }
    assert.equal(attempt.checkpoints.length,5);
    for(const target of [...actual.stations,actual.exit]) assert.ok(path(actual,{x:1,y:1},target).length>0);
    assert.ok(actual.stations.every(p => Number.isFinite(terminalPose(actual,p).yaw)));
  }
});
test('coordinate units round trip, 12x virtual distance and 590 speed conversion', () => {
  assert.equal(liteToMeters(14),.7); assert.equal(metersToLite(.7),14);
  assert.deepEqual(logicalToLite({x:1,y:1}),{x:84,y:84});
  assert.ok(Math.abs(liteToThree({x:84,y:84}).x-4.2)<1e-12);
  assert.ok(Math.abs(virtualSpeedToMeters(590)-2.4583333333333335)<1e-12);
  for (const n of [-100,0,14,84,2000]) assert.ok(Math.abs(metersToLite(liteToMeters(n))-n)<1e-10);
});
for (const [w,h] of sizes) test(`${w}x${h}: frame-by-frame Lite physics and heading parity across controls/stalls/walls`, () => {
  for (const seed of seeds) {
    const map = generateLayout(w,h,seed); let v = initialVehicle(map); const ref = reference(map,v);
    ref.c.x = v.x; ref.c.y = v.y;
    for (const angle of [0,Math.PI/2,Math.PI,-Math.PI/2]) {
      ref.c.preferred = angle;
      assert.equal(chooseDriveHeading(map,v.x,v.y,angle),vm.runInContext('chooseDriveHeading(x,y,preferred)',ref.c));
    }
    const controls = [{w:true},{w:true,d:true},{},{s:true},{s:true,a:true},{a:true},{d:true},{w:true,a:true},{w:true,s:true},{}];
    for (let i=0;i<1400;i++) {
      const input=controls[Math.floor(i/70)%controls.length],dt=[1/60,1/30,.045,.5][i%4];
      v=stepDriving(map,v,input,dt); const expected=ref.step(input,dt);
      for(const key of Object.keys(expected)) assert.equal(v[key],expected[key],`${seed}/${i}/${key}`);
      assert.ok(canDriveStand(map,v.x,v.y));
    }
  }
});
test('acceleration, coasting, reverse, stationary steering and long delta cannot tunnel', () => {
  const map=generateLayout(25,19,20261022), start=initialVehicle(map);
  const gas=stepDriving(map,start,{w:true},.03); assert.equal(gas.speed,9.6);
  const coast=stepDriving(map,gas,{},.03); assert.ok(coast.speed<gas.speed&&coast.speed>0);
  const brake=stepDriving(map,gas,{s:true},.03); assert.ok(brake.speed<0);
  const turn=stepDriving(map,start,{d:true},.03); assert.equal(turn.heading,start.heading+.084); assert.equal(turn.x,start.x);
  let v={...start,speed:590};for(let i=0;i<500;i++){v=stepDriving(map,v,{w:true},100);assert.ok(canDriveStand(map,v.x,v.y));}
  assert.ok(v.speed<590);assert.ok(Math.hypot(v.x-start.x,v.y-start.y)<map.width*56);
});
test('checkpoint activation range, speed gate, single activation, locked exit, completion and reset', () => {
  const map=generateLayout(13,9,20264049),a=createAttempt(map);
  assert.equal(interact(map,a).status,'outside');
  a.vehicle={...a.vehicle,...a.checkpoints[0].position,speed:26};
  assert.equal(interact(map,a).status,'moving'); assert.equal(a.activations,0);
  a.vehicle.speed=25; assert.equal(interact(map,a).status,'activated');assert.equal(a.completed[0],true);
  assert.equal(interact(map,a).status,'inactive'); a.interaction=null;
  assert.notEqual(nearestInteraction(map,a)?.id,'Q1');
  a.vehicle={...a.vehicle,...a.exit.position,speed:0};assert.equal(interact(map,a).status,'locked');
  for(let i=1;i<5;i++){a.vehicle={...a.vehicle,...a.checkpoints[i].position,speed:0};assert.equal(interact(map,a).status,'activated');a.interaction=null;}
  assert.equal(a.activations,5);a.vehicle={...a.vehicle,...a.exit.position};assert.equal(interact(map,a).status,'activated');assert.equal(a.finished,true);
  pauseAttempt(a);assert.equal(a.vehicle.speed,0);assert.equal(a.vehicle.steer,0);
  const reset=createAttempt(map);assert.ok(reset.completed.every(x=>!x));assert.equal(reset.finished,false);assert.equal(reset.interaction,null);
});
test('a real corner slides on one axis with exactly the approved .65 speed reduction', () => {
  const map=generateLayout(25,19,20261022),{w,h}=map.driveRoad;let found=false;
  for(let y=1;y<h-1&&!found;y++)for(let x=1;x<w-1&&!found;x++){
    const v={...initialVehicle(map),x:x*14+7,y:y*14+7,speed:590,heading:Math.PI/4};
    if(!canDriveStand(map,v.x,v.y))continue;
    const next=stepDriving(map,v,{w:true},.045);
    if(next.speed===590*.65){
      assert.ok((next.x===v.x)!==(next.y===v.y));
      const ref=reference(map,v).step({w:true},.045);
      for(const key of Object.keys(ref))assert.equal(next[key],ref[key]);found=true;
    }
  }
  assert.ok(found,'The collision test must actually exercise a corner slide');
});
test('complete five-checkpoint plan replays only input and time through the actual physics', () => {
  const map=generateMap(13,9,20264049),plan=planRoute(map),a=createAttempt(map);
  for(const step of plan.steps){
    if(step.kind==='drive'){
      const input=Object.fromEntries(step.keys.map(key=>[key,true]));
      for(let remaining=step.seconds;remaining>1e-10;){const dt=Math.min(1/60,remaining);a.vehicle=stepDriving(map,a.vehicle,input,dt);remaining-=dt;assert.ok(canDriveStand(map,a.vehicle.x,a.vehicle.y));}
    }else{assert.equal(nearestInteraction(map,a).id,step.id);assert.equal(interact(map,a).status,'activated');a.interaction=null;}
  }
  assert.deepEqual(a.completed,[true,true,true,true,true]);assert.equal(a.activations,5);assert.equal(a.finished,true);
  assert.ok(a.vehicle.distance>20000);
});
