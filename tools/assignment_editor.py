"""Offline Tkinter/ttk assignment editor. Run: python tools/assignment_editor.py"""
import argparse
from pathlib import Path
import re
import sys

try:
    import tkinter as tk
    from tkinter import filedialog, font as tkfont, messagebox, ttk
except ImportError:
    raise SystemExit("Tkinter is required. Install Python with Tcl/Tk support (Windows installer: Tcl/Tk and IDLE).")

if __package__:
    from .assignment_editor_model import (
        DEFAULT_EXPORT_DIR, DEFAULT_PRIVATE_DIR, UNIT_IDS, EditorError,
        EditorModel, UnitDraft, ValidationError, check_destination, load_document,
    )
else:
    from assignment_editor_model import (
        DEFAULT_EXPORT_DIR, DEFAULT_PRIVATE_DIR, UNIT_IDS, EditorError,
        EditorModel, UnitDraft, ValidationError, check_destination, load_document,
    )


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.body = ttk.Frame(self.canvas, padding=12)
        window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(window, width=event.width))
        self.body.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def bind_wheel(self):
        def reveal(event):
            widget = event.widget
            self.update_idletasks()
            top = widget.winfo_rooty() - self.body.winfo_rooty()
            bottom = top + widget.winfo_height()
            view_top = self.canvas.canvasy(0)
            view_height = self.canvas.winfo_height()
            content_height = max(1, self.body.winfo_height())
            if top < view_top:
                self.canvas.yview_moveto(max(0, top - 12) / content_height)
            elif bottom > view_top + view_height:
                self.canvas.yview_moveto(max(0, bottom - view_height + 12) / content_height)

        def scroll(event):
            if event.num == 4:
                amount = -1
            elif event.num == 5:
                amount = 1
            else:
                amount = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
            self.canvas.yview_scroll(amount, "units")
            return "break"

        def bind_children(widget):
            widget.bind("<FocusIn>", reveal, add="+")
            # Text widgets keep their own native wheel scrolling.
            if not isinstance(widget, tk.Text):
                for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                    widget.bind(sequence, scroll)
            for child in widget.winfo_children():
                bind_children(child)
        bind_children(self.canvas)


def describe_issue(unit_id, issue):
    match = re.search(r"questions\[(\d+)\]", issue.path)
    question = f" / Q{int(match.group(1)) + 1:02}" if match else ""
    return f"{unit_id}{question} - {issue.path}: {issue.message}"


