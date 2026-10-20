"""Offline versioned v1/v2 publish validation. Incomplete drafts may be saved.

Validation never mutates input. Normalize ordinary text for export with
normalize_unit(); IDs and accepted-answer labels are exact and are not changed.
No GUI, network operations, publishing or filesystem writes occur here.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
UNIT_SCHEMA = json.loads((SCHEMA_DIR / "assignment-v1.schema.json").read_text(encoding="utf-8"))
UNIT_SCHEMA_V2 = json.loads((SCHEMA_DIR / "assignment-v2.schema.json").read_text(encoding="utf-8"))
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
    def __init__(self, schema_version=1):
        self.errors = []
        self.schema_version = schema_version

    def add(self, path, code, message):
        self.errors.append(ValidationIssue(path, code, message))

    def obj(self, value, path, allowed):
        if not isinstance(value, dict):
            self.add(path, "type", "Expected an object.")
            return False
        for key in sorted(set(value) - set(allowed)):
            self.add(f"{path}.{key}", "unknown_field", f"Unknown field in schema v{self.schema_version}.")
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
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != self.schema_version:
            self.add(f"{path}.schemaVersion", "schema_version", f"schemaVersion must be the number {self.schema_version}.")

    def unit_id(self, obj, path):
        value = self.text(obj, "unitId", path)
        if value is not None and not UNIT_ID.fullmatch(value):
            self.add(f"{path}.unitId", "unit_id", "Expected S01 through S12.")
        return value

    def url(self, obj, key, path, pattern, message):
        value = self.text(obj, key, path)
        if value is not None and not pattern.fullmatch(value):
            self.add(f"{path}.{key}", "url", message)


def _validate_unit(data, filename, version):
    data = normalize_unit(data)
    check = _Checks(version)
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
        keys = QUESTION_KEYS if version == 1 else tuple("correctOptions" if key == "correctOption" else key for key in QUESTION_KEYS)
        if not check.obj(question, path, keys):
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
            message = "Expected an array of four options in A-D order." if version == 1 else "Expected an array of three or four options in A-D order."
            check.add(f"{path}.options", "type", message)
        else:
            if len(options) not in ((4,) if version == 1 else (3, 4)):
                message = "Exactly four options are required in A-D order." if version == 1 else "Exactly three or four options are required in A-D order."
                check.add(f"{path}.options", "option_count", message)
            for option_index, option in enumerate(options):
                option_path = f"{path}.options[{option_index}]"
                if not isinstance(option, str):
                    check.add(option_path, "type", "Expected a string.")
                elif not option:
                    check.add(option_path, "blank", "Must not be blank.")
        if version == 1:
            answer = check.text(question, "correctOption", path)
            if answer is not None and answer not in ("A", "B", "C", "D"):
                check.add(f"{path}.correctOption", "answer", "Choose exactly one of A, B, C, D.")
        else:
            _check_accepted_answers(check, question, path, options)
    return check.errors


def _check_accepted_answers(check, question, path, options):
    field = f"{path}.correctOptions"
    if "correctOptions" not in question:
        check.add(field, "required", "Required field is missing.")
        return
    answers = question["correctOptions"]
    if not isinstance(answers, list):
        check.add(field, "type", "Expected an array of accepted answer labels.")
        return
    if not answers:
        check.add(field, "answer_count", "Select at least one accepted answer.")
    seen = set()
    for index, answer in enumerate(answers):
        item_path = f"{field}[{index}]"
        if not isinstance(answer, str):
            check.add(item_path, "type", "Expected a string.")
            continue
        if answer not in ("A", "B", "C", "D"):
            check.add(item_path, "answer", "Accepted labels must be A, B, C or D.")
        elif isinstance(options, list) and "ABCD".index(answer) >= len(options):
            check.add(item_path, "answer_range", "Accepted label has no corresponding option.")
        if answer in seen:
            check.add(item_path, "duplicate_answer", "Accepted labels must be distinct.")
        seen.add(answer)


def validate_unit_v1(data, filename=None):
    """The original strict v1 contract; never converts or accepts v2 data."""
    return _validate_unit(data, filename, 1)


def validate_unit_v2(data, filename=None):
    return _validate_unit(data, filename, 2)


def validate_unit(data, filename=None):
    """Dispatch explicitly by schemaVersion; preserve the v1 fallback errors."""
    if isinstance(data, dict) and data.get("schemaVersion") == 2:
        return validate_unit_v2(data, filename)
    return validate_unit_v1(data, filename)


def accepts_answer(question, selected):
    """Pure single-choice rule for future integration; does not modify gameplay."""
    if not isinstance(question, dict) or not isinstance(selected, str) or selected not in ("A", "B", "C", "D"):
        return False
    options = question.get("options")
    if not isinstance(options, list) or "ABCD".index(selected) >= len(options):
        return False
    if "correctOptions" in question:
        check = _Checks(2)
        _check_accepted_answers(check, question, "$", options)
        return "correctOption" not in question and not check.errors and len(options) in (3, 4) and selected in question["correctOptions"]
    return len(options) == 4 and selected == question.get("correctOption")


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
