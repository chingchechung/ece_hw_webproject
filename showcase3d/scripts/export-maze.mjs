// Read-only bridge: execute the approved Lite generator, never a second algorithm.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import vm from 'node:vm';

export const baseline = '823786bc01b68901455061d5fe31d6076c61f20e';
export const sha256 = value => createHash('sha256').update(value).digest('hex');
export function generatorSource() {
  const source = readFileSync(new URL('../../student/js/game.js', import.meta.url), 'utf8');
  const start = source.indexOf('  function randomizer(');
  const end = source.indexOf('  function driveRoadAt(');
  if (start < 0 || end < start) throw new Error('Reviewed Lite adapter boundaries changed');
  return source.slice(start, end);
}
export function exportMaps() {
  const generator = generatorSource();
  const maps = [[25, 19], [21, 15], [17, 13], [13, 9]].map(([w, h], index) => {
    const seed = 20261022 + index * 1009;
    const fixedMath = Object.create(Math);
    fixedMath.random = () => 0;
    const context = vm.createContext({ Math: fixedMath, Date: { now: () => seed },
      MAX_QUESTS: 5, seedCounter: 0, TILE: 28, DRIVE_TILE: 14 });
    vm.runInContext(generator + `\nvar result=generateMaze(${w},${h});buildDriveRoad(result);`, context,
      { timeout: 1000 });
    context.result.driveRoad.bits = Array.from(context.result.driveRoad.bits);
    const result = JSON.parse(JSON.stringify(context.result));
    return { ...result, seed, id: `${w}x${h}`, topologyHash: sha256(JSON.stringify(result)) };
  });
  return { baseline, generatorHash: sha256(generator), maps };
}
export function runtimeGeneratorSource() {
  const generator = generatorSource();
  if (sha256(generator) !== '03cd7fe5e60aec7d9cb47a799a8facfd73e4e3137602f5fd4edadb73b34ea564') throw new Error('Reviewed generator changed');
  return `// GENERATED read-only from lite-v1.0 student/js/game.js. Do not edit.\n// Source SHA256: ${sha256(generator)}\nexport function generateLayout(w,h,seed,questionCount=5){\n` +
    `if(![[25,19],[21,15],[17,13],[13,9]].some(s=>s[0]===w&&s[1]===h)||!Number.isInteger(seed)||seed<0||seed>4294967295||![4,5].includes(questionCount))throw new Error('Invalid maze size, uint32 seed or question count');\n` +
    `var Date={now:()=>seed},Math=Object.create(globalThis.Math);Math.random=()=>0;var MAX_QUESTS=questionCount,seedCounter=0,TILE=28,DRIVE_TILE=14;\n` + generator +
    `\nvar result=generateMaze(w,h);buildDriveRoad(result);result.driveRoad.bits=Array.from(result.driveRoad.bits);return result;\n}\n`;
}
