"""Real Tk widget/controller smoke tests. Run on a desktop or under Xvfb.

Native file/message dialogs are mocked for repeatability; real entries, Text,
tabs, radio buttons, checkbuttons, selection events and callbacks are exercised.
All generated draft/export content is synthetic and confined to a temp folder.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
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
from tests.contract_cases_v2 import fixture_v2


class GuiTestSupport(unittest.TestCase):
    schema_version = 1

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.root = tk.Tk()
        self.callback_errors = []
        self.root.report_callback_exception = lambda *error: self.callback_errors.append(error)
        self.app = gui.AssignmentEditor(self.root, gui.EditorModel(schema_version=self.schema_version))
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


class GuiSmokeTests(GuiTestSupport):
    """Preserve the complete original Phase 2 regression suite in v1 mode."""

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


class GuiV2SmokeTests(GuiTestSupport):
    schema_version = 2

    def import_v2(self, five=False):
        name = "S02.json" if five else "S01.json"
        self.askopenfilename.return_value = str(ROOT / "tests/fixtures/v2" / name)
        self.assertTrue(self.app.load_import())
        self.root.update()

    def choices(self, question_index, count):
        box = self.app.option_count_boxes[question_index]
        box.set(str(count))
        box.event_generate("<<ComboboxSelected>>")
        self.root.update()

    def test_independent_checkboxes_and_retained_d_roundtrip_with_three_choice_q05(self):
        self.import_v2(five=True)
        self.assertEqual(len(self.app.question_fields), 5)
        self.assertEqual(len(self.app.question_fields[4]["options"]), 3)
        self.assertEqual(len(self.app.answer_buttons[4]), 3)
        self.app.answer_buttons[0][2].invoke()
        self.assertEqual(self.app.model.drafts["S02"].unit["questions"][0]["correctOptions"], ["A", "C"])
        self.assertEqual(sum("selected" in button.state() for button in self.app.answer_buttons[0]), 2)
        self.choices(0, 4)
        self.app.question_fields[0]["options"][3].set("Retained D 中文")
        self.app.answer_buttons[0][3].invoke()
        self.choices(0, 3)
        self.assertEqual(len(self.app.answer_buttons[0]), 3)
        draft = self.app.model.drafts["S02"]
        self.assertTrue(draft.parked_options["Q01"]["accepted"])
        path = self.directory / "S02.draft.json"
        self.asksaveasfilename.return_value = str(path)
        self.assertTrue(self.app.save_draft())
        self.app.actions["new"].invoke()
        self.assertEqual(self.app.model.drafts["S02"].unit["schemaVersion"], 2)
        self.askopenfilename.return_value = str(path)
        self.assertTrue(self.app.load_import())
        self.choices(0, 4)
        self.assertEqual(self.app.question_fields[0]["options"][3].get(), "Retained D 中文")
        self.assertTrue(self.app.question_fields[0]["correctOptions"][3].get())
        self.assertTrue(self.app.question_fields[0]["correctOptions"][0].get())
        self.assertTrue(self.app.question_fields[0]["correctOptions"][2].get())
        self.app.notebook.select(4)
        self.root.geometry("1280x880+20+20")
        self.root.update()
        try:
            from PIL import ImageGrab
        except ImportError:
            return
        (ROOT / "test-results").mkdir(exist_ok=True)
        ImageGrab.grab(bbox=(20, 20, 1300, 900)).save(ROOT / "test-results/editor-v2.png")

    def test_empty_accepted_answers_are_savable_and_block_public_export(self):
        self.assertEqual(self.app.model.drafts["S01"].unit["schemaVersion"], 2)
        self.assertEqual(self.app.model.drafts["S01"].unit["questions"][0]["correctOptions"], [])
        path = self.directory / "S01.draft.json"
        self.app.unit_title.set("未完成的 v2 🧪")
        self.asksaveasfilename.return_value = str(path)
        self.assertTrue(self.app.save_draft())
        self.assertEqual(read_json(path)["draftVersion"], 2)
        self.assertEqual(read_json(path)["unit"]["questions"][0]["correctOptions"], [])
        self.select_export_folder()
        self.assertFalse(self.app.export_selected())
        self.assertIn("correctOptions", self.app.output.get("1.0", "end"))
        self.app.answer_buttons[0][0].invoke()
        self.app.answer_buttons[0][1].invoke()
        self.assertTrue(self.app.save_draft())
        self.assertEqual(read_json(path)["unit"]["questions"][0]["correctOptions"], ["A", "B"])

    def test_v1_conversion_requires_confirmation_and_keeps_source_unchanged(self):
        source = self.directory / "S01.draft.json"
        legacy = UnitDraft(fixture(), allow_play=True)
        legacy.save(source)
        before = source.read_bytes()
        self.askopenfilename.return_value = str(source)
        self.assertTrue(self.app.load_import())
        self.assertEqual(self.app.model.drafts["S01"].unit["schemaVersion"], 1)
        self.assertFalse(self.app.convert_to_v2())
        self.assertEqual(self.app.model.drafts["S01"].unit["schemaVersion"], 1)
        self.askyesno.return_value = True
        self.app.actions["convert"].invoke()
        self.root.update()
        converted = self.app.model.drafts["S01"]
        self.assertEqual(converted.unit["schemaVersion"], 2)
        self.assertIsNone(converted.path)
        self.assertTrue(converted.dirty)
        self.assertEqual(converted.unit["questions"][0]["correctOptions"], [fixture()["questions"][0]["correctOption"]])
        self.assertTrue(all(button.winfo_class() == "TCheckbutton" for button in self.app.answer_buttons[0]))
        self.assertEqual(source.read_bytes(), before)
        self.assertIn("disabled", self.app.convert_button.state())

    def test_v2_export_manifest_and_checkbox_change_staleness(self):
        self.import_v2()
        folder = self.select_export_folder()
        self.app.allow_button.invoke()
        self.assertTrue(self.app.export_selected())
        self.assertTrue(self.app.export_manifest())
        unit = read_json(folder / "S01.json")
        self.assertEqual(unit["schemaVersion"], 2)
        self.assertEqual(len(unit["questions"][0]["options"]), 3)
        self.assertNotIn("correctOption", unit["questions"][0])
        self.assertEqual(read_json(folder / "manifest.json")["schemaVersion"], 1)
        self.app.answer_buttons[0][2].invoke()
        self.assertFalse(self.app.export_manifest())
        self.assertIn("Stale", self.app.output.get("1.0", "end"))
        self.askyesno.return_value = True
        self.assertTrue(self.app.export_selected())
        self.assertTrue(self.app.export_manifest())
        self.assertEqual(read_json(folder / "S01.json")["questions"][0]["correctOptions"], ["A", "C"])

    def test_explicit_reference_import_keeps_urls_empty_and_chinese_text_unmodified(self):
        data = fixture_v2("S02.json")
        data["unitId"] = "S01"
        data["googleFormUrl"] = ""
        for question in data["questions"]:
            question["questionVideoUrl"] = question["explanationVideoUrl"] = ""
        data["questions"][3]["options"] = ["未翻譯測試一", "未翻譯測試二", "未翻譯測試三", "未翻譯測試四"]
        path = self.directory / "S01_reference_v2_incomplete.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.askopenfilename.return_value = str(path)
        self.assertFalse(self.app.load_import())
        self.app.actions["reference"].invoke()
        self.root.update()
        self.app.flush()
        self.assertEqual(self.app.model.drafts["S01"].unit, data)
        self.assertFalse(self.app.allow_play.get())
        self.assertEqual(len(self.app.answer_buttons[4]), 3)
        self.assertFalse(self.app.validate_selected())
        self.assertEqual(len(self.app.model.drafts["S01"].validate()), 11)
        private = self.directory / "S01.draft.json"
        UnitDraft(data, allow_play=True).save(private)
        self.askopenfilename.return_value = str(private)
        self.askyesnocancel.return_value = False
        self.app.actions["reference"].invoke()
        self.assertFalse(self.app.allow_play.get())
        self.assertIsNone(self.app.model.drafts["S01"].path)

    def test_v2_switching_keeps_multiple_selections_independent(self):
        self.app.answer_buttons[0][0].invoke()
        self.app.answer_buttons[0][2].invoke()
        self.askyesnocancel.return_value = False
        self.assertTrue(self.app.request_switch("S02"))
        self.app.answer_buttons[0][1].invoke()
        self.assertTrue(self.app.request_switch("S01"))
        self.assertEqual(self.app.model.drafts["S01"].unit["questions"][0]["correctOptions"], ["A", "C"])
        self.assertEqual(self.app.model.drafts["S02"].unit["questions"][0]["correctOptions"], ["B"])
        self.assertTrue(self.app.question_fields[0]["correctOptions"][0].get())
        self.assertFalse(self.app.question_fields[0]["correctOptions"][1].get())
        self.assertTrue(self.app.question_fields[0]["correctOptions"][2].get())

    def test_authoring_reference_order_is_not_changed_by_render_or_flush(self):
        data = fixture_v2()
        data["questions"][0]["correctOptions"] = ["C", "A"]
        self.app.model.install(UnitDraft(data))
        self.app.show_unit("S01")
        self.root.update()
        self.app.flush()
        self.assertEqual(self.app.model.drafts["S01"].unit, data)

    def test_real_entrypoint_explicit_reference_and_private_draft_startup(self):
        data = fixture_v2()
        reference = self.directory / "authoring-reference.json"
        reference.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        private = self.directory / "S01.draft.json"
        UnitDraft(data).save(private)
        # Run the real command parser and mainloop in a separate interpreter.
        # Auto-close only after verifying the instantiated editor's source data.
        script = """
import json, sys, tkinter as tk
from pathlib import Path
from tools.assignment_editor import main
source=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
expected=source['unit'] if 'draftVersion' in source else source
original=tk.Tk.mainloop
def smoke(root, *args):
    editor=root.winfo_children()[0]
    assert editor.current_id == 'S01'
    assert editor.model.drafts['S01'].unit == expected
    assert not editor.model.drafts['S01'].allow_play
    assert len(editor.answer_buttons[0]) == len(expected['questions'][0]['options'])
    root.after(100,root.destroy)
    return original(root,*args)
tk.Tk.mainloop=smoke
raise SystemExit(main(sys.argv[1:]))
"""
        for flag, path in (("--reference", reference), ("--draft", private)):
            result = subprocess.run([sys.executable, "-c", script, flag, str(path)], cwd=ROOT, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
