import { summarize } from './quality.js';
export class Metrics {
  constructor(renderer) {
    this.renderer = renderer;
    this.gl = renderer.getContext();
    const gl = this.gl, debug = gl.getExtension('WEBGL_debug_renderer_info');
    this.identity = { version: gl.getParameter(gl.VERSION), vendor: debug ? gl.getParameter(debug.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
      renderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER) };
    this.identity.classification = /swiftshader|llvmpipe|software/i.test(this.identity.renderer) ? 'Software / Cloud functional check' : 'Reported renderer; hardware results require device review';
    this.extension = gl.getExtension('EXT_disjoint_timer_query_webgl2');
    this.pending = []; this.frames = []; this.cpu = []; this.gpu = []; this.last = null;
  }
  begin(now) {
    if (this.last !== null) this.frames.push(now - this.last);
    this.last = now; this.started = performance.now();
    const gl = this.gl;
    if (this.extension && this.pending.length < 4) {
      this.active = gl.createQuery(); gl.beginQuery(this.extension.TIME_ELAPSED_EXT, this.active);
    }
  }
  end() {
    this.cpu.push(performance.now() - this.started);
    const gl = this.gl;
    if (this.active) { gl.endQuery(this.extension.TIME_ELAPSED_EXT); this.pending.push(this.active); this.active = null; }
    const disjoint = this.extension && gl.getParameter(this.extension.GPU_DISJOINT_EXT);
    while (this.pending.length && gl.getQueryParameter(this.pending[0], gl.QUERY_RESULT_AVAILABLE)) {
      const q = this.pending.shift();
      if (!disjoint) this.gpu.push(gl.getQueryParameter(q, gl.QUERY_RESULT) / 1e6);
      gl.deleteQuery(q);
    }
    if (disjoint) this.gpu = [];
    for (const samples of [this.frames, this.cpu, this.gpu]) if (samples.length > 240) samples.splice(0, samples.length - 240);
  }
  reset() {
    this.pending.forEach(query => this.gl.deleteQuery(query)); this.pending = [];
    this.frames = []; this.cpu = []; this.gpu = []; this.last = null;
  }
  snapshot() {
    const frame = summarize(this.frames);
    return { frameIntervalMs: frame, fps: frame.mean ? 1000 / frame.mean : null,
      cpuSubmissionMs: summarize(this.cpu), gpuExecutionMs: summarize(this.gpu),
      gpuTimer: this.extension ? 'Asynchronous WebGL timer query; discard disjoint samples' : 'Unavailable; CPU submission is NOT GPU time',
      samples: this.frames.length, identity: this.identity };
  }
  dispose() { this.pending.forEach(q => this.gl.deleteQuery(q)); this.pending = []; }
}
