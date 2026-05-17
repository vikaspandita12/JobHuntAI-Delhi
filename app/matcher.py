from typing import Dict
from app.profiles.vikas import VIKAS_PROFILE
from app.profiles.diksha import DIKSHA_PROFILE

DELHI_TERMS = {
    "delhi", "ncr", "noida", "gurgaon", "gurugram",
    "faridabad", "ghaziabad", "greater noida", "manesar",
}

REMOTE_TERMS = {
    "remote", "work from home", "wfh", "anywhere", "worldwide",
    "india ok", "remote (india",
}


class JobMatcher:
    def score_job(self, job: Dict) -> Dict[str, int]:
        text = " ".join([
            job.get("title", ""),
            job.get("description", ""),
            job.get("company", ""),
        ]).lower()

        location = job.get("location", "").lower()
        is_delhi  = any(t in location for t in DELHI_TERMS) or not location.strip()
        is_remote = any(t in location for t in REMOTE_TERMS)
        # Remote jobs score at full weight (can work from Delhi)
        # Non-Delhi, non-remote jobs get 0.2x penalty
        location_factor = 1.0 if (is_delhi or is_remote) else 0.2

        vikas_raw  = self._score_profile(text, VIKAS_PROFILE)
        diksha_raw = self._score_profile(text, DIKSHA_PROFILE)

        return {
            "vikas":  int(min(vikas_raw  * location_factor, 100)),
            "diksha": int(min(diksha_raw * location_factor, 100)),
        }

    def _score_profile(self, text: str, profile: Dict) -> float:
        score = 0.0

        # Title match — highest weight (40 pts)
        for t in profile["target_titles"]:
            if t.lower() in text:
                score += 40
                break

        # Keyword match — up to 35 pts
        hits = sum(1 for kw in profile["target_keywords"] if kw.lower() in text)
        score += min(hits * 4, 35)

        # Skill match — up to 25 pts
        skill_hits = sum(1 for sk in profile["key_skills"] if sk.lower() in text)
        score += min(skill_hits * 2, 25)

        return score
