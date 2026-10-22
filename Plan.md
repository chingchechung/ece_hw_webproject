# Digital Electronics EMI Maze Quest — Development Plan

> Status: Approved implementation handoff, 2026-10-20  
> Baseline: `emi_maze_dualview_v1.2` (existing working prototype).  
> Execution: Codex should work in the existing project repository and read `AGENTS.md` before making changes.

> P2 continuation: physical P1.1 navigation is approved. On `feature/3d-showcase`
> only, add an original Canvas car and the approved v1/v2 educational assignment
> flow using unchanged Lite validators and four/five-question generator parity.
> Preserve demo mode, 3D visuals/physics/controls and all prior regressions.
> Keep the default publication empty and preserve manually published JSON during
> rebuilds. See [3D-P2 results](docs/3d-p2-results.md). Stop after P2 for review;
> no merge into `work`/`main` and no further graphics/gameplay phase.

> P1.1 navigation continuation: physical P1 driving is approved. Add V-switchable
> Canvas 2D driving using the same vehicle/physics and authoritative maze; M opens
> a cumulative 30-second full map. Preserve P0/P1 visuals and the separate labelled
> presentation overview. No routing assistance or educational integration.
> See [3D-P1.1 results](docs/3d-p1.1-results.md). Stop after P1.1 for review.

> Separate showcase continuation, 2026-10-22: P0 is approved after qualitative
> UHD 770 High-preset review. P1 adapts Lite driving and adds five synthetic
> checkpoint/exit interactions on `feature/3d-showcase`, preserving Lite and P0
> visuals. No numerical Intel FPS claim; stop before P2 educational integration.
> See [3D-P1 results](docs/3d-p1-results.md).

> Separate approved showcase track, 2026-10-22: Phase 3D-P0 on
> `feature/3d-showcase` preserves reviewed Lite commit
> `823786bc01b68901455061d5fe31d6076c61f20e` / `lite-v1.0` unchanged.
> Three.js/WebGL 2 and a development build are authorized only for the isolated
> static `showcase3d/` prototype. No course gameplay integration or merge into
> `work`/`main`; stop for Windows UHD 770 / Arc 140V review. See
> [3D-P0 results](docs/3d-p0-results.md).

> Approved authoring revision, 2026-10-20: see `docs/data-contract-v2.md` and
> `docs/phase-2-multianswer-results.md`. Public v1 remains supported. V2 permits
> three/four options and multiple teacher-accepted labels while each student
> chooses one. Manifest stays v1. The original four-choice/single-answer rules
> below describe v1; v2 authoring follows the approved supplement in `AGENTS.md`.
> Phases 0–4 and CI are reviewed. Phase 5A enhances 2D artwork only; see
> `docs/phase-5a-results.md`. The reviewed 2D art now receives focused lighting
> and interaction refinement; see `docs/phase-5a-refinement-results.md`.
> Phase 5A.2 adds adjustable atmosphere and an unobstructed pending interaction
> sequence; see `docs/phase-5a2-results.md`.
> The instructor approved its lighting on real devices. Phase 5A.3 decouples
> the 2D slash from question proximity while preserving that lighting; see
> `docs/phase-5a3-results.md`.
> Phase 5A is approved, including the slash in a local browser. Phase 5B updates
> first-person artwork while preserving the approved 2D visuals and all driving
> physics/gameplay; see `docs/phase-5b-results.md`. Phase 5B.1 material/reduced-motion correction is authorized; see `docs/phase-5b1-results.md`. Stop after Phase 5B.1 for review.

## 1. Project objective

Build a low-maintenance, game-based assignment website for a Digital Electronics EMI course. The game motivates students to watch **English-language question videos**, answer four-choice questions, and optionally watch English-language answer-explanation videos. The instructor uses **Google Forms**—not the game server—to receive student names/student IDs and award submission credit.

The existing 2D maze and first-person driving modes share the **same procedural maze, question locations, session state, and finishing location**. Keep both modes.

### Non-negotiable constraints

