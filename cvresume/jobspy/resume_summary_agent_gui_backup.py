from __future__ import annotations

import argparse
import queue
import re
import sys
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.docx_writer import write_job_docx
from agents.summary_agent import generate_summary
from apps.resume_builder_gui import extract_text_from_file, parse_resume_text, render_pdf
from jobspy import scrape_jobs

BASE_SITES = [
    "indeed",
    "linkedin",
    "zip_recruiter",
    "google",
    "glassdoor",
]
COUNTRY_SITES = {
    "india": ["naukri"],
    "bangladesh": ["bdjobs"],
}
MENA_COUNTRIES = {
    "bahrain",
    "egypt",
    "iraq",
    "jordan",
    "kuwait",
    "lebanon",
    "morocco",
    "oman",
    "qatar",
    "saudi",
    "saudi arabia",
    "uae",
    "united arab emirates",
}


def select_sites(country: str) -> list[str]:
    country_norm = (country or "").strip().lower()
    sites = list(BASE_SITES)
    for key, extra_sites in COUNTRY_SITES.items():
        if key in country_norm:
            sites.extend(extra_sites)
    if any(name in country_norm for name in MENA_COUNTRIES):
        sites.append("bayt")
    return sites


def build_google_search_term(search_term: str, location: str, country: str) -> str:
    parts = [search_term.strip(), "jobs"]
    if location:
        parts.append(f"near {location.strip()}")
    if country:
        parts.append(country.strip())
    return " ".join(part for part in parts if part)


