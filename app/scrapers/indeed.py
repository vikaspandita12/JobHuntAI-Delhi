import hashlib
import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCHES = [
    # Vikas
    {"q": "CISO cybersecurity",              "l": "New Delhi, Delhi",  "profile": "vikas"},
    {"q": "Head Information Security",       "l": "Delhi NCR",         "profile": "vikas"},
    {"q": "Security Architect senior",       "l": "New Delhi, Delhi",  "profile": "vikas"},
    {"q": "Director cyber security",         "l": "Gurugram, Haryana", "profile": "vikas"},
    {"q": "VP cybersecurity",                "l": "Noida, Uttar Pradesh","profile": "vikas"},
    # Diksha
    {"q": "Cloud Engineer Azure senior",     "l": "New Delhi, Delhi",  "profile": "diksha"},
    {"q": "Cloud Architect AWS",             "l": "Delhi NCR",         "profile": "diksha"},
    {"q": "DevOps Engineer terraform",       "l": "Gurugram, Haryana", "profile": "diksha"},
    {"q": "Cloud migration specialist",      "l": "Noida, Uttar Pradesh","profile": "diksha"},
    {"q": "Azure administrator engineer",    "l": "New Delhi, Delhi",  "profile": "diksha"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


class IndeedScraper:
    BASE_URL = "https://in.indeed.com/jobs"

    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
            for s in SEARCHES:
                try:
                    params = {"q": s["q"], "l": s["l"], "fromage": "3", "sort": "date"}
                    resp = await client.get(self.BASE_URL, params=params)
                    if resp.status_code == 200:
                        jobs.extend(self._parse(resp.text, s["profile"]))
                except Exception as e:
                    logger.warning(f"Indeed scrape failed for '{s['q']}': {e}")
        return jobs

    def _parse(self, html: str, profile: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for card in soup.select("div.job_seen_beacon, div.jobsearch-SerpJobCard")[:10]:
            try:
                title_el = card.select_one("h2.jobTitle span, a.jobtitle")
                company_el = card.select_one("span.companyName, span.company")
                location_el = card.select_one("div.companyLocation, div.location")
                link_el = card.select_one("a[id^='job_'], a.jobtitle")
                salary_el = card.select_one("div.salary-snippet-container, span.salary")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else "Delhi NCR"
                href = link_el.get("href", "") if link_el else ""
                url = f"https://in.indeed.com{href}" if href.startswith("/") else href
                salary = salary_el.get_text(strip=True) if salary_el else "Not disclosed"

                if not title:
                    continue
                job_id = f"indeed_{hashlib.md5((title + company).encode()).hexdigest()[:10]}"
                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "Indeed",
                    "url": url,
                    "description": f"{title} at {company} — {location}",
                    "salary": salary,
                    "posted_date": "Recent",
                    "suggested_profile": profile,
                })
            except Exception:
                continue
        return jobs