- **12 course units only: `S01`–`S12`**. They are *units*, not weeks; do not call them Week 01–13.
- **Python desktop GUI** is an offline editor for unit data, including draft content and a per-unit **allow-play** option.
- Each released unit has **4 or 5 questions**, each with **four options A–D** and **exactly one correct choice**.
- Each question has one English **question YouTube URL**; its **explanation YouTube URL** is offered **only after a correct answer** and is optional to watch.
- YouTube videos open in a **new browser tab** so students can watch at full size. Do not embed small video players inside the maze.
- At the end of a successfully completed unit, the game opens/offers **that unit's Google Form URL**. The instructor controls form acceptance **on Google Forms itself**; the game does not implement submission deadlines, submission state, grades, or a special review mode.
- **No server-side code/database/login/progress recording**. Apache serves static HTML/CSS/JS/JSON/assets only.
- **No automatic upload**. The instructor **manually uploads** released JSON files and the manifest. GUI MUST NOT implement FTP, SFTP, SSH, HTTP upload, deployment, or remote sync.
- **Never publish unreleased questions**. Unit JSON for a not-yet-opened unit remains on the instructor's computer and is not uploaded to the web server; public `manifest.json` lists only approved playable units.
- The instructor may author all 12 units in advance, choose allowed units independently, and publish them gradually. Previously published units remain playable for review until the instructor disallows them.
- **Visual polish happens later**, after JSON/GUI/multi-unit integration is working; do not first rewrite the rendering architecture.
- Windows 11 (Chrome/Edge) and macOS (Chrome/Safari) support; low browser CPU/GPU/memory usage; no installations required for students.

## 2. Baseline inventory and migration constraints

Codex: inspect actual files before restructuring; current v1.2 code has an all-in-one HTML page and embedded JavaScript. Important areas in the existing prototype include:

- Fixed `QUESTIONS`, `FORM_URL`, `MAX_QUESTS=4`: replace with dynamic data from selected unit.
- Maze generator currently places four question stations: support **four or five** distributed, reachable, non-overlapping stations on every supported maze size.
- 2D Canvas RPG view plus lightweight Canvas 2.5D first-person driving view: **preserve both** and the `V` switch.
- Existing 2D zoom choices **150% and 175%**: preserve both, with 150% default.
- Widened driving roadway/turning intersections, approximately 12× perceived/virtual driving distance, and **maze walls instead of ocean scenery**: preserve the current direction.
- All questions must be passed before the finish is usable. A wrong answer starts a new randomized, **smaller maze**, resets all question passes, and retains the same unit questions; size never drops below the existing minimum.
- Teacher-map/minimap allowance: **30 seconds of cumulative use per attempt**; clock runs while visible, pauses when hidden, expires at 0, and is **reset to 30 seconds when restarting or after a wrong answer**. Switching units starts a fresh attempt.
- Game status/help panel is collapsible and the **whole page must not scroll**; only the game camera moves.
- Stop driving when a modal opens or browser loses focus. `E` interacts near question or finish; new-tab video link must not disturb game state.

First preserve behavior with small, isolated changes. Do not unnecessarily convert 2.5D to Three.js or introduce a build system.

## 3. Recommended repository layout

Adapt to the current repository; the layout below is a target, not permission to delete existing files:

```text
project-root/
├── AGENTS.md
├── Plan.md
├── index.html                     # student game, static entry point
├── js/                            # optional progressive extraction from index.html
│   ├── assignment-loader.js
│   ├── assignment-validator.js
│   └── game/...
├── assets/                        # only if images/sprites are extracted
├── assignments/                   # ONLY manually published public files
│   ├── manifest.json
│   ├── S01.json
│   └── ...                         # do NOT upload unreleased Sxx.json files
├── tools/
│   ├── assignment_editor.py       # Tkinter/ttk desktop GUI
│   ├── assignment_data.py         # file I/O + shared Python validation
│   └── validate_assignments.py    # optional CLI validation
├── tests/
├── teacher_data/                  # LOCAL PRIVATE draft state; gitignore
└── export/                        # LOCAL manual-upload deliverables; gitignore
    └── assignments/
```

`teacher_data/` contains incomplete and unreleased answer keys; keep it off the public web root and outside ordinary version control. `export/` contains prepared files the instructor chooses to upload manually; do not auto-copy them into the public `assignments/` folder.

## 4. JSON contract (v1)

Settle and document this format **before** implementing the GUI or student loader. The GUI export and browser validation must agree exactly.

### 4.1 One unit, e.g. `S01.json`

```json
{
  "schemaVersion": 1,
  "unitId": "S01",
  "title": "Logic Gates",
  "googleFormUrl": "https://forms.gle/XXXXXXXXXXXX",
  "questions": [
    {
      "id": "Q01",
      "title": "Inverter",
      "prompt": "Optional short English on-screen prompt",
      "questionVideoUrl": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
      "explanationVideoUrl": "https://www.youtube.com/watch?v=YYYYYYYYYYY",
      "options": ["Logic 0", "Logic 1", "High impedance", "Undefined"],
      "correctOption": "B",
      "explanationText": "Optional short English explanation."
    }
  ]
}
```

