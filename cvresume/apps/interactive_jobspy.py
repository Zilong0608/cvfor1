from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from jobspy import scrape_jobs


def build_google_search_term(search_term: str, location: str, country: str) -> str:
    parts = [search_term.strip(), "jobs"]
    if location:
        parts.append(f"near {location.strip()}")
    if country:
        parts.append(country.strip())
    return " ".join(part for part in parts if part)


def pick_columns(columns: Iterable[str], preferred: Iterable[str]) -> list[str]:
    cols = list(columns)
    lower_map = {c.lower(): c for c in cols}
    picked: list[str] = []
    for name in preferred:
        if name in cols:
            picked.append(name)
            continue
        actual = lower_map.get(name.lower())
        if actual:
            picked.append(actual)
    return picked


GENERIC_TITLE_TERMS = {
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


def _normalize_token(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def filter_by_title(jobs, keyword: str):
    if not hasattr(jobs, "columns"):
        return jobs
    title_candidates = pick_columns(jobs.columns, ["title"])
    if not title_candidates:
        return jobs
    title_col = title_candidates[0]
    raw_terms = [part for part in keyword.split() if part.strip()]
    normalized_terms = [_normalize_token(term) for term in raw_terms]
    normalized_terms = [term for term in normalized_terms if term]
    required_terms = [term for term in normalized_terms if term not in GENERIC_TITLE_TERMS]
    if not required_terms:
        return jobs
    title_series = jobs[title_col].astype(str).str.lower()

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


def expand_search_terms(search_term: str, extra_terms: list[str]) -> list[str]:
    normalized = _normalize_token(search_term)
    expanded: list[str] = []
    for _, terms in DEFAULT_SYNONYM_GROUPS:
        normalized_terms = {_normalize_token(term) for term in terms}
        if normalized in normalized_terms:
            expanded.extend(terms)
            break
    if not expanded:
        expanded = [search_term]
    if search_term not in expanded:
        expanded.insert(0, search_term)
    for extra in extra_terms:
        if extra not in expanded:
            expanded.append(extra)
    return expanded


def dedupe_jobs(jobs: pd.DataFrame) -> pd.DataFrame:
    if jobs.empty:
        return jobs
    for col in ("job_url_direct", "job_url"):
        if col in jobs.columns:
            valid = jobs[col].astype(str)
            mask = valid.notna() & valid.str.strip().ne("") & valid.str.lower().ne("nan")
            return jobs.loc[~jobs[col].duplicated(keep="first") | ~mask]
    return jobs


def main() -> None:
    print("JobSpy interactive search")
    country = input("Country (for Indeed/Glassdoor, e.g. USA): ").strip()
    location = input("Location (city/state or full address): ").strip()
    raw_input = input("Job keyword (comma-separated for extra synonyms, optional): ").strip()

    if not raw_input:
        print("Job keyword is required.")
        return

    parts = [part.strip() for part in raw_input.split(",") if part.strip()]
    search_term = parts[0]
    extra_terms = parts[1:]
    search_terms = expand_search_terms(search_term, extra_terms)
    print(f"Searching terms: {', '.join(search_terms)}")

    jobs_list: list[pd.DataFrame] = []
    for term in search_terms:
        google_search_term = build_google_search_term(term, location, country)
        kwargs = {
            "site_name": ["indeed", "linkedin", "zip_recruiter", "google"],
            "search_term": term,
            "google_search_term": google_search_term,
            "results_wanted": 100,
        }
        if location:
            kwargs["location"] = location
        if country:
            kwargs["country_indeed"] = country

        term_jobs = scrape_jobs(**kwargs)
        term_jobs = filter_by_title(term_jobs, term)
        if hasattr(term_jobs, "columns") and not term_jobs.empty:
            jobs_list.append(term_jobs)

    if jobs_list:
        jobs = pd.concat(jobs_list, ignore_index=True)
    else:
        jobs = pd.DataFrame()

    jobs = dedupe_jobs(jobs)
    print(f"Found {len(jobs)} jobs")

    preferred = ["site", "title", "company", "location", "job_url"]
    if hasattr(jobs, "columns"):
        selected = pick_columns(jobs.columns, preferred)
        if selected:
            print(jobs[selected].head(100).to_string(index=False))
            return

    print(jobs.head(100))


if __name__ == "__main__":
    main()
