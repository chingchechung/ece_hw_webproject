# AGENTS.md — Codex Engineering Instructions

You are working on **Digital Electronics EMI Maze Quest**, based on the existing `emi_maze_dualview_v1.2` HTML5 prototype. Read `Plan.md` first and implement its phases in order. These instructions apply to the repository and all subdirectories, unless a more specific `AGENTS.md` adds constraints.

## Approved v2 authoring supplement — 2026-10-20

The instructor approved the multi-accepted-answer revision documented in
`docs/data-contract-v2.md`. For **v2 only**, this supersedes the v1-only answer
and option rules below: each question has **3 or 4 options** and a nonempty,
distinct `correctOptions` array of existing labels. The teacher uses independent
checkboxes; the student will still select **exactly one** option and pass if
that label is accepted. Do not require selecting all accepted answers.

Keep public v1 and private draft v1 formats compatible, with explicit conversion
to v2 rather than silent migration. Keep public manifest version 1. Incomplete
private v2 drafts may have no accepted answers; public export may not. Preserve
retained Q05 and removed D text/acceptance privately. Reference course content
stays in ignored private drafts; do not invent missing URLs, translate supplied
Chinese choices, or commit unreleased answers. The original prototype remains
the immutable baseline. Phase 2/v2 GUI review is approved, including instructor
Windows 11 question-editing verification.
Phase 4 and CI are reviewed, including instructor-reported real-computer play.
Phase 5A is reviewed; its 2D lighting/interaction refinement is authorized.
See `docs/phase-5a-results.md` and `docs/phase-5a-refinement-results.md`.
Phase 5A.2 replaces the too-subtle refinement with Off/Normal/Strong atmosphere
and an explicitly guarded pending interaction; see `docs/phase-5a2-results.md`.
Only the cosmetic atmosphere preference may persist in localStorage.
Phase 5A.2 lighting is approved after instructor real-device testing. Phase
5A.3 authorizes a separate, always-available 2D slash and versioned static
assets; preserve the approved lighting exactly. See `docs/phase-5a3-results.md`.
Stop for instructor review before Phase 5B. Preserve the driving renderer,
physics, gameplay, authoring and validation contracts.

## 1. Priority and working method

1. Preserve existing working gameplay before adding features. Inspect the repository, identify its actual entry point, and test it locally before refactoring.
2. Prioritize, in order: **schema/validation → offline Python GUI → JSON-driven student game/multi-unit selector → regression tests → visual polish**.
3. Make small, reviewable commits or milestones; do not mix large rendering changes with JSON/GUI implementation. Explain any unavoidable behavioral changes.
4. Run appropriate tests after each modification, report actual results and any untested platforms, and provide a concise changed-files summary.
5. Do not claim Win11/macOS/Safari compatibility from Linux Chromium-only testing. Distinguish smoke tests from actual cross-platform verification.

## 2. Critical product rules — DO NOT BREAK

