# Publishable JSON contract v1

This contract implements `Plan.md` §4. It governs final public export and
browser loading. Incomplete private drafts may be saved without passing these
checks; draft I/O and local allow-play metadata belong to Phase 2.

The machine-readable schemas use JSON Schema Draft 2020-12:

- `schemas/assignment-v1.schema.json`: unit structure, question order, URL rules.
- `schemas/manifest-v1.schema.json`: public allowlist, unique unit IDs, exact files.

Normalize ordinary text before applying a generic JSON Schema validator.
Filename matching and local exported-file/allow-play evidence require contextual
checks beyond a standalone unit schema. The supplied runtime validators perform
normalization internally when checking input. They never mutate source data.

## Unit file

A unit's filename is exactly `S01.json` through `S12.json`, case sensitive, and
must match `unitId`. Pass the basename to the runtime validator at file boundaries.

| Field | Rule |
| --- | --- |
| `schemaVersion` | JSON number exactly 1; booleans and strings are invalid |
| `unitId` | Exact S01–S12 identifier |
| `title` | Required nonblank string |
| `googleFormUrl` | Required supported HTTPS Google Forms URL |
| `questions` | Array of exactly four or five question objects |

| Question field | Rule |
| --- | --- |
| `id` | Exact Q01, Q02, Q03, Q04, optionally Q05, in that array order |
| `title`, `prompt`, `explanationText` | Optional strings; empty or omitted allowed; null is invalid |
| `questionVideoUrl` | Required supported HTTPS YouTube video URL |
| `explanationVideoUrl` | Required supported HTTPS YouTube video URL, although watching is optional |
| `options` | Exactly four nonblank strings, retained in A–D order |
| `correctOption` | Exactly one string: A, B, C or D |

Unknown fields are rejected at every public object level, including `allowPlay`.
No submitted identities, progress, viewing duration, grades or form status are
part of this format. JSON is UTF-8 without a BOM; NaN and Infinity are invalid.

Complete synthetic examples live in `tests/fixtures/S01.json` and `S02.json`,
with four and five questions respectively. They are **test-only**, not released
assignments. Their video links reuse prototype demo IDs, their form URL is a
syntactically valid dummy, and their question/answer text has no course meaning.
No test contacts those services. Never upload these examples.

## Normalization

`normalize_unit` / `normalizeUnit` return a deep copy. They trim leading/trailing
ECMAScript whitespace from unit title/form URL, optional question display strings,
both video URLs, and each option. Manifest normalization trims entry titles.
This explicitly matches JavaScript `String.trim()` in Python, including BOM and
Unicode spaces. Internal whitespace and Unicode text are preserved.

Identifiers (`unitId`, question `id`), filenames and `correctOption` are exact:
they are not trimmed or uppercased. Options and questions are never reordered.
Missing optional fields remain absent. A future exporter must write the returned
normalized copy only after successful validation, retaining the source draft.

## Recognized URL forms

Only lowercase `https://` and these exact lowercase host/path forms are accepted:

- `https://www.youtube.com/watch?v=<videoId>`
- `https://youtube.com/watch?v=<videoId>`
- `https://youtu.be/<videoId>`
- `https://forms.gle/<formId>`
- `https://docs.google.com/forms/d/e/<formId>/viewform`
- `https://docs.google.com/forms/d/<formId>/viewform`
- The same docs.google.com forms paths with `edit` instead of `viewform`, or an
  account prefix `/forms/u/<digits>/d/...`.

YouTube video IDs are exactly 11 ASCII letters/digits/underscore/hyphen. Watch
URLs require exactly one `v` query parameter, in any position. Other simple
query parameters such as `t`, `si`, `list`, `feature` and `usp` are supported;
short links must not introduce another `v`. Parameters use a nonempty ASCII
letter/digit/`_.~-` name and `=` followed by zero or more letters/digits/`_.~+/-`
or valid `%HH` escapes. Multiple parameters use `&`. Simple fragments accept
letters/digits/`_=.-`. Forms IDs use ASCII letters/digits/underscore/hyphen.

Placeholder YouTube IDs made only of X, Y or Z (case insensitive), zeros,
underscores or hyphens are rejected. Forms reject those placeholder tokens and
`placeholder`, `example` (case insensitive), `YOUR_FORM_ID`, `FORM_ID`.
Wrong-length video placeholders are rejected by the ID length check.

Unlisted variants (mobile hosts, shorts, embeds, trailing path segments), ports,
userinfo, alternate hosts, HTTP, malformed percent escapes, quotes and embedded
whitespace are rejected. Convert unsupported variants to a listed canonical
URL. No network request is made to resolve short links or check existence,
availability, ownership, English language, or whether content matches a question.
The instructor must verify those properties before release.

URL patterns live in the unit schema's `$defs` and their checked-in browser
copy `js/assignment-rules.js`. Tests assert exact equality. Update both explicitly
when versioning URL rules; no browser build step is needed.

## Public manifest

`assignments/manifest.json` contains only `schemaVersion: 1` and `units`, an
array of zero to twelve objects containing exactly `unitId`, `title`, `file`.
Unit IDs are unique S01–S12; title is a nonblank string; file must be exactly
`<unitId>.json`. Paths, query strings, fragments and remote URLs are forbidden.
The empty allowlist is valid and is the initial public file in this repository.

Structural validation cannot prove the instructor's local allow-play intent.
Phase 2 must build the manifest only from locally allowed, validated, exported
sources and verify associated exports are still current. The CLI already checks
every explicitly listed sibling unit file for validity, unit/filename agreement
and title agreement; it rejects symlinks and does not probe unlisted filenames.
There is no student loader yet (Phase 3).

Export and deployment remain manual: export locally, manually upload each
`Sxx.json` **first**, then `manifest.json` **last**. Removing a manifest entry
does not delete a previously uploaded unit file; delete it manually if direct
access must end. Google Forms alone controls submission acceptance; published
playable units may remain available for review. Public static JSON exposes
answers/links to browser users.

## APIs and local checks

Python (standard library only):

```python
from tools.assignment_data import normalize_unit, read_json, validate_unit

source = read_json("tests/fixtures/S01.json")
errors = validate_unit(source, "S01.json")
if not errors:
    normalized = normalize_unit(source)
```

`validate_unit(data, filename=None)` / `validateUnit(data, filename=null)` check
content, plus exact filename if supplied. Omitting filename is for in-memory
editing only. `validate_manifest` / `validateManifest` check manifest structure.
Each returns a list/array of `{path, code, message}` errors (Python dataclasses
provide `.as_dict()`); empty means valid. Example path:
`$.questions[2].explanationVideoUrl`. No GUI or public files are written.

Browser usage (classic scripts, in order; not yet wired into the prototype):

```html
<script src="./js/assignment-rules.js"></script>
<script src="./js/assignment-validator.js"></script>
```

Use `AssignmentValidator.validateUnit`, `normalizeUnit`, `validateManifest`,
`normalizeManifest`. Node can `require('./js/assignment-validator.js')` for tests.
The validator does not fetch, render, launch units or open external URLs.

Read-only CLI:

```sh
python tools/validate_assignments.py tests/fixtures/S01.json
python tools/validate_assignments.py tests/fixtures/manifest.json assignments/manifest.json
```

Exit 0 means all requested files are valid; exit 1 prints precise errors to
stderr; command usage errors exit 2. It accepts `pathlib` paths, reads UTF-8,
and never exports, uploads or modifies data.
