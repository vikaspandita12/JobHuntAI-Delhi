import hashlib
import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCHES = [
    # Vikas — Cybersecurity leadership
    {"q": "CISO",                          "loc": "delhi",   "profile": "vikas"},
    {"q": "Head of Cybersecurity",          "loc": "delhi",   "profile": "vikas"},
    {"q": "VP Information Security",        "loc": "delhi",   "profile": "vikas"},
    {"q": "Director Cyber Security",        "loc": "delhi",   "profile": "vikas"},
    {"q": "Security Architect Senior",      "loc": "noida",   "profile": "vikas"},
    # Diksha — Cloud engineering
    {"q": "Senior Cloud Engineer Azure",    "loc": "delhi",   "profile": "diksha"},
    {"q": "Cloud Architect AWS",            "loc": "delhi",   "profile": "diksha"},
    {"q": "DevOps Engineer Terraform",      "loc": "gurugram","profile": "diksha"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.timesjobs.com/",
}


class TimesJobsScraper:
    BASE_URL = "https://www.timesjobs.com/candidate/job-search.html"

    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
            for s in SEARCHES:
                try:
                    params = {
                        "searchType": "personalizedSearch",
                        "from": "submit",
                        "txtKeywords": s["q"],
                        "txtLocation": s["loc"],
                        "sequence": 1,
                        "startPage": 1,
                        "postWeek": 1,   # Posted in last 1 week
                    }
                    resp = await client.get(self.BASE_URL, params=params)
                    if resp.status_code == 200:
                        jobs.extend(self._parse(resp.text, s["profile"]))
                except Exception as e:
                    logger.warning(f"TimesJobs scrape failed for '{s['q']}': {e}")
        return jobs

    def _parse(self, html: str, profile: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for card in soup.select("li.clearfix.job-bx, div.job-bx")[:10]:
            try:
                title_el  = card.select_one("h2 a, .job-title a")
                company_el = card.select_one(".joblist-comp-name, .comp-name")
                location_el = card.select_one(".srp-skills, .location")
                loc_label   = card.select_one("ul.top-jd-dtl li:nth-child(2), .loc")
                salary_el  = card.select_one(".salary, .sal")
                exp_el     = card.select_one(".srp-exp, .exp")

                title   = title_el.get_text(strip=True)  if title_el   else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = loc_label.get_text(strip=True) if loc_label else (
                            location_el.get_text(strip=True) if location_el else "Delhi NCR")
                url     = title_el.get("href", "") if title_el else ""
                if url and not url.startswith("http"):
                    url = f"https://www.timesjobs.com{url}"
                salary = salary_el.get_text(strip=True) if salary_el else "Not disclosed"
                exp    = exp_el.get_text(strip=True)    if exp_el    else ""

                if not title:
                    continue

                job_id = f"tj_{hashlib.md5((title + company).encode()).hexdigest()[:10]}"
                jobs.append({
                    "job_id":       job_id,
                    "title":        title,
                    "company":      company,
                    "location":     location,
                    "source":       "TimesJobs",
                    "url":          url,
                    "description":  f"{title} at {company} — {location}. Experience: {exp}",
                    "salary":       salary,
                    "posted_date":  "Recent",
                    "suggested_profile": profile,
                })
            except Exception:
                continue
        return jobs
