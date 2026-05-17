import hashlib
import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

from app.profiles.vikas import VIKAS_PROFILE
from app.profiles.diksha import DIKSHA_PROFILE

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    # Vikas — Cybersecurity leadership roles
    {"keyword": "CISO",                          "location": "delhi", "profile": "vikas", "exp": "10,20"},
    {"keyword": "Chief Information Security Officer", "location": "delhi", "profile": "vikas", "exp": "10,20"},
    {"keyword": "Head of Cybersecurity",          "location": "delhi", "profile": "vikas", "exp": "10,20"},
    {"keyword": "VP Cybersecurity",               "location": "delhi", "profile": "vikas", "exp": "10,20"},
    {"keyword": "Director Information Security",  "location": "delhi", "profile": "vikas", "exp": "8,20"},
    {"keyword": "Security Architect",             "location": "delhi", "profile": "vikas", "exp": "8,20"},
    {"keyword": "Cyber Security Manager",         "location": "noida", "profile": "vikas", "exp": "8,20"},
    {"keyword": "Head Information Security",      "location": "gurgaon", "profile": "vikas", "exp": "8,20"},
    # Diksha — Cloud engineering roles
    {"keyword": "Senior Cloud Engineer Azure",    "location": "delhi", "profile": "diksha", "exp": "5,12"},
    {"keyword": "Cloud Architect Azure",          "location": "delhi", "profile": "diksha", "exp": "5,12"},
    {"keyword": "Azure Administrator",            "location": "delhi", "profile": "diksha", "exp": "3,10"},
    {"keyword": "Cloud Migration Specialist",     "location": "delhi", "profile": "diksha", "exp": "5,12"},
    {"keyword": "DevOps Engineer Azure",          "location": "delhi", "profile": "diksha", "exp": "3,10"},
    {"keyword": "AWS Cloud Engineer",             "location": "noida", "profile": "diksha", "exp": "4,12"},
    {"keyword": "Terraform Infrastructure",       "location": "gurgaon", "profile": "diksha", "exp": "4,12"},
    {"keyword": "Cloud Platform Engineer",        "location": "delhi", "profile": "diksha", "exp": "4,12"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "appid": "109",
    "systemid": "Naukri",
    "Referer": "https://www.naukri.com/",
}


class NaukriScraper:
    API_URL = "https://www.naukri.com/api/v1/jobs"
    WEB_URL = "https://www.naukri.com/{kw}-jobs-in-{loc}"

    async def fetch_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
            for q in SEARCH_QUERIES:
                try:
                    # Try the internal API first
                    params = {
                        "keyword": q["keyword"],
                        "location": q["location"],
                        "noOfResults": 20,
                        "urlType": "search_by_keyword",
                        "searchType": "adv",
                        "src": "jobsearchDesk",
                        "experience": q["exp"],
                        "jobAge": 1,
                    }
                    resp = await client.get(self.API_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for raw in data.get("jobDetails", []):
                            jobs.append(self._parse_api(raw, q["profile"]))
                    else:
                        # Fallback to HTML scraping
                        kw_slug = q["keyword"].lower().replace(" ", "-")
                        url = self.WEB_URL.format(kw=kw_slug, loc=q["location"])
                        resp2 = await client.get(url)
                        if resp2.status_code == 200:
                            jobs.extend(self._parse_html(resp2.text, q["profile"], url))
                except Exception as e:
                    logger.warning(f"Naukri scrape failed for '{q['keyword']}': {e}")
        return jobs

    def _parse_api(self, raw: dict, profile: str) -> Dict:
        job_id_raw = str(raw.get("jobId", hashlib.md5(str(raw).encode()).hexdigest()[:8]))
        return {
            "job_id": f"naukri_{job_id_raw}",
            "title": raw.get("title", ""),
            "company": raw.get("companyName", ""),
            "location": self._extract_location(raw),
            "source": "Naukri",
            "url": f"https://www.naukri.com{raw.get('jdURL', '')}",
            "description": raw.get("jobDescription", ""),
            "salary": raw.get("salary", "Not disclosed"),
            "posted_date": raw.get("footerPlaceholderLabel", ""),
            "suggested_profile": profile,
        }

    def _extract_location(self, raw: dict) -> str:
        placeholders = raw.get("placeholders", [])
        for p in placeholders:
            if p.get("type") == "location":
                return p.get("label", "Delhi NCR")
        return "Delhi NCR"

    def _parse_html(self, html: str, profile: str, source_url: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for card in soup.select("article.jobTuple, div.jobTuple")[:15]:
            try:
                title_el = card.select_one("a.title")
                company_el = card.select_one("a.subTitle")
                location_el = card.select_one("li.location")
                salary_el = card.select_one("li.salary")
                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else "Delhi NCR"
                url = title_el.get("href", source_url) if title_el else source_url
                salary = salary_el.get_text(strip=True) if salary_el else "Not disclosed"
                job_id = f"naukri_{hashlib.md5((title + company).encode()).hexdigest()[:10]}"
                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "Naukri",
                    "url": url,
                    "description": f"{title} at {company} — {location}",
                    "salary": salary,
                    "posted_date": "Recent",
                    "suggested_profile": profile,
                })
            except Exception:
                continue
        return jobs
