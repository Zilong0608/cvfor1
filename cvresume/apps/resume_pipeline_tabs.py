from __future__ import annotations

import sys
import tempfile
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception:  # pragma: no cover - optional GUI dependency
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.resume_builder_gui import ResumeGUI
from apps.resume_summary_agent_gui import ResumeSummaryAgentGUI


if tk is None:
    class TabRoot:  # pragma: no cover - GUI only
        def __init__(self, *_args, **_kwargs) -> None:
            raise RuntimeError("tkinter is not available in this environment.")
else:
    class TabRoot(tk.Frame):
        def title(self, *_args, **_kwargs) -> None:
            pass

        def geometry(self, *_args, **_kwargs) -> None:
            pass


class ResumePipelineTabs:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Resume Pipeline (Tabs)")
        self.root.geometry("1400x900")

        self.top_bar = ttk.Frame(self.root, padding=(8, 6))
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.builder_tab = TabRoot(self.notebook)
        self.summary_tab = TabRoot(self.notebook)

        self.notebook.add(self.builder_tab, text="Resume Builder")
        self.notebook.add(self.summary_tab, text="Resume Summary Agent")

        self.builder_gui = ResumeGUI(self.builder_tab)
        self.summary_gui = ResumeSummaryAgentGUI(self.summary_tab)

        self.temp_template: Path | None = None
        self._inject_sync_controls()
        self._wire_builder_button()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _inject_sync_controls(self) -> None:
        ttk.Label(self.top_bar, text="Sync:").pack(side=tk.LEFT)
        ttk.Button(self.top_bar, text="Builder -> Summary", command=self.sync_builder_to_summary).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Label(self.top_bar, text="Use this after editing in Builder.").pack(side=tk.LEFT)

    def _wire_builder_button(self) -> None:
        if not getattr(self.builder_gui, "summary_agent_button", None):
            return
        def _open_summary_from_builder() -> None:
            if not self.sync_builder_to_summary():
                return
            self.notebook.select(self.summary_tab)
        self.builder_gui.summary_agent_button.configure(command=_open_summary_from_builder)

    def _build_raw_text_from_builder(self) -> str:
        if hasattr(self.builder_gui, "_commit_skill_input"):
            self.builder_gui._commit_skill_input()
        if hasattr(self.builder_gui, "_build_raw_text_from_gui"):
            return self.builder_gui._build_raw_text_from_gui()
        if not hasattr(self.builder_gui, "_gather_data"):
            return ""

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

    def _write_temp_template(self, raw_text: str) -> Path:
        if self.temp_template and self.temp_template.exists():
            try:
                self.temp_template.unlink()
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
            self.temp_template = Path(handle.name)
        return self.temp_template

    def _guess_output_dir(self) -> str | None:
        output_value = getattr(self.builder_gui, "output_var", None)
        if output_value is None:
            return None
        path_value = output_value.get().strip()
        if not path_value:
            return None
        try:
            output_path = Path(path_value).expanduser()
            if output_path.suffix:
                return str(output_path.parent)
            return str(output_path)
        except OSError:
            return None

    def sync_builder_to_summary(self) -> bool:
        raw_text = self._build_raw_text_from_builder()
        if not raw_text.strip():
            messagebox.showerror("Missing data", "Resume Builder has no content yet.")
            return False
        temp_template = self._write_temp_template(raw_text)
        self.summary_gui.template_var.set(str(temp_template))
        output_dir = self._guess_output_dir()
        if output_dir:
            self.summary_gui.output_var.set(output_dir)
        if hasattr(self.summary_gui, "_log"):
            self.summary_gui._log("Template updated from Resume Builder.")
        return True

    def _on_close(self) -> None:
        if self.temp_template and self.temp_template.exists():
            try:
                self.temp_template.unlink()
            except OSError:
                pass
        self.root.destroy()


def main() -> None:
    if tk is None:
        raise RuntimeError("tkinter is not available in this environment.")
    app = ResumePipelineTabs()
    app.root.mainloop()


if __name__ == "__main__":
    main()
