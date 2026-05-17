# JobHuntAI Delhi — Automated Job Discovery Platform

AI-powered job hunting assistant for **Vikas Pandita** (Cybersecurity) and **Diksha Koul** (Cloud Engineering) — targeting **Delhi NCR** roles.

## What it does

- **Daily 8 AM scan** — Naukri, LinkedIn, Indeed, Shine for Delhi NCR jobs
- **Smart scoring** — ranks each job against each profile using keyword + skill matching
- **Email digest** — sends ranked job list daily to both emails with direct Apply links
- **Cover letter AI** — generates tailored cover letters via Claude in seconds
- **Application tracker** — dashboard to track what's new / applied / skipped

## Quick Start (Docker)

```bash
git clone https://github.com/vikaspandita12/pentestai
cd pentestai
cp .env.example .env
# Fill in your API keys in .env
docker-compose up --build -d
# Dashboard: http://localhost:8000
# API:       http://localhost:8000/docs
```

## Manual Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
ANTHROPIC_API_KEY=sk-ant-...      # For cover letter generation
SMTP_USER=your@gmail.com          # Gmail for sending digests
SMTP_PASS=your_app_password       # Gmail App Password (not your login password)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard UI |
| GET | `/jobs?profile=vikas` | List jobs for Vikas |
| GET | `/jobs?profile=diksha` | List jobs for Diksha |
| POST | `/scan` | Trigger manual job scan |
| GET | `/cover-letter/{job_id}/{profile}` | Generate cover letter |
| POST | `/jobs/{job_id}/apply` | Mark job as applied |
| POST | `/jobs/{job_id}/skip` | Skip job |
| GET | `/stats` | Application statistics |
| POST | `/notify` | Send email digest now |

## Target Roles

### Vikas Pandita — Cybersecurity
- CISO, Head of Cybersecurity, VP Security, Security Architect
- 14+ years | Big 4 | IOC Olympic Games | IIM Kozhikode
- Platforms: Naukri, LinkedIn, Indeed, Shine — Delhi NCR

### Diksha Koul — Cloud Engineering
- Cloud Architect, Senior Cloud Engineer, Azure Engineer, DevOps
- 7+ years | HCL, VOIS | Azure/AWS/Terraform
- Platforms: Naukri, LinkedIn, Indeed, Shine — Delhi NCR

## Note on Automation

This tool **discovers jobs and prepares applications**. Final submission is manual (one click on the Apply link) — this is intentional. Automated form-filling on LinkedIn/Naukri violates their ToS and triggers account bans. Personalised manual applications get significantly higher response rates.

## Author
Built for Vikas Pandita & Diksha Koul — Pune → Delhi relocation 2025