**The single-question block above is illustrative only, not a valid publishable unit.** Real exported unit JSON MUST include **4 or 5 complete questions**, `Q01`…`Q04`/`Q05`; URLs above are placeholders and must be replaced. Keep strings Unicode/UTF-8. `prompt`, `title`, and `explanationText` are optional per-question display fields (empty string allowed); the question video is the authoritative source of the full spoken question. The Google Form URL and both YouTube URLs are required for publishable units. Do not store YouTube viewing duration or quiz progress.

Validation rules for *publishable* unit JSON:

1. `schemaVersion === 1`; `unitId` matches `^S(0[1-9]|1[0-2])$` and the filename.
2. `title` is nonempty; `googleFormUrl` is a valid HTTPS Google Forms link (`forms.gle` or `docs.google.com/forms/...`).
3. Exactly **4 or 5** questions; IDs unique and sequential; each has **4 nonempty** options and `correctOption` one of `A/B/C/D`.
4. `questionVideoUrl` and `explanationVideoUrl` must be recognized HTTPS YouTube URLs (e.g. `youtube.com/watch?v=...`, `youtu.be/...`; optionally supported variants documented). GUI should clearly flag malformed or placeholder URLs.
5. Normalize leading/trailing whitespace for ordinary fields; do not silently reorder choices or change the selected correct answer.
6. A draft can be incomplete; only **export/publish** requires all validations to pass. On validation failure, show specific unit/question/field errors and refuse public export.

### 4.2 Public `manifest.json`

```json
{
  "schemaVersion": 1,
  "units": [
    {"unitId": "S01", "title": "Logic Gates", "file": "S01.json"},
    {"unitId": "S02", "title": "Boolean Algebra", "file": "S02.json"}
  ]
}
```

- `manifest.json` includes **ONLY units the instructor marked as allowed to play** and with validated, exported unit content; no unreleased titles, URLs, correct answers, or units that should not be playable.
- The public manifest is a **manual export**. The GUI's allow-play checkbox changes only local draft metadata until the instructor exports the new manifest and manually uploads it.
- If an allowed unit has not yet been exported, the GUI warns or blocks manifest export until its JSON is ready. For all releases, explicitly tell the instructor to upload the corresponding `Sxx.json` files **first**, then upload `manifest.json` **last**.
- When disabling a formerly published unit, removing it from the manifest prevents normal UI access, but **does not erase** the previously uploaded JSON. If the instructor needs it unavailable by direct URL, they must manually delete that server-side file.

## 5. Teacher GUI: Python offline editor

Use Python 3.12 (or 3.11+) with standard-library **Tkinter/ttk** and `json`, `pathlib`, etc. Avoid required pip libraries unless genuinely necessary. The app is a local authoring tool—not a local HTTP service.

### UI/UX requirements

- Unit list `S01`–`S12`, with title, draft completeness, local **allow-play** checkbox, and edit selection.
- A per-unit editor to configure unit title, Google Form URL, and **4/5 questions**. Allow editing 4 and adding/removing the fifth without discarding other fields.
- Each question editor: English YouTube question URL, English YouTube explanation URL, optional title/prompt/explanation text, options A–D, and radio-button **single** correct option.
- Buttons/actions: New/open local draft, Save draft, Validate unit, Export selected `Sxx.json`, Export public `manifest.json`, and choose export folder. Clear success/error messages.
- Distinguish **Save draft** (incomplete is okay) from **Export** (complete and validated only).
- Reopen previously saved drafts; support safe loading/import of existing unit JSON as starting data. Warn before discarding unsaved changes.
- Save drafts using UTF-8 and atomic write/rename where practical. Preserve user-entered content; never silently overwrite source or published files.
- A checkbox does **not** upload or deploy anything. No upload credentials or server-related configuration anywhere in the GUI.
- Prefer readable layout and scrollable question editor instead of squeezing 5 questions into one screen; keyboard navigation should work.

### Output workflow

1. Instructor creates/edits local drafts in `teacher_data/`.
2. Instructor optionally marks `Sxx` as allowed to play, **locally**.
3. GUI validates and exports `Sxx.json` to a selected local `export/assignments/` directory.
4. GUI generates an `export/assignments/manifest.json` listing only selected/validated allowed units.
5. Instructor manually uploads selected unit JSON files to Apache; **last**, uploads manifest to activate them.
6. To keep a unit available for review, leave it marked playable; to close submission, instructor closes Google Form externally. **No submission/review state or logic in game.**

