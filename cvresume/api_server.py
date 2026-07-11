from __future__ import annotations

import os
import html
import io
import json
import re
import tempfile
import zipfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

os.environ.setdefault("DISABLE_TK", "1")

from agents.docx_writer import write_job_docx
from agents.summary_agent import generate_summary
from apps.resume_builder_gui import (
    EducationEntry,
    ExperienceEntry,
    ResumeData,
    extract_text_from_file,
    parse_resume_text,
    render_pdf,
)
from apps.resume_summary_agent_gui import (
    DEFAULT_SYNONYM_LIMIT,
    build_google_search_term,
    build_job_context,
    build_resume_context,
    dedupe_jobs,
    expand_search_terms,
    extract_requirement_lines,
    filter_by_title,
    match_resume_skills,
    safe_slug,
    safe_text,
    select_sites,
    truncate_text,
)
from jobspy import scrape_jobs


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EducationItem(BaseModel):
    school: str = ""
    period: str = ""
    degree: str = ""


class ExperienceItem(BaseModel):
    company: str = ""
    period: str = ""
    role: str = ""
    details: list[str] = Field(default_factory=list)


class ResumeDataIn(BaseModel):
    name: str = ""
    contact: str = ""
    intro: str = ""
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    phone: str | None = None
    email: str | None = None
    summary: str | None = None
    certifications: list[str] = Field(default_factory=list)
    community: list[str] = Field(default_factory=list)
    additional: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class JobSearchParams(BaseModel):
    title: str
    region: str | None = None
    country: str | None = None


