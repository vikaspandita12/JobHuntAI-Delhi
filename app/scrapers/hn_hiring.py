"""Hacker News monthly "Ask HN: Who is hiring?" — startups that hire in India or
remotely worldwide, often with a direct hiring email. Uses the public Algolia
HN API. Idea borrowed from Dossier (github.com/AienTech/dossier)."""
import html
import logging
import re
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

SEARCH = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=10"
ITEM = "https://hn.algolia.com/api/v1/items/{id}"

# Where the candidate can work from: Delhi NCR / India, or remote with no country lock
PLACE_OK = re.compile(
    r"\b(delhi|ncr|gurgaon|gurugram|noida|india|apac|asia)\b"
    r"|remote\s*\(?\s*(worldwide|global|anywhere|international|apac|asia|india)",
    re.I,
)
ROLE_OK = re.compile(
    r"\b(ciso|security|infosec|cyber|devsecops|cloud|devops|sre|site reliability|"
    r"platform engineer|infrastructure|azure|aws|kubernetes|terraform)\b",
    re.I,
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LINK = re.compile(r"https?://[^\s<>\"')]+")


class HNHiringScraper:
    async def fetch_jobs(self) -> List[Dict]:
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "JobHuntAI/1.0"}) as client:
            r = await client.get(SEARCH)
            hits = [h for h in r.json().get("hits", []) if "who is hiring" in (h.get("title") or "").lower()]
            if not hits:
                return []
            thread = hits[0]
            r = await client.get(ITEM.format(id=thread["objectID"]))
            posts = r.json().get("children", [])

        jobs: List[Dict] = []
        for p in posts:
            raw = p.get("text") or ""
            text = _plain(raw)
            first_line = text.split("\n", 1)[0]
            if not PLACE_OK.search(first_line) or not ROLE_OK.search(text):
                continue
            parts = [s.strip() for s in first_line.split("|") if s.strip()]
            company = parts[0][:80] if parts else "Startup"
            role = next((s for s in parts[1:] if ROLE_OK.search(s)), None) or (parts[1] if len(parts) > 1 else first_line)
            place = next((s for s in parts if PLACE_OK.search(s)), "Remote")
            emails = sorted(set(e for e in EMAIL.findall(text) if not e.endswith((".png", ".jpg"))))[:2]
            links = [u for u in LINK.findall(html.unescape(raw)) if "ycombinator.com" not in u]
            jobs.append({
                "job_id": f"hn_{p.get('id')}",
                "title": role[:140],
                "company": company,
                "location": place[:80],
                "salary": next((s for s in parts if re.search(r"[$€£₹]\s?\d", s)), "Not disclosed"),
                "posted_date": (p.get("created_at") or "")[:10] or "Recent",
                "url": links[0] if links else f"https://news.ycombinator.com/item?id={p.get('id')}",
                "hn_url": f"https://news.ycombinator.com/item?id={p.get('id')}",
                "apply_email": emails[0] if emails else "",
                "source": "HN Who's Hiring",
                "description": text[:6000],
            })
        return jobs


def _plain(raw: str) -> str:
    t = re.sub(r"<p>", "\n", raw)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).strip()
