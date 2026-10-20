"""Offline authoring state and local-only file operations, independent of Tk.

Private draft envelopes are versioned separately from public v1/v2 schemas.
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


def blank_question(index, schema_version=1):
    question = {
        "id": f"Q{index:02}", "title": "", "prompt": "",
        "questionVideoUrl": "", "explanationVideoUrl": "",
        "options": ["", "", "", ""], "correctOption": "", "explanationText": "",
    }
    if schema_version == 2:
        del question["correctOption"]
        question["correctOptions"] = []
    return question


def blank_unit(unit_id, schema_version=1):
    if unit_id not in UNIT_IDS:
        raise EditorError("Select a unit from S01 through S12.")
    if type(schema_version) is not int or schema_version not in (1, 2):
        raise EditorError("Choose assignment schema version 1 or 2.")
    return {"schemaVersion": schema_version, "unitId": unit_id, "title": "", "googleFormUrl": "",
            "questions": [blank_question(i, schema_version) for i in range(1, 5)]}


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
    version = result.get("schemaVersion")
    if isinstance(version, bool) or version not in (1, 2):
        raise EditorError("Unsupported assignment schemaVersion; expected 1 or 2.")
    defaults = blank_unit(raw["unitId"], int(version))
    for key in UNIT_KEYS:
        if key not in result and key not in ("schemaVersion", "unitId"):
            result[key] = deepcopy(defaults[key])
    if isinstance(result.get("questions"), list):
        for index, question in enumerate(result["questions"]):
            if isinstance(question, dict):
                for key, value in blank_question(index + 1, int(version)).items():
                    question.setdefault(key, deepcopy(value))
    structural_codes = {"type", "unknown_field", "schema_version", "unit_id", "question_id", "question_count", "option_count"}
    if version == 2:
        structural_codes.update(("answer", "answer_range", "duplicate_answer"))
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
    parked_options: dict = field(default_factory=dict)
    _saved_document: dict | None = field(default=None, repr=False)
    _disk_digest: str | None = field(default=None, repr=False)

    @classmethod
    def new(cls, unit_id, schema_version=1):
        draft = cls(blank_unit(unit_id, schema_version))
        draft._saved_document = deepcopy(draft.document())
        return draft

    def document(self):
        version = int(self.unit["schemaVersion"])
        document = {"draftVersion": version, "allowPlay": self.allow_play,
                    "unit": deepcopy(self.unit), "parkedQuestion": deepcopy(self.parked_question)}
        if version == 2:
            document["parkedOptions"] = deepcopy(self.parked_options)
        return document

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
            questions.append(deepcopy(self.parked_question) if self.parked_question is not None else blank_question(5, self.unit["schemaVersion"]))
            self.parked_question = None

    def set_option_count(self, question_index, count):
        if self.unit["schemaVersion"] != 2:
            raise EditorError("Convert this v1 draft to v2 before changing option count.")
        if count not in (3, 4):
            raise EditorError("Choose three or four options.")
        question = self.unit["questions"][question_index]
        question_id = question["id"]
        if count == 3 and len(question["options"]) == 4:
            answers = question["correctOptions"]
            self.parked_options[question_id] = {
                "text": question["options"].pop(), "accepted": "D" in answers,
                "position": answers.index("D") if "D" in answers else None,
            }
            question["correctOptions"] = [answer for answer in answers if answer != "D"]
        elif count == 4 and len(question["options"]) == 3:
            parked = self.parked_options.pop(question_id, {"text": "", "accepted": False, "position": None})
            question["options"].append(parked["text"])
            if parked["accepted"]:
                question["correctOptions"].insert(min(parked["position"], len(question["correctOptions"])), "D")

    def converted_to_v2(self):
        """Explicit migration creates an unsaved copy and never overwrites v1 source."""
        if self.unit["schemaVersion"] != 1:
            raise EditorError("Only v1 drafts can be converted to v2.")
        unit = deepcopy(self.unit)
        questions = unit["questions"]
        parked = deepcopy(self.parked_question)
        if parked is not None:
            questions.append(parked)
        for question in questions:
            answer = question["correctOption"]
            if answer not in ("", "A", "B", "C", "D"):
                raise EditorError(f"{question['id']}: fix the v1 correctOption before conversion.")
            question["correctOptions"] = [answer] if answer else []
            del question["correctOption"]
        unit["schemaVersion"] = 2
        if parked is not None:
            parked = questions.pop()
        return UnitDraft(unit, allow_play=self.allow_play, parked_question=parked)

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


def load_document(path, *, allow_reference_filename=False):
    """Read a v1/v2 draft/unit; reference filenames require explicit authoring import."""
    path = Path(path)
    source_digest = digest(path)
    raw = read_json(path)
    if digest(path) != source_digest:
        raise FileConflict("The source file changed while loading. Try loading it again.")
    if isinstance(raw, dict) and "draftVersion" in raw:
        version = raw["draftVersion"]
        if type(version) is not int or version not in (1, 2):
            raise EditorError("Unsupported private draftVersion; expected 1 or 2.")
        keys = {"draftVersion", "allowPlay", "unit", "parkedQuestion"}
        if version == 2:
            keys.add("parkedOptions")
        if set(raw) != keys:
            raise EditorError(f"Private draft v{version} fields must be exactly: {', '.join(sorted(keys))}.")
        if type(raw["allowPlay"]) is not bool:
            raise EditorError("Private allowPlay must be a checkbox boolean.")
        draft = UnitDraft(editable_unit(raw["unit"]), raw["allowPlay"])
        if draft.unit["schemaVersion"] != version:
            raise EditorError("draftVersion and unit schemaVersion must match; use explicit conversion for migration.")
        parked = raw["parkedQuestion"]
        if parked is not None:
            if len(draft.unit["questions"]) != 4:
                raise EditorError("A parked fifth question requires a four-question draft.")
            test_unit = deepcopy(draft.unit)
            test_unit["questions"].append(parked)
            draft.parked_question = editable_unit(test_unit)["questions"][4]
        if version == 2:
            draft.parked_options = _read_parked_options(raw["parkedOptions"], draft)
        draft.path = path
        draft._disk_digest = source_digest
        draft._saved_document = deepcopy(draft.document())
        if allow_reference_filename:
            # Explicit reference import copies content, never private release intent.
            draft.allow_play = False
            draft.path = None
            draft._disk_digest = None
            draft._saved_document = None
        return draft
    unit = editable_unit(raw)
    filename_errors = [issue for issue in validate_unit(unit, path.name) if issue.code == "filename"]
    if filename_errors and not allow_reference_filename:
        raise EditorError(filename_errors[0].message)
    # Imports never adopt a public file as the private save target or allow play.
    return UnitDraft(unit)


def _read_parked_options(value, draft):
    if not isinstance(value, dict):
        raise EditorError("parkedOptions must be an object.")
    questions = draft.unit["questions"] + ([draft.parked_question] if draft.parked_question else [])
    by_id = {question["id"]: question for question in questions}
    for question_id, option in value.items():
        if question_id not in by_id or len(by_id[question_id]["options"]) != 3:
            raise EditorError("Retained D requires an existing three-option question (active or retained Q05).")
        if not isinstance(option, dict) or set(option) != {"text", "accepted", "position"}:
            raise EditorError("Retained D requires text, accepted and position fields.")
        if not isinstance(option["text"], str) or type(option["accepted"]) is not bool:
            raise EditorError("Retained D text must be a string and accepted must be boolean.")
        position = option["position"]
        if (option["accepted"] and (type(position) is not int or position not in range(4))) or (not option["accepted"] and position is not None):
            raise EditorError("Retained D position must be 0-3 when accepted, otherwise null.")
    return deepcopy(value)


class EditorModel:
    def __init__(self, schema_version=1):
        self.drafts = {unit_id: UnitDraft.new(unit_id, schema_version) for unit_id in UNIT_IDS}

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
