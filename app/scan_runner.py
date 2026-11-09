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
logging.getLogger("httpx").setLevel(logging.WARNING)  # don't log every URL (keys live in some)
logger = logging.getLogger(__name__)

DOCS_DIR    = Path("docs")
VIKAS_FILE  = DOCS_DIR / "jobs_vikas.json"
DIKSHA_FILE = DOCS_DIR / "jobs_diksha.json"
STATS_FILE  = DOCS_DIR / "stats.json"

V_MIN    = int(os.getenv("VIKAS_MIN_SCORE",  "60"))
D_MIN    = int(os.getenv("DIKSHA_MIN_SCORE", "50"))
MAX_JOBS = 300


def load_existing(path: Path) -> dict:
    if path.exists() and path.stat().st_size > 2:
        try:
            return {j["job_id"]: j for j in json.loads(path.read_text())}
        except Exception:
            pass
    return {}


def apply_fit(job: dict, matcher, who: str) -> int:
    f = matcher.fit(job, who)
    job[f"{who}_score"] = f["score"]
    job[f"{who}_fit"] = {"band": f["band"], "reasons": f["reasons"], "red_flags": f["red_flags"], "gaps": f["gaps"]}
    return f["score"]


def dedup_postings(jobs, who: str) -> list:
    """One card per posting: the same job reaches us from several sources and
    searches under different IDs. Keeps the earliest-seen copy, best score first."""
    import re
    norm = lambda t: re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()
    best = {}
    for j in sorted(jobs, key=lambda x: (x.get("scanned_date", ""), x["job_id"])):
        key = (norm(j.get("title")), norm(j.get("company")))
        if key not in best:
            best[key] = j
    return sorted(best.values(), key=lambda x: x.get(f"{who}_score", 0), reverse=True)


def write_public_profiles():
    """Career facts for the dashboard's "Tailor with Claude" prompt.
    The dashboard is public, so no phone, email or LinkedIn URL goes in."""
    from app.profiles.diksha import DIKSHA_PROFILE
    from app.profiles.vikas import VIKAS_PROFILE
    keep = ("name", "current_role", "current_company", "years_experience", "relocation_note",
            "education", "certifications", "key_achievements", "key_skills", "target_titles")
    out = {who: {k: p.get(k) for k in keep} for who, p in (("vikas", VIKAS_PROFILE), ("diksha", DIKSHA_PROFILE))}
    (DOCS_DIR / "profiles.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))


async def run_source(scraper):
    name = scraper.__class__.__name__.replace("Scraper", "")
    try:
        jobs = await asyncio.wait_for(scraper.fetch_jobs(), timeout=600)
        logger.info(f"{name}: {len(jobs)} fetched")
        return name, jobs, None
    except Exception as e:
        logger.error(f"{name} failed: {e!r}")
        return name, [], repr(e)[:120]


async def main():
    from app.scrapers.freehire      import FreeHireScraper
    from app.scrapers.jobspy_source import JobSpyScraper
    from app.scrapers.jsearch       import JSearchScraper
    from app.scrapers.hn_hiring     import HNHiringScraper
    from app.scrapers.remote_boards import RemoteBoardsScraper
    from app.scrapers.adzuna        import AdzunaScraper
    from app.scrapers.remoteok      import RemoteOKScraper
    from app.scrapers.linkedin      import LinkedInScraper
    from app.matcher  import JobMatcher
    from app.notifier import EmailNotifier

    DOCS_DIR.mkdir(exist_ok=True)
    matcher = JobMatcher()

    existing_vikas  = load_existing(VIKAS_FILE)
    existing_diksha = load_existing(DIKSHA_FILE)

    # Re-score what's already saved with the current matcher; drop what no longer fits
    for store, who, minimum in ((existing_vikas, "vikas", V_MIN), (existing_diksha, "diksha", D_MIN)):
        for jid in list(store):
            if apply_fit(store[jid], matcher, who) < minimum:
                del store[jid]

    known_ids = set(existing_vikas) | set(existing_diksha)

    # Legal APIs first (reliable from GitHub's servers); HTML scrapers are best-effort
    scrapers = [
        FreeHireScraper(), JobSpyScraper(), JSearchScraper(), HNHiringScraper(),
        RemoteBoardsScraper(), AdzunaScraper(), RemoteOKScraper(), LinkedInScraper(),
    ]
    # Retired after months of 0 results from GitHub's servers (blocked / page changed):
    # indeed.py, glassdoor.py, naukri.py, shine.py, timesjobs.py, iimjobs.py — JobSpy covers
    # Indeed, Glassdoor and Naukri properly now. Files kept for reference.
    results = [await run_source(s) for s in scrapers]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    vikas_new, diksha_new = [], []
    sources = {}

    for name, jobs, error in results:
        kept = 0
        for job in jobs:
            if not job.get("job_id") or job["job_id"] in known_ids:
                continue
            job.setdefault("description", "")
            v = apply_fit(job, matcher, "vikas")
            d = apply_fit(job, matcher, "diksha")
            job["status"] = "new"
            job["scanned_date"] = today
            job["description"] = job["description"][:1500]  # keep the public JSON small
            if v >= V_MIN:
                existing_vikas[job["job_id"]] = job
                vikas_new.append(job)
            if d >= D_MIN:
                existing_diksha[job["job_id"]] = job
                diksha_new.append(job)
            if v >= V_MIN or d >= D_MIN:
                known_ids.add(job["job_id"])
                kept += 1
        sources[name] = {"fetched": len(jobs), "matched": kept, "error": error}

    vikas_sorted  = dedup_postings(existing_vikas.values(),  "vikas")[:MAX_JOBS]
    diksha_sorted = dedup_postings(existing_diksha.values(), "diksha")[:MAX_JOBS]

    VIKAS_FILE.write_text(json.dumps(vikas_sorted,  indent=2, ensure_ascii=False))
    DIKSHA_FILE.write_text(json.dumps(diksha_sorted, indent=2, ensure_ascii=False))

    stats = {
        "last_scan":        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "vikas_total":      len(vikas_sorted),
        "diksha_total":     len(diksha_sorted),
        "vikas_new_today":  len(vikas_new),
        "diksha_new_today": len(diksha_new),
        "sources":          sources,
        "platforms":        ", ".join(sources),
    }
    STATS_FILE.write_text(json.dumps(stats, indent=2))
    write_public_profiles()

    logger.info(f"Scan complete — Vikas: {len(vikas_new)} new | Diksha: {len(diksha_new)} new")
    for name, s in sources.items():
        logger.info(f"  {name:10} fetched={s['fetched']:4} matched={s['matched']:4} {s['error'] or ''}")

    EmailNotifier().send_daily_digest(vikas_new, diksha_new)


if __name__ == "__main__":
    asyncio.run(main())
