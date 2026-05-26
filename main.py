import tkinter as tk
from tkinter import filedialog, ttk
import threading
from pathlib import Path

from extractor import extract
from classifier import classify
from organizer import organize

# ─────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR = str(Path.home() / "OrganizedFiles")

# ── Colour tokens ─────────────────────────────────────────
BG        = "#0f1117"
SURFACE   = "#1a1d27"
SURFACE2  = "#22263a"
BORDER    = "#2e3350"
ACCENT    = "#4f8ef7"
ACCENT2   = "#7c3aed"
SUCCESS   = "#22c55e"
WARNING   = "#f59e0b"
DANGER    = "#ef4444"
TEXT      = "#e2e8f0"
TEXT_DIM  = "#64748b"
TEXT_MID  = "#94a3b8"
FONT_MONO = ("Consolas", 10)
FONT_BODY = ("Segoe UI", 10)
FONT_H1   = ("Segoe UI Semibold", 16)
FONT_H2   = ("Segoe UI Semibold", 13)
FONT_SMALL= ("Segoe UI", 9)
# ─────────────────────────────────────────────────────────


class Tag(tk.Frame):
    """Pill-shaped tag for file types."""
    def __init__(self, parent, text, color=ACCENT):
        super().__init__(parent, bg=SURFACE2, bd=0)
        tk.Label(self, text=text, font=("Segoe UI", 8, "bold"),
                 bg=SURFACE2, fg=color, padx=6, pady=2).pack()

