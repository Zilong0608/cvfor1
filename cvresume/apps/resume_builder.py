import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from fpdf import FPDF
except ImportError:  # pragma: no cover
    print("Missing dependency: fpdf2. Install with: pip install fpdf2")
    raise SystemExit(1)


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
    languages: list[str]


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def read_nonempty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field is required.")


def read_optional(prompt: str) -> str:
    return input(prompt).strip()


def read_list(prompt: str) -> list[str]:
    print(prompt)
    print("Enter one item per line. Blank line to finish.")
    items: list[str] = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        items.append(normalize_text(line))
    return items


def read_bullets(prompt: str) -> list[str]:
    return read_list(prompt)


def read_experience() -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    while True:
        choice = input("Add experience entry? (y/n): ").strip().lower()
        if choice != "y":
            break
        title = read_nonempty("Title: ")
        dates = read_optional("Dates (e.g., 04/2025 - 07/2025): ")
        company = read_nonempty("Company: ")
        bullets = read_bullets("Bullets for this role")
        entries.append(
            ExperienceEntry(
                title=normalize_text(title),
                dates=normalize_text(dates),
                company=normalize_text(company),
                bullets=bullets,
            )
        )
    return entries


def read_education() -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    while True:
        choice = input("Add education entry? (y/n): ").strip().lower()
        if choice != "y":
            break
        degree = read_nonempty("Degree (e.g., Master of ...): ")
        dates = read_optional("Dates (e.g., 12/2025): ")
        school = read_nonempty("School: ")
        coursework = read_optional("Relevant coursework (optional): ")
        entries.append(
            EducationEntry(
                degree=normalize_text(degree),
                dates=normalize_text(dates),
                school=normalize_text(school),
                coursework=normalize_text(coursework),
            )
        )
    return entries


def read_resume_interactive() -> ResumeData:
    print("Resume builder - interactive mode")
    name = read_nonempty("Name: ")
    phone = read_nonempty("Phone: ")
    email = read_nonempty("Email: ")
    summary = read_nonempty("Professional summary: ")
    skills = read_list("Skills")
    experience = read_experience()
    education = read_education()
    certifications = read_list("Certifications")
    community = read_list("Community service / volunteer")
    languages = read_list("Languages")

    return ResumeData(
        name=normalize_text(name),
        phone=normalize_text(phone),
        email=normalize_text(email),
        summary=normalize_text(summary),
        skills=skills,
        experience=experience,
        education=education,
        certifications=certifications,
        community=community,
        languages=languages,
    )


def extract_docx_text(path: Path) -> str:
    import zipfile
    import xml.etree.ElementTree as ET

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        xml_data = zf.read("word/document.xml")
    tree = ET.fromstring(xml_data)
    parts: list[str] = []
    for p in tree.findall(".//w:p", ns):
        p_text = "".join(t.text for t in p.findall(".//w:t", ns) if t.text)
        if p_text.strip():
            parts.append(p_text.strip())
    return "\n".join(parts)


def extract_pdf_text(path: Path) -> str:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            print("Missing dependency for PDF parsing. Install: pip install pdfplumber or PyPDF2")
            raise SystemExit(1)
        reader = PdfReader(str(path))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(text_parts)

    with pdfplumber.open(str(path)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)


