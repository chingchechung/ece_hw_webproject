export const PRESETS = {
  Low: { scale: 0.7, width: 1280, height: 720, texture: 128, anisotropy: 1, shadow: 0 },
  Medium: { scale: 0.85, width: 1600, height: 900, texture: 256, anisotropy: 4, shadow: 512 },
  High: { scale: 1, width: 1920, height: 1080, texture: 512, anisotropy: 8, shadow: 1024 }
};
export function resolution(width, height, preset, override = null) {
  const p = PRESETS[preset];
  // Deliberately do NOT multiply by devicePixelRatio. UI retains native CSS sizing.
  const scale = Math.min(override || p.scale, p.width / width, p.height / height);
  return { width: Math.max(1, Math.floor(width * scale)), height: Math.max(1, Math.floor(height * scale)), scale };
}
export function summarize(values) {
  if (!values.length) return { mean: null, p95: null };
  const sorted = [...values].sort((a, b) => a - b);
  return { mean: values.reduce((a, b) => a + b, 0) / values.length,
    p95: sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * 0.95) - 1)] };
}
