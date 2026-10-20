from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.contract_cases import fixture
from tests.contract_cases_v2 import answer_cases, fixture_v2
from tools.assignment_data import (
    accepts_answer, read_json, validate_manifest, validate_unit, validate_unit_v1, validate_unit_v2,
)
from tools.assignment_editor_model import EditorError, EditorModel, FileConflict, UnitDraft, ValidationError, load_document
from tools.validate_assignments import validate_path

ROOT = Path(__file__).resolve().parents[1]


class V2ValidationTests(unittest.TestCase):
    def test_explicit_validators_do_not_reinterpret_other_versions(self):
        self.assertEqual(validate_unit_v1(fixture()), [])
        self.assertTrue(validate_unit_v2(fixture()))
        self.assertEqual(validate_unit_v2(fixture_v2()), [])
        self.assertTrue(validate_unit_v1(fixture_v2()))
        data = fixture()
        data["questions"][0]["correctOptions"] = ["A"]
        self.assertTrue(validate_unit_v1(data))

    def test_single_student_choice_membership_and_invalid_selections(self):
        for case in answer_cases():
            with self.subTest(case=case):
                self.assertEqual(accepts_answer(case["question"], case["selected"]), case["expected"])

    @unittest.skipUnless(shutil.which("node"), "Optional Node answer parity test")
    def test_node_answer_membership_matches_python(self):
        script = "const fs=require('node:fs'),v=require('./js/assignment-validator.js');const c=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(c.map(x=>v.acceptsAnswer(x.question,x.selected))));"
        result = subprocess.run(["node", "-e", script], cwd=ROOT, input=json.dumps(answer_cases()), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [case["expected"] for case in answer_cases()])

    def test_cli_validates_v2_units_and_v1_manifest(self):
        self.assertEqual(validate_path(ROOT / "tests/fixtures/v2/manifest.json"), [])