class AssignmentEditor(ttk.Frame):
    def __init__(self, master, model=None):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.model = model or EditorModel(schema_version=2)
        self.current_id = "S01"
        self.private_dir = DEFAULT_PRIVATE_DIR
        self.export_dir = None
        self.loading = False
        self.question_fields = []
        self.answer_buttons = []
        self.option_counts = []
        self.option_count_boxes = []
        self.actions = {}
        self.title_font = tkfont.nametofont("TkDefaultFont").copy()
        self.title_font.configure(size=15, weight="bold")
        self.heading_font = tkfont.nametofont("TkDefaultFont").copy()
        self.heading_font.configure(size=12, weight="bold")
        master.title("EMI Maze Quest - Offline Assignment Editor")
        width = max(960, min(1280, master.winfo_screenwidth() - 80))
        height = max(600, min(880, master.winfo_screenheight() - 100))
        master.geometry(f"{width}x{height}")
        master.minsize(960, 600)
        master.protocol("WM_DELETE_WINDOW", self.on_close)
        master.bind("<Control-s>", lambda _event: self.save_draft())
        master.bind("<Control-Shift-S>", lambda _event: self.save_draft(save_as=True))
        if sys.platform == "darwin":
            master.bind("<Command-s>", lambda _event: self.save_draft())
        self._build()
        self.show_unit("S01")

    def _button(self, parent, text, command, key):
        button = ttk.Button(parent, text=text, command=command)
        button.pack(side="left", padx=(0, 6), pady=3)
        self.actions[key] = button
        return button

    def _build(self):
        ttk.Label(self, text="EMI Maze Quest | Teacher Assignment Editor", font=self.title_font).pack(anchor="w")
        ttk.Label(self, text="Offline local files only. Save private drafts separately; export only when ready.").pack(anchor="w", pady=(2, 8))
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x")
        self._button(toolbar, "Load / Import...", self.load_import, "load")
        self._button(toolbar, "Import Reference...", lambda: self.load_import(reference=True), "reference")
        self._button(toolbar, "Open Draft Folder...", self.open_draft_folder, "open_folder")
        self._button(toolbar, "Save Draft", self.save_draft, "save")
        self._button(toolbar, "Save Draft As...", lambda: self.save_draft(save_as=True), "save_as")
        self._button(toolbar, "New Selected Unit", self.new_unit, "new")

        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, pady=8)
        sidebar = ttk.Frame(panes, padding=(0, 0, 10, 0))
        panes.add(sidebar, weight=1)
        self.tree = ttk.Treeview(sidebar, columns=("title", "draft", "allow", "export"), show="tree headings", selectmode="browse", height=12)
        self.tree.heading("#0", text="Unit")
        self.tree.column("#0", width=52, minwidth=48, stretch=False)
        for name, title, width in (("title", "Title", 115), ("draft", "Draft", 130), ("allow", "Allow", 48), ("export", "Export", 95)):
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, minwidth=40)
        for unit_id in UNIT_IDS:
            self.tree.insert("", "end", iid=unit_id, text=unit_id)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree.bind("<Double-1>", self._toggle_allow_in_list)
        ttk.Label(sidebar, text="* Unsaved changes stay in memory when switching.\nAllow Play is private until you export a manifest.\nDouble-click the Allow column to toggle a unit.", wraplength=350).pack(anchor="w", pady=8)

        editor = ttk.Frame(panes)
        panes.add(editor, weight=3)
        heading = ttk.Frame(editor)
        heading.pack(fill="x")
        self.unit_heading = ttk.Label(heading, font=self.heading_font)
        self.unit_heading.pack(side="left")
        self.convert_button = ttk.Button(heading, text="Convert v1 to v2...", command=self.convert_to_v2)
        self.convert_button.pack(side="right")
        self.actions["convert"] = self.convert_button
        header = ttk.Frame(editor)
        header.pack(fill="x", pady=6)
        header.columnconfigure(1, weight=1)
        self.unit_title = tk.StringVar()
        self.form_url = tk.StringVar()
        self.allow_play = tk.BooleanVar()
        self.question_count = tk.StringVar(value="4")
        for row, (label, variable) in enumerate((("Unit title", self.unit_title), ("Google Form URL", self.form_url))):
            ttk.Label(header, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            ttk.Entry(header, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
            variable.trace_add("write", self._edited)
        settings = ttk.Frame(editor)
        settings.pack(fill="x", pady=(0, 6))
        self.allow_button = ttk.Checkbutton(settings, text="Allow Play (local only)", variable=self.allow_play, command=self._edited)
        self.allow_button.pack(side="left")
        ttk.Label(settings, text="Questions:").pack(side="left", padx=(22, 5))
        self.count_box = ttk.Combobox(settings, textvariable=self.question_count, values=("4", "5"), width=3, state="readonly")
        self.count_box.pack(side="left")
        self.count_box.bind("<<ComboboxSelected>>", self.change_count)
        self.draft_path = tk.StringVar()
        ttk.Label(editor, textvariable=self.draft_path, wraplength=700).pack(anchor="w", pady=(0, 5))
        self.notebook = ttk.Notebook(editor)
        self.notebook.pack(fill="both", expand=True)

        export_bar = ttk.Frame(self)
        export_bar.pack(fill="x")
        self._button(export_bar, "Validate Unit", self.validate_selected, "validate")
        self._button(export_bar, "Choose Export Folder...", self.choose_export_folder, "choose_export")
        self._button(export_bar, "Export Selected Unit JSON", self.export_selected, "export_unit")
        self._button(export_bar, "Export Public Manifest JSON", self.export_manifest, "export_manifest")
        self.export_label = tk.StringVar(value="Export folder: not selected")
        ttk.Label(self, textvariable=self.export_label, wraplength=1100).pack(anchor="w", pady=3)
        output_box = ttk.LabelFrame(self, text="Validation and messages", padding=4)
        output_box.pack(fill="x", pady=4)
        self.output = tk.Text(output_box, height=5, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(output_box, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        ttk.Label(self, text="Manual release: upload Sxx.json files FIRST, then manifest.json LAST. Google Forms controls submissions.").pack(anchor="w", pady=(3, 0))
        self.report("New drafts may be incomplete. Select a unit, enter content, then Save Draft. No files are written automatically.")

    def report(self, message):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", message)
        self.output.configure(state="disabled")

    @staticmethod
    def _value(field):
        return field.get("1.0", "end-1c") if isinstance(field, tk.Text) else field.get()

    def _field(self, parent, row, label, value, multiline=False):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=4)
        if multiline:
            field = tk.Text(parent, height=3, wrap="word", undo=True)
            field.insert("1.0", value)
            field.edit_modified(False)
            def changed(_event):
                if field.edit_modified():
                    field.edit_modified(False)
                    self._edited()
            field.bind("<<Modified>>", changed)
            field.grid(row=row, column=1, sticky="ew", pady=4)
        else:
            field = tk.StringVar(value=value)
            ttk.Entry(parent, textvariable=field).grid(row=row, column=1, sticky="ew", pady=4)
            field.trace_add("write", self._edited)
        return field

    def _question_tab(self, question):
        version = self.model.drafts[self.current_id].unit["schemaVersion"]
        question_index = len(self.question_fields)
        scroll = ScrollableFrame(self.notebook)
        self.notebook.add(scroll, text=question["id"])
        body = scroll.body
        body.columnconfigure(1, weight=1)
        fields = {}
        for row, (key, label, multiline) in enumerate((
            ("title", "Title (optional)", False),
            ("prompt", "Prompt (optional)", True),
            ("questionVideoUrl", "English question YouTube URL *", False),
            ("explanationVideoUrl", "English explanation YouTube URL *", False),
        )):
            fields[key] = self._field(body, row, label, question[key], multiline)
        label = "Options A-D *\nSelect ONE correct answer (v1)" if version == 1 else "Accepted answers *\nCheck ALL accepted labels.\nStudent chooses just ONE."
        ttk.Label(body, text=label).grid(row=4, column=0, sticky="nw", pady=8)
        options_box = ttk.Frame(body)
        options_box.grid(row=4, column=1, sticky="ew", pady=4)
        options_box.columnconfigure(1, weight=1)
        option_count = tk.StringVar(value=str(len(question["options"])))
        self.option_counts.append(option_count)
        if version == 2:
            count_row = ttk.Frame(options_box)
            count_row.grid(row=0, column=0, columnspan=2, sticky="w")
            ttk.Label(count_row, text="Choices:").pack(side="left", padx=(0, 6))
            count_box = ttk.Combobox(count_row, textvariable=option_count, values=("3", "4"), width=3, state="readonly")
            count_box.pack(side="left")
            count_box.bind("<<ComboboxSelected>>", lambda _event: self.change_option_count(question_index, int(option_count.get())))
            self.option_count_boxes.append(count_box)
            fields["correctOptions"] = []
        else:
            self.option_count_boxes.append(None)
            answer = tk.StringVar(value=question["correctOption"])
            answer.trace_add("write", self._edited)
            fields["correctOption"] = answer
        fields["options"] = []
        buttons = []
        for row, (letter, option) in enumerate(zip("ABCD"[:len(question["options"])], question["options"], strict=True), start=1):
            if version == 2:
                accepted = tk.BooleanVar(value=letter in question["correctOptions"])
                accepted.trace_add("write", self._edited)
                fields["correctOptions"].append(accepted)
                button = ttk.Checkbutton(options_box, text=letter, variable=accepted)
            else:
                button = ttk.Radiobutton(options_box, text=letter, value=letter, variable=answer)
            button.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
            buttons.append(button)
            option_field = tk.StringVar(value=option)
            option_field.trace_add("write", self._edited)
            fields["options"].append(option_field)
            ttk.Entry(options_box, textvariable=option_field).grid(row=row, column=1, sticky="ew", pady=4)
        fields["explanationText"] = self._field(body, 5, "Explanation text (optional)", question["explanationText"], True)
        ttk.Label(body, text="* Required for public export. The explanation video is optional to watch, but its URL is required.", wraplength=580).grid(row=6, column=0, columnspan=2, sticky="w", pady=10)
        scroll.bind_wheel()
        self.question_fields.append(fields)
        self.answer_buttons.append(buttons)

    def flush(self):
        if self.loading:
            return
        draft = self.model.drafts[self.current_id]
        draft.unit["title"] = self.unit_title.get()
        draft.unit["googleFormUrl"] = self.form_url.get()
        draft.allow_play = self.allow_play.get()
        for question, fields in zip(draft.unit["questions"], self.question_fields, strict=True):
            for key, field in fields.items():
                if key == "correctOptions":
                    selected = [letter for letter, variable in zip("ABCD", field) if variable.get()]
                    previous = question["correctOptions"]
                    question[key] = [letter for letter in previous if letter in selected] + [letter for letter in selected if letter not in previous]
                else:
                    question[key] = [self._value(item) for item in field] if key == "options" else self._value(field)

    def _edited(self, *_args):
        if not self.loading:
            self.flush()
            self.refresh_list()

    def refresh_list(self):
        for unit_id, draft in self.model.drafts.items():
            issues = draft.validate()
            completeness = "Ready" if not issues else f"{len(issues)} issues"
            saved = "* " if draft.dirty else ("Saved | " if draft.path else "New | ")
            state = self.model.export_state(unit_id, self.export_dir) if self.export_dir else "-"
            self.tree.item(unit_id, values=(draft.unit["title"], saved + completeness, "Yes" if draft.allow_play else "No", state))
        draft = self.model.drafts[self.current_id]
        self.unit_heading.configure(text=f"{self.current_id} | v{draft.unit['schemaVersion']} | {'Unsaved changes' if draft.dirty else ('Saved' if draft.path else 'New')}")
        self.convert_button.configure(state="normal" if draft.unit["schemaVersion"] == 1 else "disabled")

    def show_unit(self, unit_id):
        self.loading = True
        try:
            self.current_id = unit_id
            draft = self.model.drafts[unit_id]
            self.unit_title.set(draft.unit["title"])
            self.form_url.set(draft.unit["googleFormUrl"])
            self.allow_play.set(draft.allow_play)
            self.question_count.set(str(len(draft.unit["questions"])))
            self.draft_path.set(f"Private draft: {draft.path or 'not saved yet'}")
            self.question_fields = []
            self.answer_buttons = []
            self.option_counts = []
            self.option_count_boxes = []
            for tab in self.notebook.tabs():
                self.notebook.nametowidget(tab).destroy()
            for question in draft.unit["questions"]:
                self._question_tab(question)
            self.tree.selection_set(unit_id)
            self.tree.focus(unit_id)
        finally:
            self.loading = False
        self.refresh_list()

    def request_switch(self, unit_id):
        if unit_id == self.current_id:
            return True
        self.flush()
        if self.model.drafts[self.current_id].dirty:
            choice = messagebox.askyesnocancel("Unsaved changes", f"Save {self.current_id} before switching?\n\nYes: save draft. No: keep changes in this session. Cancel: stay here.", parent=self)
            if choice is None or (choice and not self.save_draft()):
                self.tree.selection_set(self.current_id)
                return False
        self.show_unit(unit_id)
        return True

    def _selected(self, _event):
        if not self.loading and self.tree.selection():
            self.request_switch(self.tree.selection()[0])

    def _toggle_allow_in_list(self, event):
        unit_id = self.tree.identify_row(event.y)
        if unit_id and self.tree.identify_column(event.x) == "#3":
            if unit_id != self.current_id:
                return  # A canceled selection must not toggle another unit.
            draft = self.model.drafts[unit_id]
            draft.allow_play = not draft.allow_play
            if unit_id == self.current_id:
                self.allow_play.set(draft.allow_play)
            self.refresh_list()

    def change_count(self, _event=None):
        self.flush()
        count = int(self.question_count.get())
        self.model.drafts[self.current_id].set_question_count(count)
        self.show_unit(self.current_id)
        self.report("Q05 is retained privately when choosing four questions and restored when choosing five. It is excluded from four-question exports.")

    def change_option_count(self, question_index, count):
        self.flush()
        self.model.drafts[self.current_id].set_option_count(question_index, count)
        self.show_unit(self.current_id)
        self.notebook.select(question_index)
        self.report("Option D text and acceptance are retained privately when choosing three choices, then restored when choosing four. A removed D is not an active accepted answer.")

    def convert_to_v2(self):
        self.flush()
        draft = self.model.drafts[self.current_id]
        if draft.unit["schemaVersion"] != 1:
            return False
        if not messagebox.askyesno("Convert v1 to v2?", "Create an unsaved v2 copy? Each existing correctOption becomes a one-item correctOptions list.\n\nThe loaded v1 file stays unchanged. Save the converted draft to a new filename to keep both versions.", parent=self):
            return False
        try:
            converted = draft.converted_to_v2()
        except (OSError, ValueError) as error:
            self._show_error(error)
            return False
        self.model.install(converted)
        self.show_unit(self.current_id)
        self.report("Converted in memory to v2. Existing v1 files were not changed. Save Draft As to a new private filename, then re-export units and manifest when ready.")
        return True

    def _show_error(self, error):
        self.report(str(error))
        summary = f"{len(error.messages)} issues. See the Validation and messages panel." if isinstance(error, ValidationError) else str(error)
        messagebox.showerror("Action not completed", summary, parent=self)

    def save_draft(self, unit_id=None, save_as=False):
        self.flush()
        unit_id = unit_id or self.current_id
        draft = self.model.drafts[unit_id]
        path = None if save_as else draft.path
        if path is None:
            filename = filedialog.asksaveasfilename(parent=self, title=f"Save private {unit_id} draft - keep outside web folders", initialdir=str(self.private_dir if self.private_dir.exists() else Path.home()), initialfile=f"{unit_id}.draft.json", defaultextension=".draft.json", filetypes=[("Private drafts", "*.draft.json"), ("JSON", "*.json")], confirmoverwrite=False)
            if not filename:
                return False
            path = Path(filename)
        same_file = draft.path is not None and path.resolve() == draft.path.resolve()
        if path.exists() and not same_file and not messagebox.askyesno("Replace existing draft?", f"Replace this local file?\n{path}", parent=self):
            return False
        try:
            if self.export_dir and path.resolve().is_relative_to(self.export_dir.resolve()):
                raise EditorError("Keep private drafts outside the selected export folder. Choose a private draft folder.")
            draft.save(path, overwrite=path.exists())
        except (OSError, ValueError) as error:
            self._show_error(error)
            return False
        self.private_dir = path.parent
        if unit_id == self.current_id:
            self.draft_path.set(f"Private draft: {path}")
        self.refresh_list()
        self.report(f"Saved private draft: {path}\nIncomplete drafts are allowed. This did not change any public JSON.")
        return True

    def _may_replace(self, unit_id):
        self.flush()
        if not self.model.drafts[unit_id].dirty:
            return True
        choice = messagebox.askyesnocancel("Replace unsaved draft?", f"Save changes to {unit_id} before replacing it?\n\nYes: save first. No: discard these unsaved changes. Cancel: keep editing.", parent=self)
        return choice is not None and (not choice or self.save_draft(unit_id))

    def load_import(self, reference=False):
        title = "Import authoring reference (not a published unit)" if reference else "Load private draft or import Sxx.json"
        filename = filedialog.askopenfilename(parent=self, title=title, initialdir=str(self.private_dir if self.private_dir.exists() else Path.home()), filetypes=[("JSON", "*.json"), ("All files", "*")])
        if not filename:
            return False
        try:
            draft = load_document(filename, allow_reference_filename=reference)
            unit_id = draft.unit["unitId"]
            if not self._may_replace(unit_id):
                return False
            if unit_id != self.current_id and not self.request_switch(unit_id):
                return False
            self.model.install(draft)
            self.show_unit(unit_id)
            if draft.path:
                self.private_dir = draft.path.parent
            self.report(f"Loaded {unit_id} from {filename}.\n" + ("Private draft restored, including Allow Play and retained Q05." if draft.path else "Imported as a new private draft; Allow Play starts unchecked. Save Draft to retain your edits."))
            return True
        except (OSError, ValueError) as error:
            self._show_error(error)
            return False

    def open_draft_folder(self):
        directory = filedialog.askdirectory(parent=self, title="Open private folder containing Sxx.draft.json", initialdir=str(self.private_dir if self.private_dir.exists() else Path.home()))
        if not directory:
            return False
        try:
            drafts = []
            for unit_id in UNIT_IDS:
                path = Path(directory) / f"{unit_id}.draft.json"
                if path.exists():
                    draft = load_document(path)
                    if draft.path is None or draft.unit["unitId"] != unit_id:
                        raise EditorError(f"{path}: expected a private {unit_id} draft.")
                    drafts.append(draft)
            if not drafts:
                raise EditorError("No S01.draft.json through S12.draft.json found. Use Load / Import for other filenames.")
            # Read all first; a malformed file or canceled prompt installs none.
            if not all(self._may_replace(draft.unit["unitId"]) for draft in drafts):
                return False
            for draft in drafts:
                self.model.install(draft)
            self.private_dir = Path(directory)
            self.show_unit(self.current_id)
            self.report(f"Opened {len(drafts)} private drafts. Units absent from this folder were kept in memory.")
            return True
        except (OSError, ValueError) as error:
            self._show_error(error)
            return False

    def new_unit(self):
        if self._may_replace(self.current_id):
            version = self.model.drafts[self.current_id].unit["schemaVersion"]
            self.model.install(UnitDraft.new(self.current_id, int(version)))
            self.show_unit(self.current_id)
            self.report(f"New blank {self.current_id} draft. Previous saved files were not removed.")

    def validate_selected(self):
        self.flush()
        issues = self.model.drafts[self.current_id].validate()
        self.report("\n".join(describe_issue(self.current_id, issue) for issue in issues) if issues else f"{self.current_id}: VALID for public export. URLs were checked offline for syntax only.")
        self.refresh_list()
        return not issues

    def choose_export_folder(self):
        directory = filedialog.askdirectory(parent=self, title="Choose local export folder (manual upload later)", initialdir=str(self.export_dir or (DEFAULT_EXPORT_DIR if DEFAULT_EXPORT_DIR.exists() else Path.home())))
        if not directory:
            return False
        try:
            if self.private_dir.resolve().is_relative_to(Path(directory).resolve()):
                raise EditorError("The export folder must not contain the private draft folder. Choose a separate folder.")
            check_destination(Path(directory) / "manifest.json", "export")
        except (OSError, ValueError) as error:
            self._show_error(error)
            return False
        self.export_dir = Path(directory)
        self.export_label.set(f"Local export folder: {self.export_dir}")
        self.refresh_list()
        return True

    def _export(self, manifest):
        self.flush()
        if self.export_dir is None and not self.choose_export_folder():
            return False
        filename = "manifest.json" if manifest else f"{self.current_id}.json"
        path = self.export_dir / filename
        try:
            if manifest:
                data = self.model.build_manifest(self.export_dir)
                if not data["units"] and not messagebox.askyesno("Empty allowlist", "No units are marked Allow Play. Export an empty manifest that lists no playable units?", parent=self):
                    return False
            else:
                issues = self.model.drafts[self.current_id].validate()
                if issues:
                    raise ValidationError([describe_issue(self.current_id, issue) for issue in issues])
            if path.exists() and not messagebox.askyesno("Replace local export?", f"Replace this local export?\n{path}", parent=self):
                return False
            if manifest:
                self.model.export_manifest(self.export_dir, overwrite=path.exists())
            else:
                self.model.export_unit(self.current_id, self.export_dir, overwrite=path.exists())
        except (OSError, ValueError) as error:
            self._show_error(error)
            return False
        self.refresh_list()
        self.report(f"Exported local file: {path}\nPrivate drafts were not saved by this action.\nManual upload: Sxx.json files FIRST, manifest.json LAST.\nRemoving a unit from the manifest does not delete its previously uploaded file. No upload has occurred.")
        return True

    def export_selected(self):
        return self._export(False)

    def export_manifest(self):
        return self._export(True)

    def on_close(self):
        self.flush()
        dirty = self.model.dirty_units
        if dirty:
            choice = messagebox.askyesnocancel("Unsaved drafts", f"Save unsaved units before closing?\n{', '.join(dirty)}\n\nYes: save each draft. No: discard unsaved edits. Cancel: keep editing.", parent=self)
            if choice is None:
                return False
            if choice and not all(self.save_draft(unit_id) for unit_id in dirty):
                return False
        self.master.destroy()
        return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    files = parser.add_mutually_exclusive_group()
    files.add_argument("--draft", type=Path, help="Explicitly open a local private draft or Sxx.json")
    files.add_argument("--reference", type=Path, help="Import local authoring JSON with any filename, without publishing")
    args = parser.parse_args(argv)
    model = EditorModel(schema_version=2)
    loaded = None
    if args.draft or args.reference:
        try:
            loaded = load_document(args.draft or args.reference, allow_reference_filename=args.reference is not None)
            model.install(loaded)
        except (OSError, ValueError) as error:
            print(f"Cannot load authoring data: {error}", file=sys.stderr)
            return 2
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Cannot open the editor display: {error}\nRun on your desktop with Python Tcl/Tk installed.", file=sys.stderr)
        return 1
    editor = AssignmentEditor(root, model)
    if loaded:
        editor.show_unit(loaded.unit["unitId"])
        if loaded.path:
            editor.private_dir = loaded.path.parent
        editor.report("Opened the explicitly selected local authoring data. Validate before export; Allow Play and exports remain separate local actions.")
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
