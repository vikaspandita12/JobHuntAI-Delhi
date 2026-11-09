"""Explainable job-fit scoring, modelled on Dossier's posting score
(github.com/AienTech/dossier): a 0–100 score, a band, the reasons behind it and
red flags. Rule-based (no API cost) and judged only on what the posting and
the profile show — it never assumes experience the profile doesn't have."""
import re
from typing import Dict, List

from app.profiles.diksha import DIKSHA_PROFILE
from app.profiles.vikas import VIKAS_PROFILE

DELHI = re.compile(r"\b(delhi|ncr|noida|gurgaon|gurugram|faridabad|ghaziabad|manesar)\b", re.I)
INDIA = re.compile(r"\b(india|bengaluru|bangalore|mumbai|pune|hyderabad|chennai|kolkata|ahmedabad|jaipur|chandigarh|kochi|indore)\b", re.I)
REMOTE = re.compile(r"\b(remote|work from home|wfh|anywhere|worldwide|virtual)\b", re.I)
REMOTE_LOCKED = re.compile(r"\b(united states|usa|\bus\b|canada|uk|united kingdom|europe|emea|eu only|germany|australia)\b", re.I)

# Roles that only mention security/cloud but aren't the job either person does
WRONG_FUNCTION = re.compile(
    r"\b(sales|account (executive|manager)|business development|bdm|marketing|recruit\w*|"
    r"talent acquisition|customer success|teacher|trainer|tutor|content writer|copywriter)\b", re.I)
JUNIOR = re.compile(r"\b(intern|internship|trainee|fresher|graduate|junior|jr\.?|entry[- ]level|associate)\b", re.I)

PROFILE_RULES = {
    "vikas": {
        "profile": VIKAS_PROFILE,
        "family": re.compile(r"\b(security|cyber|infosec|ciso|grc|risk|soc|devsecops|zero trust)\b", re.I),
        "level_good": re.compile(r"\b(chief|ciso|head|director|vp|vice president|principal|global|group|regional)\b", re.I),
        "level_ok": re.compile(r"\b(architect|lead|senior|sr\.?|manager)\b", re.I),
        "too_low": "This reads as an individual-contributor role well below 14 years of security leadership.",
    },
    "diksha": {
        "profile": DIKSHA_PROFILE,
        "family": re.compile(r"\b(cloud|devops|azure|aws|gcp|platform|sre|site reliability|infrastructure|migration|kubernetes|terraform)\b", re.I),
        "level_good": re.compile(r"\b(senior|sr\.?|lead|architect|manager|deputy manager|staff|specialist)\b", re.I),
        "level_ok": re.compile(r"\b(engineer|consultant|administrator)\b", re.I),
        "too_high": re.compile(r"\b(chief|vp|vice president|head of|director)\b", re.I),
        "too_low": "This looks junior for 7+ years of cloud engineering.",
    },
}


def band(score: int) -> str:
    if score >= 85:
        return "Excellent fit"
    if score >= 70:
        return "Good fit"
    if score >= 50:
        return "Possible fit"
    return "Poor fit"


class JobMatcher:
    def score_job(self, job: Dict) -> Dict[str, int]:
        """Back-compatible: {'vikas': n, 'diksha': n}."""
        return {p: self.fit(job, p)["score"] for p in PROFILE_RULES}

    def fit(self, job: Dict, who: str) -> Dict:
        rules = PROFILE_RULES[who]
        prof = rules["profile"]
        title = job.get("title", "") or ""
        desc = job.get("description", "") or ""
        text = f"{title} {desc}"
        location = job.get("location", "") or ""
        reasons: List[str] = []
        flags: List[str] = []
        score = 0.0
        cap = 100.0  # ceilings applied last, so no bonus can lift a mismatch

        # 1. Role — the title carries the most weight (Dossier: skills & requirements first)
        squash = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())  # "Cyber Security" == "Cybersecurity"
        exact = next((t for t in prof["target_titles"] if squash(t) in squash(title)
                      and (len(squash(t)) > 4 or re.search(rf"\b{re.escape(t)}\b", title, re.I))), None)
        if exact:
            score += 50
            reasons.append(f"Title matches a target role: “{exact}”.")
        elif rules["family"].search(title):
            score += 32
            if rules["level_good"].search(title):
                score += 10  # e.g. "Head of Security", "Director, Cloud Platform"
            reasons.append(f"Title is in the right field ({rules['family'].search(title).group(0)}).")
        elif rules["family"].search(desc):
            score += 12
        else:
            flags.append("The posting isn't about this field.")

        if WRONG_FUNCTION.search(title):
            cap = min(cap, 25)
            flags.append(f"A sales/business-side role (“{WRONG_FUNCTION.search(title).group(0)}”), not hands-on {('security leadership' if who == 'vikas' else 'cloud engineering')}.")

        # 2. Seniority, both directions (Dossier: a role well below is as much a mismatch as one above)
        if JUNIOR.search(title):
            cap = min(cap, 45)
            flags.append(rules["too_low"])
        elif rules["level_good"].search(title):
            score += 15
            reasons.append(f"Seniority fits ({rules['level_good'].search(title).group(0)}).")
        elif rules["level_ok"].search(title):
            score += 8
        elif who == "vikas" and score >= 30:
            cap = min(cap, 65)
            flags.append(rules["too_low"])
        if who == "diksha" and rules["too_high"].search(title):
            score -= 10
            flags.append("A stretch: the title is a step or two above Deputy Manager.")

        # 3. Skills from the profile that the posting names
        skills = [s for s in prof["key_skills"] if re.search(rf"(?<![\w]){re.escape(s)}(?![\w])", text, re.I)]
        skills = list(dict.fromkeys(skills))
        if skills:
            score += min(len(skills) * 3, 20)
            reasons.append("Posting asks for skills in the profile: " + ", ".join(skills[:5]) + ".")
        kws = sum(1 for k in prof["target_keywords"] if re.search(rf"\b{re.escape(k)}\b", text, re.I))
        score += min(kws * 2, 10)

        # 4. Location — they're moving to Delhi NCR
        if DELHI.search(location):
            score += 10
            reasons.append(f"Based in Delhi NCR ({location}).")
        elif REMOTE.search(location):
            if REMOTE_LOCKED.search(location):
                score *= 0.4
                flags.append(f"Remote, but tied to {REMOTE_LOCKED.search(location).group(0)}: check whether India is allowed.")
            else:
                score += 5
                reasons.append("Remote: workable from Delhi.")
        elif INDIA.search(location):
            score *= 0.6
            flags.append(f"In {location}, not Delhi NCR.")
        elif location.strip():
            score *= 0.3
            flags.append(f"Outside India ({location}); would need a work permit.")

        if not desc.strip():
            reasons.append("Only the title was available; open the posting to confirm.")

        s = int(max(0, min(cap, round(score))))
        return {"score": s, "band": band(s), "reasons": reasons[:4], "red_flags": flags[:3]}
