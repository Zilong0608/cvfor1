from __future__ import annotations

import argparse
import os
import queue
import re
import sys
import threading
from datetime import datetime
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
if os.getenv("DISABLE_TK") == "1":
    tk = None  # type: ignore[assignment]
    filedialog = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
else:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception:  # pragma: no cover - optional GUI dependency
        tk = None  # type: ignore[assignment]
        filedialog = None  # type: ignore[assignment]
        messagebox = None  # type: ignore[assignment]
        ttk = None  # type: ignore[assignment]

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


DEFAULT_SYNONYM_GROUPS: list[tuple[str, list[str]]] = [
    (
        "backend engineering",
        [
            "backend",
            "back-end",
            "back end",
            "backend engineer",
            "backend engineering",
            "backend software engineer",
            "backend developer",
            "back-end engineer",
            "back end engineer",
            "backend systems engineer",
            "backend services engineer",
            "server-side engineer",
            "server side engineer",
            "server-side engineering",
            "server side engineering",
            "server-side developer",
            "server side developer",
            "api engineer",
            "api engineering",
            "api developer",
            "service engineer",
            "services engineer",
            "microservices engineer",
        ],
    ),
    (
        "frontend engineering",
        [
            "frontend",
            "front-end",
            "front end",
            "frontend engineer",
            "front-end engineer",
            "front end engineer",
            "frontend software engineer",
            "frontend developer",
            "front-end developer",
            "front end developer",
            "web engineer",
            "web engineering",
            "web frontend engineer",
            "web frontend developer",
            "web developer",
            "web designer",
            "client-side engineer",
            "client side engineer",
            "client-side engineering",
            "client side engineering",
            "ui developer",
            "ui engineer",
            "ux engineer",
            "ui designer",
            "ux designer",
            "ui/ux designer",
            "ui ux designer",
            "ux ui designer",
            "user interface designer",
            "user experience designer",
            "interaction designer",
            "visual designer",
            "product designer",
        ],
    ),
    (
        "full stack engineering",
        [
            "full stack",
            "fullstack",
            "full-stack",
            "full stack engineer",
            "fullstack engineer",
            "full-stack engineer",
            "full stack software engineer",
            "full-stack software engineer",
            "full stack developer",
            "full-stack developer",
            "product engineer",
            "end to end engineer",
            "end to end engineering",
            "end-to-end product engineer",
            "end-to-end product engineering",
            "full stack engineering",
        ],
    ),
    (
        "mobile engineering",
        [
            "mobile engineer",
            "mobile engineering",
            "mobile application developer",
            "mobile application engineer",
            "mobile app developer",
            "mobile app engineer",
            "mobile developer",
            "mobile software engineer",
            "android engineer",
            "android developer",
            "ios engineer",
            "ios developer",
            "react native developer",
            "flutter developer",
            "cross-platform engineer",
            "cross platform engineer",
            "cross-platform developer",
            "cross platform developer",
        ],
    ),
    (
        "systems engineering",
        [
            "systems engineer",
            "system engineer",
            "systems software engineer",
            "embedded engineer",
            "embedded software engineer",
            "embedded systems engineer",
            "embedded developer",
            "firmware engineer",
            "firmware developer",
            "systems programmer",
            "c software engineer",
            "c++ software engineer",
            "c developer",
            "c++ developer",
            "c/c++ developer",
            "kernel engineer",
            "device driver engineer",
            "os engineer",
            "performance engineer",
            "low-level software engineer",
            "low level software engineer",
            "systems engineering",
        ],
    ),
    (
        "general software engineering",
        [
            "software engineer",
            "senior software engineer",
            "software engineering",
            "software developer",
            "software development engineer",
        ],
    ),
    (
        "data analysis",
        [
            "data analyst",
            "business intelligence analyst",
            "bi analyst",
            "analytics analyst",
            "insights analyst",
            "reporting analyst",
            "data analytics",
        ],
    ),
    (
        "data engineering",
        [
            "data engineer",
            "data platform engineer",
            "big data engineer",
            "data pipeline engineer",
            "data infrastructure engineer",
            "data warehouse engineer",
            "data integration engineer",
            "analytics engineer",
            "etl engineer",
            "etl developer",
        ],
    ),
    (
        "machine learning engineering",
        [
            "machine learning engineer",
            "applied machine learning engineer",
            "ml engineer",
            "machine learning engineering",
            "ml engineering",
        ],
    ),
    (
        "data science",
        [
            "data scientist",
            "applied scientist",
            "decision scientist",
            "data science",
        ],
    ),
    (
        "ai engineering",
        [
            "ai engineer",
            "applied ai engineer",
            "generative ai engineer",
            "genai engineer",
            "generative ai developer",
            "ai/ml engineer",
            "ai ml engineer",
            "machine learning engineer",
            "ml engineer",
            "applied machine learning engineer",
            "applied ml engineer",
            "llm engineer",
            "llm developer",
            "ai application engineer",
            "ai applications engineer",
            "llm application engineer",
            "ai developer",
            "ai research engineer",
            "ai researcher",
            "nlp engineer",
            "natural language processing engineer",
            "computer vision engineer",
            "mlops engineer",
            "ml ops engineer",
        ],
    ),
    (
        "qa engineering",
        [
            "qa engineer",
            "quality assurance engineer",
            "quality assurance analyst",
            "quality engineer",
            "software test engineer",
            "test engineer",
            "qa analyst",
            "software qa",
        ],
    ),
    (
        "test automation",
        [
            "automation test engineer",
            "test automation engineer",
            "sdet",
            "software development engineer in test",
            "qa automation engineer",
            "test automation",
            "automation engineer in test",
        ],
    ),
    (
        "devops",
        [
            "devops engineer",
            "dev ops engineer",
            "devops",
            "ci/cd engineer",
            "build and release engineer",
        ],
    ),
    (
        "site reliability",
        [
            "site reliability engineer",
            "sre",
            "reliability engineer",
            "site reliability",
            "production engineer",
        ],
    ),
    (
        "cloud engineering",
        [
            "cloud engineer",
            "cloud infrastructure engineer",
            "cloud platform engineer",
            "cloud solutions engineer",
            "cloud developer",
        ],
    ),
    (
        "platform engineering",
        [
            "platform engineer",
            "platform engineering",
            "platform software engineer",
            "internal platform engineer",
            "platform developer",
            "internal developer platform",
            "idp engineer",
        ],
    ),
    (
        "systems administration",
        [
            "systems administrator",
            "system administrator",
            "linux administrator",
            "linux systems administrator",
            "linux admin",
            "systems admin",
            "sysadmin",
            "windows administrator",
            "it administrator",
        ],
    ),
    (
        "network engineering",
        [
            "network engineer",
            "network infrastructure engineer",
            "network administrator",
            "network operations engineer",
            "network specialist",
        ],
    ),
    (
        "cybersecurity engineering",
        [
            "cybersecurity engineer",
            "information security engineer",
            "security engineer",
            "infosec engineer",
            "cyber security engineer",
        ],
    ),
    (
        "security operations",
        [
            "security operations engineer",
            "secops engineer",
            "secops",
            "security operations",
            "soc analyst",
            "soc engineer",
            "security analyst",
        ],
    ),
    (
        "cloud security",
        [
            "cloud security engineer",
            "application security engineer",
            "application security",
            "product security engineer",
        ],
    ),
    (
        "technical product management",
        [
            "technical product manager",
            "product manager",
            "technical product management",
            "technical product owner",
            "product owner",
        ],
    ),
    (
        "technical project management",
        [
            "technical project manager",
            "technical program manager",
            "tpm",
            "program manager",
            "project manager",
            "engineering program manager",
            "technical delivery manager",
        ],
    ),
    (
        "delivery and implementation",
        [
            "delivery manager",
            "implementation engineer",
            "implementation consultant",
            "implementation specialist",
            "delivery lead",
            "professional services engineer",
        ],
    ),
    (
        "solutions engineering",
        [
            "solutions engineer",
            "solutions architect",
            "solutions consultant",
            "customer solutions engineer",
        ],
    ),
    (
        "pre-sales engineering",
        [
            "pre-sales engineer",
            "presales engineer",
            "pre sales engineer",
            "sales engineer",
            "technical sales engineer",
            "sales engineering",
        ],
    ),
    (
        "technical consulting",
        [
            "technical consultant",
            "technology consultant",
            "implementation consultant",
            "solutions consultant",
        ],
    ),
    (
        "ui ux design",
        [
            "ui designer",
            "ux designer",
            "ui/ux designer",
            "ui ux designer",
            "ux ui designer",
            "user interface designer",
            "user experience designer",
            "interaction designer",
            "visual designer",
            "product designer",
            "ux researcher",
            "experience designer",
            "interface designer",
            "product design",
        ],
    ),
    (
        "entry level",
        [
            "graduate software engineer",
            "graduate software developer",
            "graduate engineer",
            "junior engineer",
            "junior software engineer",
            "associate data analyst",
            "graduate developer",
            "junior developer",
            "entry level engineer",
            "entry level software engineer",
            "software engineering intern",
            "intern",
            "graduate data analyst",
            "junior data analyst",
        ],
    ),
]


