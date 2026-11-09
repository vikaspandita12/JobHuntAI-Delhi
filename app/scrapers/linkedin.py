import hashlib
import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCHES = [
    # Vikas
    {"q": "CISO",                          "location": "Delhi, India",   "profile": "vikas",  "exp": "5"},
    {"q": "Head of Cybersecurity",          "location": "Delhi, India",   "profile": "vikas",  "exp": "5"},
    {"q": "VP Information Security",        "location": "Delhi, India",   "profile": "vikas",  "exp": "5"},
    {"q": "Security Architect Director",    "location": "Delhi NCR",      "profile": "vikas",  "exp": "5"},
    {"q": "Director Cybersecurity",         "location": "Gurugram, India","profile": "vikas",  "exp": "5"},
    {"q": "Chief Information Security",     "location": "Noida, India",   "profile": "vikas",  "exp": "5"},
    # Diksha
    {"q": "Senior Cloud Engineer Azure",    "location": "Delhi, India",   "profile": "diksha", "exp": "3"},
    {"q": "Cloud Architect AWS Azure",      "location": "Delhi NCR",      "profile": "diksha", "exp": "3"},
    {"q": "DevOps Engineer Azure",          "location": "Gurugram, India","profile": "diksha", "exp": "3"},
    {"q": "Cloud Migration Lead",           "location": "Noida, India",   "profile": "diksha", "exp": "3"},
    {"q": "Platform Engineer Terraform",    "location": "Delhi, India",   "profile": "diksha", "exp": "3"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs/search"

    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
            for s in SEARCHES:
                try:
                    params = {
                        "keywords": s["q"],
                        "location": s["location"],
                        "f_TPR": "r604800",  # past week; dedup drops repeats
                        "f_E": s["exp"],
                        "position": 1,
                        "pageNum": 0,
                    }
                    resp = await client.get(self.BASE_URL, params=params)
                    if resp.status_code == 200:
                        jobs.extend(self._parse(resp.text, s["profile"]))
                except Exception as e:
                    logger.warning(f"LinkedIn scrape failed for '{s['q']}': {e}")
        return jobs

    def _parse(self, html: str, profile: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for card in soup.select("div.base-card, li.jobs-search__results-list > div")[:10]:
            try:
                title_el = card.select_one("h3.base-search-card__title, h3.job-search-card__title")
                company_el = card.select_one("h4.base-search-card__subtitle, a.job-search-card__company-name")
                location_el = card.select_one("span.job-search-card__location")
                link_el = card.select_one("a.base-card__full-link, a.job-search-card__title-link")
                time_el = card.select_one("time")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else "Delhi NCR"
                url = link_el.get("href", "") if link_el else ""
                posted = time_el.get("datetime", "") if time_el else ""

                if not title:
                    continue
                job_id = f"li_{hashlib.md5((title + company + url).encode()).hexdigest()[:10]}"
                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "LinkedIn",
                    "url": url,
                    "description": f"{title} at {company} — {location}",
                    "salary": "Not disclosed",
                    "posted_date": posted,
                    "suggested_profile": profile,
                })
            except Exception:
                continue
        return jobs
