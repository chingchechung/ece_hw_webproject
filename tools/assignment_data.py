"""Offline v1 publish validation. Incomplete drafts need not pass this validator.

Validation never mutates input. Normalize ordinary text for export with
normalize_unit(); IDs and correctOption are exact identifiers and are not changed.
No GUI, network operations, publishing or filesystem writes occur here.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
UNIT_SCHEMA = json.loads((SCHEMA_DIR / "assignment-v1.schema.json").read_text(encoding="utf-8"))
UNIT_ID = re.compile(r"^S(0[1-9]|1[0-2])$")
YOUTUBE_URL = re.compile(UNIT_SCHEMA["$defs"]["youtubeUrl"]["pattern"])
FORM_URL = re.compile(UNIT_SCHEMA["$defs"]["googleFormUrl"]["pattern"])
# Exactly ECMAScript String.trim whitespace, so browser and Python agree.
TRIM_CHARS = "\u0009\u000a\u000b\u000c\u000d\u0020\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
UNIT_KEYS = ("schemaVersion", "unitId", "title", "googleFormUrl", "questions")
QUESTION_KEYS = ("id", "title", "prompt", "questionVideoUrl", "explanationVideoUrl", "options", "correctOption", "explanationText")


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    code: str
    message: str

    def as_dict(self):
        return asdict(self)


def trim(value):
    return value.strip(TRIM_CHARS) if isinstance(value, str) else value


def normalize_unit(data):
    """Return a deep copy; trim display text/URLs/options, preserve choice order."""
    result = deepcopy(data)
    if not isinstance(result, dict):
        return result
    for key in ("title", "googleFormUrl"):
        if key in result:
            result[key] = trim(result[key])
    if isinstance(result.get("questions"), list):
        for question in result["questions"]:
            if not isinstance(question, dict):
                continue
            for key in ("title", "prompt", "questionVideoUrl", "explanationVideoUrl", "explanationText"):
                if key in question:
                    question[key] = trim(question[key])
            if isinstance(question.get("options"), list):
                question["options"] = [trim(option) for option in question["options"]]
    return result


def normalize_manifest(data):
    result = deepcopy(data)
    if isinstance(result, dict) and isinstance(result.get("units"), list):
        for entry in result["units"]:
            if isinstance(entry, dict) and "title" in entry:
                entry["title"] = trim(entry["title"])
    return result


class _Checks:
    def __init__(self):
        self.errors = []

    def add(self, path, code, message):
        self.errors.append(ValidationIssue(path, code, message))

    def obj(self, value, path, allowed):
        if not isinstance(value, dict):
            self.add(path, "type", "Expected an object.")
            return False
        for key in sorted(set(value) - set(allowed)):
            self.add(f"{path}.{key}", "unknown_field", "Unknown field in schema v1.")
        return True

    def text(self, obj, key, path, required=True):
        field = f"{path}.{key}"
        if key not in obj:
            if required:
                self.add(field, "required", "Required field is missing.")
            return None
        value = obj[key]
        if not isinstance(value, str):
            self.add(field, "type", "Expected a string.")
            return None
        if required and not trim(value):
            self.add(field, "blank", "Must not be blank.")
            return None
        return value

    def version(self, obj, path):
        value = obj.get("schemaVersion")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != 1:
            self.add(f"{path}.schemaVersion", "schema_version", "schemaVersion must be the number 1.")

    def unit_id(self, obj, path):
        value = self.text(obj, "unitId", path)
        if value is not None and not UNIT_ID.fullmatch(value):
            self.add(f"{path}.unitId", "unit_id", "Expected S01 through S12.")
        return value

    def url(self, obj, key, path, pattern, message):
        value = self.text(obj, key, path)
        if value is not None and not pattern.fullmatch(value):
            self.add(f"{path}.{key}", "url", message)


def validate_unit(data, filename=None):
    """Return precise publish errors; pass the basename at every file boundary."""
    data = normalize_unit(data)
    check = _Checks()
    if not check.obj(data, "$", UNIT_KEYS):
        return check.errors
    check.version(data, "$")
    unit_id = check.unit_id(data, "$")
    expected_file = f"{unit_id}.json" if isinstance(unit_id, str) else None
    if filename is not None and (not isinstance(filename, str) or filename != expected_file):
        check.add("$.unitId", "filename", "Filename must be exactly <unitId>.json (for example S01.json).")
    check.text(data, "title", "$")
    check.url(data, "googleFormUrl", "$", FORM_URL, "Expected a supported HTTPS Google Forms URL; replace placeholders.")
    questions = data.get("questions")
    if not isinstance(questions, list):
        check.add("$.questions", "type", "Expected an array of questions.")
        return check.errors
    if len(questions) not in (4, 5):
        check.add("$.questions", "question_count", "A published unit needs exactly 4 or 5 questions.")
    for index, question in enumerate(questions):
        path = f"$.questions[{index}]"
        if not check.obj(question, path, QUESTION_KEYS):
            continue
        question_id = check.text(question, "id", path)
        expected = f"Q{index + 1:02}"
        if question_id is not None and question_id != expected:
            check.add(f"{path}.id", "question_id", f"Expected {expected}; question IDs must be unique and sequential.")
        for field in ("title", "prompt", "explanationText"):
            check.text(question, field, path, required=False)
        for field in ("questionVideoUrl", "explanationVideoUrl"):
            check.url(question, field, path, YOUTUBE_URL, "Expected a supported HTTPS YouTube video URL; replace placeholders.")
        options = question.get("options")
        if not isinstance(options, list):
            check.add(f"{path}.options", "type", "Expected an array of four options in A-D order.")
        else:
            if len(options) != 4:
                check.add(f"{path}.options", "option_count", "Exactly four options are required in A-D order.")
            for option_index, option in enumerate(options):
                option_path = f"{path}.options[{option_index}]"
                if not isinstance(option, str):
                    check.add(option_path, "type", "Expected a string.")
                elif not option:
                    check.add(option_path, "blank", "Must not be blank.")
        answer = check.text(question, "correctOption", path)
        if answer is not None and answer not in ("A", "B", "C", "D"):
            check.add(f"{path}.correctOption", "answer", "Choose exactly one of A, B, C, D.")
    return check.errors


def validate_manifest(data):
    """Validate only the public allowlist shape; exported files need a separate check."""
    data = normalize_manifest(data)
    check = _Checks()
    if not check.obj(data, "$", ("schemaVersion", "units")):
        return check.errors
    check.version(data, "$")
    units = data.get("units")
    if not isinstance(units, list):
        check.add("$.units", "type", "Expected an array of allowed units.")
        return check.errors
    if len(units) > 12:
        check.add("$.units", "unit_count", "At most 12 units are allowed.")
    seen = set()
    for index, entry in enumerate(units):
        path = f"$.units[{index}]"
        if not check.obj(entry, path, ("unitId", "title", "file")):
            continue
        unit_id = check.unit_id(entry, path)
        check.text(entry, "title", path)
        filename = check.text(entry, "file", path)
        expected_file = f"{unit_id}.json" if isinstance(unit_id, str) else None
        if filename is not None and filename != expected_file:
            check.add(f"{path}.file", "filename", "file must be exactly <unitId>.json; paths and remote URLs are forbidden.")
        if unit_id is not None:
            if unit_id in seen:
                check.add(f"{path}.unitId", "duplicate_unit", "Unit appears more than once in the allowlist.")
            seen.add(unit_id)
    return check.errors


def read_json(path):
    """UTF-8 JSON reader with JSON-standard rejection of NaN/Infinity."""
    def reject_constant(value):
        raise ValueError(f"Invalid JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant)
