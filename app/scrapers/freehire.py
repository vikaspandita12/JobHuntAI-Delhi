"""FreeHire — jobs read straight from company career pages (Greenhouse, Lever,
Workday, Ashby...). Public HTTP API, no key. Idea borrowed from Dossier
(github.com/AienTech/dossier); this is an independent Python implementation."""
import asyncio
import logging
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

BASE = "https://freehire.me/api/v1/agent/jobs/search"
HEADERS = {"User-Agent": "JobHuntAI/1.0", "Accept": "application/json"}

QUERIES = [
    "CISO in Delhi",
    "Head of Information Security in Delhi",
    "Director Cybersecurity in Gurugram",
    "Security Architect in Delhi",
    "Cybersecurity in Noida",
    "Cloud Architect in Delhi",
    "Senior Cloud Engineer in Gurugram",
    "Azure DevOps Engineer in Noida",
    "Platform Engineer in Delhi",
    "Site Reliability Engineer in Gurugram",
]


class FreeHireScraper:
    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=25, follow_redirects=True) as client:
            for q in QUERIES:
                try:
                    r = await client.get(BASE, params={
                        "q": q,
                        "countries": "IN",
                        "limit": 20,
                        "offset": 0,
                        "description_format": "text",
                        "posted_within_days": 30,
                    })
                    if r.status_code != 200:
                        logger.warning(f"FreeHire HTTP {r.status_code} for '{q}'")
                        continue
                    for item in (r.json() or {}).get("data", []):
                        job = self._parse(item)
                        if job:
                            jobs.append(job)
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"FreeHire '{q}': {e}")
        return _dedup(jobs)

    def _parse(self, item: dict) -> Dict:
        slug = item.get("public_slug")
        title = (item.get("title") or "").strip()
        url = item.get("url") or ""
        if not slug or not title or not url.startswith("http"):
            return {}
        work_mode = (item.get("work_mode") or "").lower()
        location = (item.get("location") or "").strip() or "India"
        if work_mode == "remote" and "remote" not in location.lower():
            location = f"{location} (Remote)"
        return {
            "job_id": f"fh_{slug[:60]}",
            "title": title,
            "company": (item.get("company") or "").strip(),
            "location": location,
            "salary": _salary(item.get("enrichment") or {}),
            "posted_date": (item.get("posted_at") or "Recent")[:10],
            "url": url,
            "source": "FreeHire",
            "via": (item.get("source") or "").strip(),
            "description": (item.get("description") or "")[:6000],
        }


def _salary(e: dict) -> str:
    lo, hi, cur = e.get("salary_min"), e.get("salary_max"), e.get("salary_currency") or ""
    if lo is None and hi is None:
        return "Not disclosed"
    fmt = lambda v: f"{int(v):,}"
    rng = f"{fmt(lo)}–{fmt(hi)}" if lo is not None and hi is not None and lo != hi else fmt(lo if lo is not None else hi)
    return f"{cur} {rng}".strip()


def _dedup(jobs: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for j in jobs:
        if j["job_id"] not in seen:
            seen.add(j["job_id"])
            out.append(j)
    return out
