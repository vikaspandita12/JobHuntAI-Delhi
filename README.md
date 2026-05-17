# JobHuntAI Delhi

Automated job discovery for **Vikas Pandita** (Cybersecurity — CISO / Head of Security roles) and **Diksha Koul** (Cloud Engineering — Azure / AWS / DevOps) — targeting **Delhi NCR**.

Runs entirely on GitHub. No laptop, no Docker, no local install.

## How it works

- **Daily 8 AM IST**: GitHub Actions runs `python -m app.scan_runner` automatically
- Scrapes **Naukri, LinkedIn, Indeed, Shine, TimesJobs, iimjobs** for Delhi NCR jobs
- Scores every job against both CVs
- Emails ranked digest to `vikaspandita1@gmail.com` and `dikshakoul88@gmail.com`
- Updates the mobile dashboard at the GitHub Pages URL

## Branches

- `main` — holds only the workflow file (needed for scheduled runs)
- `claude/compare-cursor-repos-E1qVk` — all the code, scrapers, dashboard, data

## Mobile Dashboard

`https://vikaspandita12.github.io/JobHuntAI-Delhi/`

## GitHub Secrets required

| Secret name | What it is |
|---|---|
| `JOB` | Vikas's Gmail App Password (vikaspandita111@gmail.com) |
| `DIKSHASECRET` | Diksha's Gmail App Password (dikshakoul88@gmail.com) |
| `ANTHROPIC_API_KEY` | Optional — for AI cover letters |

## Setup (one time, on mobile)

1. **Settings → Secrets → Actions** — add `JOB`, `DIKSHASECRET` (done ✓)
2. **Settings → Pages** — source: branch `claude/compare-cursor-repos-E1qVk` / folder `/docs`
3. **Actions tab** — tap **Daily Job Scan → Run workflow** for the first run

From tomorrow the 8 AM IST cron runs automatically every day.
