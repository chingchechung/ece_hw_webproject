# Synthetic visual comparison support

`phase-5a-renderer.js` is the original procedural artwork renderer from reviewed
commit `bc7c3fcce84c8c093355c301beb95418e31af9a4`. It contains no assignment data.
SHA-256: `fee5cbe020767406b13b7b77df89390773c61e16e01e6eddd31f274e166dc1d8`.

The refinement browser suite substitutes it in test HTTP responses for paired
performance/lighting comparisons. Keep this fixed baseline out of `student/`;
it is never deployed. The original Phase 4 comparison still uses the immutable
prototype separately.

`phase-5a1-renderer.js` is the previous subtle refinement from `f80e0e1`.
SHA-256: `0c9e484cabace70fbde80b5e815f38906a9b5ea8f66dc08fa1f7096e6bf17afd`.
Phase 5A.2 uses it for paired performance measurements. It is also test-only
original artwork with no assignment data.

`phase-5a2-renderer.js` is the instructor-approved lighting renderer from
`625fd1219407430047417177038f25851eca1004`.
SHA-256: `d990d4b61faefb942aafffe90a086f711798b46c343fd27a09e01faaf98c27af`.
Phase 5A.3 compares its actual Canvas pixels at all three viewport sizes, both
zooms, all modes and map states to ensure the approved light/artwork is unchanged
when no slash is active. It is never deployed and contains no assignment data.
