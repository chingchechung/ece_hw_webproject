// Read-only bridge: execute the approved Lite generator, never a second algorithm.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import vm from 'node:vm';

export const baseline = '823786bc01b68901455061d5fe31d6076c61f20e';
export const sha256 = value => createHash('sha256').update(value).digest('hex');
export function exportMaps() {
  const source = readFileSync(new URL('../../student/js/game.js', import.meta.url), 'utf8');
  const start = source.indexOf('  function randomizer(');
  const end = source.indexOf('  function driveRoadAt(');
  if (start < 0 || end < start) throw new Error('Reviewed Lite adapter boundaries changed');
  const generator = source.slice(start, end);
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
