import asyncio
import hashlib
import logging
import os
from typing import List, Dict
import httpx

logger = logging.getLogger(__name__)

APP_ID  = os.getenv("ADZUNA_APP_ID", "")
APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
BASE    = "https://api.adzuna.com/v1/api/jobs/in/search"

VIKAS_QUERIES = [
    "CISO",
    "Chief Information Security Officer",
    "Head of Cybersecurity",
    "VP Cybersecurity",
    "Director Information Security",
    "Security Architect Delhi",
    "Cyber Security Manager Delhi",
    "Head Information Security Delhi",
]

DIKSHA_QUERIES = [
    "Cloud Architect Azure Delhi",
    "Senior Cloud Engineer Delhi",
    "Azure Administrator Delhi",
    "DevOps Lead Delhi",
    "Cloud Migration Specialist Delhi",
    "Platform Engineer Azure Delhi",
    "Infrastructure Engineer Cloud Delhi",
]


class AdzunaScraper:
    async def fetch_jobs(self) -> List[Dict]:
        if not APP_ID or not APP_KEY:
            logger.warning("ADZUNA_APP_ID / ADZUNA_APP_KEY not set — skipping Adzuna")
            return []

        jobs = []
        async with httpx.AsyncClient(timeout=20) as client:
            for query in VIKAS_QUERIES:
                try:
                    results = await self._search(client, query, "Delhi NCR")
                    jobs.extend(results)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Adzuna Vikas '{query}': {e}")

            for query in DIKSHA_QUERIES:
                try:
                    results = await self._search(client, query, "Delhi NCR")
                    jobs.extend(results)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Adzuna Diksha '{query}': {e}")

        return self._dedup(jobs)

    async def _search(self, client: httpx.AsyncClient, query: str, location: str) -> List[Dict]:
        params = {
            "app_id":       APP_ID,
            "app_key":      APP_KEY,
            "results_per_page": 10,
            "what":         query,
            "where":        location,
            "country":      "in",
            "content-type": "application/json",
            "max_days_old": 30,
            "sort_by":      "date",
        }
        r = await client.get(f"{BASE}/1", params=params)
        if r.status_code != 200:
            logger.warning(f"Adzuna HTTP {r.status_code} for '{query}'")
            return []
        data = r.json()
        jobs = []
        for item in data.get("results", []):
            try:
                loc = item.get("location", {}).get("display_name", location)
                salary = self._salary(item)
                job_id = "adz_" + hashlib.md5(
                    f"{item.get('id', '')}{item.get('title', '')}".encode()
                ).hexdigest()[:10]
                jobs.append({
                    "job_id":      job_id,
                    "title":       item.get("title", ""),
                    "company":     item.get("company", {}).get("display_name", ""),
                    "location":    loc,
                    "salary":      salary,
                    "posted_date": (item.get("created", "") or "")[:10],
                    "url":         item.get("redirect_url", ""),
                    "source":      "Adzuna",
                    "description": item.get("description", ""),
                })
            except Exception:
                continue
        return jobs

    def _salary(self, item: dict) -> str:
        mn = item.get("salary_min")
        mx = item.get("salary_max")
        if mn and mx:
            return f"₹{int(mn):,}–{int(mx):,} pa"
        if mn:
            return f"₹{int(mn):,}+ pa"
        return "Not disclosed"

    def _dedup(self, jobs: List[Dict]) -> List[Dict]:
        seen, out = set(), []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                out.append(j)
        return out