# upload list (single file row(
class FileRow(tk.Frame):
    def __init__(self, parent, name, on_remove):
        super().__init__(parent, bg=SURFACE, bd=0,
                         highlightbackground=BORDER, highlightthickness=1)
        ext = Path(name).suffix.upper().lstrip(".") or "FILE"
        ext_colors = {
            "PDF": "#ef4444", "DOCX": "#3b82f6", "DOC": "#3b82f6",
            "TXT": TEXT_MID,  "MD": "#a78bfa",   "PNG": "#22c55e",
            "JPG": "#22c55e", "JPEG": "#22c55e",
        }
        color = ext_colors.get(ext, ACCENT)

        Tag(self, ext, color).pack(side="left", padx=(10, 8), pady=8)
        tk.Label(self, text=name, font=FONT_BODY, bg=SURFACE,
                 fg=TEXT, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(self, text="✕", font=("Segoe UI", 9), bg=SURFACE,
                  fg=TEXT_DIM, bd=0, activebackground=SURFACE,
                  activeforeground=DANGER, cursor="hand2",
                  command=on_remove).pack(side="right", padx=10)

#result row in the summary panel
class ResultRow(tk.Frame):
    def __init__(self, parent, filename, folder, index):
        bg = SURFACE if index % 2 == 0 else SURFACE2
        super().__init__(parent, bg=bg, bd=0)
        self.configure(pady=0)

        # Index number
        tk.Label(self, text=f"{index:02d}", font=FONT_MONO,
                 bg=bg, fg=TEXT_DIM, width=3, anchor="e").pack(side="left", padx=(12, 10))

        # Filename
        tk.Label(self, text=filename, font=FONT_BODY,
                 bg=bg, fg=TEXT, anchor="w", width=30).pack(side="left")

        # Arrow
        tk.Label(self, text="→", font=("Segoe UI", 11),
                 bg=bg, fg=ACCENT).pack(side="left", padx=8)

        # Folder chip
        chip_bg = SURFACE2 if bg == SURFACE else SURFACE
        chip = tk.Frame(self, bg=chip_bg,
                        highlightbackground=BORDER, highlightthickness=1)
        chip.pack(side="left", pady=6)
        tk.Label(chip, text=f"📁  {folder}", font=FONT_SMALL,
                 bg=chip_bg, fg=ACCENT, padx=8, pady=3).pack()


class Divider(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BORDER, height=1)
        self.pack(fill="x", pady=0)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("FileSort AI")
        self.root.geometry("1300x750")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.files: list[str] = []
        self.folders: list[str] = []
        self.file_widgets: dict[str, FileRow] = {}
        self.output_dir: str = DEFAULT_OUTPUT_DIR

        self._build_ui()

    # ── UI construction ───────────────────────────────────

    def _build_ui(self):
        self._build_topbar()
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        left = tk.Frame(container, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(container, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self._build_upload_panel(left)
        self._build_folders_panel(left)
        self._build_run_button(left)
        self._build_results_panel(right)

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=SURFACE, height=60,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        inner = tk.Frame(bar, bg=SURFACE)
        inner.pack(side="left", padx=20, pady=12)



        tk.Label(inner, text="FileSort", font=("Segoe UI Bold", 16),
                 bg=SURFACE, fg=TEXT).pack(side="left")
        tk.Label(inner, text="AI", font=("Segoe UI", 16),
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=(2, 0))

        # Status badge (right side)
        badge_frame = tk.Frame(bar, bg=SURFACE)
        badge_frame.pack(side="right", padx=20)
        self.status_dot = tk.Label(badge_frame, text="●", font=("Segoe UI", 10),
                                   bg=SURFACE, fg=SUCCESS)
        self.status_dot.pack(side="left")
        self.status_text = tk.Label(badge_frame, text="Ready", font=FONT_SMALL,
                                    bg=SURFACE, fg=TEXT_MID)
        self.status_text.pack(side="left", padx=(4, 0))

    def _section_header(self, parent, title, subtitle=""):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(16, 6))
        tk.Label(f, text=title, font=FONT_H2, bg=BG, fg=TEXT).pack(side="left")
        if subtitle:
            tk.Label(f, text=subtitle, font=FONT_SMALL, bg=BG,
                     fg=TEXT_DIM).pack(side="left", padx=(8, 0))

    def _build_upload_panel(self, parent):
        self._section_header(parent, "01  Documents",
                             "— any PDF, DOCX, TXT, image")

        # Drop zone
        drop = tk.Frame(parent, bg=SURFACE,
                        highlightbackground=BORDER, highlightthickness=1,
                        height=90)
        drop.pack(fill="x")
        drop.pack_propagate(False)

        inner = tk.Frame(drop, bg=SURFACE, cursor="hand2")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inner, text="⊕", font=("Segoe UI", 22),
                 bg=SURFACE, fg=ACCENT).pack()
        tk.Label(inner, text="Click to upload files",
                 font=("Segoe UI Semibold", 10), bg=SURFACE, fg=TEXT).pack()
        tk.Label(inner, text="PDF · DOCX · TXT · MD · PNG · JPG",
                 font=FONT_SMALL, bg=SURFACE, fg=TEXT_DIM).pack()

        for w in (drop, inner) + tuple(inner.winfo_children()):
            w.bind("<Button-1>", lambda e: self.pick_files())
            w.bind("<Enter>", lambda e: drop.configure(
                highlightbackground=ACCENT, highlightthickness=1))
            w.bind("<Leave>", lambda e: drop.configure(
                highlightbackground=BORDER))

        # ── Scrollable file list (fixed height so panels below stay visible) ──
        list_outer = tk.Frame(parent, bg=SURFACE,
                              highlightbackground=BORDER, highlightthickness=1)
        list_outer.pack(fill="x", pady=(6, 0))

        self._file_canvas = tk.Canvas(list_outer, bg=SURFACE, bd=0,
                                      highlightthickness=0, height=180)
        file_scrollbar = tk.Scrollbar(list_outer, orient="vertical",
                                      command=self._file_canvas.yview)
        self.file_list_frame = tk.Frame(self._file_canvas, bg=SURFACE)

        self.file_list_frame.bind(
            "<Configure>",
            lambda e: self._file_canvas.configure(
                scrollregion=self._file_canvas.bbox("all"))
        )
        self._file_canvas_window = self._file_canvas.create_window(
            (0, 0), window=self.file_list_frame, anchor="nw")

        # Make canvas window stretch to full width
        self._file_canvas.bind(
            "<Configure>",
            lambda e: self._file_canvas.itemconfig(
                self._file_canvas_window, width=e.width)
        )

        self._file_canvas.configure(yscrollcommand=file_scrollbar.set)
        self._file_canvas.pack(side="left", fill="both", expand=True)
        file_scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling when hovering the file list
        def _on_mousewheel(event):
            self._file_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._file_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.file_list_frame.bind("<MouseWheel>", _on_mousewheel)

        # File count label
        self.file_count = tk.Label(parent, text="",
                                   font=FONT_SMALL, bg=BG, fg=TEXT_DIM, anchor="w")
        self.file_count.pack(fill="x", pady=(4, 0))

    def _build_folders_panel(self, parent):
        self._section_header(parent, "02  Folder names",
                             "— one per line")

        box_frame = tk.Frame(parent, bg=SURFACE,
                             highlightbackground=BORDER, highlightthickness=1)
        box_frame.pack(fill="x")

        self.folder_box = tk.Text(
            box_frame, height=5, font=FONT_MONO,
            bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=0, padx=12, pady=10,
            selectbackground=ACCENT2, selectforeground=TEXT
        )
        self.folder_box.pack(fill="x")
        self.folder_box.insert("1.0",
            "Computer architecture notes\nMath assignments\nImages")

        hint = tk.Label(parent,
            text="💡  Tip: Be descriptive. The AI uses your folder names as clues.",
            font=FONT_SMALL, bg=BG, fg=TEXT_DIM, anchor="w")
        hint.pack(fill="x", pady=(4, 0))

    def _build_run_button(self, parent):
        tk.Frame(parent, bg=BG, height=12).pack()

        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(fill="x")

        # ── Output folder selector ────────────────────────
        out_header = tk.Frame(btn_frame, bg=BG)
        out_header.pack(fill="x", pady=(0, 4))
        tk.Label(out_header, text="03  Output folder",
                 font=FONT_H2, bg=BG, fg=TEXT).pack(side="left")
        tk.Label(out_header, text="— where files will be saved",
                 font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="left", padx=(8, 0))

        out_box = tk.Frame(btn_frame, bg=SURFACE,
                           highlightbackground=BORDER, highlightthickness=1)
        out_box.pack(fill="x", pady=(0, 6))

        folder_icon = tk.Label(out_box, text="📂", font=("Segoe UI", 11),
                               bg=SURFACE, fg=ACCENT)
        folder_icon.pack(side="left", padx=(10, 6), pady=8)

        self.output_label = tk.Label(out_box, text=self.output_dir,
                                     font=FONT_SMALL, bg=SURFACE, fg=TEXT_MID,
                                     anchor="w")
        self.output_label.pack(side="left", fill="x", expand=True)

        tk.Button(out_box, text="Change", font=FONT_SMALL,
                  bg=SURFACE2, fg=ACCENT, bd=0,
                  activebackground=BORDER, activeforeground=TEXT,
                  cursor="hand2", padx=10, pady=4,
                  command=self.pick_output_dir).pack(side="right", padx=8, pady=6)

        # ── Organise button ───────────────────────────────
        self.run_btn = tk.Button(
            btn_frame, text="▶   Organise Files",
            font=("Segoe UI Semibold", 12),
            bg=ACCENT, fg="#ffffff", bd=0,
            activebackground="#3b7de8", activeforeground="#ffffff",
            cursor="hand2", padx=0, pady=12,
            command=self.run
        )
        self.run_btn.pack(fill="x")

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            btn_frame, variable=self.progress_var,
            maximum=100, mode="determinate"
        )
        # styled via ttk — shown only during processing

    def _build_results_panel(self, parent):
        self._section_header(parent, "04  Results", "— where each file went")

        outer = tk.Frame(parent, bg=SURFACE,
                         highlightbackground=BORDER, highlightthickness=1)
        outer.pack(fill="both", expand=True)

        # Column headers
        hdr = tk.Frame(outer, bg=SURFACE2)
        hdr.pack(fill="x")
        tk.Label(hdr, text="#",   font=("Segoe UI Semibold", 9),
                 bg=SURFACE2, fg=TEXT_DIM, width=3, anchor="e").pack(
                     side="left", padx=(12, 10), pady=6)
        tk.Label(hdr, text="FILENAME", font=("Segoe UI Semibold", 9),
                 bg=SURFACE2, fg=TEXT_DIM, anchor="w", width=30).pack(side="left")
        tk.Label(hdr, text="DESTINATION", font=("Segoe UI Semibold", 9),
                 bg=SURFACE2, fg=TEXT_DIM, anchor="w").pack(side="left", padx=(8,0))

        Divider(outer)

        # Scrollable results list
        canvas = tk.Canvas(outer, bg=SURFACE, bd=0,
                           highlightthickness=0, height=300)
        self._results_canvas = canvas  # saved so _clear_results can reset scroll
        scrollbar = tk.Scrollbar(outer, orient="vertical",
                                 command=canvas.yview)
        self.results_inner = tk.Frame(canvas, bg=SURFACE)

        self.results_inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.results_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Placeholder text
        self.results_placeholder = tk.Label(
            self.results_inner,
            text="\n\n\n       Results will appear here\n       once you organise your files.",
            font=FONT_BODY, bg=SURFACE, fg=TEXT_DIM, justify="left")
        self.results_placeholder.pack(anchor="w", padx=4)

        # Footer summary
        self.results_footer = tk.Label(
            outer, text="", font=FONT_SMALL,
            bg=SURFACE2, fg=TEXT_DIM, anchor="w", pady=6, padx=12)
        self.results_footer.pack(fill="x")

    # ── Actions ───────────────────────────────────────────

    def pick_output_dir(self):
        chosen = filedialog.askdirectory(title="Choose output folder")
        if chosen:
            self.output_dir = chosen
            self.output_label.config(text=self.output_dir, fg=TEXT)
            self._set_status(f"Output folder set.", SUCCESS)

    def pick_files(self):
        chosen = filedialog.askopenfilenames(
            title="Select documents",
            filetypes=[("Documents",
                        "*.pdf *.docx *.doc *.txt *.md *.png *.jpg *.jpeg")]
        )
        for fp in chosen:
            if fp not in self.files:
                self.files.append(fp)
                self._add_file_row(fp)
        self._refresh_count()

    def _add_file_row(self, filepath):
        name = Path(filepath).name
        row = FileRow(
            self.file_list_frame, name,
            on_remove=lambda fp=filepath: self._remove_file(fp)
        )
        row.pack(fill="x", pady=1)
        self.file_widgets[filepath] = row

        # Forward mousewheel events on row children to the canvas
        def _mw(event, c=self._file_canvas):
            c.yview_scroll(int(-1 * (event.delta / 120)), "units")
        for w in (row,) + tuple(row.winfo_children()):
            w.bind("<MouseWheel>", _mw)

    def _remove_file(self, filepath):
        if filepath in self.file_widgets:
            self.file_widgets[filepath].destroy()
            del self.file_widgets[filepath]
        if filepath in self.files:
            self.files.remove(filepath)
        self._refresh_count()

    def _refresh_count(self):
        n = len(self.files)
        self.file_count.config(
            text=f"{n} file{'s' if n != 1 else ''} selected" if n else "")

    def run(self):
        raw = self.folder_box.get("1.0", "end").strip()
        self.folders = [f.strip() for f in raw.splitlines() if f.strip()]

        if not self.files:
            self._set_status("Upload at least one file first.", DANGER)
            return
        if not self.folders:
            self._set_status("Add at least one folder name.", DANGER)
            return

        self.run_btn.config(state="disabled", text="Processing...", bg="#1e3a5f")
        self.progress.pack(fill="x", pady=(4, 0))
        self._clear_results()
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        total = len(self.files)
        done = 0
        moved = []

        self._set_status("Scanning files…", ACCENT)

        for filepath in list(self.files):
            name = Path(filepath).name
            self._set_status(f"Processing  {name}…", ACCENT)

            try:
                data    = extract(filepath)
                folder  = classify(data, name, self.folders)

                if folder and folder != "unsorted":
                    dest = organize(filepath, folder, self.output_dir)
                    moved.append((name, folder))
                    # ── Remove successfully organised file from the upload list ──
                    self.root.after(0, self._remove_file, filepath)
                else:
                    moved.append((name, "unsorted (no matching folder)"))
                    # Unsorted files stay in the upload frame intentionally

                done += 1
                pct = (done / total) * 100
                self.root.after(0, self.progress_var.set, pct)
                self._add_result_row(name, folder, done)
            except Exception as e:
                self._set_status(f"Error on {name}: {str(e)}", DANGER)
                done += 1
                pct = (done / total) * 100
                self.root.after(0, self.progress_var.set, pct)
                self._add_result_row(name, f"Failed ({str(e)})", done)

        # All done
        self.root.after(0, self._finish, moved)

    def _finish(self, moved):
        self.run_btn.config(state="normal", text="▶   Organise Files", bg=ACCENT)
        self.progress.pack_forget()
        n = len(moved)
        self._set_status(f"Done — {n} file{'s' if n != 1 else ''} organised ✓", SUCCESS)


    def _set_status(self, msg, color=TEXT_MID):
        dot_colors = {ACCENT: ACCENT, SUCCESS: SUCCESS,
                      DANGER: DANGER, TEXT_MID: TEXT_DIM}
        dot = dot_colors.get(color, TEXT_DIM)
        self.root.after(0, lambda: (
            self.status_dot.config(fg=dot),
            self.status_text.config(text=msg, fg=color)
        ))

    def _clear_results(self):
        if self.results_placeholder:
            self.results_placeholder.destroy()
            self.results_placeholder = None
        for w in self.results_inner.winfo_children():
            w.destroy()
        # Reset scroll to top so new rows are visible from the beginning
        self._results_canvas.yview_moveto(0)

    def _add_result_row(self, name, folder, index):
        self.root.after(0, lambda: ResultRow(
            self.results_inner, name, folder, index).pack(fill="x"))


# ── Progressbar style ─────────────────────────────────────
def _style_progressbar():
    s = ttk.Style()
    s.theme_use("default")
    s.configure("TProgressbar",
                troughcolor=SURFACE2,
                background=ACCENT,
                bordercolor=BORDER,
                lightcolor=ACCENT,
                darkcolor=ACCENT,
                thickness=4)

if __name__ == "__main__":
    root = tk.Tk()
    _style_progressbar()
    App(root)
    root.mainloop()