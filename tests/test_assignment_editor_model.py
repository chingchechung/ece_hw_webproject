from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.contract_cases import fixture
from tools.assignment_data import normalize_unit, read_json, validate_manifest, validate_unit
from tools.assignment_editor_model import (
    REPOSITORY, UNIT_IDS, EditorError, EditorModel, FileConflict, OverwriteRequired,
    UnitDraft, ValidationError, atomic_write_json, check_destination, load_document,
)


class EditorModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.model = EditorModel()

    def tearDown(self):
        self.temp.cleanup()

    def valid(self, unit_id="S01", five=False):
        data = fixture("S02.json" if five else "S01.json")
        data["unitId"] = unit_id
        draft = UnitDraft(data)
        self.model.install(draft)
        return draft

    def test_create_save_reload_incomplete_and_independent_all_twelve(self):
        self.assertEqual(tuple(self.model.drafts), UNIT_IDS)
        for unit_id, draft in self.model.drafts.items():
            draft.unit["title"] = f" {unit_id} 未完成 🧪 "
            draft.unit["questions"][0]["prompt"] = "Line one\n第二行\n"
            draft.allow_play = unit_id in ("S01", "S12")
            path = self.root / "private" / f"{unit_id}.draft.json"
            before = deepcopy(draft.document())
            self.assertTrue(draft.dirty)
            self.assertTrue(draft.validate())
            draft.save(path)
            restored = load_document(path)
            self.assertEqual(restored.document(), before)
            self.assertFalse(restored.dirty)
            self.assertEqual(read_json(path)["unit"], draft.unit)
        self.model.drafts["S01"].unit["questions"][0]["options"][0] = "Only S01"
        self.assertEqual(self.model.drafts["S12"].unit["questions"][0]["options"][0], "")
        self.assertEqual(self.model.dirty_units, ["S01"])

    def test_fifth_question_roundtrip_without_data_loss_and_no_public_leak(self):
        draft = self.valid(five=True)
        fifth = deepcopy(draft.unit["questions"][4])
        first_four = deepcopy(draft.unit["questions"][:4])
        draft.set_question_count(4)
        self.assertEqual(draft.parked_question, fifth)
        self.assertEqual(draft.unit["questions"], first_four)
        draft.save(self.root / "S01.draft.json")
        restored = load_document(self.root / "S01.draft.json")
        self.model.install(restored)
        public = read_json(self.model.export_unit("S01", self.root / "export"))
        self.assertEqual(len(public["questions"]), 4)
        self.assertNotIn("parkedQuestion", public)
        restored.set_question_count(5)
        self.assertEqual(restored.unit["questions"][4], fifth)
        restored.set_question_count(5)
        self.assertEqual(len(restored.unit["questions"]), 5)
        with self.assertRaises(EditorError):
            restored.set_question_count(6)

    def test_valid_export_reuses_phase_one_without_mutating_source(self):
        for five in (False, True):
            draft = self.valid("S01", five=five)
            draft.unit["title"] = " 中文 Logic Gates 🧪 "
            draft.unit["googleFormUrl"] = "https://forms.gle/EmiMazeTestOnly123"
            draft.unit["questions"][0]["options"] = [" D ", " C ", " B ", " A "]
            draft.unit["questions"][0]["correctOption"] = "C"
            before = deepcopy(draft.document())
            path = self.model.export_unit("S01", self.root / str(five))
            self.assertEqual(validate_unit(read_json(path), path.name), [])
            self.assertEqual(read_json(path), normalize_unit(draft.unit))
            self.assertEqual(draft.document(), before)
            self.assertNotIn(b"\\u4e2d", path.read_bytes())
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))
            self.assertEqual(self.model.export_state("S01", path.parent), "Current")

    def test_invalid_exports_do_not_create_or_replace_any_files(self):
        folder = self.root / "export"
        with self.assertRaises(ValidationError) as context:
            self.model.export_unit("S01", folder)
        self.assertIn("S01 $.googleFormUrl", str(context.exception))
        self.assertFalse(folder.exists())
        self.valid()
        path = self.model.export_unit("S01", folder)
        before = path.read_bytes()
        self.model.drafts["S01"].unit["questions"][0]["correctOption"] = "AB"
        with self.assertRaises(ValidationError):
            self.model.export_unit("S01", folder, overwrite=True)
        self.assertEqual(path.read_bytes(), before)

    def test_manifest_only_explicit_allowed_current_exports(self):
        s01, s02 = self.valid(), self.valid("S02", five=True)
        self.model.export_unit("S01", self.root)
        self.model.export_unit("S02", self.root)
        s02.allow_play = True
        path = self.model.export_manifest(self.root)
        manifest = read_json(path)
        self.assertEqual([entry["unitId"] for entry in manifest["units"]], ["S02"])
        self.assertEqual(validate_manifest(manifest), [])
        s01.allow_play = True
        self.model.export_manifest(self.root, overwrite=True)
        self.assertEqual([entry["unitId"] for entry in read_json(path)["units"]], ["S01", "S02"])
        s01.allow_play = s02.allow_play = False
        self.model.export_manifest(self.root, overwrite=True)
        self.assertEqual(read_json(path)["units"], [])
        self.assertTrue((self.root / "S01.json").exists())  # Disallowing never deletes files.

    def test_manifest_missing_invalid_stale_and_changed_folder_blocked(self):
        draft = self.valid()
        draft.allow_play = True
        with self.assertRaisesRegex(ValidationError, "Missing"):
            self.model.build_manifest(self.root)
        exported = self.model.export_unit("S01", self.root)
        self.model.export_manifest(self.root)
        old_manifest = (self.root / "manifest.json").read_bytes()
        draft.unit["questions"][0]["correctOption"] = "D"
        self.assertEqual(self.model.export_state("S01", self.root), "Stale (changed)")
        with self.assertRaisesRegex(ValidationError, "Stale"):
            self.model.export_manifest(self.root, overwrite=True)
        self.assertEqual((self.root / "manifest.json").read_bytes(), old_manifest)
        self.model.export_unit("S01", self.root, overwrite=True)
        self.assertEqual(self.model.export_state("S01", self.root), "Current")
        with self.assertRaisesRegex(ValidationError, "Missing"):
            self.model.build_manifest(self.root / "other")
        exported.write_text("{broken", encoding="utf-8")
        self.assertEqual(self.model.export_state("S01", self.root), "Stale (unreadable)")
        exported.write_text('{"schemaVersion": 2}', encoding="utf-8")
        self.assertEqual(self.model.export_state("S01", self.root), "Stale (invalid)")

    def test_manifest_detects_external_export_tampering_and_invalid_allowed_draft(self):
        draft = self.valid()
        draft.allow_play = True
        path = self.model.export_unit("S01", self.root)
        changed = read_json(path)
        changed["questions"][1]["explanationVideoUrl"] = "https://youtu.be/xDARFvArIpc"
        path.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "Stale"):
            self.model.build_manifest(self.root)
        self.model.drafts["S12"].allow_play = True
        with self.assertRaises(ValidationError) as context:
            self.model.build_manifest(self.root)
        self.assertTrue(any("S12" in item for item in context.exception.messages))

    def test_staleness_based_on_normalized_public_content(self):
        draft = self.valid()
        self.model.export_unit("S01", self.root)
        draft.unit["title"] = " " + draft.unit["title"] + " "
        draft.allow_play = True
        self.assertEqual(self.model.export_state("S01", self.root), "Current")
        self.assertEqual(len(self.model.build_manifest(self.root)["units"]), 1)
        draft.set_question_count(5)
        self.assertEqual(self.model.export_state("S01", self.root), "Stale (invalid)")

    def test_public_import_is_new_private_draft_not_a_bound_public_save(self):
        source = self.root / "S02.json"
        source.write_text(json.dumps(fixture("S02.json")), encoding="utf-8")
        draft = load_document(source)
        self.assertIsNone(draft.path)
        self.assertFalse(draft.allow_play)
        self.assertTrue(draft.dirty)
        self.assertEqual(draft.validate(), [])
        draft.save(self.root / "Imported S02.draft.json")
        self.assertEqual(read_json(source), fixture("S02.json"))
        with self.assertRaises(EditorError):
            draft.save(source, overwrite=True)

    def test_import_incomplete_fields_fill_without_reordering_or_trimming(self):
        unit = {"schemaVersion":1, "unitId":"S01", "title":" incomplete "}
        path = self.root / "S01.json"
        path.write_text(json.dumps(unit), encoding="utf-8")
        draft = load_document(path)
        self.assertEqual(draft.unit["title"], " incomplete ")
        self.assertEqual(len(draft.unit["questions"]), 4)
        self.assertEqual(draft.unit["questions"][0]["correctOption"], "")

    def test_malformed_imports_rejected_without_changing_model(self):
        before = {key: draft.document() for key, draft in self.model.drafts.items()}
        malformed = [None, [], {"schemaVersion":1, "unitId":"S13"}]
        for mutate in (
            lambda data: data.update(schemaVersion=2),
            lambda data: data.update(title=None),
            lambda data: data["questions"][0].update(id="Q03"),
            lambda data: data["questions"][0].update(options=["one"]),
            lambda data: data.update(allowPlay=True),
        ):
            data = fixture()
            mutate(data)
            malformed.append(data)
        doc = UnitDraft.new("S01").document()
        malformed.extend([dict(doc, draftVersion=2), dict(doc, allowPlay="yes"), dict(doc, extra="unknown"), dict(doc, parkedQuestion={"id":"Q01"})])
        path = self.root / "S01.json"
        for raw in malformed:
            with self.subTest(raw=raw):
                path.write_text(json.dumps(raw), encoding="utf-8")
                with self.assertRaises(EditorError):
                    load_document(path)
        self.assertEqual({key: draft.document() for key, draft in self.model.drafts.items()}, before)

    def test_private_and_public_paths_never_written_to_source_directories(self):
        self.valid()
        for target in (REPOSITORY / "assignments", REPOSITORY / "tests", REPOSITORY / "emi_maze_dualview_v1.2", REPOSITORY):
            with self.subTest(target=target):
                with self.assertRaises(EditorError):
                    self.model.export_unit("S01", target)
                with self.assertRaises(EditorError):
                    self.model.drafts["S01"].save(target / "S01.draft.json")
        for raw in ("https://example.com/file.json", "//server/share/file.json", "\\\\server\\share\\file.json"):
            with self.assertRaises(EditorError):
                check_destination(raw, "draft")
        self.assertEqual(check_destination(REPOSITORY / "teacher_data/S01.draft.json", "draft").parent.name, "teacher_data")

    def test_symlinks_and_directory_aliases_do_not_bypass_privacy(self):
        draft = self.valid()
        alias = self.root / "public-alias"
        alias.symlink_to(REPOSITORY / "assignments", target_is_directory=True)
        with self.assertRaises(EditorError):
            self.model.export_unit("S01", alias)
        path = self.root / "S01.json"
        path.symlink_to(REPOSITORY / "tests/fixtures/S01.json")
        self.assertEqual(self.model.export_state("S01", self.root), "Stale (symlink)")
        with self.assertRaises(EditorError):
            self.model.export_unit("S01", self.root, overwrite=True)
        self.assertTrue(draft.dirty)

    def test_export_refuses_folders_containing_private_drafts(self):
        draft = self.valid()
        draft.save(self.root / "S01.draft.json")
        with self.assertRaisesRegex(EditorError, "private drafts"):
            self.model.export_unit("S01", self.root)
        self.assertFalse((self.root / "S01.json").exists())


class AtomicSaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "S01.draft.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_existing_file_requires_consent_and_saved_file_conflicts_are_blocked(self):
        draft = UnitDraft.new("S01")
        draft.save(self.path)
        before = self.path.read_bytes()
        draft.unit["title"] = "Changed"
        with self.assertRaises(OverwriteRequired):
            draft.save(self.path)
        self.assertEqual(self.path.read_bytes(), before)
        draft.save(self.path, overwrite=True)
        self.assertFalse(draft.dirty)
        self.path.write_text("External edits", encoding="utf-8")
        with self.assertRaises(FileConflict):
            draft.save(self.path, overwrite=True)
        self.assertEqual(self.path.read_text(), "External edits")
        self.path.unlink()
        with self.assertRaises(FileConflict):
            draft.save(self.path)

    def test_failed_atomic_replace_keeps_original_and_dirty_state_and_cleans_temp(self):
        draft = UnitDraft.new("S01")
        draft.save(self.path)
        before = self.path.read_bytes()
        draft.unit["title"] = "Must survive failure"
        with patch("tools.assignment_editor_model.os.replace", side_effect=OSError("disk problem")):
            with self.assertRaises(OSError):
                draft.save(self.path, overwrite=True)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertTrue(draft.dirty)
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), [self.path.name])

    def test_concurrent_new_file_is_never_clobbered(self):
        def competing_writer(_source, target):
            Path(target).write_text("Another writer", encoding="utf-8")
            raise FileExistsError()
        operation = "os.rename" if os.name == "nt" else "os.link"
        with patch(f"tools.assignment_editor_model.{operation}", side_effect=competing_writer):
            with self.assertRaises(OverwriteRequired):
                atomic_write_json(self.path, {"draftVersion":1})
        self.assertEqual(self.path.read_text(), "Another writer")
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_failed_first_write_and_non_json_data_leave_no_partial_target(self):
        with patch("tools.assignment_editor_model.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                atomic_write_json(self.path, {"text":"測試"})
        self.assertEqual(list(self.root.iterdir()), [])
        with self.assertRaises(ValueError):
            atomic_write_json(self.path, {"number":float("nan")})
        self.assertFalse(self.path.exists())

    def test_deterministic_readable_utf8_output(self):
        data = {"label":"中文 🧪", "lines":"one\ntwo"}
        atomic_write_json(self.path, data)
        before = self.path.read_bytes()
        atomic_write_json(self.path, data, overwrite=True)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(read_json(self.path), data)
        self.assertIn("中文", self.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
