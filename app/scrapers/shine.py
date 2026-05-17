import hashlib
import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCHES = [
    # Vikas
    {"q": "CISO",                     "loc": "delhi",   "profile": "vikas"},
    {"q": "Head cybersecurity",        "loc": "delhi",   "profile": "vikas"},
    {"q": "Security architect",        "loc": "delhi",   "profile": "vikas"},
    # Diksha
    {"q": "Cloud engineer azure",      "loc": "delhi",   "profile": "diksha"},
    {"q": "DevOps engineer",           "loc": "delhi",   "profile": "diksha"},
    {"q": "Cloud architect",           "loc": "noida",   "profile": "diksha"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


class ShineScraper:
    BASE_URL = "https://www.shine.com/job-search/{q}-jobs-in-{loc}"

    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
            for s in SEARCHES:
                try:
                    slug_q = s["q"].lower().replace(" ", "-")
                    url = self.BASE_URL.format(q=slug_q, loc=s["loc"])
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        jobs.extend(self._parse(resp.text, s["profile"]))
                except Exception as e:
                    logger.warning(f"Shine scrape failed for '{s['q']}': {e}")
        return jobs

    def _parse(self, html: str, profile: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for card in soup.select("div.job-title-wrap, article.job-card")[:10]:
            try:
                title_el = card.select_one("h3 a, h2 a, .job-title a")
                company_el = card.select_one(".company-name, .comp-name")
                location_el = card.select_one(".location, .loc")
                salary_el = card.select_one(".salary, .sal")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else "Delhi NCR"
                url = title_el.get("href", "") if title_el else ""
                if url and not url.startswith("http"):
                    url = f"https://www.shine.com{url}"
                salary = salary_el.get_text(strip=True) if salary_el else "Not disclosed"

                if not title:
                    continue
                job_id = f"shine_{hashlib.md5((title + company).encode()).hexdigest()[:10]}"
                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "Shine",
                    "url": url,
                    "description": f"{title} at {company} — {location}",
                    "salary": salary,
                    "posted_date": "Recent",
                    "suggested_profile": profile,
                })
            except Exception:
                continue
        return jobs
