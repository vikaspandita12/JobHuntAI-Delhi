import asyncio
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")


class JobScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=IST)

    def start(self):
        hour   = int(os.getenv("SCAN_CRON_HOUR",   "8"))
        minute = int(os.getenv("SCAN_CRON_MINUTE",  "0"))
        self.scheduler.add_job(
            self._run,
            CronTrigger(hour=hour, minute=minute, timezone=IST),
            id="daily_scan",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info(f"Scheduler started — daily scan at {hour:02d}:{minute:02d} IST across 6 platforms")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _run(self):
        logger.info("Daily job scan triggered by scheduler")
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_scan_and_notify())
        finally:
            loop.close()


async def _scan_and_notify():
    from app.scrapers.naukri    import NaukriScraper
    from app.scrapers.linkedin  import LinkedInScraper
    from app.scrapers.indeed    import IndeedScraper
    from app.scrapers.shine     import ShineScraper
    from app.scrapers.timesjobs import TimesJobsScraper
    from app.scrapers.iimjobs   import IIMJobsScraper
    from app.matcher   import JobMatcher
    from app.database  import Database
    from app.notifier  import EmailNotifier

    db       = Database()
    matcher  = JobMatcher()
    notifier = EmailNotifier()

    scrapers = [
        NaukriScraper(),
        LinkedInScraper(),
        IndeedScraper(),
        ShineScraper(),
        TimesJobsScraper(),
        IIMJobsScraper(),
    ]

    all_jobs = []
    for scraper in scrapers:
        try:
            jobs = await scraper.fetch_jobs()
            all_jobs.extend(jobs)
            logger.info(f"{scraper.__class__.__name__}: {len(jobs)} jobs fetched")
        except Exception as e:
            logger.error(f"{scraper.__class__.__name__} failed: {e}")

    v_min = int(os.getenv("VIKAS_MIN_SCORE",  "60"))
    d_min = int(os.getenv("DIKSHA_MIN_SCORE", "50"))

    new_count   = 0
    vikas_new   = []
    diksha_new  = []

    for job in all_jobs:
        if not db.job_exists(job["job_id"]):
            scores = matcher.score_job(job)
            job["vikas_score"]     = scores["vikas"]
            job["diksha_score"]    = scores["diksha"]
            job["primary_profile"] = "vikas" if scores["vikas"] >= scores["diksha"] else "diksha"
            db.save_job(job)
            new_count += 1
            if scores["vikas"]  >= v_min:
                vikas_new.append(job)
            if scores["diksha"] >= d_min:
                diksha_new.append(job)

    logger.info(
        f"Scan complete: {new_count} new jobs | "
        f"Vikas: {len(vikas_new)} matches | Diksha: {len(diksha_new)} matches"
    )
    notifier.send_daily_digest(vikas_new, diksha_new)
