"""JSearch — Google for Jobs index: LinkedIn, Naukri, Indeed, Glassdoor,
company sites and more, through one legal API. Optional: runs only when the
JSEARCH_API_KEY secret is set. Free tier is small, so queries are kept few.

JSEARCH_HOST: "rapidapi" (default, key from rapidapi.com) or "openwebninja".
Idea borrowed from Dossier (github.com/AienTech/dossier)."""
import asyncio
import logging
import os
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

HOSTS = {
    "rapidapi": ("https://jsearch.p.rapidapi.com",
                 lambda k: {"x-rapidapi-key": k, "x-rapidapi-host": "jsearch.p.rapidapi.com"}),
    "openwebninja": ("https://api.openwebninja.com/jsearch", lambda k: {"x-api-key": k}),
}

# 6 queries/day ≈ 180/month — inside the free tier
QUERIES = [
    "CISO in Delhi NCR",
    "Head of Cyber Security in Gurugram",
    "Security Architect in Delhi NCR",
    "Senior Cloud Engineer Azure in Delhi NCR",
    "Cloud Architect in Gurugram",
    "DevOps Lead in Noida",
]


class JSearchScraper:
    async def fetch_jobs(self) -> List[Dict]:
        key = os.getenv("JSEARCH_API_KEY", "").strip()
        if not key:
            logger.info("JSEARCH_API_KEY not set — skipping JSearch (LinkedIn/Naukri/Indeed via Google Jobs)")
            return []
        base, headers = HOSTS.get(os.getenv("JSEARCH_HOST", "rapidapi").strip().lower(), HOSTS["rapidapi"])
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=40, headers=headers(key)) as client:
            for q in QUERIES:
                try:
                    r = await client.get(f"{base}/search", params={
                        "query": q, "country": "in", "date_posted": "week",
                        "page": 1, "num_pages": 1,
                    })
                    if r.status_code != 200:
                        logger.warning(f"JSearch HTTP {r.status_code} for '{q}'")
                        if r.status_code in (401, 403, 429):
                            break
                        continue
                    data = r.json().get("data")
                    items = data.get("jobs", []) if isinstance(data, dict) else (data or [])
                    jobs.extend(j for j in (self._parse(i) for i in items) if j)
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"JSearch '{q}': {e}")
        seen, out = set(), []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                out.append(j)
        return out

    def _parse(self, i: dict) -> Dict:
        if not i.get("job_id") or not i.get("job_title"):
            return {}
        options = i.get("apply_options") or []
        direct = next((o for o in options if o.get("is_direct")), None)
        url = (direct or {}).get("apply_link") or i.get("job_apply_link") or i.get("job_google_link") or ""
        loc = ", ".join(x for x in [i.get("job_city"), i.get("job_state")] if x) or (i.get("job_location") or "India")
        if i.get("job_is_remote"):
            loc += " (Remote)"
        lo, hi = i.get("job_min_salary"), i.get("job_max_salary")
        salary = i.get("job_salary") or (f"{i.get('job_salary_currency') or ''} {int(lo):,}–{int(hi):,}".strip() if lo and hi else "Not disclosed")
        return {
            "job_id": f"js_{str(i['job_id'])[:80]}",
            "title": i["job_title"].strip(),
            "company": (i.get("employer_name") or "").strip(),
            "location": loc,
            "salary": salary,
            "posted_date": (i.get("job_posted_at_datetime_utc") or "Recent")[:10],
            "url": url,
            "source": "JSearch",
            "via": (i.get("job_publisher") or "").strip(),
            "description": (i.get("job_description") or "")[:6000],
        }
