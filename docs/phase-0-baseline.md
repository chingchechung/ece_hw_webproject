# Phase 0 — Baseline preservation

Completed 2026-10-20 using Python 3.12.14, Node 24.19.0, Python Playwright
1.62.0 and Linux headless Chromium. No gameplay source edits.

## Inventory

- Supplied source: `emi_maze_dualview_v1.2.zip`; archive contains just
  `emi_maze_dualview_v1.2/index.html` (72,147 bytes) and `README.txt`.
- Entry point: extracted `emi_maze_dualview_v1.2/index.html`.
- Canvas 2D and Canvas 2.5D share the maze/player/stations/passed flags.
  Sprite artwork is an embedded PNG data URL. No runtime library, CDN, build
  system, backend, or external assets are required to render the game.
- Controls: WASD/arrows, E/space interaction, V view switch, canvas click,
  touch directional buttons, 150%/175% camera, collapsible progress/help,
  teacher map, restart, and a prototype-only simulated-wrong-answer button.
- Four fixed questions, two demo YouTube URLs, empty `FORM_URL`.
- Maze sizes: 25×19, 21×15, 17×13, 13×9. Driving uses 12× virtual distance
  and a widened road mask with continuous maze walls.
- No preexisting test suite or Python application.

## Actual checks and results

`python -m unittest discover -s tests -v`: **1 passed**. Extracted HTML and
README bytes match the original archive.

`python tests/browser_baseline.py`: **4 passed** over a local HTTP server.

- Original uninstrumented page renders in both modes without JavaScript
  errors; screenshots visually inspected (`test-results/baseline-2d.png`,
  `test-results/baseline-drive.png`).
- 800 deterministic generated mazes: 200 per supported size, all distinct,
  four unique reachable stations, reachable finish, no station on start/finish.
- E opens questions; four answer buttons; actual new-tab video navigation
  with a stub destination; safe link attributes; explanation appears after
  correct answers; all four answers unlock the prototype finish in both modes.
- V keeps positions, stations and passed flags. Acceleration works; blur and
  question dialogs clear input and stop speed.
- Wrong answer/new round clears progress, changes maze, shrinks to the minimum,
  and resets map time. Manual restart restores initial size and map allowance.
- Map use counts down while shown, pauses while hidden, expires/auto-closes,
  disables at zero, and resets to 30 seconds on restart.
- 150% initial camera and 175% selection; help opens/closes. No vertical page
  scroll at 1366×768, 1024×768 and 390×844 viewport sizes.

The first browser invocation was blocked by the execution sandbox's localhost
socket restriction. The same command passed when run with the approved local
server/browser execution permission; this was not a product failure.

## Observations reserved for later phases

- Five-question gameplay and real unit-specific Google Form links do not
  exist in this baseline. They require Phases 3–4, not Phase 0 changes.
- The region candidate loop skips open maze cells (`if(!maze[cy][cx]...)`),
  so station placement currently uses the fallback. Reachability passes;
  intended regional distribution needs attention in Phase 4.
- Passed flags are cleared when the user starts the next round after the
  wrong-answer dialog. The dialog immediately restores map time.
- Reload preserves remaining map budget in localStorage, as the original
  prototype documents. Unit-switch fresh-attempt semantics come later.
- The prototype still uses weekly wording and demonstration content.

## Changed files

- `emi_maze_dualview_v1.2/index.html`, `emi_maze_dualview_v1.2/README.txt`:
  extracted unchanged working baseline.
- `.gitignore`: exclude private drafts, local export files, Python caches,
  browser screenshots.
- `tests/test_baseline.py`: archive byte-preservation check.
- `tests/browser_baseline.py`: isolated HTTP/Chromium gameplay smoke tests
  and seeded maze checks; hooks are only in test-intercepted responses.
- `README.md`: local run/test instructions and phase report link.
- `docs/phase-0-baseline.md`: this report.

## Manual verification and limits

Serve the extracted student directory using the README command. Walk/drive
through intersections with WASD, toggle V, open a nearby station with E, open
the video, return and answer; exercise wrong answers, restart, map show/hide,
zoom and help. Complete four questions and reach finish.

Automated traversal checks establish connectivity, not human driving feel or
physical touch usability. Real Windows 11 Chrome/Edge, macOS Chrome/Safari,
physical touch devices and integrated-GPU performance are **untested**.
No real YouTube playback or Google Form submission was attempted.

Phase 1 prerequisites are satisfied: baseline located, served, preserved and
tested. Next: v1 data contract/validators and test-only dummy fixtures.