- Units are exactly **`S01` through `S12`** (not 13 weeks).
- Static-only student site on Apache: HTML/CSS/JavaScript/JSON/images; **no backend, DB, login, student log, or grades**.
- Teacher writes questions using a **local, offline Python Tkinter/ttk GUI**. GUI must **only create/edit/save/validate/export local files**.
- **NEVER implement uploads or remote synchronization** (no FTP, SFTP, SSH, HTTP PUT, cloud API, deployment credentials, or automatic copying to server). Instructor manually uploads published JSON.
- Keep **private drafts** and unreleased answers outside any public web directory; add `teacher_data/` and `export/` to `.gitignore` unless repository layout requires equivalent privacy. Do not commit unreleased answer keys by default.
- GUI has **allow-play** per unit; publishing is not automatic. Public `manifest.json` must list **only allowed, validated, ready-to-export units**. The student game must not request/guess a JSON file absent from the manifest.
- Submission availability is managed solely by **Google Forms**. The game does not create "open for submission", "closed", or "review only" states. A previously published playable unit stays selectable for review, whether or not its Google Form accepts responses.
- English **question YouTube URL** opens in a **new tab**. After a correct choice, offer the **optional English explanation YouTube URL** in a new tab. Chinese lecture and separate English overview videos are outside scope.
- Four or five questions per unit, **A–D** four-choice answers, **one** correct choice; all must be passed before unlocking the unit's Google Form.
- A wrong answer resets all passed questions and starts a new, progressively smaller randomized maze; manual restart returns to the initial maze. Both restore the **30-second teacher-map budget**. Within a round the 30-second timer counts only while the map is open; closing it pauses the count.
- Preserve `V` toggle between **2D maze** and **first-person driving**, using the same map, stations, positions, passed flags and finish. Preserve `E` interaction. 2D camera only **150% / 175%**.
- Preserve wide two-lane-style driving paths, maneuverable intersections, approximately **12× virtual driving-distance feel**, and continuous **maze walls**, **not ocean scenery**. Preserve whole-page no-scroll behavior and collapsible game progress/help.
- Preserve low resource usage and broad Windows 11 Chrome/Edge plus macOS Chrome/Safari browser compatibility. No mandatory heavy game engine or JS build process without user approval.

## 3. JSON data contract (exact names)

Implement the v1 schema documented in `Plan.md`:

**`assignments/S01.json` etc.**

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
      "prompt": "Optional short prompt",
      "questionVideoUrl": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
      "explanationVideoUrl": "https://www.youtube.com/watch?v=YYYYYYYYYYY",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correctOption": "B",
      "explanationText": "Optional short explanation"
    }
  ]
}
```

**This is a schematic single-question snippet only. Never publish it as a unit.** Actual published units have 4 or 5 complete question objects with sequential unique IDs. Preserve option order. Optional text fields may be empty; URLs and answer must be present and valid before public export.

**Public manifest** is an allowlist only:

```json
{
  "schemaVersion": 1,
  "units": [
    {"unitId": "S01", "title": "Logic Gates", "file": "S01.json"}
  ]
}
```

Contract checks:
- Exact `schemaVersion` 1; `unitId` `S01`…`S12` and matches the `Sxx.json` filename.
- Exactly 4 or 5 questions, each with four nonblank options and `correctOption` `A`, `B`, `C`, or `D`.
- Question IDs are `Q01`…`Q04` or `Q05`, unique and sequential.
- Require valid HTTPS YouTube links for both question and explanation; Google Form link under `forms.gle` or `docs.google.com/forms`.
- Drafts may be incomplete. **Only final export** is blocked by missing/invalid fields; show precise GUI errors.
- The Python validator, GUI exporter, JavaScript loader, and fixtures MUST use **identical field names and validation expectations**. Version future migrations explicitly; do not silently change field names.

## 4. Python teacher GUI rules

- Standard-library **Tkinter/ttk**, Python 3.12 preferred; no compulsory third-party GUI framework.
- Display S01–S12 with completeness and a local **allow-play checkbox**. Allow incomplete unpublished drafts.
- For each unit: edit title, Google Form URL, and four or five questions. Each question includes two YouTube URLs, optional on-screen text, A–D options and a **radio group** for a single correct answer.
- Expose clear actions: **Save draft**, **Load/import**, **Validate**, **Export selected Sxx.json**, **Export manifest.json**. Do not implement "Publish to server".
- Use `pathlib`, `json` with UTF-8 (`ensure_ascii=False`), human-readable indentation, atomic file replacement as practical, and careful unsaved-changes prompts.
- Export only to a teacher-selected **local** directory. Do not assume GitHub or the Apache server is writable from the GUI.
- When exporting a manifest, check that each checked unit has a complete/validated source and associated export; warn/block otherwise. Explain that instructor uploads `Sxx.json` first and `manifest.json` last.
- Treat draft source as private; do not place automatic backups within `assignments/` or web root.

## 5. Student JavaScript rules

- Load relative public `assignments/manifest.json` and only load `Sxx.json` explicitly named by an allowed manifest entry. Do not probe unreleased filenames.
- Handle absent/invalid JSON and fetch errors gracefully. Ensure relative paths work under `https://host/~user/subdirectory/`.
- Opening the unit selector and refreshing its manifest pause the active attempt without discarding it. Offer cancel/return. Warn and require confirmation before replacing an active attempt; only commit the reset after the new unit validates. Failed/canceled switches preserve the loaded attempt. Confirmed successful loading resets answers, maze, player/drive state and teacher-map allowance.
- Replace hardcoded v1.2 `QUESTIONS`, `FORM_URL`, and `MAX_QUESTS` carefully. Maze station generation must handle 4 **and** 5 questions on every existing maze size, including the smallest map.
- Use safe DOM text and escaped strings. Avoid inline execution of teacher-authored text. Open external URLs via standard anchor clicks in a new tab using `rel="noopener noreferrer"`.
- Modal open/browser blur must stop driving speed and directional input. Do not change the play experience unexpectedly.
- Static JSON exposes answer keys and links to browser users; **do not falsely claim secure anti-cheating**. Do not add a backend just to obscure client-visible answers.
- Prefer minimal browser-native JavaScript. Avoid new CDN dependencies; keep deployment workable from a directory of static files. Serve using HTTP for local testing (do not depend on `file://` fetch semantics).

