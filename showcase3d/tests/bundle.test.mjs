import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { sha256 } from '../scripts/export-maze.mjs';
const root = fileURLToPath(new URL('../', import.meta.url));
function manifest() { return Object.fromEntries(readdirSync(`${root}/dist`).sort().map(name => [name, sha256(readFileSync(`${root}/dist/${name}`))])); }
test('committed local deployment exactly matches two reproducible source builds', () => {
  const committed = manifest();
  execFileSync(process.execPath, ['scripts/build.mjs'], { cwd: root });
  assert.deepEqual(manifest(), committed, 'Regenerate and commit dist after source edits');
  execFileSync(process.execPath, ['scripts/build.mjs'], { cwd: root });
  assert.deepEqual(manifest(), committed);
});
test('entry resources are relative and complete; no CDN imports or fetches', () => {
  const html = readFileSync(`${root}/dist/index.html`, 'utf8');
  for (const match of html.matchAll(/(?:src|href)="(\.[^"]+)"/g)) {
    assert.ok(readdirSync(`${root}/dist`).includes(match[1].slice(2)));
  }
  assert.ok(!/https?:\/\//.test(html));
  for (const name of readdirSync(`${root}/dist`).filter(n => /\.(js|css)$/.test(n))) {
    const text = readFileSync(`${root}/dist/${name}`, 'utf8');
    assert.ok(!/(?:import\s*\(|from\s*)["']https?:|url\(["']?https?:|fetch\(["']https?:/.test(text));
    if (name.endsWith('.js')) assert.equal(text.split('03cd7fe5e60aec7d9cb47a799a8facfd73e4e3137602f5fd4edadb73b34ea564').length-1,1,'Bundle must embed the fixed maze data once');
  }
  const lock = JSON.parse(readFileSync(`${root}/package-lock.json`));
  assert.equal(lock.packages['node_modules/three'].version, '0.180.0');
  assert.equal(lock.packages['node_modules/esbuild'].version, '0.25.12');
});
test('venue launcher and packaging serve/include only the standalone dist allowlist', () => {
  const ps = readFileSync(`${root}/launch.ps1`, 'utf8'), pack = readFileSync(`${root}/scripts/package.py`, 'utf8');
  assert.match(ps, /IPAddress\]::Loopback/); assert.match(ps, /Join-Path \$PSScriptRoot 'dist'/);
  assert.match(ps, /OrdinalIgnoreCase/); assert.match(ps, /403 Forbidden/);
  assert.ok(!/node|npm|teacher_data|assignments/i.test(ps.replace(/^#.*$/gm, '')));
  assert.ok(!/rglob|teacher_data|export\/|node_modules/.test(pack));
});
