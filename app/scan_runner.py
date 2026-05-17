"""
Standalone scan runner — called by GitHub Actions daily.
No FastAPI, no server. Just scrape → score → save JSON → email.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

DOCS_DIR    = Path("docs")
VIKAS_FILE  = DOCS_DIR / "jobs_vikas.json"
DIKSHA_FILE = DOCS_DIR / "jobs_diksha.json"
STATS_FILE  = DOCS_DIR / "stats.json"

V_MIN    = int(os.getenv("VIKAS_MIN_SCORE",  "60"))
D_MIN    = int(os.getenv("DIKSHA_MIN_SCORE", "50"))
MAX_JOBS = 200


def load_existing(path: Path) -> dict:
    if path.exists() and path.stat().st_size > 2:
        try:
            return {j["job_id"]: j for j in json.loads(path.read_text())}
        except Exception:
            pass
    return {}


async def main():
    from app.scrapers.naukri     import NaukriScraper
    from app.scrapers.linkedin   import LinkedInScraper
    from app.scrapers.indeed     import IndeedScraper
    from app.scrapers.shine      import ShineScraper
    from app.scrapers.timesjobs  import TimesJobsScraper
    from app.scrapers.iimjobs    import IIMJobsScraper
    from app.scrapers.glassdoor  import GlassdoorScraper
    from app.scrapers.remoteok   import RemoteOKScraper
    from app.matcher  import JobMatcher
    from app.notifier import EmailNotifier

    DOCS_DIR.mkdir(exist_ok=True)

    existing_vikas  = load_existing(VIKAS_FILE)
    existing_diksha = load_existing(DIKSHA_FILE)
    known_ids = set(existing_vikas) | set(existing_diksha)

    scrapers = [
        NaukriScraper(),
        LinkedInScraper(),
        IndeedScraper(),
        ShineScraper(),
        TimesJobsScraper(),
        IIMJobsScraper(),
        GlassdoorScraper(),
        RemoteOKScraper(),
    ]

    all_jobs = []
    for scraper in scrapers:
        try:
            jobs = await scraper.fetch_jobs()
            all_jobs.extend(jobs)
            logger.info(f"{scraper.__class__.__name__}: {len(jobs)} fetched")
        except Exception as e:
            logger.error(f"{scraper.__class__.__name__} failed: {e}")

    matcher = JobMatcher()
    today   = datetime.utcnow().strftime("%Y-%m-%d")
    vikas_new, diksha_new = [], []

    for job in all_jobs:
        if job["job_id"] in known_ids:
            continue
        scores = matcher.score_job(job)
        job["vikas_score"]  = scores["vikas"]
        job["diksha_score"] = scores["diksha"]
        job["status"]       = "new"
        job["scanned_date"] = today
        added = False
        if scores["vikas"] >= V_MIN:
            existing_vikas[job["job_id"]] = job
            vikas_new.append(job)
            added = True
        if scores["diksha"] >= D_MIN:
            existing_diksha[job["job_id"]] = job
            diksha_new.append(job)
            added = True
        if added:
            known_ids.add(job["job_id"])

    vikas_sorted  = sorted(existing_vikas.values(),  key=lambda x: x.get("vikas_score",  0), reverse=True)[:MAX_JOBS]
    diksha_sorted = sorted(existing_diksha.values(), key=lambda x: x.get("diksha_score", 0), reverse=True)[:MAX_JOBS]

    VIKAS_FILE.write_text(json.dumps(vikas_sorted,  indent=2, ensure_ascii=False))
    DIKSHA_FILE.write_text(json.dumps(diksha_sorted, indent=2, ensure_ascii=False))

    stats = {
        "last_scan":        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "vikas_total":      len(vikas_sorted),
        "diksha_total":     len(diksha_sorted),
        "vikas_new_today":  len(vikas_new),
        "diksha_new_today": len(diksha_new),
        "platforms":        "Naukri, LinkedIn, Indeed, Shine, TimesJobs, IIMJobs, Glassdoor, RemoteOK",
    }
    STATS_FILE.write_text(json.dumps(stats, indent=2))

    logger.info(f"Scan complete — Vikas: {len(vikas_new)} new | Diksha: {len(diksha_new)} new")

    EmailNotifier().send_daily_digest(vikas_new, diksha_new)


if __name__ == "__main__":
    asyncio.run(main())
