import { initialVehicle, rayDistance } from './driving.js';
import { logicalToLite, liteToThree } from './coordinates.js';
export const INTERACTION_RANGE = 70; // Lite drive-mode range, world pixels (3.5 m).
export const INTERACTION_SPEED = 25; // Lite's virtual-speed gate, <=25 accepted.
export function createAttempt(map) {
  return { vehicle: initialVehicle(map), completed: Array(5).fill(false), finished: false,
    interaction: null, activations: 0, checkpoints: map.stations.map((logical, index) => {
      const position = logicalToLite(logical);
      return { id: `Q${index+1}`, label: `LAB ${String(index+1).padStart(2, '0')}`, logical: { ...logical }, position, world: liteToThree(position) };
    }), exit: { logical: { ...map.exit }, position: logicalToLite(map.exit), world: liteToThree(logicalToLite(map.exit)) } };
}
export function pauseAttempt(attempt) {
  attempt.vehicle = { ...attempt.vehicle, speed: 0, moving: false, steer: 0 };
}
export function nearestInteraction(map, attempt) {
  if (attempt.finished) return null;
  const p = attempt.vehicle; let best = INTERACTION_RANGE, nearest = null;
  const consider = (position, candidate) => {
    const distance = Math.hypot(position.x-p.x, position.y-p.y);
    if (distance >= best) return;
    // Prevent a nearby marker across a wall from offering an activation.
    if (rayDistance(map, p.x, p.y, Math.atan2(position.y-p.y, position.x-p.x), distance + 0.01) + 0.01 < distance) return;
    best = distance; nearest = { ...candidate, distance };
  };
  attempt.checkpoints.forEach((c, index) => { if (!attempt.completed[index]) consider(c.position, { type: 'checkpoint', index, id: c.id, label: c.label }); });
  consider(attempt.exit.position, { type: 'finish', id: 'EXIT', label: 'Exit' });
  return nearest;
}
export function interact(map, attempt) {
  if (attempt.interaction || attempt.finished) return { status: 'inactive' };
  const near = nearestInteraction(map, attempt);
  if (!near) return { status: 'outside' };
  if (Math.abs(attempt.vehicle.speed) > INTERACTION_SPEED) return { status: 'moving', ...near };
  if (near.type === 'finish' && !attempt.completed.every(Boolean)) return { status: 'locked', ...near };
  pauseAttempt(attempt);
  if (near.type === 'checkpoint') { attempt.completed[near.index] = true; attempt.activations++; }
  else attempt.finished = true;
  attempt.interaction = { ...near };
  return { status: 'activated', ...near };
}
