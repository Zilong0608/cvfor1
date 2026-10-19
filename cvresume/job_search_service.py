"""Bounded searches with incremental results and a short, public-job-only cache."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from collections import OrderedDict
from copy import deepcopy
from threading import BoundedSemaphore, Lock
from time import monotonic
from typing import Any, Iterator

import pandas as pd

from apps.resume_summary_agent_gui import (
    build_google_search_term, dedupe_jobs, expand_search_terms,
    filter_by_title, select_sites,
)
from jobspy import scrape_jobs

_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="job-search")
# Includes queued work; timed-out running calls keep their slot until they finish.
_slots = BoundedSemaphore(18)
_lock = Lock()
_cache: OrderedDict[tuple, tuple[float, dict]] = OrderedDict()
COUNTRIES = {"US": "USA", "AU": "Australia", "UK": "UK", "CA": "Canada", "SG": "Singapore"}
FAST_SEARCH_SECONDS = 35
EXPANDED_SEARCH_SECONDS = 60


def _fetch(site: str, term: str, location: str, country: str, count: int):
    try:
        # Raise failures to the API so a broken platform is not cached as an empty result.
        jobs = scrape_jobs(site_name=[site], search_term=term,
                           google_search_term=build_google_search_term(term, location, country),
                           location=location or None, country_indeed=country,
                           results_wanted=count, raise_on_error=True)
        return filter_by_title(jobs, term)
    finally:
        _slots.release()


def search_events(title: str, region: str = "", country: str = "AU",
                  expanded: bool = False, results_per_site: int = 20) -> Iterator[dict[str, Any]]:
    title, region = title.strip(), region.strip()
    if not title:
        yield {"type": "error", "message": "Please enter a job title."}
        return
    country = COUNTRIES.get(country.strip().upper(), country.strip() or "Australia")
    # Validate before scheduling workers.
    from jobspy.model import Country
    try:
        Country.from_string(country)
    except ValueError:
        yield {"type": "error", "message": "Unsupported country."}
        return
    terms = [title]
    if expanded:
        terms += [term for term in expand_search_terms(title, []) if term.lower() != title.lower()][:2]
    sites = select_sites(country)
    if not expanded:
        sites = [site for site in sites if site in {"indeed", "linkedin", "google", "naukri", "bdjobs", "bayt"}]
    if country.lower() not in {"usa", "us", "united states", "canada"}:
        sites = [site for site in sites if site != "zip_recruiter"]
    key = (title.casefold(), region.casefold(), country.casefold(), expanded, results_per_site)
    now = monotonic()
    with _lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < 300:
            result = deepcopy(cached[1])
        else:
            result = None
            _cache.pop(key, None)
    if result is not None:
        yield {"type": "log", "message": "Using recent search results."}
        yield result
        return

    frames, pending, failures = [], {}, []
    deadline = monotonic() + (EXPANDED_SEARCH_SECONDS if expanded else FAST_SEARCH_SECONDS)
    yield {"type": "log", "message": f"Searching: {', '.join(terms)}. Sites: {', '.join(sites)}"}
    for term in terms:
        for site in sites:
            if not _slots.acquire(blocking=False):
                failures.append(f"{site}: search capacity busy")
                continue
            try:
                future = _pool.submit(_fetch, site, term, region, country, results_per_site)
            except Exception:
                _slots.release()
                raise
            # _fetch cannot release the slot when cancelled before it starts.
            future.add_done_callback(lambda f: _slots.release() if f.cancelled() else None)
            pending[future] = site

    def snapshot():
        jobs = dedupe_jobs(pd.concat(frames, ignore_index=True)) if frames else pd.DataFrame()
        columns = ["title", "company", "location", "site", "description", "job_url", "job_url_direct"]
        records = jobs.reindex(columns=columns).fillna("").to_dict("records")
        counts = jobs["site"].value_counts().to_dict() if not jobs.empty else {}
        analysis = f"Search terms: {', '.join(terms)}\nTotal unique jobs: {len(records)}"
        if counts:
            analysis += "\nBy site: " + ", ".join(f"{s}: {n}" for s, n in counts.items())
        return {"jobs": records, "total": len(records), "analysis": analysis}

    try:
        while pending and monotonic() < deadline:
            done, _ = wait(pending, timeout=min(1, max(0, deadline - monotonic())), return_when=FIRST_COMPLETED)
            if not done:
                yield {"type": "heartbeat"}
            for future in done:
                site = pending.pop(future)
                try:
                    jobs = future.result()
                    if not jobs.empty:
                        frames.append(jobs)
                    yield {"type": "log", "message": f"{site}: {len(jobs)} jobs fetched."}
                    yield {"type": "results", **snapshot()}
                except Exception:
                    failures.append(f"{site}: unavailable")
                    yield {"type": "log", "message": f"{site} is unavailable; keeping other results."}
        for site in pending.values():
            failures.append(f"{site}: timed out")
        result = {"type": "done", **snapshot(), "warnings": failures}
        # Do not cache partial/failed results; the next attempt can recover.
        if not failures:
            with _lock:
                _cache[key] = (monotonic(), deepcopy(result))
                _cache.move_to_end(key)
                while len(_cache) > 64:
                    _cache.popitem(last=False)
        yield result
    finally:
        for future in pending:
            future.cancel()
