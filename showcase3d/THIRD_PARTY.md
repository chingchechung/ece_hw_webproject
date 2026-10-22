# Assets and dependencies

- **Three.js 0.180.0**, MIT, https://github.com/mrdoob/three.js. Renderer,
  materials, geometry, PMREM and OrbitControls bundled locally. Its full MIT
  notice is shipped as `dist/LICENSES.txt` and retained in the bundle.
- **esbuild 0.25.12**, MIT, https://github.com/evanw/esbuild. Development-only
  bundler; never required on the presentation computer.
- All laboratory textures, studio environment, screen waveforms, terminal/exit
  geometry, markings and UI are original procedural assets created for this
  repository. No downloaded HDRs, fonts, models, proprietary game images or CDNs.
- Maze layouts derive read-only from the repository's reviewed Lite generator;
  provenance is recorded in `src/maze/maps.json` and `dist/build-info.json`.

No image generation is used for test evidence. Screenshots and navigation video
are captured from the actual Chromium/WebGL 2 application.
