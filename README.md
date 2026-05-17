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

## Setup (one time, 3 minutes on mobile)

1. **Settings → Secrets → Actions** — add `SMTP_USER`, `SMTP_PASS`, `ANTHROPIC_API_KEY`
2. **Settings → Pages** — source: branch `claude/compare-cursor-repos-E1qVk` / folder `/docs`
3. **Actions tab** — tap **Daily Job Scan → Run workflow** for the first run

That's it. The 8 AM IST cron will take over from tomorrow.
