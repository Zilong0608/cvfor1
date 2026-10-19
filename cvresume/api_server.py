from __future__ import annotations

import os
import html
import io
import json
import re
import tempfile
import zipfile
import logging
from time import monotonic
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

os.environ.setdefault("DISABLE_TK", "1")

from agents.docx_writer import write_job_docx
from agents.summary_agent import generate_summary
from agents.resume_parser import parse_with_ai
from job_search_service import search_events
from apps.resume_builder_gui import (
    EducationEntry,
    ExperienceEntry,
    ResumeData,
    extract_text_from_file,
    parse_resume_text,
    render_pdf,
)
from apps.resume_summary_agent_gui import (
    build_job_context,
    build_resume_context,
    extract_requirement_lines,
    match_resume_skills,
    safe_slug,
    safe_text,
    truncate_text,
)


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
    expanded: bool = False
    results_per_site: int = Field(default=20, ge=5, le=100)


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
    warnings: list[str] = Field(default_factory=list)


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
ZIP_STORE: dict[str, tuple[Path, str]] = {}


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<(?:br\s*/?|/p|/div|/li|/h[1-6]|/tr)\s*>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()).strip()


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
    if "contact" not in data.model_fields_set and not phone and data.phone:
        phone = data.phone
    if "contact" not in data.model_fields_set and not email and data.email:
        email = data.email
    # The editable frontend field is authoritative, including an intentional blank.
    summary = data.intro if "intro" in data.model_fields_set else (data.summary or "")
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


def _ndjson(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


@app.post("/api/resume/parse")
async def parse_resume_endpoint(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
) -> JSONResponse:
    started = monotonic()
    if file is None and not text:
        raise HTTPException(status_code=400, detail="Missing resume file or text.")

    resume_text = ""
    if file is not None:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".pdf", ".docx", ".txt", ".html", ".htm"}:
            raise HTTPException(status_code=400, detail="Use PDF, DOCX, TXT or HTML.")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".tmp") as tmp:
                tmp_path = Path(tmp.name)
                size = 0
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 10 * 1024 * 1024:
                        raise HTTPException(status_code=413, detail="Resume must be smaller than 10 MB.")
                    tmp.write(chunk)
            if suffix in {".html", ".htm"}:
                raw = tmp_path.read_text(encoding="utf-8", errors="ignore")
                resume_text = _strip_html(raw)
            else:
                resume_text = await run_in_threadpool(extract_text_from_file, tmp_path)
        except HTTPException:
            raise
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

    if len(resume_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="No readable resume text. For scanned PDFs, upload a text-based PDF or DOCX.")
    if len(resume_text) > 40000:
        raise HTTPException(status_code=413, detail="Resume is too long. Please upload a shorter document.")
    warnings: list[str] = []
    method = "rules"
    resume = None
    if os.getenv("RESUME_AI_PARSE", "1") != "0" and (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")):
        try:
            resume = await run_in_threadpool(parse_with_ai, resume_text)
            method = "ai"
        except Exception as exc:
            logging.getLogger("uvicorn.error").warning("AI resume parse failed (%s); using rules", type(exc).__name__)
            warnings.append("AI extraction is temporarily unavailable. Review the extracted fields carefully.")
    else:
        warnings.append("Basic extraction was used. Review the extracted fields carefully.")
    if resume is None:
        try:
            parsed = await run_in_threadpool(parse_resume_text, resume_text)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Could not read the resume structure. Try DOCX or a text-based PDF.") from exc
        resume = _resume_to_frontend(parsed)
    logging.getLogger("uvicorn.error").info("resume_parse method=%s seconds=%.2f chars=%d", method, monotonic() - started, len(resume_text))
    return JSONResponse({"resume": resume, "method": method, "warnings": warnings})


@app.get("/api/health")
def health_endpoint() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/jobs/search/stream")
def search_jobs_stream(params: JobSearchParams) -> StreamingResponse:
    events = search_events(params.title, params.region or "", params.country or "AU",
                           params.expanded, params.results_per_site)
    return StreamingResponse((_ndjson(event) for event in events),
                             media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/jobs/search")
def search_jobs_endpoint(params: JobSearchParams) -> JobSearchResponse:
    for event in search_events(params.title, params.region or "", params.country or "AU",
                               params.expanded, params.results_per_site):
        if event["type"] == "error":
            raise HTTPException(status_code=400, detail=event["message"])
        if event["type"] == "done":
            return JobSearchResponse(**{key: value for key, value in event.items() if key != "type"})
    raise HTTPException(status_code=503, detail="Search did not complete. Please retry.")


def _write_resume_files(data: ResumeData, output_dir: Path, job_lines: list[str]) -> None:
    """Never include a partial/corrupt PDF in a batch download."""
    pdf_path = output_dir / "resume.pdf"
    docx_path = output_dir / "job_info.docx"
    try:
        render_pdf(data, pdf_path)
        write_job_docx(docx_path, job_lines)
    except Exception:
        pdf_path.unlink(missing_ok=True)
        docx_path.unlink(missing_ok=True)
        raise


@app.post("/api/resumes/zip")
def generate_zip_endpoint(payload: GenerateZipRequest) -> StreamingResponse:
    if not payload.jobs:
        raise HTTPException(status_code=400, detail="No jobs provided.")

    resume_data = _resume_from_frontend(payload.resume)
    resume_context = build_resume_context(resume_data)

    errors: list[str] = []
    generated = 0
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
            try:
                _write_resume_files(data_copy, output_dir, job_lines)
                generated += 1
            except Exception as exc:
                logging.getLogger("uvicorn.error").exception("Resume file generation failed")
                errors.append(f"{idx:03d} {title or 'Untitled role'}: PDF generation failed ({type(exc).__name__}).")
                continue

        if generated == 0:
            raise HTTPException(status_code=500, detail="No resume PDFs could be generated. Check the server PDF/font configuration and retry.")

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
        generated = 0
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
                try:
                    _write_resume_files(data_copy, output_dir, job_lines)
                    generated += 1
                except Exception as exc:
                    logging.getLogger("uvicorn.error").exception("Resume file generation failed")
                    message = f"[{index + 1}/{total}] PDF generation failed ({type(exc).__name__})."
                    errors.append(message)
                    yield _ndjson({"type": "log", "message": message})

                yield _ndjson({"type": "progress", "current": index + 1, "total": total})

            if generated == 0:
                yield _ndjson({"type": "error", "message": "No resume PDFs could be generated. Check the server PDF/font configuration and retry."})
                return

            failed = end - start - generated
            yield _ndjson({"type": "log", "message": f"Generated {generated} resumes; {failed} failed. See errors.txt in the ZIP for any failures."})

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
                "generated": generated,
                "failed": failed,
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
