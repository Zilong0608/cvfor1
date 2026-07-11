from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests

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


@dataclass
class ExperienceEntry:
    title: str
    dates: str
    company: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    degree: str
    dates: str
    school: str
    major: str
    coursework: str


@dataclass
class ResumeData:
    name: str
    phone: str
    email: str
    summary: str
    skills: list[str]
    experience: list[ExperienceEntry]
    education: list[EducationEntry]
    certifications: list[str]
    community: list[str]
    additional: list[str]
    languages: list[str]


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def strip_leading_bullets(text: str) -> str:
    return re.sub(r"^[\-\u2022\u25CF\u25A0\u25AA\*\+\s]+", "", text).strip()


def break_long_tokens(text: str, max_len: int = 30) -> str:
    parts: list[str] = []
    for token in text.split(" "):
        if len(token) <= max_len:
            parts.append(token)
        else:
            chunks = [token[i : i + max_len] for i in range(0, len(token), max_len)]
            parts.append(" ".join(chunks))
    return " ".join(parts)


def safe_text(text: str) -> str:
    return break_long_tokens(normalize_text(text))


def _xml_text(node: ET.Element, ns: dict[str, str]) -> str:
    return "".join(t.text for t in node.findall(".//w:t", ns) if t.text).strip()


def extract_docx_text(path: Path) -> str:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        xml_data = zf.read("word/document.xml")
    tree = ET.fromstring(xml_data)
    parts: list[str] = []

    body = tree.find(".//w:body", ns)
    if body is None:
        return ""

    for child in list(body):
        tag = child.tag.split("}")[-1]
        if tag == "p":
            text = _xml_text(child, ns)
            if text:
                parts.append(text)
        elif tag == "tbl":
            for row in child.findall(".//w:tr", ns):
                row_texts: list[str] = []
                for cell in row.findall(".//w:tc", ns):
                    cell_text = _xml_text(cell, ns)
                    if cell_text:
                        row_texts.append(cell_text)
                if row_texts:
                    parts.append(" | ".join(row_texts))
    return "\n".join(parts)


