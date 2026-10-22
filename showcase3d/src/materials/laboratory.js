import * as THREE from 'three';

function noise(x, y) {
  let n = Math.imul(x + 37, 374761393) ^ Math.imul(y + 71, 668265263);
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}
function surface(size, floor, anisotropy) {
  const canvases = Array.from({ length: 3 }, () => Object.assign(document.createElement('canvas'), { width: size, height: size }));
  const contexts = canvases.map(c => c.getContext('2d'));
  const images = contexts.map(c => c.createImageData(size, size));
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const u = x / size, v = y / size, i = (y * size + x) * 4;
    const grain = (noise(x, y) - 0.5) * (floor ? 14 : 4);
    const clouds = Math.sin(u * 20 + Math.sin(v * 13)) * Math.cos(v * 21) * (floor ? 3 : 0.8);
    const seam = floor ? Math.min(u, v, 1 - u, 1 - v) < 0.007
      : u < 0.009 || u > 0.991 || Math.abs(v - 0.18) < 0.004 || Math.abs(v - 0.83) < 0.004;
    const lower = !floor && v > 0.83;
    const base = floor ? [112, 124, 129] : lower ? [61, 78, 87] : [154, 165, 168];
    const fastener = !floor && [0.04, 0.96].some(a => Math.hypot(u - a, v - 0.22) < 0.008);
    for (let c = 0; c < 3; c++) images[0].data[i + c] = seam ? base[c] * 0.48 : fastener ? 50 : base[c] + grain + clouds;
    // Tangent normal map: small grain and a recessed seam, not painted lighting.
    images[1].data[i] = 128 + (noise(x + 1, y) - noise(x - 1, y)) * (floor ? 13 : 4);
    images[1].data[i + 1] = seam ? 110 : 128 + Math.sin(v * size * 1.1) * (floor ? 2 : 1);
    images[1].data[i + 2] = 254;
    images[2].data[i] = seam ? 145 : 255; // AO
    images[2].data[i + 1] = floor ? 204 + grain : lower ? 155 : 134 + grain; // roughness
    images[2].data[i + 2] = floor ? 18 : lower ? 150 : 105; // metalness
    images.forEach(image => { image.data[i + 3] = 255; });
  }
  return canvases.map((canvas, i) => {
    contexts[i].putImageData(images[i], 0, 0);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = i === 0 ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.anisotropy = anisotropy;
    return texture;
  });
}
export function createMaterials(preset, maxAnisotropy) {
  const textures = [], anisotropy = Math.min(maxAnisotropy, preset.anisotropy);
  function pbr(floor) {
    const [map, normalMap, orm] = surface(preset.texture, floor, anisotropy);
    textures.push(map, normalMap, orm);
    return new THREE.MeshStandardMaterial({ map, normalMap, aoMap: orm, roughnessMap: orm, metalnessMap: orm,
      roughness: 1, metalness: 1, normalScale: new THREE.Vector2(0.7, 0.7), envMapIntensity: floor ? 0.55 : 0.85 });
  }
  const materials = {
    wall: pbr(false), floor: pbr(true),
    dark: new THREE.MeshStandardMaterial({ color: '#263a46', roughness: 0.62, metalness: 0.55 }),
    top: new THREE.MeshStandardMaterial({ color: '#8d9da3', roughness: 0.65, metalness: 0.35 }),
    ceiling: new THREE.MeshStandardMaterial({ color: '#829194', roughness: 0.85, side: THREE.DoubleSide }),
    light: new THREE.MeshStandardMaterial({ color: '#e5f5f4', emissive: '#d2f6ef', emissiveIntensity: 1.8 }),
    accent: new THREE.MeshStandardMaterial({ color: '#477b83', roughness: 0.45, metalness: 0.4 }),
    gold: new THREE.MeshStandardMaterial({ color: '#cfaa60', roughness: 0.65, metalness: 0.2 }),
    exit: new THREE.MeshStandardMaterial({ color: '#aac3b3', emissive: '#35775d', emissiveIntensity: 0.4, roughness: 0.6 })
  };
  return { materials, textures, estimatedTextureBytes: 6 * preset.texture ** 2 * 4 * 4 / 3,
    dispose() { textures.forEach(t => t.dispose()); Object.values(materials).forEach(m => m.dispose()); } };
}
export function studioEnvironment(renderer) {
  const canvas = Object.assign(document.createElement('canvas'), { width: 512, height: 256 });
  const g = canvas.getContext('2d'), gradient = g.createLinearGradient(0, 0, 0, 256);
  gradient.addColorStop(0, '#d6e5e6'); gradient.addColorStop(0.48, '#7f9ca7');
  gradient.addColorStop(0.52, '#344b57'); gradient.addColorStop(1, '#26313b');
  g.fillStyle = gradient; g.fillRect(0, 0, 512, 256);
  g.fillStyle = '#f6faf5';
  [24, 155, 286, 417].forEach(x => g.fillRect(x, 35, 40, 33));
  const input = new THREE.CanvasTexture(canvas);
  input.mapping = THREE.EquirectangularReflectionMapping; input.colorSpace = THREE.SRGBColorSpace;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const target = pmrem.fromEquirectangular(input);
  input.dispose(); pmrem.dispose();
  return target;
}