DEFAULT_SYNONYM_LIMIT = 5


def expand_search_terms(search_term: str, extra_terms: list[str]) -> list[str]:
    normalized = re.sub(r"[^a-z0-9]+", "", search_term.lower())
    base_terms: list[str] = []
    for _, terms in DEFAULT_SYNONYM_GROUPS:
        normalized_terms = {re.sub(r"[^a-z0-9]+", "", term.lower()) for term in terms}
        if normalized in normalized_terms:
            base_terms = list(terms)
            break
    if not base_terms:
        base_terms = [search_term]
    if search_term not in base_terms:
        base_terms.insert(0, search_term)
    expanded = list(base_terms)
    for extra in extra_terms:
        if extra not in expanded:
            expanded.append(extra)
    return expanded


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def build_job_key(row: pd.Series) -> str:
    for col in ("job_url_direct", "job_url"):
        val = safe_text(row.get(col))
        if val:
            return f"url:{val.lower()}"
    title = normalize_key(safe_text(row.get("title")))
    company = normalize_key(safe_text(row.get("company")))
    location = normalize_key(safe_text(row.get("location")))
    if title or company or location:
        return f"title:{title}|company:{company}|location:{location}"
    return ""


def filter_seen_jobs(jobs: pd.DataFrame, seen_keys: set[str]) -> pd.DataFrame:
    if jobs.empty:
        return jobs
    keys = jobs.apply(build_job_key, axis=1)
    keep_mask: list[bool] = []
    for key in keys:
        if not key:
            keep_mask.append(True)
            continue
        if key in seen_keys:
            keep_mask.append(False)
        else:
            keep_mask.append(True)
            seen_keys.add(key)
    return jobs.loc[keep_mask].copy()


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
        self.continue_button: ttk.Button | None = None
        self.jobs_df: pd.DataFrame | None = None
        self.next_index = 0
        self.resume_data = None
        self.resume_context = ""
        self.output_root: Path | None = None
        self.run_output_root: Path | None = None
        self.search_terms: list[str] = []
        self.search_term_index = 0
        self.search_state: dict[str, Any] = {}
        self.seen_job_keys: set[str] = set()
        self.search_more_button = None

        self._build_ui()
        self._poll_log_queue()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Resume template (docx/pdf/txt):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.template_var, width=60).grid(row=0, column=1, sticky=tk.W)
        ttk.Button(frame, text="Browse", command=self._browse_template).grid(row=0, column=2, padx=6)

        ttk.Label(frame, text="Job keyword (comma-separated for extra synonyms):").grid(
            row=1, column=0, sticky=tk.W, pady=4
        )
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
        self.continue_button = ttk.Button(frame, text="Continue", command=self._start_continue, state=tk.DISABLED)
        self.continue_button.grid(row=7, column=1, pady=8, sticky=tk.W)
        self.search_more_button = ttk.Button(frame, text="Search More", command=self._start_search_more, state=tk.DISABLED)
        self.search_more_button.grid(row=7, column=2, pady=8, sticky=tk.W)

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

    def _next_search_terms(self) -> list[str]:
        if not self.search_terms:
            return []
        start = self.search_term_index
        end = min(start + DEFAULT_SYNONYM_LIMIT, len(self.search_terms))
        return self.search_terms[start:end]

    def _log_search_batch(self, terms: list[str]) -> None:
        total = len(self.search_terms) if self.search_terms else len(terms)
        start = self.search_term_index + 1
        end = self.search_term_index + len(terms)
        self._log(
            f"Searching terms (rounds {start}-{end} of {total}, batch size {DEFAULT_SYNONYM_LIMIT}): {', '.join(terms)}"
        )

    def _log_site_counts(self, jobs: pd.DataFrame, label: str = "By site") -> None:
        if jobs.empty or "site" not in jobs.columns:
            return
        site_counts = jobs["site"].value_counts().to_dict()
        if not site_counts:
            return
        site_summary = ", ".join(f"{key}: {val}" for key, val in site_counts.items())
        self._log(f"{label}: {site_summary}")

    def _fetch_jobs_for_terms(
        self,
        terms: list[str],
        *,
        location: str,
        country: str,
        results_wanted: int,
        sites: list[str],
    ) -> pd.DataFrame:
        self._log("Fetching jobs...")
        all_jobs: list[pd.DataFrame] = []
        for term in terms:
            google_search_term = build_google_search_term(term, location, country)
            kwargs = {
                "site_name": sites,
                "search_term": term,
                "google_search_term": google_search_term,
                "results_wanted": results_wanted,
            }
            if location:
                kwargs["location"] = location
            if country:
                kwargs["country_indeed"] = country

            self._log(f"Sites: {', '.join(sites)}")
            jobs_df = scrape_jobs(**kwargs)
            self._log(f"Jobs fetched: {len(jobs_df)}")
            if self.title_filter_var.get():
                jobs_df = filter_by_title(jobs_df, term)
                self._log(f"After title filter: {len(jobs_df)}")
            jobs_df = dedupe_jobs(jobs_df)
            self._log(f"After dedupe: {len(jobs_df)}")
            if hasattr(jobs_df, "columns") and not jobs_df.empty:
                all_jobs.append(jobs_df)

        if all_jobs:
            jobs = pd.concat(all_jobs, ignore_index=True)
        else:
            jobs = pd.DataFrame()

        jobs = dedupe_jobs(jobs)
        return jobs

    def _append_jobs(self, jobs: pd.DataFrame) -> int:
        if jobs.empty:
            return 0
        filtered = filter_seen_jobs(jobs, self.seen_job_keys)
        if filtered.empty:
            return 0
        if self.jobs_df is None or self.jobs_df.empty:
            self.jobs_df = filtered
        else:
            self.jobs_df = pd.concat([self.jobs_df, filtered], ignore_index=True)
            self.jobs_df = dedupe_jobs(self.jobs_df)
        return len(filtered)

    def _update_button_states(self) -> None:
        self.run_button.configure(state=tk.NORMAL)
        if self.continue_button:
            cont_state = (
                tk.NORMAL
                if self.jobs_df is not None
                and not self.jobs_df.empty
                and self.next_index < len(self.jobs_df)
                else tk.DISABLED
            )
            self.continue_button.configure(state=cont_state)
        if self.search_more_button:
            more_state = (
                tk.NORMAL
                if self.search_terms and self.search_term_index < len(self.search_terms)
                else tk.DISABLED
            )
            self.search_more_button.configure(state=more_state)
    def _start_generation(self) -> None:
        if not self.search_var.get().strip():
            messagebox.showerror("Missing input", "Job keyword is required.")
            return
        self.run_button.configure(state=tk.DISABLED)
        if self.continue_button:
            self.continue_button.configure(state=tk.DISABLED)
        if self.search_more_button:
            self.search_more_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_generation, args=("start",), daemon=True).start()

    def _start_continue(self) -> None:
        if self.jobs_df is None or self.jobs_df.empty:
            messagebox.showerror("Missing input", "No previous job list. Click Start first.")
            return
        if self.next_index >= len(self.jobs_df):
            messagebox.showinfo("Done", "No more jobs to generate.")
            return
        self.run_button.configure(state=tk.DISABLED)
        if self.continue_button:
            self.continue_button.configure(state=tk.DISABLED)
        if self.search_more_button:
            self.search_more_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_generation, args=("continue",), daemon=True).start()

    def _start_search_more(self) -> None:
        if not self.search_terms:
            messagebox.showerror("Missing input", "No previous search. Click Start first.")
            return
        if self.search_term_index >= len(self.search_terms):
            messagebox.showinfo("Done", "No more search terms to run.")
            return
        self.run_button.configure(state=tk.DISABLED)
        if self.continue_button:
            self.continue_button.configure(state=tk.DISABLED)
        if self.search_more_button:
            self.search_more_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_search_more, daemon=True).start()

    def _run_search_more(self) -> None:
        try:
            if not self.search_state:
                self._log("Search state missing. Click Start first.")
                return
            terms = self._next_search_terms()
            if not terms:
                self._log("No more search terms.")
                return
            self._log_search_batch(terms)

            new_jobs = self._fetch_jobs_for_terms(
                terms,
                location=self.search_state.get("location", ""),
                country=self.search_state.get("country", ""),
                results_wanted=self.search_state.get("results_wanted", 100),
                sites=self.search_state.get("sites", BASE_SITES),
            )
            self.search_term_index += len(terms)
            added = self._append_jobs(new_jobs)
            self._log(f"New unique jobs: {added}")
            if self.jobs_df is not None:
                self._log_site_counts(self.jobs_df)
                self._log(f"Total unique jobs: {len(self.jobs_df)}")
            remaining = len(self.search_terms) - self.search_term_index
            if remaining > 0:
                self._log(f"Remaining terms: {remaining}")
        except Exception as exc:
            self._log(f"Error: {exc}")
        finally:
            self.root.after(0, self._update_button_states)

    def _run_generation(self, mode: str) -> None:
        try:
            template_path = Path(self.template_var.get()).expanduser()
            output_root = Path(self.output_var.get()).expanduser()
            search_input = self.search_var.get().strip()
            location = self.location_var.get().strip()
            country = self.country_var.get().strip()
            try:
                results_wanted = int(self.results_var.get())
            except ValueError:
                results_wanted = 100

            if mode == "start":
                if not template_path.exists():
                    self._log(f"Template not found: {template_path}")
                    return

                output_root.mkdir(parents=True, exist_ok=True)
                resume_text = extract_text_from_file(template_path)
                self.resume_data = parse_resume_text(resume_text)
                self.resume_context = build_resume_context(self.resume_data)
                self.output_root = output_root
                run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_slug = safe_slug(search_input.split(",")[0].strip(), "run")
                self.run_output_root = output_root / f"run_{run_stamp}_{run_slug}"
                self.run_output_root.mkdir(parents=True, exist_ok=True)
                self._log(f"Output folder: {self.run_output_root}")

                parts = [part.strip() for part in search_input.split(",") if part.strip()]
                if not parts:
                    self._log("Job keyword is required.")
                    return
                search_term = parts[0]
                extra_terms = parts[1:]
                self.search_terms = expand_search_terms(search_term, extra_terms)
                self.search_term_index = 0
                self.seen_job_keys = set()
                self.jobs_df = pd.DataFrame()
                self.next_index = 0

                sites = select_sites(country)
                self.search_state = {
                    "location": location,
                    "country": country,
                    "results_wanted": results_wanted,
                    "sites": sites,
                }

                terms = self._next_search_terms()
                if not terms:
                    self._log("No search terms available.")
                    return
                self._log_search_batch(terms)

                new_jobs = self._fetch_jobs_for_terms(
                    terms,
                    location=location,
                    country=country,
                    results_wanted=results_wanted,
                    sites=sites,
                )
                self.search_term_index += len(terms)
                added = self._append_jobs(new_jobs)
                if added:
                    self._log(f"New unique jobs: {added}")
                if self.jobs_df is None or self.jobs_df.empty:
                    self._log("No jobs found.")
                    return
                self._log_site_counts(self.jobs_df)
                self._log(f"Total unique jobs: {len(self.jobs_df)}")
                remaining = len(self.search_terms) - self.search_term_index
                if remaining > 0:
                    self._log(f"Remaining terms: {remaining}")

            if self.jobs_df is None or self.jobs_df.empty:
                self._log("No jobs to process. Click Start first.")
                return

            if self.resume_data is None:
                self._log("Resume data missing. Click Start first.")
                return

            output_root = self.run_output_root or self.output_root or output_root
            batch_start = self.next_index
            batch_end = min(batch_start + results_wanted, len(self.jobs_df))
            if batch_start >= batch_end:
                self._log("No more jobs found.")
                return

            batch_df = self.jobs_df.iloc[batch_start:batch_end]
            total = len(batch_df)
            self._log(f"Generating {total} resumes ({batch_start + 1}-{batch_end} of {len(self.jobs_df)})...")

            for idx, (_, row) in enumerate(batch_df.iterrows(), start=batch_start + 1):
                title = safe_text(row.get("title"))
                company = safe_text(row.get("company"))
                location_val = safe_text(row.get("location"))
                site = safe_text(row.get("site"))
                description = safe_text(row.get("description"))
                description = truncate_text(description, 1200) if description else ""
                job_url = safe_text(row.get("job_url_direct")) or safe_text(row.get("job_url"))

                requirements_lines = extract_requirement_lines(description)
                requirements_text = "; ".join(requirements_lines) if requirements_lines else ""
                matched_skills = match_resume_skills(description, self.resume_data.skills)
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

                self._log(f"[{idx}/{len(self.jobs_df)}] Summarizing: {title or 'Untitled role'}")
                try:
                    summary = generate_summary(
                        self.resume_context,
                        job_context,
                        company_name=company,
                    )
                except Exception as exc:
                    self._log(f"[{idx}/{len(self.jobs_df)}] Summary failed: {exc}")
                    continue

                data_copy = deepcopy(self.resume_data)
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

            self.next_index = batch_end
            self._log("Batch complete.")
        except Exception as exc:
            self._log(f"Error: {exc}")
        finally:
            self.root.after(0, self._update_button_states)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume Summary Agent")
    parser.add_argument("--template", help="Resume template path to prefill")
    parser.add_argument("--output", help="Output folder to prefill")
    args = parser.parse_args()

    if tk is None:
        raise RuntimeError("tkinter is not available in this environment.")
    root = tk.Tk()
    ResumeSummaryAgentGUI(root, template_path=args.template, output_path=args.output)
    root.mainloop()


if __name__ == "__main__":
    main()
