from __future__ import annotations

import tempfile
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception:  # pragma: no cover - optional GUI dependency
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]

from apps.resume_builder_gui import ResumeGUI
from apps.resume_summary_agent_gui import ResumeSummaryAgentGUI


class ResumePipelineController:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Resume Pipeline")

        self.builder_window: tk.Toplevel | None = None
        self.builder_gui: ResumeGUI | None = None
        self.summary_window: tk.Toplevel | None = None
        self.summary_gui: ResumeSummaryAgentGUI | None = None
        self.last_temp_template: Path | None = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._open_builder()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Controller: open the Resume Builder first, then send data to Summary Agent.",
        ).pack(anchor="w")

        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w", pady=(10, 0))

        ttk.Button(buttons, text="Open Resume Builder", command=self._open_builder).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Open Summary Agent", command=self._open_summary).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Send Builder Data -> Summary", command=self._sync_to_summary).pack(
            side=tk.LEFT, padx=6
        )

        note = (
            "Tip: use 'Send Builder Data -> Summary' after you finish editing "
            "so the Summary Agent uses the latest content."
        )
        ttk.Label(frame, text=note, foreground="#555").pack(anchor="w", pady=(10, 0))

    def _open_builder(self) -> None:
        if self.builder_window and self.builder_window.winfo_exists():
            self.builder_window.lift()
            return
        self.builder_window = tk.Toplevel(self.root)
        self.builder_window.title("Resume Builder")
        self.builder_gui = ResumeGUI(self.builder_window)
        self.builder_window.protocol("WM_DELETE_WINDOW", self._close_builder)

    def _open_summary(self, template_path: str | None = None, output_path: str | None = None) -> None:
        if self.summary_window and self.summary_window.winfo_exists():
            if template_path and self.summary_gui:
                self.summary_gui.template_var.set(template_path)
            if output_path and self.summary_gui:
                self.summary_gui.output_var.set(output_path)
            self.summary_window.lift()
            return
        self.summary_window = tk.Toplevel(self.root)
        self.summary_window.title("Resume Summary Agent")
        self.summary_gui = ResumeSummaryAgentGUI(
            self.summary_window,
            template_path=template_path,
            output_path=output_path,
        )
        self.summary_window.protocol("WM_DELETE_WINDOW", self._close_summary)

    def _close_builder(self) -> None:
        if self.builder_window:
            self.builder_window.destroy()
        self.builder_window = None
        self.builder_gui = None

    def _close_summary(self) -> None:
        if self.summary_window:
            self.summary_window.destroy()
        self.summary_window = None
        self.summary_gui = None

    def _on_close(self) -> None:
        if self.builder_window and self.builder_window.winfo_exists():
            self.builder_window.destroy()
        if self.summary_window and self.summary_window.winfo_exists():
            self.summary_window.destroy()
        self.root.destroy()

    def _build_raw_text_from_builder(self) -> str:
        if not self.builder_gui:
            return ""
        if hasattr(self.builder_gui, "_commit_skill_input"):
            self.builder_gui._commit_skill_input()
        if hasattr(self.builder_gui, "_build_raw_text_from_gui"):
            return self.builder_gui._build_raw_text_from_gui()
        if hasattr(self.builder_gui, "_gather_data"):
            data = self.builder_gui._gather_data()
            parts: list[str] = []
            if data.name:
                parts.append(data.name)
            if data.email:
                parts.append(data.email)
            if data.summary:
                parts.extend(["Summary", data.summary])
            if data.skills:
                parts.append("Skills")
                parts.extend(data.skills)
            if data.experience:
                parts.append("Experience")
                for entry in data.experience:
                    if entry.title:
                        parts.append(entry.title)
                    if entry.company:
                        parts.append(entry.company)
                    if entry.dates:
                        parts.append(entry.dates)
                    parts.extend(entry.bullets)
            if data.education:
                parts.append("Education")
                for entry in data.education:
                    if entry.degree:
                        parts.append(entry.degree)
                    if entry.school:
                        parts.append(entry.school)
                    if entry.dates:
                        parts.append(entry.dates)
                    if entry.coursework:
                        parts.append(entry.coursework)
            return "\n".join(part for part in parts if part)
        return ""

    def _write_temp_template(self, raw_text: str) -> Path:
        if self.last_temp_template and self.last_temp_template.exists():
            try:
                self.last_temp_template.unlink()
            except OSError:
                pass
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            prefix="resume_pipeline_",
            delete=False,
        ) as handle:
            handle.write(raw_text)
            temp_path = Path(handle.name)
        self.last_temp_template = temp_path
        return temp_path

    def _suggest_output_dir(self) -> str | None:
        if not self.builder_gui or not hasattr(self.builder_gui, "output_var"):
            return None
        output_value = self.builder_gui.output_var.get().strip()
        if not output_value:
            return None
        try:
            output_path = Path(output_value).expanduser()
            if output_path.suffix:
                return str(output_path.parent)
            return str(output_path)
        except OSError:
            return None

    def _sync_to_summary(self) -> None:
        if not self.builder_gui or not (self.builder_window and self.builder_window.winfo_exists()):
            messagebox.showerror("Missing Resume Builder", "Open the Resume Builder first.")
            return
        raw_text = self._build_raw_text_from_builder()
        if not raw_text.strip():
            messagebox.showerror("Missing data", "Resume Builder has no content yet.")
            return
        temp_template = self._write_temp_template(raw_text)
        output_dir = self._suggest_output_dir()
        self._open_summary(str(temp_template), output_dir)


def main() -> None:
    if tk is None:
        raise RuntimeError("tkinter is not available in this environment.")
    controller = ResumePipelineController()
    controller.root.mainloop()


if __name__ == "__main__":
    main()