## 6. Gameplay regression checklist

After any modification to the browser code, verify at minimum:

1. Both 2D and drive mode load and toggle (`V`) without changing position or question progress.
2. Both 150% and 175% 2D zoom work; no full-page vertical scrolling.
3. Four-question **and** five-question unit layouts generate reachable, distinct question markers on initial and minimum-sized mazes; finish is reachable.
4. Pressing `E` opens nearby question; question video opens in new tab; answer selects exactly one A–D choice.
5. Correct answer marks the question passed and displays optional **explanation video** link; wrong answer clears all passes, shrinks/re-randomizes maze, teacher-map budget returns to 30s.
6. Manual restart resets the maze size/progress and restores teacher-map 30s. Unit switching begins a fresh attempt.
7. All correct answers unlock only that unit's **Google Form URL** at finish. No submission or response tracking.
8. A missing/unpublished unit JSON cannot be launched; malformed JSON produces a useful error and return action.
9. A public manifest refresh picks up newly allowed units without a forced browser-cache purge (test on actual static server).
10. Keyboard, click/touch interactions and opening videos do not leave the car accelerating in the background.

Use Python `unittest` or equivalent stdlib for data/schema tests and a browser smoke test for UI if available. For random maps, test many seeds and all sizes; check station count/uniqueness/reachability rather than testing one screenshot.

## 7. Code quality and security

- Preserve meaningful original functions and existing tested behavior. Refactor incrementally into modules only when it improves maintainability.
- Keep source files UTF-8, code readable, and comments useful. Prefer descriptive names and avoid magic positional indexes for schema fields.
- Treat JSON content as untrusted text; validate before rendering, escape HTML, and do not permit executable code from teacher inputs.
- Do not add telemetry, analytics, student identifiers or personal-data collection.
- Prefer original/licensed assets; Gather.town is a **style reference**, not a license to copy its images, sprites or characters.
- Avoid unnecessary filesystem writes and network requests; protect private draft data, especially answer keys. Do not silently overwrite edited data.

## 8. Definition of task completion for each phase

Before saying a phase is done, state:

- Exactly what files changed and why.
- What manual verification to perform and what test commands were actually run.
- Known limitations, including untested macOS/Safari/Win11 hardware if applicable.
- The next phase and whether prerequisites are satisfied.

Do **not** start Phase 5 visual polish until the instructor has confirmed the JSON GUI and multi-unit student game are behaving correctly, or expressly authorized parallel visual work.
