import hashlib
import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# iimjobs.com targets IIM alumni, senior management, and C-suite roles.
# Ideal for Vikas (IIM Kozhikode EPGP) and Diksha's senior cloud positions.
SEARCHES = [
    # Vikas — C-suite / senior leadership cybersecurity
    {"q": "CISO",                          "l": "delhi-ncr", "profile": "vikas"},
    {"q": "Chief Information Security",    "l": "delhi-ncr", "profile": "vikas"},
    {"q": "Head Cybersecurity",            "l": "delhi-ncr", "profile": "vikas"},
    {"q": "VP Cyber Security",             "l": "delhi-ncr", "profile": "vikas"},
    {"q": "Security Architect Director",   "l": "delhi-ncr", "profile": "vikas"},
    # Diksha — senior cloud / platform engineering
    {"q": "Cloud Architect Azure",         "l": "delhi-ncr", "profile": "diksha"},
    {"q": "Senior Cloud Engineer",         "l": "delhi-ncr", "profile": "diksha"},
    {"q": "DevOps Lead Platform",          "l": "delhi-ncr", "profile": "diksha"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.iimjobs.com/",
}


class IIMJobsScraper:
    SEARCH_URL = "https://www.iimjobs.com/search"

    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=25, headers=HEADERS, follow_redirects=True) as client:
            for s in SEARCHES:
                try:
                    params = {"q": s["q"], "l": s["l"]}
                    resp = await client.get(self.SEARCH_URL, params=params)
                    if resp.status_code == 200:
                        jobs.extend(self._parse(resp.text, s["profile"]))
                except Exception as e:
                    logger.warning(f"iimjobs scrape failed for '{s['q']}': {e}")
        return jobs

    def _parse(self, html: str, profile: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # iimjobs card selectors — may use job-wrap or listing divs
        cards = soup.select(
            "div.job-wrap, li.job-listing, div.listing-item, article.job-card"
        )
        if not cards:
            # Fallback: look for any heading links inside known list containers
            cards = soup.select("ul.job-listings > li, div.jobs-list > div")

        for card in cards[:12]:
            try:
                title_el   = card.select_one("h2 a, h3 a, .job-title a, a.title")
                company_el = card.select_one(".company, .comp-name, .employer")
                location_el = card.select_one(".location, .loc, .city")
                salary_el  = card.select_one(".salary, .sal, .ctc")
                exp_el     = card.select_one(".exp, .experience")

                title   = title_el.get_text(strip=True)   if title_el   else ""
                company = company_el.get_text(strip=True)  if company_el else ""
                location = location_el.get_text(strip=True) if location_el else "Delhi NCR"
                href    = title_el.get("href", "")         if title_el   else ""
                url     = href if href.startswith("http") else f"https://www.iimjobs.com{href}"
                salary  = salary_el.get_text(strip=True)  if salary_el  else "Not disclosed"
                exp     = exp_el.get_text(strip=True)     if exp_el     else ""

                if not title:
                    continue

                job_id = f"iimj_{hashlib.md5((title + company).encode()).hexdigest()[:10]}"
                jobs.append({
                    "job_id":       job_id,
                    "title":        title,
                    "company":      company,
                    "location":     location,
                    "source":       "iimjobs",
                    "url":          url,
                    "description":  f"{title} at {company} — {location}. {exp}".strip(),
                    "salary":       salary,
                    "posted_date":  "Recent",
                    "suggested_profile": profile,
                })
            except Exception:
                continue
        return jobs
