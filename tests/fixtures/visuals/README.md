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

`phase-5a3-drive.js` freezes the approved driving drawing functions from
`b5626bdbc962c98e6aaf10effa148d1d4ed8bc54`, before Phase 5B artwork changes.
SHA-256: `01bfa3e151cdadf1b8166c97ed2e462600fe0f5f855535fa8ff148e34b3eafc2`.
Browser tests evaluate it only in a synthetic response closure sharing the
unchanged physics/road state. It supports matched screenshots, state/control
comparisons and performance measurements. No assignment data is present; never
deploy this reference or any test bridge. Phase 5B separately hashes all
approved gameplay blocks and the entire unchanged Phase 5A.3 2D renderer.

`phase-5b-drive.js` freezes the complete driving artwork/cache functions from
reviewed commit `11b0cdfab1ceb3df9a87e34183d3965e1d4870de` for Phase 5B.1 pairs.
SHA-256: `30b43edfffbc7c12b4bf2044ef1689c4ddaba775a7a8aff9d2634f5a30f9186d`.
It keeps its own derived caches in a test-only closure and shares the unchanged
physics/state. No teacher data/assets are included. The older 5A.3 reference and
all original gameplay routes remain. Phase 5B.1 source checks normalize only the
authorized slash OS-preference gates/listener and release marker before hashing
the approved gameplay/2D source; lighting still has exact pixel parity coverage.
