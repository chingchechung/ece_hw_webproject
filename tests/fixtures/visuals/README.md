# Synthetic visual comparison support

`phase-5a-renderer.js` is the original procedural artwork renderer from reviewed
commit `bc7c3fcce84c8c093355c301beb95418e31af9a4`. It contains no assignment data.
SHA-256: `fee5cbe020767406b13b7b77df89390773c61e16e01e6eddd31f274e166dc1d8`.

The refinement browser suite substitutes it in test HTTP responses for paired
performance/lighting comparisons. Keep this fixed baseline out of `student/`;
it is never deployed. The original Phase 4 comparison still uses the immutable
prototype separately.
