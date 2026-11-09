"""Free public remote-job APIs (no keys): Remotive, Jobicy and Himalayas.
Each posting keeps the board's stated eligibility ("Worldwide", "USA only",
"India"...) as its location, so the matcher can flag country-locked roles.
Terms: each board asks for a link back to the original posting — kept in `url`."""
import asyncio
import html
import logging
import re
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "JobHuntAI/1.0", "Accept": "application/json"}

SEARCHES = ["security", "cloud", "devops", "sre"]
JOBICY_TAGS = ["security", "devops", "cloud", "aws"]


def _text(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", raw or "")).strip()[:6000]


def _date(v) -> str:
    from datetime import datetime, timezone
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000 if v > 1e12 else v, timezone.utc).strftime("%Y-%m-%d")
    return str(v or "Recent")[:10]


def _remote(where: str) -> str:
    where = (where or "").strip() or "Worldwide"
    return f"Remote ({where})"


class RemoteBoardsScraper:
    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            for name, fn in (("Remotive", self._remotive), ("Jobicy", self._jobicy), ("Himalayas", self._himalayas)):
                try:
                    got = await fn(client)
                    logger.info(f"  {name}: {len(got)}")
                    jobs.extend(got)
                except Exception as e:
                    logger.warning(f"{name} failed: {e!r}"[:200])
        seen, out = set(), []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                out.append(j)
        return out

    async def _remotive(self, client) -> List[Dict]:
        out = []
        for q in SEARCHES:
            r = await client.get("https://remotive.com/api/remote-jobs", params={"search": q, "limit": 50})
            for i in r.json().get("jobs", []):
                out.append({
                    "job_id": f"rmt_{i.get('id')}", "title": i.get("title", ""), "company": i.get("company_name", ""),
                    "location": _remote(i.get("candidate_required_location")), "salary": i.get("salary") or "Not disclosed",
                    "posted_date": (i.get("publication_date") or "")[:10], "url": i.get("url", ""),
                    "source": "Remotive", "description": _text(i.get("description")),
                })
            await asyncio.sleep(2)
        return out

    async def _jobicy(self, client) -> List[Dict]:
        out = []
        for tag in JOBICY_TAGS:
            r = await client.get("https://jobicy.com/api/v2/remote-jobs", params={"count": 50, "tag": tag})
            for i in r.json().get("jobs", []):
                lo, hi = i.get("annualSalaryMin"), i.get("annualSalaryMax")
                out.append({
                    "job_id": f"jcy_{i.get('id')}", "title": _text(i.get("jobTitle")), "company": i.get("companyName", ""),
                    "location": _remote(i.get("jobGeo")),
                    "salary": f"{i.get('salaryCurrency') or ''} {lo:,}–{hi:,}".strip() if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) else "Not disclosed",
                    "posted_date": (i.get("pubDate") or "")[:10], "url": i.get("url", ""),
                    "source": "Jobicy", "description": _text(i.get("jobDescription") or i.get("jobExcerpt")),
                })
            await asyncio.sleep(2)
        return out

    async def _himalayas(self, client) -> List[Dict]:
        out = []
        for q in SEARCHES:
            r = await client.get("https://himalayas.app/jobs/api/search", params={"q": q, "country": "India"})
            if r.status_code != 200:
                continue
            for i in r.json().get("jobs", []):
                where = ", ".join(i.get("locationRestrictions") or []) or "Worldwide"
                out.append({
                    "job_id": f"hml_{i.get('guid') or i.get('applicationLink')}"[:120],
                    "title": i.get("title", ""), "company": i.get("companyName", ""),
                    "location": _remote(where), "salary": "Not disclosed",
                    "posted_date": _date(i.get("pubDate")),
                    "url": i.get("applicationLink") or i.get("guid") or "",
                    "source": "Himalayas", "description": _text(i.get("description") or i.get("excerpt")),
                })
            await asyncio.sleep(2)
        return [j for j in out if j["url"].startswith("http")]
