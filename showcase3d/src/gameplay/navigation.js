// Cumulative wall-clock allowance belongs to the shared attempt, never a renderer.
export const MAP_ALLOWANCE_MS = 30000;
export function createMapAllowance() { return { remainingMs: MAP_ALLOWANCE_MS, open: false }; }
export function setMapOpen(attempt, open) {
  attempt.map.open = Boolean(open && attempt.map.remainingMs > 0 && !attempt.interaction && !attempt.finished);
  return attempt.map.open;
}
export function consumeMapAllowance(attempt, elapsedMs, visible) {
  if (attempt.map.open && visible && Number.isFinite(elapsedMs) && elapsedMs > 0) {
    attempt.map.remainingMs = Math.max(0, attempt.map.remainingMs - elapsedMs);
    if (!attempt.map.remainingMs) attempt.map.open = false;
  }
  return attempt.map.remainingMs;
}
