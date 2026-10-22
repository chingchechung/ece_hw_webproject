import { move } from '../maze/layout.js';
export class Controller {
  constructor(canvas, reset) {
    this.keys = new Set(); this.pose = { x: 0, z: 0, yaw: 0, pitch: 0 };
    window.addEventListener('keydown', event => {
      if (['INPUT', 'SELECT', 'BUTTON', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      const key = event.key.toLowerCase();
      if ('wasdr'.includes(key) || key.startsWith('arrow')) event.preventDefault();
      if (key === 'r' && !event.repeat) reset();
      this.keys.add(key);
    });
    window.addEventListener('keyup', e => this.keys.delete(e.key.toLowerCase()));
    window.addEventListener('blur', () => this.clear());
    document.addEventListener('visibilitychange', () => this.clear());
    canvas.addEventListener('pointerdown', e => { canvas.focus({ preventScroll: true }); this.drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', e => {
      if (!this.drag || !this.enabled) return;
      this.pose.yaw += (e.clientX - this.drag.x) * 0.004;
      this.pose.pitch = Math.max(-0.65, Math.min(0.65, this.pose.pitch - (e.clientY - this.drag.y) * 0.003));
      this.drag = { x: e.clientX, y: e.clientY };
    });
    for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(event, () => { this.drag = null; });
  }
  clear() { this.keys.clear(); this.drag = null; }
  update(map, dt, camera) {
    if (!this.enabled) return;
    const k = this.keys;
    this.pose.yaw += ((k.has('d') || k.has('arrowright') ? 1 : 0) - (k.has('a') || k.has('arrowleft') ? 1 : 0)) * dt * 1.6;
    const distance = ((k.has('w') || k.has('arrowup') ? 1 : 0) - (k.has('s') || k.has('arrowdown') ? 1 : 0)) * dt * 3.2;
    move(map, this.pose, distance);
    this.apply(camera);
  }
  apply(camera) {
    const p = this.pose;
    camera.position.set(p.x, 1.65, p.z);
    camera.lookAt(p.x + Math.cos(p.yaw), 1.65 + Math.tan(p.pitch), p.z + Math.sin(p.yaw));
  }
}