class V2DraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.model = EditorModel(schema_version=2)

    def tearDown(self):
        self.temp.cleanup()

    def valid(self, unit_id="S01", five=False):
        data = fixture_v2("S02.json" if five else "S01.json")
        data["unitId"] = unit_id
        draft = UnitDraft(data)
        self.model.install(draft)
        return draft

    def test_all_twelve_incomplete_v2_drafts_save_reload_and_preserve_empty_answers(self):
        for unit_id, draft in self.model.drafts.items():
            draft.unit["title"] = f"{unit_id} 未完成 🧪"
            path = self.root / f"{unit_id}.draft.json"
            draft.save(path)
            restored = load_document(path)
            self.assertEqual(restored.document(), draft.document())
            self.assertEqual(restored.unit["questions"][0]["correctOptions"], [])
            self.assertFalse(restored.dirty)
            self.assertEqual(read_json(path)["draftVersion"], 2)
            with self.assertRaises(ValidationError):
                self.model.export_unit(unit_id, self.root / "export")

    def test_retained_d_and_q05_save_reload_restore_text_flags_and_order(self):
        draft = self.valid(five=True)
        draft.set_option_count(4, 4)
        fifth = draft.unit["questions"][4]
        fifth["options"][3] = "保留 D\nSecond line"
        fifth["correctOptions"] = ["D", "A", "C"]
        before = deepcopy(fifth)
        draft.set_option_count(4, 3)
        self.assertEqual(fifth["correctOptions"], ["A", "C"])
        draft.set_question_count(4)
        path = self.root / "S01.draft.json"
        draft.save(path)
        restored = load_document(path)
        restored.set_question_count(5)
        restored.set_option_count(4, 4)
        self.assertEqual(restored.unit["questions"][4], before)
        self.assertEqual(restored.parked_options, {})

    def test_removing_only_accepted_d_blocks_export_until_active_answer_selected(self):
        draft = self.valid()
        draft.set_option_count(0, 4)
        draft.unit["questions"][0]["options"][3] = "Dummy D"
        draft.unit["questions"][0]["correctOptions"] = ["D"]
        draft.set_option_count(0, 3)
        self.assertEqual(draft.unit["questions"][0]["correctOptions"], [])
        with self.assertRaisesRegex(ValidationError, "Select at least one"):
            self.model.export_unit("S01", self.root / "export")
        draft.unit["questions"][0]["correctOptions"] = ["B"]
        path = self.model.export_unit("S01", self.root / "export")
        exported = read_json(path)
        self.assertEqual(len(exported["questions"][0]["options"]), 3)
        self.assertNotIn("parkedOptions", exported)
        self.assertEqual(exported["questions"][0]["correctOptions"], ["B"])
        draft.set_option_count(0, 4)
        self.assertEqual(set(draft.unit["questions"][0]["correctOptions"]), {"B", "D"})

    def test_incomplete_reference_preserved_and_all_eleven_empty_urls_block_export(self):
        draft = self.valid(five=True)
        draft.unit["googleFormUrl"] = ""
        for question in draft.unit["questions"]:
            question["questionVideoUrl"] = question["explanationVideoUrl"] = ""
        draft.unit["questions"][3]["options"] = ["測試一", "測試二", "測試三", "測試四"]
        reference = self.root / "S01_reference_v2_incomplete.json"
        reference.write_text(json.dumps(draft.unit, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(EditorError):
            load_document(reference)  # Normal public import retains strict filename checks.
        imported = load_document(reference, allow_reference_filename=True)
        self.assertEqual(imported.unit, draft.unit)
        self.assertFalse(imported.allow_play)
        self.assertIsNone(imported.path)
        self.assertEqual(len(imported.validate()), 11)
        self.assertTrue(all(error.code == "blank" for error in imported.validate()))
        self.model.install(imported)
        with self.assertRaises(ValidationError):
            self.model.export_unit("S01", self.root / "export")
        self.assertFalse((self.root / "export").exists())
        imported.allow_play = True
        private = self.root / "S01.draft.json"
        imported.save(private)
        self.assertTrue(load_document(private).allow_play)
        copied = load_document(private, allow_reference_filename=True)
        self.assertEqual(copied.unit, imported.unit)
        self.assertFalse(copied.allow_play)
        self.assertIsNone(copied.path)
        self.assertTrue(copied.dirty)

    def test_explicit_conversion_preserves_v1_source_and_retained_fifth_question(self):
        source = UnitDraft(fixture("S02.json"), allow_play=True)
        source.set_question_count(4)
        path = self.root / "S02.draft.json"
        source.save(path)
        original = path.read_bytes()
        converted = load_document(path).converted_to_v2()
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(read_json(path)["draftVersion"], 1)
        self.assertEqual(set(read_json(path)), {"draftVersion", "allowPlay", "unit", "parkedQuestion"})
        self.assertIsNone(converted.path)
        self.assertTrue(converted.dirty)
        self.assertTrue(converted.allow_play)
        self.assertEqual(converted.unit["schemaVersion"], 2)
        for original_q, converted_q in zip(source.unit["questions"], converted.unit["questions"], strict=True):
            self.assertEqual(converted_q["correctOptions"], [original_q["correctOption"]])
            self.assertEqual(converted_q["options"], original_q["options"])
        self.assertEqual(converted.parked_question["correctOptions"], [source.parked_question["correctOption"]])
        converted.save(self.root / "S02 v2.draft.json")
        self.assertEqual(path.read_bytes(), original)

    def test_empty_v1_answer_converts_to_empty_list_without_making_draft_publishable(self):
        old = UnitDraft.new("S01")
        converted = old.converted_to_v2()
        self.assertEqual(converted.unit["questions"][0]["correctOptions"], [])
        self.assertTrue(converted.validate())
        old.unit["questions"][0]["correctOption"] = "AB"
        with self.assertRaises(EditorError):
            old.converted_to_v2()
        self.assertEqual(old.unit["questions"][0]["correctOption"], "AB")
        with self.assertRaises(EditorError):
            old.set_option_count(0, 3)

    def test_mixed_version_manifest_and_accepted_answer_staleness(self):
        draft = self.valid()
        draft.allow_play = True
        legacy_data = fixture("S02.json")
        legacy = UnitDraft(legacy_data, allow_play=True)
        self.model.install(legacy)
        self.model.export_unit("S01", self.root / "export")
        self.model.export_unit("S02", self.root / "export")
        manifest_path = self.model.export_manifest(self.root / "export")
        manifest = read_json(manifest_path)
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(validate_manifest(manifest), [])
        self.assertEqual(validate_path(manifest_path), [])
        draft.unit["questions"][0]["correctOptions"].append("C")
        self.assertEqual(self.model.export_state("S01", self.root / "export"), "Stale (changed)")
        before = manifest_path.read_bytes()
        with self.assertRaises(ValidationError):
            self.model.export_manifest(self.root / "export", overwrite=True)
        self.assertEqual(manifest_path.read_bytes(), before)
        self.model.export_unit("S01", self.root / "export", overwrite=True)
        self.assertEqual(self.model.export_state("S01", self.root / "export"), "Current")
        draft.set_option_count(0, 4)
        self.assertEqual(self.model.export_state("S01", self.root / "export"), "Stale (invalid)")

    def test_v2_migration_invalidates_v1_export_until_reexported(self):
        old = UnitDraft(fixture(), allow_play=True)
        self.model.install(old)
        self.model.export_unit("S01", self.root / "export")
        self.model.install(old.converted_to_v2())
        self.assertEqual(self.model.export_state("S01", self.root / "export"), "Stale (changed)")
        with self.assertRaises(ValidationError):
            self.model.build_manifest(self.root / "export")

    def test_v2_draft_format_mismatch_and_malformed_retained_data_rejected(self):
        draft = self.valid()
        draft.set_option_count(1, 3)
        document = draft.document()
        invalid = [dict(document, draftVersion=1), dict(document, draftVersion=3), dict(document, parkedOptions=[])]
        for bad in (
            {"Q99":{"text":"d", "accepted":True, "position":0}},
            {"Q02":{"text":None, "accepted":True, "position":0}},
            {"Q02":{"text":"d", "accepted":"yes", "position":0}},
            {"Q02":{"text":"d", "accepted":True, "position":True}},
            {"Q02":{"text":"d", "accepted":False, "position":0}},
        ):
            invalid.append(dict(document, parkedOptions=bad))
        for answers in (["D"], ["A", "A"], ["E"], [None]):
            bad = deepcopy(document)
            bad["unit"]["questions"][0]["correctOptions"] = answers
            invalid.append(bad)
        path = self.root / "S01.draft.json"
        for bad in invalid:
            with self.subTest(bad=bad):
                path.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises(EditorError):
                    load_document(path)

    def test_v2_failed_atomic_save_and_external_conflict_keep_all_selections(self):
        draft = self.valid()
        path = self.root / "S01.draft.json"
        draft.save(path)
        before = path.read_bytes()
        draft.unit["questions"][0]["correctOptions"] = ["A", "B"]
        with patch("tools.assignment_editor_model.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                draft.save(path, overwrite=True)
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue(draft.dirty)
        path.write_text("External edits", encoding="utf-8")
        with self.assertRaises(FileConflict):
            draft.save(path, overwrite=True)
        self.assertEqual(draft.unit["questions"][0]["correctOptions"], ["A", "B"])

    def test_numeric_two_point_zero_can_roundtrip_in_private_integer_envelope(self):
        draft = self.valid()
        draft.unit["schemaVersion"] = 2.0
        path = self.root / "S01.draft.json"
        draft.save(path)
        self.assertEqual(read_json(path)["draftVersion"], 2)
        self.assertEqual(load_document(path).unit, draft.unit)


if __name__ == "__main__":
    unittest.main()
