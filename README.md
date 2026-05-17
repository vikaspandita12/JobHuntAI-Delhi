# JobHuntAI Delhi — Automated Job Discovery Platform

AI-powered job hunting assistant for **Vikas Pandita** (Cybersecurity) and **Diksha Koul** (Cloud Engineering) — targeting **Delhi NCR** roles.

## What it does

- **Daily 8 AM scan** — Naukri, LinkedIn, Indeed, Shine, TimesJobs, iimjobs for Delhi NCR jobs
- **Smart scoring** — ranks every job against each profile (0–100 match score)
- **Email digest** — sends ranked job list daily to both emails with direct Apply links
- **Cover letter AI** — generates tailored cover letters via Claude in seconds
- **Application tracker** — dashboard to track new / applied / skipped jobs

---

## Quick Start (2 commands, no Docker)

```bash
# 1. One-time setup
bash setup.sh

# 2. Edit your keys in .env (takes 1 minute)
nano .env

# 3. Start the app
bash start.sh
```

Then open **http://localhost:8000** in your browser.

---

## .env Configuration

```bash
# Anthropic API — for Claude cover letter generation
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Gmail SMTP — for daily email digests
# Use a Gmail App Password: myaccount.google.com/apppasswords
SMTP_USER=your.email@gmail.com
SMTP_PASS=your_gmail_app_password
```

That's it. Emails go to **vikaspandita1@gmail.com** and **dikshakoul88@gmail.com** automatically.

---

## Job Platforms Covered

| Platform | Vikas (Cybersecurity) | Diksha (Cloud) |
|----------|----------------------|----------------|
| Naukri   | 8 searches           | 8 searches     |
| LinkedIn | 6 searches           | 5 searches     |
| Indeed   | 5 searches           | 5 searches     |
| Shine    | 3 searches           | 3 searches     |
| TimesJobs| 5 searches           | 3 searches     |
| iimjobs  | 5 searches (IIM alumni tier) | 3 searches |

**Total: 60 search queries run every morning at 8 AM IST**

---

## Dashboard Features

- **Vikas tab** — cybersecurity roles sorted by match score
- **Diksha tab** — cloud engineering roles sorted by match score
- **Match score** (0–100) — green ≥80, amber ≥60, grey <60
- **View & Apply** — opens the job directly
- **Mark Applied** / **Skip** — tracks your pipeline
- **Cover Letter** — generates Claude-powered personalised letter
- **Scan Now** — manual trigger anytime
- **Send Email** — send digest immediately

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/` | Dashboard UI |
| GET  | `/jobs?profile=vikas` | Jobs for Vikas |
| GET  | `/jobs?profile=diksha` | Jobs for Diksha |
| POST | `/scan` | Trigger manual scan |
| GET  | `/cover-letter/{job_id}/{profile}` | Generate cover letter |
| POST | `/jobs/{job_id}/apply` | Mark as applied |
| POST | `/jobs/{job_id}/skip` | Skip job |
| POST | `/notify` | Send email digest now |
| GET  | `/stats` | Application statistics |
| GET  | `/docs` | Interactive API docs |

---

## Target Roles

### Vikas Pandita — Cybersecurity Leadership
- CISO, Head of Cybersecurity, VP Security, Director InfoSec, Security Architect
- 14+ years | Big 4 (Deloitte, KPMG, EY, TCS) | IOC Olympic Games | IIM Kozhikode

### Diksha Koul — Cloud Engineering
- Cloud Architect, Senior Cloud Engineer, Azure Engineer, DevOps Lead, Platform Engineer
- 7+ years | HCL Technologies, VOIS | Azure/AWS/Terraform | RHCSA 300/300

---

## System Requirements

- Python 3.10 or higher
- Internet connection
- Gmail account (for email digests)
- Anthropic API key (for cover letters — optional but recommended)

## Note on Automation

This tool **discovers jobs and prepares applications**. You apply with one click on the Apply link. Automated form-filling on LinkedIn/Naukri violates their ToS and risks account bans — especially harmful for senior roles where profile visibility matters.

---
*Built for Vikas Pandita & Diksha Koul — Pune → Delhi NCR relocation 2025*
