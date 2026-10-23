# Unified release candidate — English Lite and approved 3D

Candidate: **1.0.0-rc1**, both editions together on `feature/3d-showcase`.
Lite's application UI is English; the 3D runtime remains the reviewed P2.1.1
build. Historical tags are preserved. No merge, deployment or final tag is made.

This report is being completed during verification. Exact tested source SHA,
actual GitHub Actions URLs/counts, package hashes and screenshots will be recorded
after the complete local and hosted suites finish. Pending checks are not claimed
as passing.

## Authorized scope and preservation

Only `student/index.html`, `student/js/assignment-loader.js` and
`student/js/game.js` change in the deployed Lite application. These changes cover
owned English strings, badge removal, HTML language/version metadata and cache
keys for the translated scripts. Inline CSS, IDs, controls, artwork, lighting,
slash behavior, generator, physics and assignment values/rules are retained.
The `5b1-1` renderer/material/gameplay compatibility marker remains separate from
the unified `1.0.0-rc1` application version in the Lite HTML metadata.

The immutable 69-file `showcase3d/tests/lite-baseline.json` is unchanged.
`lite-english-release.json` pins that historical manifest's hash and identifies
exactly seven deliberate current-release differences: the three UI files and
four existing test files whose Chinese/cache/source expectations must change.
The other 62 files still match the historical hashes. A reversible edit ledger
in `tests/fixtures/lite-english-ui.json` recovers every historical byte of all
three UI files. The original source-region hash checks then run against that
recovered source. Generator and driving parity continue against the actual
current source, not a substitute fixture. No preservation test is disabled.

Unchanged protected source includes the Python GUI/model, schemas, shared and
deployed validators/rules, 2D renderer/materials, original prototype, all 3D
application sources, read-only generated adapter, maps and committed 3D runtime.
The historical `lite-v1.0`, `showcase3d-p0-approved` and
`showcase3d-v1.0.0-rc1` tags are not moved. The unified candidate is identified by
its source SHA and ZIP, without creating another tag.

## Package and deployment

`release/package.py` builds the deterministic
`test-results/unified-release/Engineering-Maze-Lab-1.0.0-rc1.zip` from `student/`
and `showcase3d/dist/`. Its 16 entries contain eight Lite files, six 3D files,
README and release-info.json. Fixed entry order, ZIP timestamps, permissions and
compression make repeated builds byte-identical with the same Python/zlib and
inputs. The inventory records both edition versions and every payload hash.

Both manifests must be empty. Unexpected files, private draft filenames,
symlinks, inconsistent versions or a changed 3D build fail packaging. No tests,
private course data, student records, tools, schemas or credentials are deployed.
Teacher `tools/` and `schemas/` remain available together in the source release.
The separate 3D Windows launcher ZIP is also retained and rebuilt.

Follow the [packaging and Apache guide](../release/README.md). Deploy `lite/`
and `3d/` independently under arbitrary nested URLs. For an upgrade, back up
first, upload runtime assets and then index last, **leaving the entire existing
`assignments/` directory untouched**, including every manifest and unit JSON.
Never replace the live manifest with an empty bootstrap manifest. No automatic
publishing or deployment is configured.

## English interface screenshots

Only synthetic fixtures appear in these screenshots. The 3D image uses its
separate synthetic demonstration mode; the Lite image uses a disposable test
assignment, never a published course assignment.

![English Lite interface](images/unified-release/lite-english.png)

![Approved English 3D interface](images/unified-release/3d-english.png)

## Validation and review gate

The workflow is renamed **Unified release candidate — Lite + 3D**. It retains
read-only token permissions, all existing suites, native Windows launcher checks
and failure artifacts. It adds extracted unified-package browser tests and a
separate unified ZIP/evidence artifact. The Lite job name describes preserved
behavior with English UI rather than byte identity to 5B.1.

The added tests cover deterministic/privacy-safe packaging, English desktop and
mobile UI, identical v1/v2 four/five-question JSON accepted by both extracted
editions, unchanged Chinese synthetic instructor text, English correct/incorrect
and completion dialogs, map expiration/reset, and both nested deployment paths.
Existing suites retain control-driven navigation, answer semantics, switching,
failed loads, unit review, 2D/drive modes, 3D demonstration/education, graphics,
native fullscreen Escape/rejections, GUI, validation and no-scroll/error checks.

Ubuntu/Chromium and software WebGL establish functional regressions only.
No new physical Intel GPU, Safari or macOS GUI compatibility claim is made.
The source README retains a separate optional macOS/WebKit strategy.
**Stop for instructor review; do not merge into main/work or create v1.0.0.**
