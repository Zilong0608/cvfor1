from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

if load_dotenv is not None:
    base_dir = Path(__file__).resolve().parents[1]
    load_dotenv(base_dir / ".env", override=False)

import requests

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "summary_system_prompt.txt"
DEFAULT_SYSTEM_PROMPT = """You are ResumeSummaryAgent.

Goal:
Generate a single English resume summary customized for a specific job post,
grounded ONLY in the provided resume content and job details.

Inputs:
- resume_context: condensed resume info (skills, education, experience)
- job_post: title, description, requirements, location, site, url (if available)

Output:
- One paragraph, 60–90 words, English.

Style & structure:
- Use this structure: who you are -> core technical direction -> problems you solve/value -> suitable role.
- Third-person tone (e.g., "Full-stack oriented software engineer...").
- No headings, no bullets, no quotes, plain text only.
- When job requirements/skills are provided, highlight ONLY the ones supported by resume_context.

Hard constraints:
- Do NOT invent facts or skills not present in resume_context.
- Do NOT include company names.
- Do NOT include personal identifiers not in resume_context.
- If a job requirement is not supported by resume_context, avoid claiming it.
- Prefer specific skills only if present; otherwise use general strengths grounded in resume_context.
"""


def load_system_prompt() -> str:
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_SYSTEM_PROMPT


def get_openai_config() -> tuple[str, str, str]:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    model = (
        os.getenv("OPENAI_MODEL")
        or os.getenv("OPENAI_MODEL_NAME")
        or os.getenv("OPENAI_CHAT_MODEL")
        or "gpt-4o-mini"
    )
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")
    return api_key, model, base_url.rstrip("/")


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split()).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text))


def contains_company(summary: str, company_name: str | None) -> bool:
    if not company_name:
        return False
    cleaned = re.sub(r"\s+", " ", company_name).strip()
    if len(cleaned) < 3:
        return False
    return cleaned.lower() in summary.lower()


def build_user_prompt(
    resume_context: str,
    job_context: str,
    extra_instruction: str | None = None,
) -> str:
    prompt = f"Resume context:\n{resume_context}\n\nJob context:\n{job_context}"
    if extra_instruction:
        prompt = f"{prompt}\n\nAdditional instruction:\n{extra_instruction}"
    return prompt


def call_openai_chat(
    *,
    api_key: str,
    model: str,
    base_url: str,
    system_prompt: str,
    user_prompt: str,
    timeout_seconds: int = 30,
) -> str:
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_completion_tokens": 220,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout_seconds)
    if not response.ok:
        raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_summary(
    resume_context: str,
    job_context: str,
    *,
    company_name: str | None = None,
    min_words: int = 60,
    max_words: int = 90,
    max_retries: int = 2,
    api_max_retries: int = 2,
    sleep_seconds: float = 1.0,
) -> str:
    system_prompt = load_system_prompt()
    api_key, model, base_url = get_openai_config()
    extra_instruction = None
    summary = ""

    for attempt in range(max_retries + 1):
        user_prompt = build_user_prompt(resume_context, job_context, extra_instruction)
        for api_attempt in range(api_max_retries + 1):
            try:
                summary = call_openai_chat(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                break
            except Exception as exc:
                if api_attempt >= api_max_retries:
                    raise
                time.sleep(sleep_seconds * (2**api_attempt))
                summary = ""
        summary = normalize_text(summary)
        wc = word_count(summary)
        has_company = contains_company(summary, company_name)
        if min_words <= wc <= max_words and not has_company:
            return summary
        extra_parts = []
        if wc < min_words:
            extra_parts.append(f"Increase length to {min_words}-{max_words} words.")
        elif wc > max_words:
            extra_parts.append(f"Reduce length to {min_words}-{max_words} words.")
        if has_company:
            extra_parts.append("Remove any company names.")
        extra_instruction = " ".join(extra_parts) if extra_parts else None
        if attempt < max_retries:
            time.sleep(sleep_seconds)

    if summary:
        if contains_company(summary, company_name) and company_name:
            summary = re.sub(re.escape(company_name), "", summary, flags=re.IGNORECASE)
            summary = normalize_text(summary)
        return summary
    raise RuntimeError("Failed to generate summary.")
