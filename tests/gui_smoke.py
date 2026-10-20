"""Real Tk widget/controller smoke tests. Run on a desktop or under Xvfb.

Native file/message dialogs are mocked for repeatability; real entries, Text,
tabs, radio buttons, checkbuttons, selection events and callbacks are exercised.
All generated draft/export content is synthetic and confined to a temp folder.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import assignment_editor as gui
from tools.assignment_editor_model import UNIT_IDS, UnitDraft, load_document
from tools.assignment_data import read_json, validate_manifest, validate_unit
from tests.contract_cases import fixture


class GuiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.root = tk.Tk()
        self.callback_errors = []
        self.root.report_callback_exception = lambda *error: self.callback_errors.append(error)
        self.app = gui.AssignmentEditor(self.root)
        self.root.update()
        for module, name, value in (
            (gui.messagebox, "askyesnocancel", None),
            (gui.messagebox, "askyesno", False),
            (gui.messagebox, "showerror", None),
            (gui.filedialog, "askopenfilename", ""),
            (gui.filedialog, "asksaveasfilename", ""),
            (gui.filedialog, "askdirectory", ""),
        ):
            replacement = self.addCleanupPatch(module, name, value)
            setattr(self, name, replacement)

    def addCleanupPatch(self, module, name, value):
        patcher = patch.object(module, name, return_value=value)
        replacement = patcher.start()
        self.addCleanup(patcher.stop)
        return replacement

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.temp.cleanup()
        self.assertEqual(self.callback_errors, [])

    def text(self, field, value):
        field.delete("1.0", "end")
        field.insert("1.0", value)
        self.root.update()

    def choose_count(self, count):
        self.app.count_box.set(str(count))
        self.app.count_box.event_generate("<<ComboboxSelected>>")
        self.root.update()

    def import_valid(self):
        self.askopenfilename.return_value = str(ROOT / "tests/fixtures/S01.json")
        self.assertTrue(self.app.load_import())
        self.root.update()

    def select_export_folder(self):
        folder = self.directory / "export"
        folder.mkdir(exist_ok=True)
        self.askdirectory.return_value = str(folder)
        self.app.actions["choose_export"].invoke()
        self.root.update()
        self.assertEqual(self.app.export_dir, folder)
        return folder

    def test_edit_save_reload_unicode_fifth_question_and_single_radio_answer(self):
        self.assertEqual(tuple(self.app.tree.get_children()), UNIT_IDS)
        self.app.unit_title.set("S01 中文未完成 🧪")
        self.text(self.app.question_fields[0]["prompt"], "First line\n第二行\n")
        for index, button in enumerate(self.app.answer_buttons[0]):
            button.invoke()
            self.assertEqual(self.app.question_fields[0]["correctOption"].get(), "ABCD"[index])
            self.assertEqual(sum("selected" in radio.state() for radio in self.app.answer_buttons[0]), 1)
        self.choose_count(5)
        self.text(self.app.question_fields[4]["explanationText"], "Retain Q05 五")
        self.choose_count(4)
        self.assertEqual(len(self.app.notebook.tabs()), 4)
        self.app.allow_button.invoke()
        path = self.directory / "S01.draft.json"
        self.asksaveasfilename.return_value = str(path)
        self.app.actions["save"].invoke()
        self.assertTrue(path.exists())
        self.assertFalse(self.app.model.drafts["S01"].dirty)
        self.assertTrue(self.app.model.drafts["S01"].validate())  # Incomplete is saved.
        self.app.actions["new"].invoke()
        self.assertEqual(self.app.unit_title.get(), "")
        self.askopenfilename.return_value = str(path)
        self.app.actions["load"].invoke()
        self.root.update()
        self.assertEqual(self.app.unit_title.get(), "S01 中文未完成 🧪")
        self.assertTrue(self.app.allow_play.get())
        self.assertEqual(self.app._value(self.app.question_fields[0]["prompt"]), "First line\n第二行\n")
        self.choose_count(5)
        self.assertEqual(self.app._value(self.app.question_fields[4]["explanationText"]), "Retain Q05 五")

    def test_switch_prompts_keep_cancel_save_failure_and_actual_tree_selection(self):
        self.app.unit_title.set("Keep S01 changes")
        self.assertFalse(self.app.request_switch("S02"))  # Cancel by default.
        self.assertEqual(self.app.current_id, "S01")
        x, y, width, height = self.app.tree.bbox("S02", "allow")
        self.app._toggle_allow_in_list(SimpleNamespace(x=x + width // 2, y=y + height // 2))
        self.assertFalse(self.app.model.drafts["S02"].allow_play)
        self.askyesnocancel.return_value = True
        self.assertFalse(self.app.request_switch("S02"))  # Save chooser canceled.
        self.askyesnocancel.return_value = False
        self.app.tree.selection_set("S02")
        self.root.update()
        self.assertEqual(self.app.current_id, "S02")
        self.app.unit_title.set("Separate S02")
        self.app.tree.selection_set("S01")
        self.root.update()
        self.assertEqual(self.app.unit_title.get(), "Keep S01 changes")
        self.assertEqual(self.app.model.drafts["S02"].unit["title"], "Separate S02")
        self.askyesnocancel.return_value = True
        path = self.directory / "S01.draft.json"
        self.asksaveasfilename.return_value = str(path)
        self.assertTrue(self.app.request_switch("S12"))
        self.assertEqual(load_document(path).unit["title"], "Keep S01 changes")

    def test_validated_local_export_allowlist_staleness_and_overwrite_cancel(self):
        self.import_valid()
        self.assertFalse(self.app.allow_play.get())
        self.app.form_url.set("https://forms.gle/EmiMazeTestOnly123")
        self.app.actions["validate"].invoke()
        self.assertIn("VALID", self.app.output.get("1.0", "end"))
        folder = self.select_export_folder()
        self.app.allow_button.invoke()
        self.app.actions["export_unit"].invoke()
        self.app.actions["export_manifest"].invoke()
        unit_path, manifest_path = folder / "S01.json", folder / "manifest.json"
        self.assertEqual(validate_unit(read_json(unit_path), unit_path.name), [])
        self.assertEqual(validate_manifest(read_json(manifest_path)), [])
        self.assertEqual([item["unitId"] for item in read_json(manifest_path)["units"]], ["S01"])
        self.assertIn("FIRST", self.app.output.get("1.0", "end"))
        old_manifest, old_unit = manifest_path.read_bytes(), unit_path.read_bytes()
        self.app.question_fields[0]["options"][0].set("Changed answer text 中文")
        self.assertFalse(self.app.export_manifest())
        self.assertIn("Stale", self.app.output.get("1.0", "end"))
        self.assertEqual(manifest_path.read_bytes(), old_manifest)
        self.assertFalse(self.app.export_selected())  # Decline replacement.
        self.assertEqual(unit_path.read_bytes(), old_unit)
        self.askyesno.return_value = True
        self.assertTrue(self.app.export_selected())
        self.assertTrue(self.app.export_manifest())
        self.assertEqual(self.app.model.export_state("S01", folder), "Current")
        self.app.allow_button.invoke()  # Disallow; empty-manifest confirmation.
        self.askyesno.return_value = False
        self.assertFalse(self.app.export_manifest())
        self.assertEqual(manifest_path.read_bytes(), old_manifest)
        self.askyesno.return_value = True
        self.assertTrue(self.app.export_manifest())
        self.assertEqual(read_json(manifest_path)["units"], [])
        self.assertTrue(unit_path.exists())

    def test_invalid_export_precise_validation_and_bad_import_leave_data_untouched(self):
        folder = self.select_export_folder()
        self.app.unit_title.set("Still editing")
        self.assertFalse(self.app.export_selected())
        self.assertIn("S01 / Q01", self.app.output.get("1.0", "end"))
        self.assertIn("explanationVideoUrl", self.app.output.get("1.0", "end"))
        self.assertFalse((folder / "S01.json").exists())
        source = self.directory / "S01.json"
        data = fixture()
        data["schemaVersion"] = 2
        source.write_text(json.dumps(data), encoding="utf-8")
        self.askopenfilename.return_value = str(source)
        self.assertFalse(self.app.load_import())
        self.assertEqual(self.app.unit_title.get(), "Still editing")
        self.app.actions["load"].invoke()
        self.assertTrue(self.showerror.called)

    def test_replacement_and_close_cancel_save_all_and_save_conflict(self):
        self.app.unit_title.set("Unsaved S01")
        self.import_path = str(ROOT / "tests/fixtures/S01.json")
        self.askopenfilename.return_value = self.import_path
        self.assertFalse(self.app.load_import())  # Replacement prompt canceled.
        self.app.actions["new"].invoke()
        self.assertEqual(self.app.unit_title.get(), "Unsaved S01")
        self.assertFalse(self.app.on_close())
        self.askyesnocancel.return_value = False
        self.assertTrue(self.app.request_switch("S02"))
        self.app.unit_title.set("Unsaved S02")
        self.askyesnocancel.return_value = True
        first, second = self.directory / "S01.draft.json", self.directory / "S02.draft.json"
        self.asksaveasfilename.side_effect = [str(first), ""]
        self.assertFalse(self.app.on_close())
        self.assertTrue(first.exists())
        self.assertTrue(self.app.model.drafts["S02"].dirty)
        self.asksaveasfilename.side_effect = [str(second)]
        self.assertTrue(self.app.save_draft())
        second.write_text("external edits", encoding="utf-8")
        self.app.unit_title.set("Must not overwrite external edits")
        self.assertFalse(self.app.save_draft())
        self.assertEqual(second.read_text(), "external edits")
        self.assertTrue(self.app.model.drafts["S02"].dirty)
        self.asksaveasfilename.side_effect = None
        self.asksaveasfilename.return_value = str(self.directory / "Recovered S02.draft.json")
        self.assertTrue(self.app.save_draft(save_as=True))
        self.assertTrue(self.app.on_close())

    def test_open_twelve_drafts_then_bad_folder_is_all_or_nothing(self):
        for unit_id in UNIT_IDS:
            draft = UnitDraft.new(unit_id)
            draft.unit["title"] = f"{unit_id} saved title"
            draft.allow_play = unit_id == "S12"
            draft.save(self.directory / f"{unit_id}.draft.json")
        self.askdirectory.return_value = str(self.directory)
        self.app.actions["open_folder"].invoke()
        self.root.update()
        self.assertEqual(self.app.model.drafts["S12"].unit["title"], "S12 saved title")
        self.assertTrue(self.app.model.drafts["S12"].allow_play)
        before = deepcopy({key: draft.document() for key, draft in self.app.model.drafts.items()})
        (self.directory / "S12.draft.json").write_text("broken", encoding="utf-8")
        self.assertFalse(self.app.open_draft_folder())
        self.assertEqual({key: draft.document() for key, draft in self.app.model.drafts.items()}, before)

    def test_safe_folder_and_dialog_cancellations(self):
        self.assertFalse(self.app.choose_export_folder())
        self.assertFalse(self.app.load_import())
        self.assertFalse(self.app.save_draft())
        self.assertFalse(self.app.open_draft_folder())
        self.assertFalse(self.app.export_selected())
        self.askdirectory.return_value = str(ROOT / "assignments")
        self.assertFalse(self.app.choose_export_folder())
        self.assertIsNone(self.app.export_dir)
        self.assertTrue(self.showerror.called)
        self.select_export_folder()
        self.asksaveasfilename.return_value = str(self.app.export_dir / "S01.draft.json")
        self.assertFalse(self.app.save_draft())
        self.assertFalse((self.app.export_dir / "S01.draft.json").exists())

    def test_render_tabs_scroll_and_optional_screenshot(self):
        self.import_valid()
        self.choose_count(5)
        self.assertEqual(len(self.app.notebook.tabs()), 5)
        self.app.notebook.select(4)
        self.root.update()
        tab = self.app.notebook.nametowidget(self.app.notebook.tabs()[4])
        self.assertGreater(tab.canvas.bbox("all")[3], 0)
        self.app.notebook.select(0)
        self.root.geometry("1040x720")
        self.root.update()
        first_tab = self.app.notebook.nametowidget(self.app.notebook.tabs()[0])
        first_tab.canvas.event_generate("<Button-5>")
        self.root.update()
        self.assertGreater(first_tab.canvas.yview()[0], 0)
        first_tab.canvas.yview_moveto(0)
        self.app.question_fields[0]["explanationText"].event_generate("<FocusIn>")
        self.root.update()
        self.assertGreater(first_tab.canvas.yview()[0], 0)
        self.root.geometry("1280x880+20+20")
        self.root.update()
        first_tab.canvas.yview_moveto(0)
        self.root.update()
        try:
            from PIL import ImageGrab
        except ImportError:
            return  # Screenshot capture alone is optional; Tk test already ran.
        (ROOT / "test-results").mkdir(exist_ok=True)
        ImageGrab.grab(bbox=(20, 20, 1300, 900)).save(ROOT / "test-results/phase-2-editor.png")


if __name__ == "__main__":
    unittest.main(verbosity=2)