def extract_text_from_file(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".docx":
        return extract_docx_text(path)
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    raise ValueError("Unsupported file type. Use docx, pdf, or txt.")


def split_sections(text: str) -> dict[str, list[str]]:
    headings = {
        "summary": ["summary", "professional summary"],
        "skills": ["skills", "skills & certifications", "skills and certifications"],
        "experience": ["experience", "work experience"],
        "education": ["education"],
        "certifications": ["certifications"],
        "community": ["community service", "volunteer", "community service & volunteer work"],
        "languages": ["languages"],
    }

    current = "summary"
    sections: dict[str, list[str]] = {key: [] for key in headings}

    for line in text.splitlines():
        clean = normalize_text(line)
        if not clean:
            continue
        lowered = clean.lower()
        matched = None
        for key, names in headings.items():
            if any(lowered == name for name in names):
                matched = key
                break
        if matched:
            current = matched
            continue
        sections[current].append(clean)

    return sections


def parse_skills(lines: Iterable[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        if "," in line:
            items.extend([normalize_text(part) for part in line.split(",") if part.strip()])
        else:
            items.append(line)
    return items


def parse_bullets(lines: Iterable[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        item = re.sub(r"^[\-\*\u2022\s]+", "", line).strip()
        if item:
            bullets.append(item)
    return bullets


def parse_experience(lines: Iterable[str]) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    current: list[str] = []
    for line in lines:
        if line == "":
            if current:
                entries.append(_parse_experience_block(current))
                current = []
            continue
        current.append(line)
    if current:
        entries.append(_parse_experience_block(current))
    return [entry for entry in entries if entry.title or entry.company]


def _parse_experience_block(lines: list[str]) -> ExperienceEntry:
    title = lines[0] if lines else ""
    company = lines[1] if len(lines) > 1 else ""
    bullets = parse_bullets(lines[2:]) if len(lines) > 2 else []
    title, dates = split_title_dates(title)
    return ExperienceEntry(title=title, dates=dates, company=company, bullets=bullets)


def parse_education(lines: Iterable[str]) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    current: list[str] = []
    for line in lines:
        if line == "":
            if current:
                entries.append(_parse_education_block(current))
                current = []
            continue
        current.append(line)
    if current:
        entries.append(_parse_education_block(current))
    return [entry for entry in entries if entry.degree or entry.school]


def _parse_education_block(lines: list[str]) -> EducationEntry:
    degree = lines[0] if lines else ""
    school = lines[1] if len(lines) > 1 else ""
    coursework = ""
    if len(lines) > 2:
        coursework = lines[2]
        coursework = coursework.replace("Relevant Coursework:", "").strip()
    degree, dates = split_title_dates(degree)
    return EducationEntry(degree=degree, dates=dates, school=school, coursework=coursework)


def split_title_dates(line: str) -> tuple[str, str]:
    if "," in line:
        title, dates = line.split(",", 1)
        return normalize_text(title), normalize_text(dates)
    return normalize_text(line), ""


def parse_resume_text(text: str) -> ResumeData:
    sections = split_sections(text)
    summary = " ".join(sections.get("summary", []))
    skills = parse_skills(sections.get("skills", []))
    experience = parse_experience(sections.get("experience", []))
    education = parse_education(sections.get("education", []))
    certifications = parse_bullets(sections.get("certifications", []))
    community = sections.get("community", [])
    languages = parse_bullets(sections.get("languages", []))

    return ResumeData(
        name="",
        phone="",
        email="",
        summary=normalize_text(summary),
        skills=skills,
        experience=experience,
        education=education,
        certifications=certifications,
        community=community,
        languages=languages,
    )


def polish_bullets(bullets: list[str]) -> list[str]:
    polished: list[str] = []
    for bullet in bullets:
        text = normalize_text(bullet)
        if text and text[-1] not in ".!?":
            text = f"{text}."
        polished.append(text)
    return polished


def render_pdf(data: ResumeData, output_path: Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, data.name, ln=1)

    pdf.set_font("Helvetica", "", 10)
    contact = " | ".join(part for part in [data.phone, data.email] if part)
    pdf.cell(0, 6, contact, ln=1)

    add_heading(pdf, "Professional Summary")
    pdf.multi_cell(0, 5, data.summary)

    add_heading(pdf, "Skills & Certifications")
    for skill in data.skills:
        pdf.multi_cell(0, 5, f"- {skill}")

    add_heading(pdf, "Experience")
    for entry in data.experience:
        title_line = entry.title
        if entry.dates:
            title_line = f"{title_line}, {entry.dates}"
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, title_line)
        pdf.set_font("Helvetica", "", 10)
        if entry.company:
            pdf.multi_cell(0, 5, entry.company)
        for bullet in polish_bullets(entry.bullets):
            pdf.multi_cell(0, 5, f"- {bullet}")
        pdf.ln(1)

    add_heading(pdf, "Education")
    for entry in data.education:
        degree_line = entry.degree
        if entry.dates:
            degree_line = f"{degree_line}, {entry.dates}"
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, degree_line)
        pdf.set_font("Helvetica", "", 10)
        if entry.school:
            pdf.multi_cell(0, 5, entry.school)
        if entry.coursework:
            pdf.multi_cell(0, 5, f"Relevant Coursework: {entry.coursework}")
        pdf.ln(1)

    add_heading(pdf, "Certifications")
    for cert in data.certifications:
        pdf.multi_cell(0, 5, f"- {cert}")

    add_heading(pdf, "Community Service & Volunteer Work")
    for item in data.community:
        pdf.multi_cell(0, 5, item)

    add_heading(pdf, "Languages")
    for lang in data.languages:
        pdf.multi_cell(0, 5, lang)

    pdf.output(str(output_path))


def add_heading(pdf: FPDF, text: str) -> None:
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, text, ln=1)
    x_left = pdf.l_margin
    x_right = pdf.w - pdf.r_margin
    y = pdf.get_y()
    pdf.line(x_left, y, x_right, y)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)


def fill_missing_header(data: ResumeData) -> ResumeData:
    if data.name:
        return data
    data.name = read_nonempty("Name: ")
    data.phone = read_nonempty("Phone: ")
    data.email = read_nonempty("Email: ")
    return data


def main() -> None:
    print("Resume formatter")
    mode = input("Choose mode: (1) interactive (2) import file: ").strip()
    if mode == "2":
        file_path = read_nonempty("Resume file path (.docx/.pdf/.txt): ")
        text = extract_text_from_file(Path(file_path))
        data = parse_resume_text(text)
        data = fill_missing_header(data)
    else:
        data = read_resume_interactive()

    output = read_optional("Output PDF path (default: formatted_resume.pdf): ")
    output_path = Path(output) if output else Path("formatted_resume.pdf")
    render_pdf(data, output_path)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
