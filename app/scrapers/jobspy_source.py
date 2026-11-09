"""JobSpy — open-source multi-board scraper (github.com/speedyapply/JobSpy,
PyPI: python-jobspy, MIT). One call searches LinkedIn, Indeed India, Naukri,
Glassdoor and Google Jobs concurrently and returns structured rows, with
browser-grade TLS that gets through where plain HTTP scrapers are blocked."""
import asyncio
import logging
import math
from typing import Dict, List

logger = logging.getLogger(__name__)

# glassdoor and google answer 403 / nothing to GitHub-hosted runners, so they are off
SITES = ["linkedin", "indeed", "naukri"]
PRETTY = {"linkedin": "LinkedIn", "indeed": "Indeed", "naukri": "Naukri", "glassdoor": "Glassdoor",
          "google": "Google Jobs", "zip_recruiter": "ZipRecruiter"}

SEARCHES = [
    # Vikas — security leadership
    "CISO",
    "Head of Information Security",
    "Director Cyber Security",
    "Security Architect",
    # Diksha — cloud engineering
    "Senior Cloud Engineer Azure",
    "Cloud Architect",
    "DevOps Lead",
    "Site Reliability Engineer",
]


def _clean(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v


class JobSpyScraper:
    async def fetch_jobs(self) -> List[Dict]:
        try:
            from jobspy import scrape_jobs
        except ImportError:
            logger.warning("python-jobspy not installed — skipping JobSpy")
            return []
        jobs: List[Dict] = []
        for term in SEARCHES:
            try:
                df = await asyncio.to_thread(
                    scrape_jobs,
                    site_name=SITES,
                    search_term=term,
                    google_search_term=f"{term} jobs near Delhi, India since last week",
                    location="Delhi, India",
                    distance=50,
                    results_wanted=15,
                    hours_old=168,
                    country_indeed="india",
                    description_format="markdown",
                    verbose=0,
                )
                for site, err in (df.attrs.get("errors") or {}).items():
                    logger.warning(f"JobSpy {site} '{term}': {str(err)[:120]}")
                for row in df.to_dict("records"):
                    job = self._parse(row)
                    if job:
                        jobs.append(job)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"JobSpy '{term}': {e!r}"[:200])
        seen, out = set(), []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                out.append(j)
        by_site = {}
        for j in out:
            by_site[j["source"]] = by_site.get(j["source"], 0) + 1
        logger.info(f"JobSpy by site: {by_site}")
        return out

    def _parse(self, r: dict) -> Dict:
        site = _clean(r.get("site")) or "jobspy"
        title = _clean(r.get("title"))
        url = _clean(r.get("job_url_direct")) or _clean(r.get("job_url"))
        if not title or not url:
            return {}
        loc = r.get("location") or {}
        if isinstance(loc, dict):
            country = loc.get("country")
            country = getattr(country, "value", country)
            location = ", ".join(str(x) for x in (loc.get("city"), loc.get("state")) if _clean(x)) or str(country or "India")
        else:
            location = str(loc)
        if _clean(r.get("is_remote")):
            location += " (Remote)"
        lo, hi, cur = _clean(r.get("min_amount")), _clean(r.get("max_amount")), _clean(r.get("currency")) or ""
        salary = f"{cur} {int(lo):,}–{int(hi):,}".strip() if lo and hi else "Not disclosed"
        emails = _clean(r.get("emails")) or []
        if isinstance(emails, str):  # JobSpy serialises the list as "a@x, b@y"
            emails = [e.strip() for e in emails.split(",") if "@" in e]
        posted = _clean(r.get("date_posted"))
        return {
            "job_id": f"jsp_{site}_{_clean(r.get('id')) or abs(hash(url))}",
            "title": str(title).strip(),
            "company": str(_clean(r.get("company")) or "").strip(),
            "location": location,
            "salary": salary,
            "posted_date": str(posted)[:10] if posted else "Recent",
            "url": url,
            "source": PRETTY.get(site, site.title()),
            "via": "JobSpy",
            "apply_email": emails[0] if isinstance(emails, list) and emails else "",
            "description": str(_clean(r.get("description")) or "")[:6000],
        }
