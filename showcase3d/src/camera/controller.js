import { liteToThree } from '../gameplay/coordinates.js';

// Input/camera adapter only. Vehicle equations live in the pure gameplay module.
export class Controller {
  constructor(canvas, callbacks) {
    this.keys = new Set(); this.pose = { x: 0, z: 0, yaw: 0, pitch: 0 }; this.pitch = 0;
    this.driving = true;
    window.addEventListener('keydown', event => {
      const key = event.key.toLowerCase();
      if (key === 'escape') { callbacks.close(); return; }
      if (event.ctrlKey || event.metaKey || event.altKey || ['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)) return;
      if (key === 'r' && !event.repeat) { event.preventDefault(); callbacks.reset(); return; }
      if (document.activeElement.tagName === 'BUTTON') return;
      if (['w','a','s','d','r','e','arrowup','arrowdown','arrowleft','arrowright'].includes(key)) event.preventDefault();
      if (!callbacks.canDrive()) return;
      if (key === 'e') { if (!event.repeat) callbacks.interact(); return; }
      this.keys.add(key);
    });
    window.addEventListener('keyup', e => this.keys.delete(e.key.toLowerCase()));
    const release = () => { this.clear(); callbacks.pause(); };
    window.addEventListener('blur', release);
    document.addEventListener('visibilitychange', () => { if (document.hidden) release(); });
    canvas.addEventListener('pointerdown', e => {
      canvas.focus({ preventScroll: true }); this.drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove', e => {
      if (!this.drag || !this.enabled) return;
      const pitch = Math.max(-.65,Math.min(.65,(this.driving ? this.pitch : this.pose.pitch)-(e.clientY-this.drag.y)*.003));
      if (this.driving) this.pitch = pitch;
      else { this.pose.pitch = pitch; this.pose.yaw += (e.clientX-this.drag.x)*.004; }
      this.drag = { x: e.clientX, y: e.clientY };
    });
    for (const event of ['pointerup','pointercancel','lostpointercapture']) canvas.addEventListener(event, () => { this.drag = null; });
  }
  clear() { this.keys.clear(); this.drag = null; }
  input() { return Object.fromEntries([...this.keys].map(key => [key,true])); }
  follow(vehicle, camera) {
    this.pose = { ...liteToThree(vehicle), yaw: vehicle.heading, pitch: this.pitch }; this.apply(camera);
  }
  apply(camera) {
    const p = this.pose;
    camera.position.set(p.x,1.65,p.z);
    camera.lookAt(p.x+Math.cos(p.yaw),1.65+Math.tan(p.pitch),p.z+Math.sin(p.yaw));
  }
}
