# AI Security Checklist — JobHuntAI-Delhi

Reference: [Awesome AI Security](https://github.com/vikaspandita12/awesome-ai-security)

**AI features:** Optional Anthropic cover letters · GitHub Actions daily scan

## Secrets (GitHub Actions)

- [ ] `JOB`, `DIKSHASECRET`, `ANTHROPIC_API_KEY` only in repo Secrets
- [ ] Workflows never echo secrets; job JSON in git has no credentials

## Anthropic usage

- [ ] Minimal prompt: job title, company, bullets — not full CV + email passwords
- [ ] [OWASP Top 10 for LLM](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

**Tracking issue:** #1
