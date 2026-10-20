# Digital Electronics EMI Maze Quest

Read [AGENTS.md](AGENTS.md) and [Plan.md](Plan.md) before development.

The working v1.2 baseline is `emi_maze_dualview_v1.2/index.html`, extracted
byte-for-byte from the supplied ZIP. No gameplay migration has happened yet.

Run the original prototype locally:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory emi_maze_dualview_v1.2
```

Open `http://127.0.0.1:8000/`. Serve only the student directory, never private
draft/export directories or the whole repository on a public server.

Run standard-library tests:

```sh
python -m unittest discover -s tests -v
```

Optional browser baseline test (Python Playwright and `/usr/bin/chromium`):

```sh
python tests/browser_baseline.py
```

That test starts and stops its own loopback HTTP server, stubs external video
navigation, and writes ignored screenshots to `test-results/`.

Phase 1 adds [the v1 data contract](docs/data-contract-v1.md), JSON Schemas,
matching Python/browser validators, and a read-only local CLI. It does not yet
connect JSON to the prototype or implement the Python GUI.

```sh
python tools/validate_assignments.py tests/fixtures/manifest.json assignments/manifest.json
python tests/browser_validation.py
```

`tests/fixtures/` contains complete **test-only** S01 (four questions), S02 (five
questions), and a test manifest. Never deploy that directory. Public
`assignments/manifest.json` starts with an empty allowlist and no unit files.
`teacher_data/` and `export/` are ignored private local directories; keep actual
drafts outside any served web directory. Validation does not upload or export.

The runtime Python tools use only the standard library. Node runs optional
Python/JavaScript parity tests; the optional `jsonschema` test package checks
the formal Draft 2020-12 schemas. Both checks ran in this environment. Browser
scripts require no npm install, bundler, CDN, or build step.

Phase reports: [Phase 0](docs/phase-0-baseline.md), [Phase 1](docs/phase-1-validation.md).
Next is Phase 2, the offline Tkinter/ttk editor. GUI work has not started.