class JobResult(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    site: str | None = None
    description: str | None = None
    job_url: str | None = None
    job_url_direct: str | None = None


class JobSearchResponse(BaseModel):
    jobs: list[JobResult]
    analysis: str | None = None
    total: int | None = None


class GenerateZipRequest(BaseModel):
    resume: ResumeDataIn
    jobs: list[JobResult]


class GenerateZipStreamRequest(BaseModel):
    resume: ResumeDataIn
    jobs: list[JobResult]
    start: int = 0
    limit: int = 100


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
COUNTRY_CODE_MAP = {
    "US": "USA",
    "AU": "Australia",
    "UK": "UK",
    "CA": "Canada",
    "SG": "Singapore",
}

ZIP_STORE: dict[str, tuple[Path, str]] = {}


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _split_contact(contact: str) -> tuple[str, str]:
    if not contact:
        return "", ""
    email_match = EMAIL_RE.search(contact)
    phone_match = PHONE_RE.search(contact)
    email = email_match.group(0) if email_match else ""
    phone = phone_match.group(0).strip() if phone_match else ""
    return phone, email


def _resume_to_frontend(data: ResumeData) -> dict[str, Any]:
    contact_parts = [part for part in [data.phone, data.email] if part]
    contact = " | ".join(contact_parts)

    education = []
    for entry in data.education:
        degree_parts = [entry.degree]
        if entry.major:
            degree_parts.append(f"Major: {entry.major}")
        if entry.coursework:
            degree_parts.append(f"Coursework: {entry.coursework}")
        education.append(
            {
                "school": entry.school or "",
                "period": entry.dates or "",
                "degree": " | ".join(part for part in degree_parts if part),
            }
        )

    experience = []
    for entry in data.experience:
        experience.append(
            {
                "company": entry.company or "",
                "period": entry.dates or "",
                "role": entry.title or "",
                "details": [bullet for bullet in entry.bullets if bullet],
            }
        )

    return {
        "name": data.name or "",
        "contact": contact,
        "intro": data.summary or "",
        "education": education,
        "experience": experience,
        "skills": list(data.skills or []),
        "phone": data.phone or "",
        "email": data.email or "",
        "summary": data.summary or "",
        "certifications": list(data.certifications or []),
        "community": list(data.community or []),
        "additional": list(data.additional or []),
        "languages": list(data.languages or []),
    }


def _resume_from_frontend(data: ResumeDataIn) -> ResumeData:
    phone, email = _split_contact(data.contact)
    if not phone and data.phone:
        phone = data.phone
    if not email and data.email:
        email = data.email
    summary = data.summary if data.summary is not None else data.intro
    education = [
        EducationEntry(
            degree=item.degree or "",
            dates=item.period or "",
            school=item.school or "",
            major="",
            coursework="",
        )
        for item in data.education
    ]
    experience = [
        ExperienceEntry(
            title=item.role or "",
            dates=item.period or "",
            company=item.company or "",
            bullets=list(item.details or []),
        )
        for item in data.experience
    ]
    return ResumeData(
        name=data.name or "",
        phone=phone,
        email=email,
        summary=summary or "",
        skills=list(data.skills or []),
        experience=experience,
        education=education,
        certifications=list(data.certifications or []),
        community=list(data.community or []),
        additional=list(data.additional or []),
        languages=list(data.languages or []),
    )


def _df_to_jobs(jobs: pd.DataFrame) -> list[dict[str, Any]]:
    if jobs is None or jobs.empty:
        return []
    columns = [
        "title",
        "company",
        "location",
        "site",
        "description",
        "job_url",
        "job_url_direct",
    ]
    for col in columns:
        if col not in jobs.columns:
            jobs[col] = None
    records: list[dict[str, Any]] = []
    for _, row in jobs.iterrows():
        item = {col: safe_text(row.get(col)) for col in columns}
        for key, value in item.items():
            if value == "":
                item[key] = None
        records.append(item)
    return records


def _build_analysis(terms: list[str], jobs: pd.DataFrame) -> str:
    lines = []
    if terms:
        lines.append(f"Search terms: {', '.join(terms)}")
    total = 0 if jobs is None else len(jobs)
    lines.append(f"Total unique jobs: {total}")
    if jobs is not None and not jobs.empty and "site" in jobs.columns:
        counts = jobs["site"].value_counts().to_dict()
        if counts:
            lines.append("By site: " + ", ".join(f"{key}: {val}" for key, val in counts.items()))
    return "\n".join(lines)


def _ndjson(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


@app.post("/api/resume/parse")
async def parse_resume_endpoint(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
) -> JSONResponse:
    if file is None and not text:
        raise HTTPException(status_code=400, detail="Missing resume file or text.")

    resume_text = ""
    if file is not None:
        suffix = Path(file.filename or "").suffix.lower()
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".tmp") as tmp:
                tmp.write(await file.read())
                tmp_path = Path(tmp.name)
            if suffix in {".html", ".htm"}:
                raw = tmp_path.read_text(encoding="utf-8", errors="ignore")
                resume_text = _strip_html(raw)
            else:
                resume_text = extract_text_from_file(tmp_path)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            if "tmp_path" in locals():
                try:
                    tmp_path.unlink(missing_ok=True)
                except Exception:
                    pass
    else:
        resume_text = text or ""

    try:
        parsed = parse_resume_text(resume_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse({"resume": _resume_to_frontend(parsed)})


@app.post("/api/jobs/search/stream")
def search_jobs_stream(params: JobSearchParams) -> StreamingResponse:
    title = (params.title or "").strip()
    if not title:
        return StreamingResponse(
            iter([_ndjson({"type": "error", "message": "Missing job title."})]),
            media_type="application/x-ndjson",
        )

    location = (params.region or "").strip()
    country_code = (params.country or "").strip().upper()
    country = COUNTRY_CODE_MAP.get(country_code, country_code)

    terms = expand_search_terms(title, [])
    if not terms:
        terms = [title]
    terms = terms[:DEFAULT_SYNONYM_LIMIT]
    sites = select_sites(country)

    def iter_lines():
        try:
            total_terms = len(terms)
            if total_terms:
                yield _ndjson(
                    {
                        "type": "log",
                        "message": f"Searching terms (1-{total_terms} of {total_terms}): {', '.join(terms)}",
                    }
                )
            if sites:
                yield _ndjson({"type": "log", "message": f"Sites: {', '.join(sites)}"})

            all_jobs: list[pd.DataFrame] = []
            for term in terms:
                yield _ndjson({"type": "log", "message": f"Fetching jobs for: {term}"})
                google_search_term = build_google_search_term(term, location, country)
                kwargs: dict[str, Any] = {
                    "site_name": sites,
                    "search_term": term,
                    "google_search_term": google_search_term,
                    "results_wanted": 100,
                }
                if location:
                    kwargs["location"] = location
                if country:
                    kwargs["country_indeed"] = country
                jobs_df = scrape_jobs(**kwargs)
                yield _ndjson({"type": "log", "message": f"Jobs fetched: {len(jobs_df)}"})
                if not jobs_df.empty:
                    jobs_df = filter_by_title(jobs_df, term)
                    yield _ndjson({"type": "log", "message": f"After title filter: {len(jobs_df)}"})
                    jobs_df = dedupe_jobs(jobs_df)
                    yield _ndjson({"type": "log", "message": f"After dedupe: {len(jobs_df)}"})
                    all_jobs.append(jobs_df)

            if all_jobs:
                jobs = pd.concat(all_jobs, ignore_index=True)
                jobs = dedupe_jobs(jobs)
            else:
                jobs = pd.DataFrame()

            if jobs is not None and not jobs.empty and "site" in jobs.columns:
                counts = jobs["site"].value_counts().to_dict()
                if counts:
                    site_summary = ", ".join(f"{key}: {val}" for key, val in counts.items())
                    yield _ndjson({"type": "log", "message": f"By site: {site_summary}"})

            yield _ndjson({"type": "log", "message": f"Total unique jobs: {len(jobs)}"})
            analysis = _build_analysis(terms, jobs)
            yield _ndjson(
                {
                    "type": "done",
                    "jobs": _df_to_jobs(jobs),
                    "analysis": analysis,
                    "total": len(jobs),
                }
            )
        except Exception as exc:
            yield _ndjson({"type": "error", "message": str(exc)})

    return StreamingResponse(iter_lines(), media_type="application/x-ndjson")


@app.post("/api/jobs/search")
def search_jobs_endpoint(params: JobSearchParams) -> JobSearchResponse:
    title = (params.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Missing job title.")

    location = (params.region or "").strip()
    country_code = (params.country or "").strip().upper()
    country = COUNTRY_CODE_MAP.get(country_code, country_code)

    terms = expand_search_terms(title, [])
    if not terms:
        terms = [title]
    terms = terms[:DEFAULT_SYNONYM_LIMIT]
    sites = select_sites(country)

    all_jobs: list[pd.DataFrame] = []
    for term in terms:
        google_search_term = build_google_search_term(term, location, country)
        kwargs: dict[str, Any] = {
            "site_name": sites,
            "search_term": term,
            "google_search_term": google_search_term,
            "results_wanted": 100,
        }
        if location:
            kwargs["location"] = location
        if country:
            kwargs["country_indeed"] = country
        try:
            jobs_df = scrape_jobs(**kwargs)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        if not jobs_df.empty:
            jobs_df = filter_by_title(jobs_df, term)
            jobs_df = dedupe_jobs(jobs_df)
            all_jobs.append(jobs_df)

    if all_jobs:
        jobs = pd.concat(all_jobs, ignore_index=True)
        jobs = dedupe_jobs(jobs)
    else:
        jobs = pd.DataFrame()

    analysis = _build_analysis(terms, jobs)
    return JobSearchResponse(jobs=_df_to_jobs(jobs), analysis=analysis, total=len(jobs))


@app.post("/api/resumes/zip")
def generate_zip_endpoint(payload: GenerateZipRequest) -> StreamingResponse:
    if not payload.jobs:
        raise HTTPException(status_code=400, detail="No jobs provided.")

    resume_data = _resume_from_frontend(payload.resume)
    resume_context = build_resume_context(resume_data)

    errors: list[str] = []
    buffer = io.BytesIO()

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        for idx, job in enumerate(payload.jobs, start=1):
            title = safe_text(job.title)
            company = safe_text(job.company)
            location_val = safe_text(job.location)
            site = safe_text(job.site)
            description = safe_text(job.description)
            description = truncate_text(description, 1200) if description else ""
            job_url = safe_text(job.job_url_direct) or safe_text(job.job_url)

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

            summary = ""
            try:
                summary = generate_summary(resume_context, job_context, company_name=company)
            except Exception as exc:
                errors.append(f"{idx:03d} {title or 'Untitled role'}: {exc}")
                summary = resume_data.summary

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
            output_dir = root / folder_name
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

        if errors:
            (root / "errors.txt").write_text("\n".join(errors), encoding="utf-8")

        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for file_path in root.rglob("*"):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(root).as_posix())

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=resumes.zip"},
    )


@app.post("/api/resumes/zip/stream")
def generate_zip_stream(payload: GenerateZipStreamRequest) -> StreamingResponse:
    def iter_lines():
        if not payload.jobs:
            yield _ndjson({"type": "error", "message": "No jobs provided."})
            return

        resume_data = _resume_from_frontend(payload.resume)
        resume_context = build_resume_context(resume_data)

        total = len(payload.jobs)
        start = max(0, payload.start)
        limit = max(1, payload.limit)
        end = min(start + limit, total)

        if start >= total:
            yield _ndjson({"type": "error", "message": "No more jobs to process."})
            return

        yield _ndjson(
            {
                "type": "log",
                "message": f"Generating {end - start} resumes ({start + 1}-{end} of {total})...",
            }
        )

        errors: list[str] = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            for index in range(start, end):
                job = payload.jobs[index]
                title = safe_text(job.title)
                company = safe_text(job.company)
                location_val = safe_text(job.location)
                site = safe_text(job.site)
                description = safe_text(job.description)
                description = truncate_text(description, 1200) if description else ""
                job_url = safe_text(job.job_url_direct) or safe_text(job.job_url)

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

                display_title = title or "Untitled role"
                yield _ndjson(
                    {
                        "type": "log",
                        "message": f"[{index + 1}/{total}] Summarizing: {display_title}",
                    }
                )

                summary = ""
                try:
                    summary = generate_summary(resume_context, job_context, company_name=company)
                except Exception as exc:
                    errors.append(f"{index + 1:03d} {display_title}: {exc}")
                    yield _ndjson(
                        {
                            "type": "log",
                            "message": f"[{index + 1}/{total}] Summary failed: {exc}",
                        }
                    )
                    summary = resume_data.summary

                data_copy = deepcopy(resume_data)
                data_copy.summary = summary

                folder_name = "_".join(
                    [
                        f"{index + 1:03d}",
                        safe_slug(site, "site"),
                        safe_slug(company, "company"),
                        safe_slug(title, "role"),
                    ]
                )
                output_dir = root / folder_name
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

                yield _ndjson({"type": "progress", "current": index + 1, "total": total})

            if errors:
                (root / "errors.txt").write_text("\n".join(errors), encoding="utf-8")

            zip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            zip_path = Path(zip_file.name)
            zip_file.close()

            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
                for file_path in root.rglob("*"):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.relative_to(root).as_posix())

        job_id = uuid4().hex
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"resumes_{start + 1}-{end}_{timestamp}.zip"
        ZIP_STORE[job_id] = (zip_path, zip_name)

        yield _ndjson(
            {
                "type": "done",
                "job_id": job_id,
                "zip_name": zip_name,
                "start": start,
                "end": end,
                "count": end - start,
                "total": total,
            }
        )

    return StreamingResponse(iter_lines(), media_type="application/x-ndjson")


@app.get("/api/resumes/zip/download/{job_id}")
def download_zip(job_id: str) -> FileResponse:
    entry = ZIP_STORE.get(job_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Zip not found or expired.")
    zip_path, zip_name = entry
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip file missing.")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_name,
    )
