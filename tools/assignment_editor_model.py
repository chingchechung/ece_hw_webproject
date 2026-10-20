"""Offline authoring state and local-only file operations, independent of Tk.

The private draft envelope is separate from the unchanged public v1 schema.
All publish decisions reuse assignment_data; there is no second publish validator.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import tempfile

if __package__:
    from .assignment_data import UNIT_KEYS, normalize_unit, read_json, validate_manifest, validate_unit
else:
    from assignment_data import UNIT_KEYS, normalize_unit, read_json, validate_manifest, validate_unit

UNIT_IDS = tuple(f"S{i:02}" for i in range(1, 13))
REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE_DIR = Path.home() / "EMI Maze Quest" / "teacher_data"
DEFAULT_EXPORT_DIR = Path.home() / "EMI Maze Quest" / "export" / "assignments"


class EditorError(ValueError):
    """An actionable local authoring error, safe to display to the instructor."""


class ValidationError(EditorError):
    def __init__(self, messages):
        self.messages = messages
        super().__init__("\n".join(messages))


class OverwriteRequired(EditorError):
    pass


class FileConflict(EditorError):
    pass


def blank_question(index):
    return {
        "id": f"Q{index:02}", "title": "", "prompt": "",
        "questionVideoUrl": "", "explanationVideoUrl": "",
        "options": ["", "", "", ""], "correctOption": "", "explanationText": "",
    }


def blank_unit(unit_id):
    if unit_id not in UNIT_IDS:
        raise EditorError("Select a unit from S01 through S12.")
    return {"schemaVersion": 1, "unitId": unit_id, "title": "", "googleFormUrl": "",
            "questions": [blank_question(i) for i in range(1, 5)]}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_destination(path, kind):
    """Keep authoring writes out of checked-in/public directories, including aliases."""
    if str(path).startswith(("//", "\\\\")) or "://" in str(path):
        raise EditorError("Choose a local filesystem path, not a URL or network share.")
    path = Path(path).expanduser()
    if path.is_symlink():
        raise EditorError("Refusing to overwrite a symbolic link; choose a regular local file.")
    resolved = path.resolve()
    permitted = REPOSITORY / ("teacher_data" if kind == "draft" else "export")
    if resolved.is_relative_to(REPOSITORY) and not resolved.is_relative_to(permitted):
        raise EditorError(
            f"Keep {kind} files outside the source/public directories. "
            f"Use a private local folder or the ignored {permitted.name}/ directory."
        )
    if kind == "export" and any(path.parent.glob("*.draft.json")):
        raise EditorError("This folder contains private drafts. Choose a separate local export folder.")
    return path


def atomic_write_json(path, data, *, overwrite=False, expected_digest=None):
    """Write complete UTF-8 JSON in the same directory, then commit atomically.

    First writes use Windows rename or a POSIX exclusive hard link, preventing
    a concurrent new file from being overwritten. Replacements use os.replace. The saved
    digest detects changes since load/save and is checked again before commit.
    Failures retain the old target and remove the temporary file.
    """
    path = Path(path)
    content = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    replacing = path.exists()
    if overwrite and expected_digest is None and replacing and path.is_file() and not path.is_symlink():
        expected_digest = digest(path)

    def check_target():
        if path.is_symlink():
            raise EditorError("Refusing to replace a symbolic link.")
        if expected_digest is not None:
            if not path.is_file() or digest(path) != expected_digest:
                raise FileConflict("The file changed or was removed outside this editor. Save to a new filename or reload it.")
        if path.exists() and not overwrite:
            raise OverwriteRequired(f"File already exists: {path}")

    check_target()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        check_target()
        if overwrite and replacing:
            os.replace(temporary, path)
        else:
            # Windows rename refuses existing targets; POSIX rename would clobber.
            try:
                if os.name == "nt":
                    os.rename(temporary, path)
                else:
                    os.link(temporary, path)
            except FileExistsError as error:
                raise OverwriteRequired(f"File appeared while saving: {path}") from error
    finally:
        temporary.unlink(missing_ok=True)


def editable_unit(raw):
    """Fill absent editor fields, reject structures the form cannot preserve.

    This checks import/editability only. Blank/invalid text and answers remain
    editable. Final export always calls the unmodified Phase 1 validator.
    """
    if not isinstance(raw, dict) or raw.get("unitId") not in UNIT_IDS:
        raise EditorError("Imported unit must identify S01 through S12.")
    result = deepcopy(raw)
    defaults = blank_unit(raw["unitId"])
    for key in UNIT_KEYS:
        if key not in result and key not in ("schemaVersion", "unitId"):
            result[key] = deepcopy(defaults[key])
    if isinstance(result.get("questions"), list):
        for index, question in enumerate(result["questions"]):
            if isinstance(question, dict):
                for key, value in blank_question(index + 1).items():
                    question.setdefault(key, deepcopy(value))
    structural_codes = {"type", "unknown_field", "schema_version", "unit_id", "question_id", "question_count", "option_count"}
    errors = [issue for issue in validate_unit(result) if issue.code in structural_codes]
    if errors:
        raise ValidationError([f"{result['unitId']} {issue.path}: {issue.message}" for issue in errors])
    return result


@dataclass
class UnitDraft:
    unit: dict
    allow_play: bool = False
    parked_question: dict | None = None
    path: Path | None = None
    _saved_document: dict | None = field(default=None, repr=False)
    _disk_digest: str | None = field(default=None, repr=False)

    @classmethod
    def new(cls, unit_id):
        draft = cls(blank_unit(unit_id))
        draft._saved_document = deepcopy(draft.document())
        return draft

    def document(self):
        return {"draftVersion": 1, "allowPlay": self.allow_play,
                "unit": deepcopy(self.unit), "parkedQuestion": deepcopy(self.parked_question)}

    @property
    def dirty(self):
        return self.document() != self._saved_document

    def set_question_count(self, count):
        if count not in (4, 5):
            raise EditorError("Choose four or five questions.")
        questions = self.unit["questions"]
        if count == 4 and len(questions) == 5:
            self.parked_question = questions.pop()
        elif count == 5 and len(questions) == 4:
            questions.append(deepcopy(self.parked_question) if self.parked_question is not None else blank_question(5))
            self.parked_question = None

    def validate(self):
        return validate_unit(self.unit, f"{self.unit['unitId']}.json")

    def save(self, path, *, overwrite=False):
        path = check_destination(path, "draft")
        if not path.name.endswith(".draft.json"):
            raise EditorError("Private drafts must use a .draft.json filename; public unit JSON is a separate export.")
        same_file = self.path is not None and path.resolve() == self.path.resolve()
        document = self.document()
        atomic_write_json(path, document, overwrite=overwrite,
                          expected_digest=self._disk_digest if same_file else None)
        self.path = path
        self._disk_digest = digest(path)
        self._saved_document = deepcopy(document)


def load_document(path):
    """Read a private draft or import a public v1 unit; no model changes on error."""
    path = Path(path)
    source_digest = digest(path)
    raw = read_json(path)
    if digest(path) != source_digest:
        raise FileConflict("The source file changed while loading. Try loading it again.")
    if isinstance(raw, dict) and "draftVersion" in raw:
        if type(raw["draftVersion"]) is not int or raw["draftVersion"] != 1:
            raise EditorError("Unsupported private draftVersion; expected 1.")
        if set(raw) != {"draftVersion", "allowPlay", "unit", "parkedQuestion"}:
            raise EditorError("Private draft fields are draftVersion, allowPlay, unit, parkedQuestion.")
        if type(raw["allowPlay"]) is not bool:
            raise EditorError("Private allowPlay must be a checkbox boolean.")
        draft = UnitDraft(editable_unit(raw["unit"]), raw["allowPlay"])
        parked = raw["parkedQuestion"]
        if parked is not None:
            if len(draft.unit["questions"]) != 4:
                raise EditorError("A parked fifth question requires a four-question draft.")
            test_unit = deepcopy(draft.unit)
            test_unit["questions"].append(parked)
            draft.parked_question = editable_unit(test_unit)["questions"][4]
        draft.path = path
        draft._disk_digest = source_digest
        draft._saved_document = deepcopy(draft.document())
        return draft
    unit = editable_unit(raw)
    filename_errors = [issue for issue in validate_unit(unit, path.name) if issue.code == "filename"]
    if filename_errors:
        raise EditorError(filename_errors[0].message)
    # Imports never adopt a public file as the private save target or allow play.
    return UnitDraft(unit)


class EditorModel:
    def __init__(self):
        self.drafts = {unit_id: UnitDraft.new(unit_id) for unit_id in UNIT_IDS}

    def install(self, draft):
        self.drafts[draft.unit["unitId"]] = draft

    @property
    def dirty_units(self):
        return [unit_id for unit_id, draft in self.drafts.items() if draft.dirty]

    def export_state(self, unit_id, directory):
        draft = self.drafts[unit_id]
        path = Path(directory) / f"{unit_id}.json"
        if path.is_symlink():
            return "Stale (symlink)"
        if not path.exists():
            return "Missing"
        try:
            exported = read_json(path)
            if draft.validate() or validate_unit(exported, path.name):
                return "Stale (invalid)"
            if normalize_unit(exported) != normalize_unit(draft.unit):
                return "Stale (changed)"
        except (OSError, ValueError):
            return "Stale (unreadable)"
        return "Current"

    def export_unit(self, unit_id, directory, *, overwrite=False):
        draft = self.drafts[unit_id]
        issues = draft.validate()
        if issues:
            raise ValidationError([f"{unit_id} {issue.path}: {issue.message}" for issue in issues])
        path = check_destination(Path(directory) / f"{unit_id}.json", "export")
        atomic_write_json(path, normalize_unit(draft.unit), overwrite=overwrite)
        return path

    def build_manifest(self, directory):
        units, errors = [], []
        for unit_id, draft in self.drafts.items():
            if not draft.allow_play:
                continue
            issues = draft.validate()
            if issues:
                errors.extend(f"{unit_id} {issue.path}: {issue.message}" for issue in issues)
                continue
            state = self.export_state(unit_id, directory)
            if state != "Current":
                errors.append(f"{unit_id}: {state}. Export the current unit to this folder before exporting the manifest.")
                continue
            units.append({"unitId": unit_id, "title": normalize_unit(draft.unit)["title"], "file": f"{unit_id}.json"})
        if errors:
            raise ValidationError(errors)
        manifest = {"schemaVersion": 1, "units": units}
        issues = validate_manifest(manifest)
        if issues:
            raise ValidationError([f"{issue.path}: {issue.message}" for issue in issues])
        return manifest

    def export_manifest(self, directory, *, overwrite=False):
        manifest = self.build_manifest(directory)
        path = check_destination(Path(directory) / "manifest.json", "export")
        atomic_write_json(path, manifest, overwrite=overwrite)
        return path
