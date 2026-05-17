import asyncio
import hashlib
import logging
from typing import List, Dict
import httpx

logger = logging.getLogger(__name__)

# Tags relevant to Vikas (cybersecurity) and Diksha (cloud/devops)
VIKAS_TAGS  = ["cybersecurity", "security", "infosec", "devsecops"]
DIKSHA_TAGS = ["devops", "cloud", "azure", "kubernetes", "platform", "infrastructure", "aws"]


class RemoteOKScraper:
    API = "https://remoteok.com/api"

    async def fetch_jobs(self) -> List[Dict]:
        jobs = []
        headers = {
            "User-Agent": "Mozilla/5.0 JobHuntAI/1.0 (github.com/vikaspandita12/JobHuntAI-Delhi)",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(headers=headers, timeout=20, follow_redirects=True) as client:
            for tag in VIKAS_TAGS + DIKSHA_TAGS:
                try:
                    r = await client.get(self.API, params={"tag": tag})
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    # Index 0 is metadata — skip it
                    for item in data[1:12]:
                        if not isinstance(item, dict):
                            continue
                        raw_loc = item.get("location") or ""
                        location = (
                            "Remote (India OK)"
                            if raw_loc.lower() in ("", "worldwide", "anywhere", "remote")
                            else raw_loc
                        )
                        salary_raw = item.get("salary") or item.get("salary_min") or ""
                        salary = str(salary_raw) if salary_raw else "Not disclosed"
                        slug = item.get("slug", "")
                        url = item.get("url") or f"https://remoteok.com/l/{slug}"
                        job_id = "rok_" + str(
                            item.get("id",
                            hashlib.md5(f"{item.get('position','')}{item.get('company','')}".encode()).hexdigest()[:8])
                        )
                        jobs.append({
                            "job_id": job_id,
                            "title": item.get("position", ""),
                            "company": item.get("company", ""),
                            "location": location,
                            "salary": salary,
                            "posted_date": (item.get("date") or "Recent")[:10],
                            "url": url,
                            "source": "RemoteOK",
                            "description": item.get("description", ""),
                        })
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"RemoteOK '{tag}': {e}")
        return self._dedup(jobs)

    def _dedup(self, jobs: List[Dict]) -> List[Dict]:
        seen, out = set(), []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                out.append(j)
        return out
