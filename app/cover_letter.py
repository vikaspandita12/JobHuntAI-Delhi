import os
import logging
from typing import Dict

import anthropic

from app.profiles.vikas import VIKAS_PROFILE
from app.profiles.diksha import DIKSHA_PROFILE

logger = logging.getLogger(__name__)

PROFILES = {"vikas": VIKAS_PROFILE, "diksha": DIKSHA_PROFILE}


class CoverLetterGenerator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def generate(self, job: Dict, profile_name: str) -> str:
        if not self.client:
            return self._fallback(job, profile_name)

        profile = PROFILES.get(profile_name, VIKAS_PROFILE)
        achievements = "\n".join(f"- {a}" for a in profile["key_achievements"][:5])
        skills_top = ", ".join(profile["key_skills"][:12])
        certs_top = ", ".join(profile["certifications"][:4])

        prompt = f"""Write a professional, compelling cover letter for this job application. Be specific, not generic.

APPLICANT:
- Name: {profile['name']}
- Current Role: {profile['current_role']} at {profile['current_company']}
- Experience: {profile['years_experience']}+ years
- Education: {' | '.join(profile['education'])}
- Key Certifications: {certs_top}
- Top Skills: {skills_top}
- Key Achievements:
{achievements}
- Note: {profile['relocation_note']}

JOB:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- Location: {job.get('location', 'Delhi NCR')}
- Description: {str(job.get('description', ''))[:800]}
- Salary: {job.get('salary', 'Not specified')}
- Source: {job.get('source', 'N/A')}

Write a 3-paragraph cover letter:
1. Strong opening — name the specific role and company, lead with the most impressive credential or achievement relevant to this role.
2. 2-3 specific achievements with metrics that directly match this job's requirements.
3. Confident closing — mention Delhi relocation readiness, express genuine interest, clear call to action.

Rules: Under 350 words. No clichés ("I am writing to apply", "passionate", "team player"). Confident, executive tone. First person."""

        try:
            msg = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            return self._fallback(job, profile_name)

    def _fallback(self, job: Dict, profile_name: str) -> str:
        profile = PROFILES.get(profile_name, VIKAS_PROFILE)
        return (
            f"Dear Hiring Manager,\n\n"
            f"I am {profile['name']}, currently serving as {profile['current_role']} at "
            f"{profile['current_company']} with {profile['years_experience']}+ years of experience. "
            f"I am writing to express my strong interest in the {job.get('title', 'role')} position at {job.get('company', 'your organisation')}.\n\n"
            f"[Add ANTHROPIC_API_KEY to .env to auto-generate a personalised cover letter using Claude AI]\n\n"
            f"Best regards,\n{profile['name']}\n{profile['email']} | {profile['phone']}"
        )