def extract_pdf_text(path: Path) -> str:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            raise RuntimeError("Missing dependency for PDF parsing. Install: pip install pdfplumber  (or PyPDF2)")
        reader = PdfReader(str(path))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(text_parts)

    with pdfplumber.open(str(path)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        return extract_docx_text(path)
    if suffix == ".pdf":
        return extract_pdf_text(path)
    raise ValueError("Unsupported file type. Use docx, pdf, or txt.")


def split_sections(text: str) -> dict[str, list[str]]:
    headings = {
        "summary": ["summary", "professional summary"],
        "skills": [
            "skills",
            "technical skills",
            "skills & certifications",
            "skills and certifications",
        ],
        "experience": [
            "experience",
            "work experience",
            "personal experience",
            "professional experience",
            "work history",
        ],
        "education": ["education"],
        "certifications": ["certifications"],
        "community": ["community service", "volunteer", "community service & volunteer work"],
        "additional": ["additional information", "additional info"],
        "languages": ["languages"],
    }

    current = "summary"
    sections: dict[str, list[str]] = {key: [] for key in headings}

    def _split_heading_line(line: str) -> tuple[str | None, str, str]:
        lowered = line.lower()
        for key, names in headings.items():
            for name in sorted(names, key=len, reverse=True):
                idx = lowered.find(name)
                if idx == -1:
                    continue
                before_ok = idx == 0 or not lowered[idx - 1].isalnum()
                after_idx = idx + len(name)
                after_ok = after_idx == len(lowered) or not lowered[after_idx].isalnum()
                if not (before_ok and after_ok):
                    continue
                pre = line[:idx].strip(" :-")
                post = line[after_idx:].strip(" :-")
                return key, pre, post
        return None, line, ""

    for line in text.splitlines():
        clean = normalize_text(line)
        if not clean:
            sections[current].append("")
            continue
        lowered = re.sub(r"[:\-\s]+$", "", clean.lower())
        matched = None
        for key, names in headings.items():
            if any(lowered == name for name in names):
                matched = key
                break
            if any(lowered.startswith(name) and len(lowered) <= len(name) + 6 for name in names):
                matched = key
                break
        if matched:
            current = matched
            continue

        split_key, pre, post = _split_heading_line(clean)
        if split_key:
            if pre:
                sections[current].append(pre)
            current = split_key
            if post:
                sections[current].append(post)
            continue

        sections[current].append(clean)

    return sections


def parse_skills(lines: Iterable[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        cleaned = strip_leading_bullets(line)
        if not cleaned:
            continue
        if ":" in cleaned:
            items.append(cleaned)
        elif "," in cleaned and "(" not in cleaned and ")" not in cleaned:
            items.extend([normalize_text(part) for part in cleaned.split(",") if part.strip()])
        else:
            items.append(cleaned)
    return items


def parse_bullets(lines: Iterable[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        item = strip_leading_bullets(line)
        if item:
            bullets.append(item)
    return bullets


def split_title_dates(line: str) -> tuple[str, str]:
    if "," in line:
        title, dates = line.split(",", 1)
        return normalize_text(title), normalize_text(dates)
    return normalize_text(line), ""


def _looks_like_date_line(line: str) -> bool:
    return bool(
        re.search(
            r"(\b(19|20)\d{2}\b|\b\d{1,2}/\d{4}\b|\b\d{4}\s*-\s*(\d{4}|present|current)\b|\b(19|20)\d{2}\b\s+(present|current|\b(19|20)\d{2}\b))",
            line,
            re.I,
        )
    )


def _looks_like_school(line: str) -> bool:
    if _looks_like_degree(line):
        return False
    if re.search(r"(?i)university|college|school|institute|academy|education|polytechnic", line):
        return True
    return bool(re.match(r"^[A-Z]{2,6}\b", line))


def _looks_like_degree(line: str) -> bool:
    return bool(
        re.search(
            r"(?i)degree|bachelor|master|phd|doctor|diploma|certificate|program|programme|foundation|associate|bsc|bs|ba|msc|ms|ma|mba|meng|mphil|beng|b\.sc|m\.sc|b\.s|m\.s|b\.a|m\.a",
            line,
        )
    )


def _looks_like_coursework(line: str) -> bool:
    return "relevant coursework" in line.lower() or "coursework" in line.lower()


def _looks_like_major(line: str) -> bool:
    return "major" in line.lower() or "specialization" in line.lower() or "specialisation" in line.lower()


def _is_bullet_line(line: str) -> bool:
    return bool(re.match(r"^[\-\u2022\u25CF\u25A0\u25AA\*\+]\s+", line.strip()))


def parse_experience(lines: Iterable[str]) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    current: list[str] = []
    seen_blank = False
    for line in lines:
        if line == "":
            seen_blank = True
            if current:
                entries.append(_parse_experience_block(current))
                current = []
            continue
        if not seen_blank and _looks_like_date_line(line) and current:
            entries.append(_parse_experience_block(current))
            current = [line]
            continue
        current.append(line)
    if current:
        entries.append(_parse_experience_block(current))
    return [entry for entry in entries if entry.title or entry.company]


def _parse_experience_block(lines: list[str]) -> ExperienceEntry:
    title = strip_leading_bullets(lines[0]) if lines else ""
    company = strip_leading_bullets(lines[1]) if len(lines) > 1 else ""
    bullets: list[str] = []
    if len(lines) > 1 and _is_bullet_line(lines[1]):
        company = ""
        bullets.extend(parse_bullets(lines[1:]))
    elif len(lines) > 2:
        bullets.extend(parse_bullets(lines[2:]))
    title, dates = split_title_dates(title)
    return ExperienceEntry(title=title, dates=dates, company=company, bullets=bullets)


def extract_community_from_experience(experience: list[ExperienceEntry]) -> tuple[list[ExperienceEntry], list[str]]:
    community: list[str] = []
    for entry in experience:
        kept: list[str] = []
        for bullet in entry.bullets:
            if re.search(r"(?i)\b(volunteer|community|orientation)\b", bullet):
                community.append(normalize_text(bullet))
            else:
                kept.append(bullet)
        entry.bullets = kept
    return experience, community



def parse_education(lines: Iterable[str]) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    current = EducationEntry(degree="", dates="", school="", major="", coursework="")
    collecting_coursework = False
    pending_coursework: list[str] = []
    pending_dates = ""

    date_token_re = re.compile(r"\b(19|20)\d{2}\b|\b\d{1,2}/\d{4}\b|\bpresent\b|\bcurrent\b", re.I)

    def _extract_dates(line: str) -> tuple[str, str]:
        matches = list(date_token_re.finditer(line))
        if not matches:
            return line, ""
        tokens = [m.group(0) for m in matches]
        year_tokens = [t for t in tokens if re.match(r"\d", t)]
        if not year_tokens:
            return line, ""
        has_present = any(t.lower() in {"present", "current"} for t in tokens)
        dates = f"{year_tokens[0]} Present" if has_present else f"{year_tokens[0]} {year_tokens[-1]}" if len(year_tokens) > 1 else year_tokens[0]
        start = matches[0].start()
        end = matches[-1].end()
        cleaned = (line[:start] + line[end:]).strip(" ,;-")
        return cleaned, dates

    def _looks_like_location(line: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z\s]+,\s*[A-Za-z\s]+", line))

    def _flush() -> None:
        nonlocal current, pending_coursework, collecting_coursework, pending_dates
        if pending_coursework and not current.coursework:
            current.coursework = normalize_text(" ".join(pending_coursework))
        if pending_dates and not current.dates and (current.school or current.degree):
            current.dates = pending_dates
        if any([current.school, current.degree, current.dates, current.major, current.coursework]):
            entries.append(current)
        current = EducationEntry(degree="", dates="", school="", major="", coursework="")
        pending_coursework = []
        pending_dates = ""
        collecting_coursework = False

    def _assign_school(school: str) -> None:
        nonlocal current, pending_dates
        if current.school and (current.degree or current.dates or current.coursework or current.major):
            _flush()
        current.school = current.school or normalize_text(school)
        if pending_dates and not current.dates and current.degree:
            current.dates = pending_dates
            pending_dates = ""

    def _assign_degree(degree: str) -> None:
        nonlocal current, pending_dates
        if current.degree and (current.school or current.dates or current.coursework):
            _flush()
        current.degree = current.degree or normalize_text(degree)
        if pending_dates and not current.dates:
            current.dates = pending_dates
            pending_dates = ""

    def _handle_piece(piece: str) -> None:
        nonlocal current
        if not piece:
            return
        if "," in piece:
            prefix, rest = [p.strip() for p in piece.split(",", 1)]
            if prefix and rest and _looks_like_degree(prefix):
                _assign_degree(prefix)
                piece = rest
            elif prefix and rest and _looks_like_school(prefix):
                _assign_school(prefix)
                piece = rest
        degree_match = re.search(
            r"(?i)\b(bachelor|master|phd|doctor|diploma|certificate|program|programme|foundation|associate|degree)\b",
            piece,
        )
        if degree_match and degree_match.start() > 0:
            leading = piece[: degree_match.start()].strip(" ,;-")
            if leading and _looks_like_school(leading):
                _assign_school(leading)
                piece = piece[degree_match.start() :].strip()
            elif leading:
                piece = piece[degree_match.start() :].strip()
        if (
            current.school
            and not current.degree
            and not _looks_like_degree(piece)
            and not _looks_like_school(piece)
            and re.fullmatch(r"[A-Za-z\s]+", piece or "")
            and len(piece.split()) <= 2
        ):
            return
        if _looks_like_location(piece):
            return
        if _looks_like_degree(piece):
            _assign_degree(piece)
            return
        if _looks_like_school(piece):
            _assign_school(piece)
            return
        if current.school and not current.degree:
            _assign_degree(piece)
        elif not current.school:
            _assign_school(piece)
        else:
            separator = ", " if "(" in current.degree and ")" not in current.degree else " "
            current.degree = normalize_text(f"{current.degree}{separator}{piece}".strip())

    for raw in lines:
        raw_line = strip_leading_bullets(raw)
        line = raw_line.strip(" ,")
        if not line:
            _flush()
            continue

        if line.startswith(","):
            line = line.lstrip(",").strip()

        has_location = bool(re.search(r"[A-Za-z]+\s*,\s*[A-Za-z]+", line))
        line, found_dates = _extract_dates(line)
        has_location = bool(re.search(r"[A-Za-z]+\s*,\s*[A-Za-z]+", line))
        if found_dates:
            if not line:
                pending_dates = normalize_text(found_dates)
                continue
            if current.school or current.degree:
                if has_location and _looks_like_degree(line) and current.school:
                    pending_dates = found_dates
                else:
                    current.dates = current.dates or normalize_text(found_dates)
            else:
                pending_dates = normalize_text(found_dates)
            if not _looks_like_school(line) and not _looks_like_degree(line) and (has_location or len(line.split()) <= 3):
                continue

        if current.school and not current.degree and not _looks_like_degree(line) and not _looks_like_school(line):
            if has_location or len(line.split()) <= 2:
                continue

        if not line:
            continue

        low = line.lower()
        if low in {"relevant coursework", "coursework"}:
            collecting_coursework = True
            continue
        if collecting_coursework:
            if _looks_like_school(line) or _looks_like_degree(line) or _looks_like_date_line(line):
                collecting_coursework = False
            else:
                pending_coursework.append(line)
                continue

        if _looks_like_coursework(line):
            parts = re.split(r"(?i)relevant coursework\s*: ?", line, maxsplit=1)
            prefix = normalize_text(parts[0]) if parts else ""
            if prefix and prefix.lower() not in {"relevant coursework", "coursework"}:
                if "|" in prefix:
                    for part in [p.strip() for p in prefix.split("|") if p.strip()]:
                        _handle_piece(part)
                else:
                    _handle_piece(prefix)
            text = normalize_text(parts[1] if len(parts) > 1 else "")
            if text:
                current.coursework = normalize_text(f"{current.coursework} {text}".strip()) if current.coursework else text
            continue

        if _looks_like_major(line):
            parts = re.split(r"(?i)major|specialization|specialisation", line, maxsplit=1)
            if len(parts) > 1 and not current.major:
                current.major = normalize_text(parts[1].lstrip(":").strip())
            if not _looks_like_degree(line):
                continue

        if "|" in line:
            for part in [p.strip() for p in line.split("|") if p.strip()]:
                _handle_piece(part)
            continue

        _handle_piece(line)

    _flush()
    return merge_education_entries([entry for entry in entries if entry.degree or entry.school])


def merge_education_entries(entries: list[EducationEntry]) -> list[EducationEntry]:
    merged: list[EducationEntry] = []
    idx = 0
    while idx < len(entries):
        current = entries[idx]
        if idx + 1 < len(entries):
            nxt = entries[idx + 1]
            if current.degree and not current.school and nxt.school and not nxt.degree:
                merged.append(
                    EducationEntry(
                        degree=current.degree,
                        dates=current.dates or nxt.dates,
                        school=nxt.school,
                        major=current.major or nxt.major,
                        coursework=current.coursework or nxt.coursework,
                    )
                )
                idx += 2
                continue
            if current.school and not current.degree and nxt.degree and not nxt.school:
                merged.append(
                    EducationEntry(
                        degree=nxt.degree,
                        dates=current.dates or nxt.dates,
                        school=current.school,
                        major=current.major or nxt.major,
                        coursework=current.coursework or nxt.coursework,
                    )
                )
                idx += 2
                continue
        merged.append(current)
        idx += 1
    return merged
def _parse_education_block(lines: list[str]) -> EducationEntry:
    cleaned = [strip_leading_bullets(line) for line in lines if strip_leading_bullets(line)]
    degree = ""
    school = ""
    dates = ""
    major = ""
    coursework = ""
    collecting_coursework = False
    date_pattern = re.compile(
        r"(?:\b(19|20)\d{2}\b\s*[-–]\s*(present|current|\b(19|20)\d{2}\b)"
        r"|\b(19|20)\d{2}\b\s+(present|current|\b(19|20)\d{2}\b)"
        r"|\b\d{1,2}/\d{4}\b\s*[-–]\s*\d{1,2}/\d{4}\b)",
        re.I,
    )

    def _extract_dates(line: str) -> tuple[str, str]:
        match = date_pattern.search(line)
        if not match:
            return line, ""
        dates_part = match.group(0).strip()
        cleaned_line = (line[: match.start()] + line[match.end() :]).strip(" ,;-")
        return cleaned_line, dates_part

    for line in cleaned:
        line, found_dates = _extract_dates(line)
        if found_dates and not dates:
            dates = normalize_text(found_dates)
        if line.lower() in {"relevant coursework", "coursework"}:
            collecting_coursework = True
            continue
        if _looks_like_coursework(line):
            parts = re.split(r"(?i)relevant coursework\s*: ?", line, maxsplit=1)
            coursework = normalize_text(parts[1] if len(parts) > 1 else line)
            continue
        if collecting_coursework and not _looks_like_date_line(line):
            coursework = normalize_text(" ".join([coursework, line]).strip()) if coursework else normalize_text(line)
            continue
        if _looks_like_major(line):
            parts = re.split(r"(?i)major|specialization|specialisation", line, maxsplit=1)
            if len(parts) > 1:
                major = normalize_text(parts[1].lstrip(":").strip())
            continue
        if _looks_like_date_line(line) and not dates:
            dates = normalize_text(line)
            continue
        if _looks_like_school(line) and not school:
            school = normalize_text(line)
            continue
        if _looks_like_degree(line) and not degree:
            degree = normalize_text(line)
            continue
        if "|" in line and not school:
            parts = [normalize_text(part) for part in line.split("|") if part.strip()]
            for part in parts:
                if _looks_like_school(part) and not school:
                    school = part
                elif _looks_like_degree(part) and not degree:
                    degree = part
        if dates and not school and line and len(line.split()) <= 4:
            school = normalize_text(line)

    if not degree and cleaned:
        for line in cleaned:
            if line != school and line != dates and not _looks_like_coursework(line):
                degree = normalize_text(line)
                break

    if degree and not school and dates and len(degree.split()) <= 4 and not _looks_like_degree(degree):
        school = degree
        degree = ""

    degree, split_dates = split_title_dates(degree)
    if not dates:
        dates = split_dates

    if "relevant coursework" in degree.lower():
        parts = re.split(r"(?i)relevant coursework\s*: ?", degree, maxsplit=1)
        degree = normalize_text(parts[0])
        if len(parts) > 1 and not coursework:
            coursework = normalize_text(parts[1])

    if "major" in degree.lower() or "specialization" in degree.lower() or "specialisation" in degree.lower():
        parts = re.split(r"(?i)major|specialization|specialisation", degree, maxsplit=1)
        degree = normalize_text(parts[0])
        if len(parts) > 1 and not major:
            major = normalize_text(parts[1].lstrip(":").strip())

    return EducationEntry(degree=degree, dates=dates, school=school, major=major, coursework=coursework)


def parse_resume_text(text: str) -> ResumeData:
    sections = split_sections(text)
    name, phone, email = extract_header_info(text)
    summary_lines = [line for line in sections.get("summary", []) if line]
    if email:
        summary_lines = [line for line in summary_lines if email not in line]
    if phone:
        summary_lines = [line for line in summary_lines if phone not in line]
    summary = " ".join(summary_lines)
    skills = parse_skills(sections.get("skills", []))
    experience = parse_experience(sections.get("experience", []))
    education = parse_education(sections.get("education", []))
    certifications = parse_bullets(sections.get("certifications", []))
    experience, community_from_exp = extract_community_from_experience(experience)
    community = community_from_exp + normalize_section_items(sections.get("community", []))
    additional = sections.get("additional", [])
    languages = parse_bullets(sections.get("languages", []))

    return ResumeData(
        name=name,
        phone=phone,
        email=email,
        summary=normalize_text(summary),
        skills=skills,
        experience=experience,
        education=education,
        certifications=certifications,
        community=community,
        additional=additional,
        languages=languages,
    )


def normalize_section_items(lines: Iterable[str]) -> list[str]:
    items: list[str] = []
    buffer = ""
    for raw in lines:
        line = normalize_text(raw)
        if not line:
            if buffer:
                items.append(buffer)
                buffer = ""
            continue
        is_year_only = bool(re.fullmatch(r"\(?\d{4}\)?", line))
        is_paren_year = bool(re.fullmatch(r"\(?\d{4}\)?", line.strip()))
        is_short_prefix = is_year_only or (line.startswith("(") and line.endswith(")") and len(line) <= 8)
        is_continuation = line[:1].islower()

        if is_short_prefix:
            buffer = f"{line} {buffer}".strip() if buffer else line
            continue

        if is_continuation and buffer:
            buffer = f"{buffer} {line}".strip()
            continue

        if buffer:
            items.append(buffer)
        buffer = line

    if buffer:
        items.append(buffer)
    return items


def polish_bullets(bullets: list[str]) -> list[str]:
    polished: list[str] = []
    for bullet in bullets:
        text = safe_text(bullet)
        if not text:
            continue
        if text[-1] not in ".!?":
            text = f"{text}."
        polished.append(text)
    return polished


def extract_header_info(text: str) -> tuple[str, str, str]:
    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    email = ""
    phone = ""
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.IGNORECASE)
    if email_match:
        email = email_match.group(0)
    phone_match = re.search(r"(?:\\+?\\d[\\d\\s().-]{7,}\\d)", text)
    if phone_match:
        phone = phone_match.group(0).strip()
    if not phone:
        for line in lines:
            if re.search(r"(?i)mobile|phone|tel", line):
                digits = re.search(r"(?:\\+?\\d[\\d\\s().-]{7,}\\d)", line)
                if digits:
                    phone = digits.group(0).strip()
                    break

    headings = {
        "summary",
        "professional summary",
        "skills",
        "technical skills",
        "skills & certifications",
        "skills and certifications",
        "experience",
        "work experience",
        "personal experience",
        "professional experience",
        "work history",
        "education",
        "certifications",
        "community service",
        "community service & volunteer work",
        "volunteer",
        "additional information",
        "additional info",
        "languages",
    }

    name = ""
    for line in lines:
        lower = line.lower()
        if lower in headings:
            continue
        if email and email in line:
            continue
        if phone and phone in line:
            continue
        if "@" in line:
            continue
        if re.search(r"[A-Za-z\\u4e00-\\u9fff]", line):
            if len(line.split()) <= 6:
                name = line
                break
    return name, phone, email


def find_cjk_font() -> Path | None:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\arialuni.ttf"),
    ]
    for font_path in candidates:
        if font_path.exists():
            return font_path
    return None


def _write_line(pdf, text: str) -> None:
    if not text:
        return
    try:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, text, wrapmode="CHAR")
    except TypeError:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, text)


def _split_to_lines(pdf, text: str, width: float) -> list[str]:
    try:
        return pdf.multi_cell(width, 5, text, dry_run=True, output="LINES")
    except TypeError:
        try:
            return pdf.multi_cell(width, 5, text, split_only=True)
        except TypeError:
            return [text]


def _write_centered_bold(pdf, text: str, font_name: str, size: int, line_height: int, force_fake_bold: bool) -> None:
    pdf.set_font(font_name, "", size)
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    lines = _split_to_lines(pdf, text, usable_width)
    start_y = pdf.get_y()
    for idx, line in enumerate(lines):
        y = start_y + (idx + 1) * line_height
        line_width = pdf.get_string_width(line)
        x = pdf.l_margin + max((usable_width - line_width) / 2, 0)
        if force_fake_bold:
            pdf.set_font(font_name, "", size)
            pdf.text(x, y, line)
            pdf.text(x + 0.3, y, line)
        else:
            pdf.set_font(font_name, "B", size)
            pdf.text(x, y, line)
    pdf.set_y(start_y + len(lines) * line_height)


def _write_two_column_list(pdf, items: list[str], font_name: str) -> None:
    if not items:
        return
    gutter = 6
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_width = (usable_width - gutter) / 2
    line_height = 5
    safe_items = [safe_text(item) for item in items]
    line_counts = [
        max(1, len(_split_to_lines(pdf, f"- {item}", col_width))) if item else 1
        for item in safe_items
    ]
    left_items, right_items = _distribute_columns(safe_items, line_counts)

    start_y = pdf.get_y()
    left_y = start_y
    for item in left_items:
        lines = _split_to_lines(pdf, f"- {item}", col_width)
        for line in lines:
            pdf.set_xy(pdf.l_margin, left_y)
            pdf.cell(col_width, line_height, line)
            left_y += line_height

    right_y = start_y
    right_x = pdf.l_margin + col_width + gutter
    for item in right_items:
        lines = _split_to_lines(pdf, f"- {item}", col_width)
        for line in lines:
            pdf.set_xy(right_x, right_y)
            pdf.cell(col_width, line_height, line)
            right_y += line_height

    pdf.set_y(max(left_y, right_y))


def render_pdf(data: ResumeData, output_path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError("Missing dependency: fpdf2. Install with: pip install fpdf2") from exc

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    font_name = "Helvetica"
    cjk_font = find_cjk_font()
    if cjk_font:
        pdf.add_font("CJK", "", str(cjk_font))
        pdf.add_font("CJK", "B", str(cjk_font))
        font_name = "CJK"

    if data.name:
        _write_centered_bold(pdf, safe_text(data.name), font_name, 16, 8, force_fake_bold=font_name == "CJK")

    pdf.set_font(font_name, "", 10)
    contact = " | ".join(part for part in [data.phone, data.email] if part)
    if contact:
        try:
            pdf.cell(0, 6, safe_text(contact), ln=1, align="C")
        except TypeError:
            _write_line(pdf, safe_text(contact))

    if data.summary:
        add_heading(pdf, "Professional Summary", font_name)
        _write_line(pdf, safe_text(data.summary))

        if data.skills:
            add_heading(pdf, "Skills & Certifications", font_name)
            _write_two_column_list(pdf, data.skills, font_name)

    if data.experience:
        add_heading(pdf, "Experience", font_name)
        for entry in data.experience:
            title_line = entry.title
            if entry.dates:
                title_line = f"{title_line}, {entry.dates}"
            pdf.set_font(font_name, "B", 10)
            if title_line.strip():
                _write_line(pdf, safe_text(title_line))
            pdf.set_font(font_name, "", 10)
            if entry.company:
                _write_line(pdf, safe_text(entry.company))
            for bullet in polish_bullets(entry.bullets):
                _write_line(pdf, f"- {bullet}")
            pdf.ln(1)

    if data.education:
        add_heading(pdf, "Education", font_name)
        for entry in data.education:
            degree_line = entry.degree
            if entry.dates:
                degree_line = f"{degree_line}, {entry.dates}" if degree_line else entry.dates
            pdf.set_font(font_name, "B", 10)
            if degree_line.strip():
                _write_line(pdf, safe_text(degree_line))
            if entry.school:
                _write_line(pdf, safe_text(entry.school))
            if entry.major:
                _write_line(pdf, f"Major: {safe_text(entry.major)}")
            if entry.coursework:
                _write_line(pdf, f"Relevant Coursework: {safe_text(entry.coursework)}")
            pdf.ln(1)

    if data.certifications:
        add_heading(pdf, "Certifications", font_name)
        for cert in data.certifications:
            _write_line(pdf, f"- {safe_text(cert)}")

    if data.community:
        add_heading(pdf, "Community Service & Volunteer Work", font_name)
        for item in data.community:
            _write_line(pdf, safe_text(item))

    if data.additional:
        add_heading(pdf, "Additional Information", font_name)
        for item in data.additional:
            _write_line(pdf, safe_text(item))

    if data.languages:
        add_heading(pdf, "Languages", font_name)
        for lang in data.languages:
            _write_line(pdf, safe_text(lang))

    pdf.output(str(output_path))


def add_heading(pdf, text: str, font_name: str) -> None:
    pdf.ln(4)
    _write_centered_bold(pdf, text, font_name, 11, 6, force_fake_bold=font_name == "CJK")
    x_left = pdf.l_margin
    x_right = pdf.w - pdf.r_margin
    y = pdf.get_y() + 1
    pdf.line(x_left, y, x_right, y)
    pdf.ln(3)
    pdf.set_font(font_name, "", 10)


def _split_pairs(items: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    idx = 0
    while idx < len(items):
        left = items[idx]
        right = items[idx + 1] if idx + 1 < len(items) else ""
        pairs.append((left, right))
        idx += 2
    return pairs


def _distribute_columns(items: list[str], line_counts: list[int]) -> tuple[list[str], list[str]]:
    left_items: list[str] = []
    right_items: list[str] = []
    left_height = 0
    right_height = 0
    for item, count in zip(items, line_counts):
        if left_height <= right_height:
            left_items.append(item)
            left_height += count
        else:
            right_items.append(item)
            right_height += count
    return left_items, right_items


def _format_skill_lines(skills: list[str]) -> list[str]:
    if not skills:
        return []
    lengths = [len(f"- {skill}") for skill in skills]
    max_len = max(lengths) if lengths else 36
    col_width = min(max(34, max_len + 4), 60)
    line_counts = [
        max(1, (len(f"- {skill}") + col_width - 1) // col_width) for skill in skills
    ]
    left_items, right_items = _distribute_columns(skills, line_counts)
    pairs = list(zip(left_items, right_items + [""] * (len(left_items) - len(right_items))))
    left_lengths = [len(f"- {left}") for left, _ in pairs if left]
    max_left = max(left_lengths) if left_lengths else 36
    col_width = min(max(34, max_left + 4), 60)
    lines: list[str] = []
    for left, right in pairs:
        left_text = f"- {left}"
        right_text = f"- {right}" if right else ""
        lines.append(left_text.ljust(col_width) + right_text)
    return lines


class ResumeGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Resume Formatter")
        self.root.geometry("1200x760")
        self.root.configure(bg="#f5f6f8")

        self.experience_entries: list[ExperienceEntry] = []
        self.education_entries: list[EducationEntry] = []

        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.output_var = tk.StringVar(value="formatted_resume.pdf")
        self.imported_text = ""
        self.last_export_path: Path | None = None
        self.polish_button: ttk.Button | None = None
        self.summary_agent_button: ttk.Button | None = None

        self._setup_style()
        self._build_layout()
        self._bind_live_updates()

    def _setup_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f5f6f8")
        style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"), background="#f5f6f8")
        style.configure("Section.TLabelframe", background="#f5f6f8", padding=10)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"), background="#f5f6f8")
        style.configure("TButton", padding=6)

    def _build_layout(self) -> None:
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=3)
        paned.add(right, weight=2)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, container: ttk.Frame) -> None:
        canvas = tk.Canvas(container, bg="#f5f6f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._bind_mousewheel(canvas)

        self._section_header(scroll_frame)
        self._section_summary(scroll_frame)
        self._section_skills(scroll_frame)
        self._section_experience(scroll_frame)
        self._section_education(scroll_frame)
        self._section_certifications(scroll_frame)
        self._section_community(scroll_frame)
        self._section_additional(scroll_frame)
        self._section_languages(scroll_frame)

    def _build_right_panel(self, container: ttk.Frame) -> None:
        toolbar = ttk.Frame(container)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(toolbar, text="Import", command=self._import_file).pack(side=tk.LEFT)
        self.polish_button = ttk.Button(
            toolbar,
            text="\u542f\u52a8\u6da6\u8272",
            command=self._start_polish,
        )
        self.polish_button.pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="Export PDF", command=self._generate_pdf).pack(side=tk.LEFT, padx=6)
        self.summary_agent_button = ttk.Button(
            toolbar,
            text="Open Summary Agent",
            command=self._open_summary_agent,
            state=tk.DISABLED,
        )
        self.summary_agent_button.pack(side=tk.LEFT, padx=6)

        ttk.Label(toolbar, text="Output PDF", style="Header.TLabel").pack(side=tk.LEFT, padx=(20, 6))
        ttk.Entry(toolbar, textvariable=self.output_var, width=35).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Browse", command=self._browse_output).pack(side=tk.LEFT, padx=6)

        ttk.Label(container, text="Live Preview", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
        self.preview_text = tk.Text(container, wrap=tk.WORD, height=40, bg="#ffffff")
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.tag_configure("heading", justify="center", font=("Segoe UI", 10, "bold"))
        self.preview_text.tag_configure("name", justify="center", font=("Segoe UI", 12, "bold"))
        self.preview_text.tag_configure("center", justify="center", font=("Segoe UI", 10))
        self.preview_text.configure(state=tk.DISABLED)

    def _section_header(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Header", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)

        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.name_var, width=40).grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(frame, text="Phone").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.phone_var, width=40).grid(row=1, column=1, padx=6, pady=4)

        ttk.Label(frame, text="Email").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.email_var, width=40).grid(row=2, column=1, padx=6, pady=4)

    def _section_summary(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Professional Summary", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)

        self.summary_text = tk.Text(frame, height=6)
        self.summary_text.pack(fill=tk.X, padx=6, pady=4)

    def _section_skills(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Skills", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(form, text="Category").grid(row=0, column=0, sticky="w", padx=6, pady=2)
        self.skill_category_entry = ttk.Entry(form, width=30)
        self.skill_category_entry.grid(row=0, column=1, padx=6, pady=2, sticky="w")

        ttk.Label(form, text="Items (one per line or ; separated)").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.skill_items_text = tk.Text(form, height=4, width=60)
        self.skill_items_text.grid(row=1, column=1, padx=6, pady=2, sticky="we")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btn_frame, text="Add", command=self._add_skill_group).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Update", command=self._update_skill_group).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Remove", command=self._remove_skill_group).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Up", command=lambda: self._move_skill_group(-1)).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Down", command=lambda: self._move_skill_group(1)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Clear Input", command=self._clear_skill_fields).pack(side=tk.LEFT, padx=6)

        ttk.Label(frame, text="Saved skill groups").pack(anchor="w", padx=6, pady=2)
        self.skill_list = tk.Listbox(frame, height=6)
        self.skill_list.pack(fill=tk.X, padx=6, pady=4)
        self.skill_list.bind("<<ListboxSelect>>", self._load_skill_selection)

    def _section_experience(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Experience", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(form, text="Title").grid(row=0, column=0, sticky="w", padx=6, pady=2)
        self.exp_title_entry = ttk.Entry(form, width=35)
        self.exp_title_entry.grid(row=0, column=1, padx=6, pady=2)

        ttk.Label(form, text="Dates").grid(row=0, column=2, sticky="w", padx=6, pady=2)
        self.exp_dates_entry = ttk.Entry(form, width=25)
        self.exp_dates_entry.grid(row=0, column=3, padx=6, pady=2)

        ttk.Label(form, text="Company").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.exp_company_entry = ttk.Entry(form, width=35)
        self.exp_company_entry.grid(row=1, column=1, padx=6, pady=2)

        ttk.Label(form, text="Bullets (one per line)").grid(row=2, column=0, sticky="w", padx=6, pady=2)
        self.exp_bullets_text = tk.Text(form, height=5, width=60)
        self.exp_bullets_text.grid(row=2, column=1, columnspan=3, padx=6, pady=2, sticky="we")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btn_frame, text="Add", command=self._add_experience).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Update", command=self._update_experience).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Remove", command=self._remove_experience).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Up", command=lambda: self._move_experience(-1)).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Down", command=lambda: self._move_experience(1)).pack(side=tk.LEFT)

        self.exp_listbox = tk.Listbox(frame, height=6)
        self.exp_listbox.pack(fill=tk.X, padx=6, pady=4)
        self.exp_listbox.bind("<<ListboxSelect>>", self._load_experience_selection)

    def _section_education(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Education", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(form, text="Degree").grid(row=0, column=0, sticky="w", padx=6, pady=2)
        self.edu_degree_entry = ttk.Entry(form, width=35)
        self.edu_degree_entry.grid(row=0, column=1, padx=6, pady=2)

        ttk.Label(form, text="Dates").grid(row=0, column=2, sticky="w", padx=6, pady=2)
        self.edu_dates_entry = ttk.Entry(form, width=25)
        self.edu_dates_entry.grid(row=0, column=3, padx=6, pady=2)

        ttk.Label(form, text="School").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.edu_school_entry = ttk.Entry(form, width=35)
        self.edu_school_entry.grid(row=1, column=1, padx=6, pady=2)

        ttk.Label(form, text="Major").grid(row=1, column=2, sticky="w", padx=6, pady=2)
        self.edu_major_entry = ttk.Entry(form, width=25)
        self.edu_major_entry.grid(row=1, column=3, padx=6, pady=2)

        ttk.Label(form, text="Relevant Coursework").grid(row=2, column=0, sticky="w", padx=6, pady=2)
        self.edu_coursework_entry = ttk.Entry(form, width=60)
        self.edu_coursework_entry.grid(row=2, column=1, columnspan=3, padx=6, pady=2, sticky="we")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btn_frame, text="Add", command=self._add_education).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Update", command=self._update_education).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Remove", command=self._remove_education).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Up", command=lambda: self._move_education(-1)).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Down", command=lambda: self._move_education(1)).pack(side=tk.LEFT)

        self.edu_listbox = tk.Listbox(frame, height=6)
        self.edu_listbox.pack(fill=tk.X, padx=6, pady=4)
        self.edu_listbox.bind("<<ListboxSelect>>", self._load_education_selection)

    def _section_certifications(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Certifications", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)
        self._build_simple_list(frame, "Certification", "cert")

    def _section_community(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Community Service", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)
        self._build_simple_list(frame, "Community Item", "community")

    def _section_additional(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Additional Information", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)
        self._build_simple_list(frame, "Additional Item", "additional")

    def _section_languages(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Languages", style="Section.TLabelframe")
        frame.pack(fill=tk.X, pady=6)
        self._build_simple_list(frame, "Language", "language")

    def _build_simple_list(self, frame: ttk.LabelFrame, label: str, name: str) -> None:
        entry = ttk.Entry(frame, width=50)
        entry.pack(fill=tk.X, padx=6, pady=4)
        listbox = tk.Listbox(frame, height=5)
        listbox.pack(fill=tk.X, padx=6, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btn_frame, text="Add", command=lambda: self._add_list_item(entry, listbox)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Remove", command=lambda: self._remove_list_item(listbox)).pack(side=tk.LEFT, padx=6)

        setattr(self, f"{name}_entry", entry)
        setattr(self, f"{name}_list", listbox)

    def _bind_mousewheel(self, widget: tk.Widget) -> None:
        def _on_mousewheel(event):
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

        widget.bind_all("<MouseWheel>", _on_mousewheel)

    def _bind_live_updates(self) -> None:
        for var in (self.name_var, self.phone_var, self.email_var):
            var.trace_add("write", lambda *args: self._update_preview())
        self.summary_text.bind("<KeyRelease>", lambda event: self._update_preview())
        self.skill_items_text.bind("<KeyRelease>", lambda event: self._update_preview())
        self.skill_category_entry.bind("<KeyRelease>", lambda event: self._update_preview())

    def _add_list_item(self, entry: tk.Entry, listbox: tk.Listbox) -> None:
        text = normalize_text(entry.get())
        if not text:
            return
        listbox.insert(tk.END, text)
        entry.delete(0, tk.END)
        self._update_preview()

    def _remove_list_item(self, listbox: tk.Listbox) -> None:
        for idx in reversed(listbox.curselection()):
            listbox.delete(idx)
        self._update_preview()

    def _collect_skill_items_input(self) -> list[str]:
        raw = self.skill_items_text.get("1.0", tk.END)
        items: list[str] = []
        for line in raw.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            if ";" in cleaned:
                items.extend([normalize_text(part) for part in cleaned.split(";") if part.strip()])
            else:
                items.append(normalize_text(cleaned))
        return items

    def _build_skill_line(self, category: str, items: list[str]) -> str:
        items_text = "; ".join(items)
        if category:
            return f"{category}: {items_text}".strip() if items_text else f"{category}:"
        return items_text

    def _parse_skill_line(self, line: str) -> tuple[str, list[str]]:
        if ":" in line:
            category, rest = [part.strip() for part in line.split(":", 1)]
            items = [normalize_text(part) for part in rest.split(";") if part.strip()]
            return category, items
        return "", [normalize_text(part) for part in line.split(";") if part.strip()]

    def _clear_skill_fields(self) -> None:
        self.skill_category_entry.delete(0, tk.END)
        self.skill_items_text.delete("1.0", tk.END)

    def _add_skill_group(self) -> None:
        category = normalize_text(self.skill_category_entry.get())
        items = self._collect_skill_items_input()
        line = self._build_skill_line(category, items)
        if not line:
            return
        self.skill_list.insert(tk.END, line)
        self._clear_skill_fields()
        self._update_preview()

    def _update_skill_group(self) -> None:
        selection = self.skill_list.curselection()
        if not selection:
            return
        idx = selection[0]
        category = normalize_text(self.skill_category_entry.get())
        items = self._collect_skill_items_input()
        line = self._build_skill_line(category, items)
        if not line:
            return
        self.skill_list.delete(idx)
        self.skill_list.insert(idx, line)
        self._update_preview()

    def _remove_skill_group(self) -> None:
        for idx in reversed(self.skill_list.curselection()):
            self.skill_list.delete(idx)
        self._update_preview()

    def _move_skill_group(self, direction: int) -> None:
        selection = self.skill_list.curselection()
        if not selection:
            return
        idx = selection[0]
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= self.skill_list.size():
            return
        item = self.skill_list.get(idx)
        self.skill_list.delete(idx)
        self.skill_list.insert(new_idx, item)
        self.skill_list.selection_set(new_idx)
        self._update_preview()

    def _load_skill_selection(self, event=None) -> None:
        selection = self.skill_list.curselection()
        if not selection:
            return
        line = self.skill_list.get(selection[0])
        category, items = self._parse_skill_line(line)
        self.skill_category_entry.delete(0, tk.END)
        self.skill_category_entry.insert(0, category)
        self.skill_items_text.delete("1.0", tk.END)
        if items:
            self.skill_items_text.insert(tk.END, "\n".join(items))

    def _commit_skill_input(self) -> None:
        category = normalize_text(self.skill_category_entry.get())
        items = self._collect_skill_items_input()
        if not category and not items:
            return
        line = self._build_skill_line(category, items)
        if not line:
            return
        selection = self.skill_list.curselection()
        if selection:
            idx = selection[0]
            self.skill_list.delete(idx)
            self.skill_list.insert(idx, line)
        else:
            self.skill_list.insert(tk.END, line)
        self._clear_skill_fields()

    def _add_experience(self) -> None:
        title = normalize_text(self.exp_title_entry.get())
        dates = normalize_text(self.exp_dates_entry.get())
        company = normalize_text(self.exp_company_entry.get())
        bullets = [normalize_text(line) for line in self.exp_bullets_text.get("1.0", tk.END).splitlines() if line.strip()]

        if not any([title, dates, company, bullets]):
            return

        entry = ExperienceEntry(title=title, dates=dates, company=company, bullets=bullets)
        self.experience_entries.append(entry)
        self.exp_listbox.insert(tk.END, f"{title} | {company}")
        self._clear_experience_fields()
        self._update_preview()

    def _update_experience(self) -> None:
        selection = self.exp_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self.experience_entries[idx] = ExperienceEntry(
            title=normalize_text(self.exp_title_entry.get()),
            dates=normalize_text(self.exp_dates_entry.get()),
            company=normalize_text(self.exp_company_entry.get()),
            bullets=[normalize_text(line) for line in self.exp_bullets_text.get("1.0", tk.END).splitlines() if line.strip()],
        )
        self._refresh_experience_listbox()
        self._update_preview()

    def _remove_experience(self) -> None:
        for idx in reversed(self.exp_listbox.curselection()):
            self.exp_listbox.delete(idx)
            del self.experience_entries[idx]
        self._update_preview()

    def _move_experience(self, direction: int) -> None:
        selection = self.exp_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.experience_entries):
            return
        self.experience_entries[idx], self.experience_entries[new_idx] = (
            self.experience_entries[new_idx],
            self.experience_entries[idx],
        )
        self._refresh_experience_listbox()
        self.exp_listbox.selection_set(new_idx)
        self._update_preview()

    def _refresh_experience_listbox(self) -> None:
        self.exp_listbox.delete(0, tk.END)
        for entry in self.experience_entries:
            self.exp_listbox.insert(tk.END, f"{entry.title} | {entry.company}")

    def _load_experience_selection(self, event=None) -> None:
        selection = self.exp_listbox.curselection()
        if not selection:
            return
        entry = self.experience_entries[selection[0]]
        self.exp_title_entry.delete(0, tk.END)
        self.exp_title_entry.insert(0, entry.title)
        self.exp_dates_entry.delete(0, tk.END)
        self.exp_dates_entry.insert(0, entry.dates)
        self.exp_company_entry.delete(0, tk.END)
        self.exp_company_entry.insert(0, entry.company)
        self.exp_bullets_text.delete("1.0", tk.END)
        if entry.bullets:
            self.exp_bullets_text.insert(tk.END, "\n".join(entry.bullets))

    def _clear_experience_fields(self) -> None:
        self.exp_title_entry.delete(0, tk.END)
        self.exp_dates_entry.delete(0, tk.END)
        self.exp_company_entry.delete(0, tk.END)
        self.exp_bullets_text.delete("1.0", tk.END)

    def _add_education(self) -> None:
        degree = normalize_text(self.edu_degree_entry.get())
        dates = normalize_text(self.edu_dates_entry.get())
        school = normalize_text(self.edu_school_entry.get())
        major = normalize_text(self.edu_major_entry.get())
        coursework = normalize_text(self.edu_coursework_entry.get())

        if not any([degree, dates, school, major, coursework]):
            return

        entry = EducationEntry(degree=degree, dates=dates, school=school, major=major, coursework=coursework)
        self.education_entries.append(entry)
        self.edu_listbox.insert(tk.END, f"{degree} | {school}")
        self._clear_education_fields()
        self._update_preview()

    def _update_education(self) -> None:
        selection = self.edu_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self.education_entries[idx] = EducationEntry(
            degree=normalize_text(self.edu_degree_entry.get()),
            dates=normalize_text(self.edu_dates_entry.get()),
            school=normalize_text(self.edu_school_entry.get()),
            major=normalize_text(self.edu_major_entry.get()),
            coursework=normalize_text(self.edu_coursework_entry.get()),
        )
        self._refresh_education_listbox()
        self._update_preview()

    def _remove_education(self) -> None:
        for idx in reversed(self.edu_listbox.curselection()):
            self.edu_listbox.delete(idx)
            del self.education_entries[idx]
        self._update_preview()

    def _move_education(self, direction: int) -> None:
        selection = self.edu_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.education_entries):
            return
        self.education_entries[idx], self.education_entries[new_idx] = (
            self.education_entries[new_idx],
            self.education_entries[idx],
        )
        self._refresh_education_listbox()
        self.edu_listbox.selection_set(new_idx)
        self._update_preview()

    def _refresh_education_listbox(self) -> None:
        self.edu_listbox.delete(0, tk.END)
        for entry in self.education_entries:
            self.edu_listbox.insert(tk.END, f"{entry.degree} | {entry.school}")

    def _load_education_selection(self, event=None) -> None:
        selection = self.edu_listbox.curselection()
        if not selection:
            return
        entry = self.education_entries[selection[0]]
        self.edu_degree_entry.delete(0, tk.END)
        self.edu_degree_entry.insert(0, entry.degree)
        self.edu_dates_entry.delete(0, tk.END)
        self.edu_dates_entry.insert(0, entry.dates)
        self.edu_school_entry.delete(0, tk.END)
        self.edu_school_entry.insert(0, entry.school)
        self.edu_major_entry.delete(0, tk.END)
        self.edu_major_entry.insert(0, entry.major)
        self.edu_coursework_entry.delete(0, tk.END)
        self.edu_coursework_entry.insert(0, entry.coursework)

    def _clear_education_fields(self) -> None:
        self.edu_degree_entry.delete(0, tk.END)
        self.edu_dates_entry.delete(0, tk.END)
        self.edu_school_entry.delete(0, tk.END)
        self.edu_major_entry.delete(0, tk.END)
        self.edu_coursework_entry.delete(0, tk.END)

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self.output_var.set(path)

    def _import_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Resume files", "*.docx *.pdf *.txt"), ("All files", "*")]
        )
        if not path:
            return
        try:
            text = extract_text_from_file(Path(path))
            data = parse_resume_text(text)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))
            return

        self.imported_text = text
        self._load_data(data)
        messagebox.showinfo("Import complete", "Content imported. Please review and edit before export.")

    def _start_polish(self) -> None:
        if self.polish_button:
            self.polish_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_polish, daemon=True).start()

    def _run_polish(self) -> None:
        try:
            raw_text = self.imported_text.strip()
            if not raw_text:
                raw_text = self._build_raw_text_from_gui()
            payload = self._build_polish_payload(raw_text)
            result = self._call_polish_agent(payload)
            self.root.after(0, lambda: self._apply_polish_result(result))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Polish failed", str(exc)))
        finally:
            if self.polish_button:
                self.root.after(0, lambda: self.polish_button.configure(state=tk.NORMAL))

    def _build_raw_text_from_gui(self) -> str:
        data = self._gather_data()
        parts: list[str] = []
        if data.name:
            parts.append(data.name)
        if data.email:
            parts.append(data.email)
        if data.summary:
            parts.append("Summary")
            parts.append(data.summary)
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

    def _build_polish_payload(self, raw_text: str) -> dict:
        data = self._gather_data()
        current_experience = [
            {
                "title": entry.title,
                "company": entry.company,
                "dates": entry.dates,
                "bullets": entry.bullets,
            }
            for entry in data.experience
        ]
        return {
            "raw_text": raw_text,
            "current_summary": data.summary,
            "current_skills": data.skills,
            "current_experience": current_experience,
        }

    def _call_polish_agent(self, payload: dict) -> dict:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        model = os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_MODEL_NAME") or "gpt-4o-mini"
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY in environment.")

        system_prompt = (
            "You are a resume polishing assistant. Rewrite only the summary, skills, and experience "
            "based strictly on the provided resume content. Do not invent facts.\n\n"
            "Summary rules:\n"
            "- English, 60-90 words.\n"
            "- Objective third-person voice only; avoid first-person pronouns (I, me, my).\n"
            "- Structure: who you are -> core technical direction -> problems you solve/value -> suitable roles.\n\n"
            "Skills rules:\n"
            "- Group skills into clear categories with descriptive category titles inferred from the skills.\n"
            "- Do NOT use fixed category names.\n"
            "- Keep all skills factual; no additions.\n\n"
            "Experience rules:\n"
            "- Rewrite all experience bullets using STAR style with concrete actions and technologies.\n"
            "- Avoid repetitive verbs like Assisted/Supported; lead with strong action verbs.\n"
            "- A short lead-in label (2-4 words) followed by a colon is acceptable when helpful.\n"
            "- You may add brief clarifying detail only if it is supported by the resume text.\n"
            "- Do not invent metrics, tools, or achievements.\n\n"
            "Output JSON only with this schema:\n"
            "{"
            "\"summary\": \"...\","
            "\"skills\": [{\"category\": \"...\", \"items\": [\"...\", \"...\"]}],"
            "\"experience\": [{\"title\": \"...\", \"company\": \"...\", \"dates\": \"...\", \"bullets\": [\"...\", \"...\"]}]"
            "}"
        )

        user_prompt = (
            "Resume raw text:\n"
            f"{payload['raw_text']}\n\n"
            "Current parsed summary:\n"
            f"{payload.get('current_summary', '')}\n\n"
            "Current parsed skills:\n"
            f"{payload.get('current_skills', '')}\n\n"
            "Current parsed experience:\n"
            f"{payload.get('current_experience', '')}"
        )

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 900,
        }
        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
        if not response.ok:
            raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")
        content = response.json()["choices"][0]["message"]["content"]
        return self._extract_json(content)

    def _extract_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```json\\s*(\\{.*?\\})\\s*```", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        match = re.search(r"(\\{.*\\})", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError("LLM response did not contain valid JSON.")

    def _apply_polish_result(self, result: dict) -> None:
        summary = (result.get("summary") or "").strip()
        if summary:
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert(tk.END, summary)

        skills = result.get("skills") or []
        if isinstance(skills, list):
            formatted_skills = []
            for entry in skills:
                category = (entry.get("category") or "").strip()
                items = [item.strip() for item in entry.get("items") or [] if item.strip()]
                if category and items:
                    formatted_skills.append(f"{category}: " + "; ".join(items))
                elif items:
                    formatted_skills.append("; ".join(items))
            if formatted_skills:
                self._set_listbox_items(self.skill_list, formatted_skills)
                self._clear_skill_fields()

        experience = result.get("experience") or []
        if isinstance(experience, list):
            new_entries = []
            for entry in experience:
                title = (entry.get("title") or "").strip()
                company = (entry.get("company") or "").strip()
                dates = (entry.get("dates") or "").strip()
                bullets = [b.strip() for b in entry.get("bullets") or [] if b.strip()]
                if title or company or dates or bullets:
                    new_entries.append(
                        ExperienceEntry(
                            title=title,
                            dates=dates,
                            company=company,
                            bullets=bullets,
                        )
                    )
            if new_entries:
                self.experience_entries = new_entries
                self._refresh_experience_listbox()

        self._update_preview()
        if self.summary_agent_button:
            self.summary_agent_button.configure(state=tk.NORMAL)

    def _load_data(self, data: ResumeData) -> None:
        if data.name:
            self.name_var.set(data.name)
        if data.phone:
            self.phone_var.set(data.phone)
        if data.email:
            self.email_var.set(data.email)
        if data.summary:
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert(tk.END, data.summary)

        self._set_listbox_items(self.skill_list, data.skills)
        self._clear_skill_fields()
        self._set_listbox_items(self.cert_list, data.certifications)
        self._set_listbox_items(self.community_list, data.community)
        self._set_listbox_items(self.additional_list, data.additional)
        self._set_listbox_items(self.language_list, data.languages)

        self.experience_entries = data.experience
        self._refresh_experience_listbox()

        self.education_entries = data.education
        self._refresh_education_listbox()

        self._update_preview()
        if self.summary_agent_button:
            self.summary_agent_button.configure(state=tk.DISABLED)

    def _set_listbox_items(self, listbox: tk.Listbox, items: Iterable[str]) -> None:
        listbox.delete(0, tk.END)
        for item in items:
            listbox.insert(tk.END, item)

    def _get_listbox_items(self, listbox: tk.Listbox) -> list[str]:
        return [listbox.get(i) for i in range(listbox.size())]

    def _collect_skills_for_preview(self) -> list[str]:
        return self._get_listbox_items(self.skill_list)

    def _gather_data(self) -> ResumeData:
        summary = normalize_text(self.summary_text.get("1.0", tk.END))
        skills = self._get_listbox_items(self.skill_list)
        certifications = self._get_listbox_items(self.cert_list)
        community = self._get_listbox_items(self.community_list)
        additional = self._get_listbox_items(self.additional_list)
        languages = self._get_listbox_items(self.language_list)

        return ResumeData(
            name=normalize_text(self.name_var.get()),
            phone=normalize_text(self.phone_var.get()),
            email=normalize_text(self.email_var.get()),
            summary=summary,
            skills=skills,
            experience=self.experience_entries,
            education=self.education_entries,
            certifications=certifications,
            community=community,
            additional=additional,
            languages=languages,
        )

    def _format_skills_preview(self, skills: list[str]) -> list[str]:
        if not skills:
            return []
        return _format_skill_lines(skills)

    def _update_preview(self) -> None:
        data = self._gather_data()
        skills_preview = self._collect_skills_for_preview()

        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)

        def write_line(text: str, tag: str | None = None) -> None:
            if tag:
                self.preview_text.insert(tk.END, text + "\n", tag)
            else:
                self.preview_text.insert(tk.END, text + "\n")

        def add_section(title: str, body: list[str]) -> None:
            if not body:
                return
            if self.preview_text.index("end-1c") != "1.0":
                write_line("")
            write_line(title, "heading")
            for line in body:
                write_line(line)

        if data.name:
            write_line(data.name, "name")
        contact = " | ".join(part for part in [data.phone, data.email] if part)
        if contact:
            write_line(contact, "center")

        if data.summary:
            add_section("Professional Summary", [data.summary])

        if skills_preview:
            add_section("Skills & Certifications", self._format_skills_preview(skills_preview))

        if data.experience:
            exp_lines: list[str] = []
            for entry in data.experience:
                title_line = entry.title
                if entry.dates:
                    title_line = f"{title_line}, {entry.dates}"
                if title_line.strip():
                    exp_lines.append(title_line)
                if entry.company:
                    exp_lines.append(entry.company)
                for bullet in entry.bullets:
                    exp_lines.append(f"- {bullet}")
                exp_lines.append("")
            add_section("Experience", exp_lines[:-1] if exp_lines and exp_lines[-1] == "" else exp_lines)

        if data.education:
            edu_lines: list[str] = []
            for entry in data.education:
                degree_line = entry.degree
                if entry.dates:
                    degree_line = f"{degree_line}, {entry.dates}" if degree_line else entry.dates
                if degree_line.strip():
                    edu_lines.append(degree_line)
                if entry.school:
                    edu_lines.append(entry.school)
                if entry.major:
                    edu_lines.append(f"Major: {entry.major}")
                if entry.coursework:
                    edu_lines.append(f"Relevant Coursework: {entry.coursework}")
                edu_lines.append("")
            add_section("Education", edu_lines[:-1] if edu_lines and edu_lines[-1] == "" else edu_lines)

        if data.certifications:
            add_section("Certifications", [f"- {cert}" for cert in data.certifications])

        if data.community:
            add_section("Community Service & Volunteer Work", data.community)

        if data.additional:
            add_section("Additional Information", data.additional)

        if data.languages:
            add_section("Languages", data.languages)

        self.preview_text.configure(state=tk.DISABLED)

    def _generate_pdf(self) -> None:
        self._commit_skill_input()
        data = self._gather_data()
        output_path = Path(self.output_var.get() or "formatted_resume.pdf")
        try:
            render_pdf(data, output_path)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return

        self.last_export_path = output_path.resolve()
        messagebox.showinfo("Done", f"Saved to: {output_path}")

    def _open_summary_agent(self) -> None:
        template_path = self.last_export_path
        if template_path is None or not template_path.is_file():
            proceed = messagebox.askyesno(
                "Export resume",
                "Resume not exported yet. Export now?",
            )
            if not proceed:
                return
            self._generate_pdf()
            template_path = self.last_export_path
            if template_path is None or not template_path.is_file():
                messagebox.showerror("Missing file", "Resume export failed or file not found.")
                return

        script_path = Path(__file__).resolve().parent / "resume_summary_agent_gui.py"
        if not script_path.exists():
            messagebox.showerror("Missing script", f"Summary agent not found: {script_path}")
            return

        try:
            subprocess.Popen(
                [sys.executable, str(script_path), "--template", str(template_path)]
            )
        except Exception as exc:
            messagebox.showerror("Launch failed", str(exc))


def main() -> None:
    if tk is None:
        raise RuntimeError("tkinter is not available in this environment.")
    root = tk.Tk()
    ResumeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
