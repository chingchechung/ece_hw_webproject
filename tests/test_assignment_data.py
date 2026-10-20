from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.contract_cases import contract_cases, fixture
from tools.assignment_data import (
    SCHEMA_DIR, UNIT_SCHEMA, normalize_manifest, normalize_unit,
    read_json, validate_manifest, validate_unit,
)
from tools.validate_assignments import main, validate_path
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]


def validate_case(case):
    if case["kind"] == "unit":
        return validate_unit(case["data"], case["filename"])
    return validate_manifest(case["data"])


class AssignmentContractTests(unittest.TestCase):
    def test_publish_acceptance_corpus(self):
        for case in contract_cases():
            with self.subTest(case=case["name"]):
                errors = validate_case(case)
                self.assertEqual(not errors, case["valid"], [issue.as_dict() for issue in errors])

    def test_validation_and_normalization_never_mutate_drafts(self):
        for case in contract_cases():
            original = deepcopy(case["data"])
            validate_case(case)
            self.assertEqual(case["data"], original, case["name"])
        draft = {"unitId": "S01", "title": " unfinished "}
        self.assertTrue(validate_unit(draft))  # Save-draft need not call publish validation.
        self.assertEqual(draft, {"unitId": "S01", "title": " unfinished "})

    def test_normalization_preserves_options_answer_and_optional_fields(self):
        data = fixture()
        data["title"] = "\ufeff 中文 🧪 \u3000"
        data["questions"][0]["options"] = [" second ", " first ", " fourth ", " third "]
        normalized = normalize_unit(data)
        self.assertEqual(normalized["title"], "中文 🧪")
        self.assertEqual(normalized["questions"][0]["options"], ["second", "first", "fourth", "third"])
        self.assertEqual(normalized["questions"][0]["correctOption"], "A")
        self.assertNotEqual(data["title"], normalized["title"])
        del data["questions"][0]["prompt"]
        self.assertNotIn("prompt", normalize_unit(data)["questions"][0])
        self.assertEqual(validate_unit(data, "S01.json"), [])

    def test_precise_errors(self):
        data = fixture()
        del data["questions"][2]["explanationVideoUrl"]
        data["questions"][1]["correctOption"] = "AB"
        data["questions"][3]["options"][2] = " "
        errors = validate_unit(data, "S01.json")
        self.assertEqual([(e.path, e.code) for e in errors], [
            ("$.questions[1].correctOption", "answer"),
            ("$.questions[2].explanationVideoUrl", "required"),
            ("$.questions[3].options[2]", "blank"),
        ])

    def test_public_allowlist_empty_and_test_fixtures_separate(self):
        public = ROOT / "assignments"
        self.assertEqual(sorted(p.name for p in public.iterdir()), ["manifest.json"])
        self.assertEqual(read_json(public / "manifest.json"), {"schemaVersion": 1, "units": []})
        self.assertEqual(validate_path(public / "manifest.json"), [])
        self.assertEqual(validate_path(ROOT / "tests/fixtures/manifest.json"), [])

    @unittest.skipUnless(shutil.which("node"), "Node is only needed for optional Python/JS parity tests")
    def test_javascript_python_parity_for_all_cases_and_schema_patterns(self):
        cases = contract_cases()
        process = subprocess.run(
            ["node", str(ROOT / "tests/validate_in_js.cjs")],
            input=json.dumps(cases, ensure_ascii=False), capture_output=True, text=True, check=True,
        )
        output = json.loads(process.stdout)
        self.assertEqual(output["rules"], {key: UNIT_SCHEMA["$defs"][key]["pattern"] for key in ("youtubeUrl", "googleFormUrl")})
        for case, result in zip(cases, output["results"], strict=True):
            with self.subTest(case=case["name"]):
                self.assertEqual(result["errors"], [issue.as_dict() for issue in validate_case(case)])
                normalized = normalize_unit(case["data"]) if case["kind"] == "unit" else normalize_manifest(case["data"])
                self.assertEqual(result["normalized"], normalized)

    def test_json_schemas_agree_with_acceptance_corpus(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Optional jsonschema package unavailable; runtime validators use stdlib only")
        manifest_schema = read_json(SCHEMA_DIR / "manifest-v1.schema.json")
        validators = {}
        for kind, schema in (("unit", UNIT_SCHEMA), ("manifest", manifest_schema)):
            Draft202012Validator.check_schema(schema)
            validators[kind] = Draft202012Validator(schema)
        for case in contract_cases():
            with self.subTest(case=case["name"]):
                normalized = normalize_unit(case["data"]) if case["kind"] == "unit" else normalize_manifest(case["data"])
                errors = list(validators[case["kind"]].iter_errors(normalized))
                expected = case["valid"]
                # A unit's filename is external context, not part of its JSON schema.
                runtime_errors = validate_case(case)
                if case["kind"] == "unit" and runtime_errors and all(e.code == "filename" for e in runtime_errors):
                    expected = True
                self.assertEqual(not errors, expected, [e.message for e in errors])


class ValidationCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_utf8_json_parse_errors_and_nonfinite_numbers(self):
        path = self.write("S01.json", fixture())
        self.assertEqual(read_json(path), fixture())
        for source in ('{"schemaVersion":', '{"schemaVersion":NaN}', '{"schemaVersion":Infinity}', '\ufeff{}'):
            path.write_text(source, encoding="utf-8")
            self.assertIn("cannot read UTF-8 JSON", validate_path(path)[0])
        path.write_bytes(b"\xff\xfe")
        self.assertIn("cannot read UTF-8 JSON", validate_path(path)[0])

    def test_manifest_missing_mismatched_and_invalid_exports(self):
        manifest = {"schemaVersion":1, "units":[fixture("manifest.json")["units"][0]]}
        path = self.write("manifest.json", manifest)
        self.assertIn("cannot read", validate_path(path)[0])
        unit_path = self.write("S01.json", fixture())
        self.assertEqual(validate_path(path), [])
        changed = fixture()
        changed["title"] = "Changed since manifest was prepared"
        self.write("S01.json", changed)
        self.assertIn("title does not match", validate_path(path)[0])
        changed["unitId"] = "S02"
        self.write("S01.json", changed)
        self.assertTrue(any("[filename]" in error for error in validate_path(path)))
        unit_path.unlink()
        unit_path.symlink_to(ROOT / "tests/fixtures/S01.json")
        self.assertIn("symlink", validate_path(path)[0])

    def test_invalid_manifest_never_reads_traversal_target(self):
        data = fixture("manifest.json")
        data["units"][0]["file"] = "../teacher_data/S01.json"
        path = self.write("manifest.json", data)
        errors = validate_path(path)
        self.assertTrue(any("[filename]" in error for error in errors))
        self.assertFalse(any("cannot read" in error for error in errors))

    def test_cli_exit_status_diagnostics_and_no_writes(self):
        path = self.write("S01.json", fixture())
        before = {p: p.read_bytes() for p in self.root.iterdir()}
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(main([str(path)]), 0)
            self.assertEqual(main([str(self.root / "S02.json")]), 1)
        self.assertIn("VALID:", out.getvalue())
        self.assertIn("cannot read", err.getvalue())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.iterdir()})


if __name__ == "__main__":
    unittest.main()