def filter_by_title(jobs: pd.DataFrame, keyword: str) -> pd.DataFrame:
    if jobs.empty or "title" not in jobs.columns or not keyword:
        return jobs
    generic_terms = {
        "engineer",
        "engineering",
        "developer",
        "development",
        "software",
        "programmer",
        "coder",
        "specialist",
        "senior",
        "sr",
        "junior",
        "jr",
        "lead",
        "principal",
        "staff",
        "intern",
        "internship",
        "associate",
    }
    raw_terms = [part for part in keyword.split() if part.strip()]
    normalized_terms = [re.sub(r"[^a-z0-9]+", "", term.lower()) for term in raw_terms]
    normalized_terms = [term for term in normalized_terms if term]
    required_terms = [term for term in normalized_terms if term not in generic_terms]
    if not required_terms:
        return jobs

    title_series = jobs["title"].astype(str).str.lower()

    def matches_required(title: str) -> bool:
        words = re.findall(r"[a-z0-9]+", title)
        joined = "".join(words)
        for term in required_terms:
            if len(term) <= 2:
                if term not in words:
                    return False
            else:
                if term not in joined:
                    return False
        return True

    mask = title_series.apply(matches_required)
    return jobs[mask]


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def truncate_text(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rsplit(" ", 1)[0] + "..."


def safe_slug(value: str, fallback: str) -> str:
    if not value:
        return fallback
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned[:60] if cleaned else fallback


def build_resume_context(resume_data) -> str:
    parts: list[str] = []
    if resume_data.summary:
        parts.append(f"Current summary: {resume_data.summary}")
    if resume_data.skills:
        parts.append(f"Skills: {'; '.join(resume_data.skills)}")
    if resume_data.education:
        for entry in resume_data.education:
            line_parts = [entry.degree, entry.school, entry.dates]
            if entry.major:
                line_parts.append(f"Major: {entry.major}")
            if entry.coursework:
                line_parts.append(f"Coursework: {entry.coursework}")
            line = ", ".join(part for part in line_parts if part)
            if line:
                parts.append(f"Education: {line}")
    if resume_data.experience:
        for entry in resume_data.experience:
            line_parts = [entry.title, entry.dates]
            line = ", ".join(part for part in line_parts if part)
            bullets = [b for b in entry.bullets if b][:3]
            if bullets:
                line = f"{line} | Highlights: {'; '.join(bullets)}" if line else f"Highlights: {'; '.join(bullets)}"
            if line:
                parts.append(f"Experience: {line}")
    if resume_data.certifications:
        parts.append(f"Certifications: {'; '.join(resume_data.certifications)}")
    if resume_data.languages:
        parts.append(f"Languages: {'; '.join(resume_data.languages)}")
    context = "\n".join(parts)
    return truncate_text(context, 3500)


def _strip_markup(text: str) -> str:
    if "<" in text and ">" in text:
        text = re.sub(r"<[^>]+>", " ", text)
    return text


def extract_requirement_lines(description: str, max_lines: int = 8) -> list[str]:
    if not description:
        return []
    text = _strip_markup(description)
    text = text.replace("\r", "\n")
    text = re.sub(r"[•\u2022]", "\n", text)
    lines = [line.strip() for line in text.splitlines()]
    headings = [
        "requirements",
        "qualifications",
        "skills",
        "must have",
        "what you will need",
        "what you'll need",
        "minimum qualifications",
        "preferred qualifications",
        "basic qualifications",
        "required",
    ]
    collected: list[str] = []
    capture = False
    for line in lines:
        if not line:
            if capture and collected:
                break
            continue
        normalized = re.sub(r"[:\-]+$", "", line.lower()).strip()
        if any(
            normalized == key or normalized.startswith(key + ":")
            for key in headings
        ):
            capture = True
            continue
        if capture:
            if any(
                normalized == key or normalized.startswith(key + ":")
                for key in headings
            ):
                break
            cleaned = re.sub(r"^[-*]\s+", "", line)
            if cleaned:
                collected.append(cleaned)
        if len(collected) >= max_lines:
            break
    return collected


def match_resume_skills(description: str, resume_skills: list[str]) -> list[str]:
    if not description or not resume_skills:
        return []
    text = _strip_markup(description).lower()
    matches: list[str] = []
    for skill in resume_skills:
        skill_clean = skill.strip()
        if not skill_clean:
            continue
        pattern = r"\b" + re.escape(skill_clean.lower()) + r"\b"
        if re.search(pattern, text) or skill_clean.lower() in text:
            matches.append(skill_clean)
    return matches[:12]


def build_job_context(job: dict[str, str]) -> str:
    parts = []
    if job.get("title"):
        parts.append(f"Title: {job['title']}")
    if job.get("location"):
        parts.append(f"Location: {job['location']}")
    if job.get("site"):
        parts.append(f"Site: {job['site']}")
    if job.get("requirements"):
        parts.append(f"Requirements: {job['requirements']}")
    if job.get("matched_skills"):
        parts.append(f"Matched skills: {job['matched_skills']}")
    if job.get("description"):
        parts.append(f"Description: {job['description']}")
    return "\n".join(parts)


def dedupe_jobs(jobs: pd.DataFrame) -> pd.DataFrame:
    if jobs.empty:
        return jobs
    jobs = jobs.copy()
    url_direct = jobs["job_url_direct"] if "job_url_direct" in jobs.columns else None
    url_base = jobs["job_url"] if "job_url" in jobs.columns else None
    if url_direct is not None and url_base is not None:
        key = url_direct.fillna(url_base)
    elif url_base is not None:
        key = url_base
    elif url_direct is not None:
        key = url_direct
    else:
        return jobs
    key_str = key.astype(str)
    valid_mask = key.notna() & key_str.str.strip().ne("") & key_str.str.lower().ne("nan")
    duplicate_mask = key.duplicated(keep="first") & valid_mask
    return jobs.loc[~duplicate_mask]


class ResumeSummaryAgentGUI:
    def __init__(self, root: tk.Tk, template_path: str | None = None, output_path: str | None = None) -> None:
        self.root = root
        self.root.title("Resume Summary Agent")
        self.log_queue: queue.Queue[str] = queue.Queue()

        base_dir = Path(__file__).resolve().parents[1]
        default_template = base_dir / "templates" / "resume_template.docx"
        default_output = base_dir / "outputs" / "简历返回"

        template_value = str(default_template)
        if template_path:
            template_value = template_path
        self.template_var = tk.StringVar(value=template_value)
        self.search_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.country_var = tk.StringVar(value="USA")
        self.results_var = tk.StringVar(value="100")
        output_value = str(default_output)
        if output_path:
            output_value = output_path
        self.output_var = tk.StringVar(value=output_value)
        self.title_filter_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._poll_log_queue()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Resume template (docx/pdf/txt):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.template_var, width=60).grid(row=0, column=1, sticky=tk.W)
        ttk.Button(frame, text="Browse", command=self._browse_template).grid(row=0, column=2, padx=6)

        ttk.Label(frame, text="Job keyword:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.search_var, width=40).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(frame, text="Location:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.location_var, width=40).grid(row=2, column=1, sticky=tk.W)

        ttk.Label(frame, text="Country:").grid(row=3, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.country_var, width=20).grid(row=3, column=1, sticky=tk.W)

        ttk.Label(frame, text="Results wanted:").grid(row=4, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.results_var, width=10).grid(row=4, column=1, sticky=tk.W)

        ttk.Checkbutton(frame, text="Filter by title keyword", variable=self.title_filter_var).grid(
            row=5, column=1, sticky=tk.W, pady=4
        )

        ttk.Label(frame, text="Output folder:").grid(row=6, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.output_var, width=60).grid(row=6, column=1, sticky=tk.W)
        ttk.Button(frame, text="Browse", command=self._browse_output).grid(row=6, column=2, padx=6)

        self.run_button = ttk.Button(frame, text="Start", command=self._start_generation)
        self.run_button.grid(row=7, column=0, pady=8, sticky=tk.W)

        self.log_text = tk.Text(frame, height=16, width=90, state=tk.DISABLED)
        self.log_text.grid(row=8, column=0, columnspan=3, pady=8)

    def _browse_template(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Resume files", "*.docx *.pdf *.txt"), ("All files", "*")]
        )
        if path:
            self.template_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def _log(self, message: str) -> None:
        print(message)
        self.log_queue.put(message)

    def _poll_log_queue(self) -> None:
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(200, self._poll_log_queue)

    def _start_generation(self) -> None:
        if not self.search_var.get().strip():
            messagebox.showerror("Missing input", "Job keyword is required.")
            return
        self.run_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_generation, daemon=True).start()

    def _run_generation(self) -> None:
        try:
            template_path = Path(self.template_var.get()).expanduser()
            output_root = Path(self.output_var.get()).expanduser()
            search_term = self.search_var.get().strip()
            location = self.location_var.get().strip()
            country = self.country_var.get().strip()
            try:
                results_wanted = int(self.results_var.get())
            except ValueError:
                results_wanted = 100

            if not template_path.exists():
                self._log(f"Template not found: {template_path}")
                return

            output_root.mkdir(parents=True, exist_ok=True)
            resume_text = extract_text_from_file(template_path)
            resume_data = parse_resume_text(resume_text)
            resume_context = build_resume_context(resume_data)

            self._log("Fetching jobs...")
            google_search_term = build_google_search_term(search_term, location, country)
            sites = select_sites(country)
            kwargs = {
                "site_name": sites,
                "search_term": search_term,
                "google_search_term": google_search_term,
                "results_wanted": results_wanted,
            }
            if location:
                kwargs["location"] = location
            if country:
                kwargs["country_indeed"] = country

            self._log(f"Sites: {', '.join(sites)}")
            jobs_df = scrape_jobs(**kwargs)
            total_scraped = len(jobs_df)
            self._log(f"Jobs fetched: {total_scraped}")
            if self.title_filter_var.get():
                jobs_df = filter_by_title(jobs_df, search_term)
                self._log(f"After title filter: {len(jobs_df)}")
            jobs_df = dedupe_jobs(jobs_df)
            self._log(f"After dedupe: {len(jobs_df)}")
            if not jobs_df.empty and "site" in jobs_df.columns:
                site_counts = jobs_df["site"].value_counts().to_dict()
                site_summary = ", ".join(f"{key}: {val}" for key, val in site_counts.items())
                if site_summary:
                    self._log(f"By site: {site_summary}")

            if jobs_df.empty:
                self._log("No jobs found.")
                return

            jobs_df = jobs_df.head(results_wanted)
            total = len(jobs_df)
            self._log(f"Generating {total} resumes...")

            for idx, (_, row) in enumerate(jobs_df.iterrows(), start=1):
                title = safe_text(row.get("title"))
                company = safe_text(row.get("company"))
                location_val = safe_text(row.get("location"))
                site = safe_text(row.get("site"))
                description = safe_text(row.get("description"))
                description = truncate_text(description, 1200) if description else ""
                job_url = safe_text(row.get("job_url_direct")) or safe_text(row.get("job_url"))

                requirements_lines = extract_requirement_lines(description)
                requirements_text = "; ".join(requirements_lines) if requirements_lines else ""
                matched_skills = match_resume_skills(description, resume_data.skills)
                matched_skills_text = "; ".join(matched_skills) if matched_skills else ""

                job_info = {
                    "title": title,
                    "company": company,
                    "location": location_val,
                    "site": site,
                    "description": description,
                    "job_url": job_url,
                    "requirements": requirements_text,
                    "matched_skills": matched_skills_text,
                }
                job_context = build_job_context(job_info)

                self._log(f"[{idx}/{total}] Summarizing: {title or 'Untitled role'}")
                try:
                    summary = generate_summary(
                        resume_context,
                        job_context,
                        company_name=company,
                    )
                except Exception as exc:
                    self._log(f"[{idx}/{total}] Summary failed: {exc}")
                    continue

                data_copy = deepcopy(resume_data)
                data_copy.summary = summary

                folder_name = "_".join(
                    [
                        f"{idx:03d}",
                        safe_slug(site, "site"),
                        safe_slug(company, "company"),
                        safe_slug(title, "role"),
                    ]
                )
                output_dir = output_root / folder_name
                output_dir.mkdir(parents=True, exist_ok=True)

                render_pdf(data_copy, output_dir / "resume.pdf")

                job_lines = [
                    f"Job Title: {title}",
                    f"Company: {company}",
                    f"Location: {location_val}",
                    f"Site: {site}",
                    f"Job URL: {job_url}",
                    "",
                    "Description:",
                    description,
                ]
                write_job_docx(output_dir / "job_info.docx", job_lines)

            self._log("Done.")
        except Exception as exc:
            self._log(f"Error: {exc}")
        finally:
            self.root.after(0, lambda: self.run_button.configure(state=tk.NORMAL))


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume Summary Agent")
    parser.add_argument("--template", help="Resume template path to prefill")
    parser.add_argument("--output", help="Output folder to prefill")
    args = parser.parse_args()

    root = tk.Tk()
    ResumeSummaryAgentGUI(root, template_path=args.template, output_path=args.output)
    root.mainloop()


if __name__ == "__main__":
    main()