## 6. Student web game: multi-unit integration

### Selection & loading

- On startup, use relative `fetch('./assignments/manifest.json')` to obtain playable units; support a cache-refresh mechanism appropriate to static hosting so teacher updates become visible after reload without manually clearing browser cache.
- Show **S01–S12** identification; only entries in the public manifest can be launched. Do not fetch data for unlisted units or infer their URLs. Unreleased unit titles need not be displayed.
- When selected, fetch the selected unit JSON (based on manifest's `file`), validate it, then initialize a **fresh** maze attempt with question progress at 0 and teacher-map time at 30 seconds.
- Handle `404`, malformed JSON, unsupported schema, empty/invalid manifest, network failure, and file mismatch with a friendly error and retry/back action—not a blank screen.
- Opening selection and refreshing the manifest pause and preserve the active attempt; offer cancel/return. Warn and confirm before replacing it. Only a successfully validated new unit commits the reset; failed/canceled switches preserve current progress, position and map time. Browser reload starts fresh; no persistent student tracking.
- Read all strings via safe text APIs/escaping; do not insert untrusted JSON fields as unescaped HTML. Open external links with `target="_blank"` and `rel="noopener noreferrer"`.

### Gameplay integration

- Replace fixed `MAX_QUESTS`, `QUESTIONS`, `FORM_URL` references with the selected unit's data, **without breaking v1.2**.
- Dynamically place **4 or 5** questions in distinct reachable positions for all maze sizes, including after failures. Do not spawn stations in walls, on each other, on the start, or on finish.
- Use the same stations in 2D and drive view. `V` switches view without changing player position or question progress.
- Pressing `E` near an incomplete question opens its English question YouTube video link (new tab) and A–D answer UI. The explanation YouTube link is shown as optional **after** the answer is correct; it must also open in a new tab.
- A wrong answer clears all passed questions and regenerates the maze at the next smaller size. The current unit's content remains unchanged; teacher map resets to 30s.
- When all questions are passed, the existing finish point allows opening the selected unit's Google Form in a new tab; do **not** record submission, and do **not** implement form status handling.
- Allow leaving an attempt and returning to the unit selector. Keep the selected unit visible in compact game HUD; the page must not scroll vertically.

## 7. Visual polishing — after functionality passes

**Do not start this phase until Phase 4 tests pass.** Continue from the existing code, do not replace the game with another framework for appearance alone.

- **2D**: improve the Gather.town-*inspired* pixel RPG character, walk cycles, walls/floors, desks/question terminals, and exit. Use original or license-cleared art; do not copy Gather.town's proprietary assets.
- **Driving**: keep the v1.2 direction—**maze walls and road corridors, NO ocean/coastal scenery**. Preserve easy-to-read junctions, wide two-lane-style driving paths, forgiving arcade turns, and speed sensation with ~12× virtual distance rather than multiplying logical maze complexity.
- Keep both modes synchronized and low-resource. Prefer Canvas 2D/2.5D and shared lightweight assets. Avoid mandatory WebGL/Three.js unless separately approved based on measured benefits and fallback.
- Scale/cull rendering; avoid large textures, heavyweight libraries, unnecessary continuous animations offscreen. Do not introduce page scroll.

## 8. Implementation milestones & acceptance checks

### Phase 0 — Baseline preservation

- [ ] Inspect repository and identify entry point, original v1.2 source, current controls, assets, and tests.
- [ ] Run a local HTTP server and verify the original 2D/drive prototype; capture baseline behavior.
- [ ] Add focused checks or tests before refactoring; keep a working baseline.

### Phase 1 — Data contract and validator

- [ ] Implement a documented schema version 1, sample **complete** S01 (dummy data used only for testing), and manifest.
- [ ] Unit validation handles 4 and 5 questions, malformed URLs, missing fields, invalid answer, duplicate IDs, wrong unit/file match, and schema errors.
- [ ] Keep local unpublished examples out of public/deployable directories.

### Phase 2 — Python GUI

- [ ] S01–S12 create/edit/save/reload private drafts; allow-play selection.
- [ ] A–D correct-answer radio groups; 4/5 questions; required links; Google Form URL.
- [ ] Export selected validated unit JSON; export validated allowlist manifest; **no upload function**.
- [ ] Cancel/unsaved-change/invalid-input handling; deterministic UTF-8 JSON output; test edits and round trips.

### Phase 3 — Web loading and unit selection

- [x] Student selector lists only playable units from manifest.
- [x] S01 and S02 can load distinct titles, videos, answer keys, and form links.
- [x] Missing/unreleased S03 cannot be launched; no load attempt against guessed JSON paths.
- [x] Switching units starts a fresh attempt without leaking prior unit state; clear error states.

### Phase 4 — Full gameplay integration

- [x] Four-question and five-question units complete in **both** display modes.
- [x] Randomized station placement remains distributed and reachable on **every** maze size.
- [x] Answer wrong → all reset, smaller maze, teacher-map budget restored to 30s.
- [x] Manual restart → full-size initial maze and teacher-map budget 30s.
- [x] 150%/175% 2D zoom; no page scroll; `E`/`V` controls; new-tab video links.
- [x] Finish → correct unit-specific Google Form link; no submission tracking.
- [x] Re-open S01 for review even when newer units exist; Google Form closed/open is handled outside the app.

### Phase 5A — 2D RPG art and performance

- [x] Original procedural character, four directions, idle/walking frames and crisp sprites.
- [x] Readable laboratory floor/wall artwork, terminals and locked/unlocked exit.
- [x] Cached static scenery and three-viewport paired Phase 4 performance measurements.
- [x] Visual review artifacts and regression/CI integration.
- [x] Reviewed-art refinement: subtle player focus light, directional interaction cue and state feedback.
- [x] Phase 5A.2: Off/Normal/Strong preference, stronger light/arc, explicit pending/cancellation and temporal evidence.
- [x] Phase 5A.3: Free E-key slash, shared contextual animation, unchanged approved lighting and versioned static scripts.
- [x] Instructor approval of 2D graphics, atmosphere and locally tested slash before Phase 5B.

### Phase 5B — Driving visual enhancement

- [x] Lab pavement/panel walls, readable checkpoints/finish and restrained motion feedback with frozen-reference comparisons.
- [x] Preserve approved 2D artwork and tested physics; record synthetic driving screenshots/video and three-viewport benchmarks.
- [x] Instructor reviewed Phase 5B on Windows; requested material realism and confirmed the OS reduced-motion slash issue.

### Phase 5B.1 — Materials and Windows slash compatibility

- [x] Cached world-anchored wall/floor materials, distance filtering and matched Phase 5B comparisons.
- [x] Normal/Strong slash independent of OS animation preference; preserve spotlight and full reveal/cancellation sequence.
- [x] Add preference/texture/recording/performance tests; retain all gameplay regression suites.
- [ ] Instructor review of Phase 5B.1 before any further refinement or Phase 6.
- [ ] Smoke test Chrome/Edge Windows 11 and Chrome/Safari macOS (or explicitly record untested real-device platforms).
- [ ] Verify acceptable responsiveness on ordinary integrated-GPU laptops; no external network dependency except YouTube/Google Form.

### Phase 6 — Release packaging and documentation

- [ ] Document `python tools/assignment_editor.py` and a lightweight static HTTP test command (e.g. `python -m http.server 8000`).
- [ ] Document exact **manual upload order**: `Sxx.json` first, public `manifest.json` last; no deployment automation.
- [ ] Verify Apache serves JSON correctly, relative paths work from subdirectory hosting, and refreshes see latest public manifest.
- [ ] Provide a short test checklist for teacher GUI and the student site, plus known limitations of static answers/URLs.

## 9. Explicit out of scope

- Teacher or student accounts, grades, attendance logs, completion receipts, cloud databases, server-side verification, AI-cheating prevention.
- Automatic upload, FTP/SFTP integration, remote server access, private unpublished questions served by Apache.
- Google Forms API integration, submission deadlines, form open/closed states, automatic grading/score exports.
- Separate Chinese-language full lecture and English lecture recap videos (managed outside this game).
- Multiplayer, chat, racing opponents, realistic physics, high-end 3D racing graphics.

## 10. Definition of done

The instructor can use the local GUI to build/save incomplete drafts for S01–S12, export valid 4/5-question JSON for a chosen unit, independently select allowed units and export a public manifest, and **manually** upload those files. Students can launch any published unit in either 2D or driving view, answer all required English video questions, optionally watch English explanations, and reach the correct Google Form. The site requires only static Apache hosting and stays usable on supported Win11/Mac browsers. Only after this functionality is reliable should Codex focus on visual polish.
