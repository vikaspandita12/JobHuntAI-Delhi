# JobHuntAI Delhi

Automated job discovery for **Vikas Pandita** (Cybersecurity — CISO / Head of Security) and **Diksha Koul** (Cloud Engineering — Azure / AWS / DevOps), targeting **Delhi NCR** and remote roles open to India.

Runs entirely on GitHub: a scheduled GitHub Actions scan every day at **8:00 AM IST**, results on a mobile dashboard served by GitHub Pages. No laptop, no Docker.

**Dashboard:** https://vikaspandita12.github.io/JobHuntAI-Delhi/

## Job sources

| Source | What it covers | Type | Key needed | Code |
|---|---|---|---|---|
| **FreeHire** | Jobs read directly from company career pages (Greenhouse, Lever, Workday, Ashby…) plus Naukri, iimjobs, hirist listings | Public JSON API | No | `app/scrapers/freehire.py` |
| **JobSpy** | LinkedIn, Indeed India and Naukri in one call (its Glassdoor and Google Jobs scrapers are blocked from GitHub's servers, so they're off) | Open-source package | No | `app/scrapers/jobspy_source.py` |
| **JSearch** | Google for Jobs index — LinkedIn, Naukri, Indeed, Glassdoor, company sites | API (free tier ~200 calls/month) | `JSEARCH_API_KEY` (optional) | `app/scrapers/jsearch.py` |
| **Hacker News "Who is hiring?"** | Monthly startup hiring thread, filtered to India / remote-worldwide, with hiring emails | Algolia HN API | No | `app/scrapers/hn_hiring.py` |
| **Remotive, Jobicy, Himalayas** | Remote jobs with stated country eligibility | Public JSON APIs | No | `app/scrapers/remote_boards.py` |
| **RemoteOK** | Remote tech jobs | Public JSON API | No | `app/scrapers/remoteok.py` |
| **Adzuna India** | Aggregated Indian job boards | API | `ADZUNA` | `app/scrapers/adzuna.py` |
| **LinkedIn (guest pages)** | Public LinkedIn job search, past week | HTML | No | `app/scrapers/linkedin.py` |

Retired (blocked from GitHub's servers or page layout changed, 0 results for months): direct HTML scrapers for Indeed, Glassdoor, Naukri, Shine, TimesJobs and iimjobs. JobSpy now covers Indeed and Naukri; for Glassdoor listings add the optional JSearch key. The files stay in `app/scrapers/` for reference.

The dashboard's **⋯ → Sources in the last scan** shows how many jobs each source found and kept.

## Open-source projects and packages

| Project / package | Version | Used for | Licence |
|---|---|---|---|
| [JobSpy](https://github.com/speedyapply/JobSpy) (`python-jobspy`) | 1.4.1 | Multi-board scraping: LinkedIn, Indeed, Naukri | MIT |
| [Dossier](https://github.com/AienTech/dossier) | — | Design ideas only: explainable fit score with reasons / red flags / gaps, application board, "Write it with Claude" handoff, job sources (FreeHire, HN, JSearch, Adzuna). Re-implemented in Python/JS; no code copied | AGPL-3.0 |
| [httpx](https://github.com/encode/httpx) | 0.27.2 | Async HTTP for all API sources | BSD-3 |
| [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) + [lxml](https://lxml.de) | 4.12.3 / 5.3.0 | HTML parsing (LinkedIn guest pages) | MIT / BSD |
| [pandas](https://pandas.pydata.org) | via JobSpy | JobSpy's result table | BSD-3 |
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | 0.34.2 | Optional cover letters in the local server mode | MIT |
| FastAPI, uvicorn, APScheduler, Jinja2 | see `requirements.txt` | Optional local server mode (`start.sh`) — not used by the daily scan | MIT / BSD |

## How a scan works

1. `.github/workflows/daily_scan.yml` (on `main`) runs `python -m app.scan_runner` from the `claude/compare-cursor-repos-E1qVk` branch.
2. Every source is queried; each job is scored for both profiles by `app/matcher.py`: a 0–100 fit with a band (Excellent / Good / Possible / Poor), reasons, red flags (seniority mismatch, sales roles, location, country-locked remote) and **gaps** (what the posting asks for that the profile doesn't show).
3. Saved jobs are re-scored, the same posting from several sources is shown once, and the results are written to `docs/*.json`.
4. Both people get an email digest; the dashboard updates.

## Dashboard

- **Jobs:** search, filters, fit reasons, red flags and gaps per job.
- **Board:** Saved → Applied → Interview → Offer → Rejected, with notes and interview dates.
- **Insights:** funnel, applications per week, follow-ups due, upcoming interviews.
- **Resume:** base resume from the profile, 3 themes, Save as PDF.
- **✍️ Tailor / Interview prep / Follow-up email:** opens a new Claude chat with the posting and the profile, told to use only facts from the profile.

Tracking data (saved jobs, stages, notes) stays in the browser of the device you use; ⋯ → Export / Import moves it between devices.

## Secrets (Settings → Secrets and variables → Actions)

| Secret | Purpose |
|---|---|
| `JOB` | Gmail App Password for vikaspandita111@gmail.com (sends the digest) |
| `DIKSHASECRET` | Gmail App Password for dikshakoul88@gmail.com |
| `ADZUNA` | Adzuna API key (app id is public, set in code) |
| `JSEARCH_API_KEY` | Optional — RapidAPI key for JSearch |
| `ANTHROPIC_API_KEY` | Optional — local cover-letter mode only |

## Branches

- `main` — the scheduled workflow (GitHub only runs schedules from the default branch) and this README.
- `claude/compare-cursor-repos-E1qVk` — all code, scrapers, dashboard and data. GitHub Pages serves its `/docs` folder.
