import fixed from './maps.json' with { type: 'json' };
import { generateLayout } from './lite-generated.js';
export function generateMap(width, height, seed) {
  const approved = fixed.maps.find(map => map.width === width && map.height === height && map.seed === seed);
  if (approved) return approved;
  const result = generateLayout(width, height, seed);
  // Diagnostic identity only, NOT a security digest; fixed P0 maps retain SHA256.
  const text = JSON.stringify(result); let hash = 2166136261;
  for (let i = 0; i < text.length; i++) hash = Math.imul(hash ^ text.charCodeAt(i), 16777619) >>> 0;
  return { ...result, seed, id: `${width}x${height}`, topologyHash: `fnv1a-${hash.toString(16).padStart(8, '0')}` };
}
