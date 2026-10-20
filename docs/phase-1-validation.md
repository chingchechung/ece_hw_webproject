# Phase 1 — Data contract and validator

Completed after Phase 0 on 2026-10-20. Python GUI work has not started.
The extracted v1.2 HTML/README and the original ZIP remain unchanged.

## Results

- Documented and implemented v1 unit and public allowlist schemas with exact
  field names from `Plan.md`, S01–S12, sequential Q01–Q04/Q05, four A–D options,
  one answer, required question/explanation videos and Google Forms URL.
- Shared Python/JavaScript expectations, precise field-level errors, no input
  mutation, deterministic normalization, preserved Unicode and option order.
- Explicit offline HTTPS URL/placeholder rules and rejection of private extra
  fields; see `data-contract-v1.md` for accepted URL variants and limits.
- Read-only offline CLI checks files, manifest entries and listed unit exports.
  It reports missing/invalid exports and title mismatches without probing other
  units or making network requests.
- Complete test-only four-question S01, five-question S02 and matching manifest
  under `tests/fixtures/`. Public `assignments/` has only an empty manifest.
  Private drafts and local export deliverables remain ignored and uncreated.

## Tests actually run

- `python -m unittest discover -s tests -v`: **12 passed**, no skips in this
  environment. This includes the original archive-preservation check, 296 shared
  acceptance cases, exact Python/Node error and normalization parity, JSON
  Schema agreement, UTF-8/invalid JSON, mutation prevention, field diagnostics,
  manifest/export checks, CLI exit behavior and read-only behavior.
- `python tests/browser_validation.py`: **1 passed**. The same 296 cases agree
  with Python when both classic scripts are loaded over local HTTP in Linux
  headless Chromium. No JavaScript page errors.
- `python tools/validate_assignments.py tests/fixtures/S01.json tests/fixtures/S02.json tests/fixtures/manifest.json assignments/manifest.json`:
  **all four valid**, exit 0.
- `node --check js/assignment-rules.js`,
  `node --check js/assignment-validator.js`,
  `node --check tests/validate_in_js.cjs`: **passed**.
- `python -m compileall -q tools tests`: **passed**.

An initial schema test caught that Draft 2020-12 `items` does not apply to
`prefixItems`; the first five elements now each reference the complete question
schema. The complete suite passed after correction. Explicit end-of-string
matching also rejects trailing-newline identifiers in both schemas and validators.

## Changed files in this phase

- `schemas/assignment-v1.schema.json`: formal publishable unit schema.
- `schemas/manifest-v1.schema.json`: formal allowlist schema.
- `tools/assignment_data.py`: stdlib normalization, publish validation and JSON reader.
- `tools/validate_assignments.py`: read-only validation CLI and listed-file checks.
- `js/assignment-rules.js`: checked-in URL patterns matching the schema.
- `js/assignment-validator.js`: browser-native validator with the same Python rules.
- `assignments/manifest.json`: empty public allowlist, no dummy published units.
- `tests/fixtures/S01.json`: complete four-question synthetic test unit.
- `tests/fixtures/S02.json`: complete five-question synthetic test unit.
- `tests/fixtures/manifest.json`: allowlist only for those test fixtures.
- `tests/__init__.py`: explicit importable test package.
- `tests/contract_cases.py`: shared 296-case valid/invalid corpus.
- `tests/test_assignment_data.py`: Python, schema, Node parity and CLI checks.
- `tests/validate_in_js.cjs`: Node corpus runner.
- `tests/browser_validation.py`: classic-script validation over local HTTP.
- `docs/data-contract-v1.md`: contract, APIs, URL forms and release constraints.
- `docs/phase-1-validation.md`: this report.
- `README.md`: validation commands, private fixture boundary and phase status.

No modifications to `AGENTS.md`, `Plan.md`, the ZIP, or the extracted prototype.
No GUI, uploads, student loader, unit selector or rendering changes.

## Manual verification and limitations

Run the CLI commands above. In a temporary private folder, copy the fixture to
`S01.json`, change a correct answer to `AB`, remove a required video URL or
duplicate an ID; rerun the CLI and confirm the exact field errors and exit 1.
Rename a copy to `S02.json` to check filename mismatch. Run the optional browser
command to verify script order/global API through HTTP.

Validation proves structure and recognized syntax, not remote video/form
availability, English content or instructor release intent. Local allow-play
metadata and checked export freshness will be implemented in Phase 2. The public
manifest is not yet consumed by the prototype. Four/five-question gameplay,
unit switching and real form integration remain Phases 3–4.

Only Linux Chromium was browser-tested. Real Windows 11 Chrome/Edge and macOS
Chrome/Safari remain untested; no platform-compatibility claim is made. The
optional `jsonschema` and Playwright packages are test tools only; runtime Python
validation requires no third-party packages and browser scripts require no build.

Phase 2 prerequisites are satisfied: tested, documented v1 contract and reusable
validator APIs. Next: offline Tkinter/ttk drafts, allow-play controls and validated
local export, with no upload functionality. Work stops here for this request.
