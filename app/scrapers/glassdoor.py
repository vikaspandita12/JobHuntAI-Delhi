import asyncio
import hashlib
import logging
from typing import List, Dict
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.glassdoor.co.in/",
}

VIKAS_QUERIES  = ["CISO", "Chief Information Security Officer", "Head Cybersecurity",
                   "VP Cybersecurity", "Security Architect", "Director InfoSec"]
DIKSHA_QUERIES = ["Cloud Architect", "Azure Cloud Engineer", "DevOps Lead",
                   "Platform Engineer", "Senior Cloud Engineer"]

# Glassdoor location ID for Delhi NCR
DELHI_LOC_ID = "2940282"


class GlassdoorScraper:
    BASE = "https://www.glassdoor.co.in"

    async def fetch_jobs(self) -> List[Dict]:
        jobs = []
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=25, follow_redirects=True
        ) as client:
            for query in VIKAS_QUERIES + DIKSHA_QUERIES:
                try:
                    results = await self._search(client, query)
                    jobs.extend(results)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.warning(f"Glassdoor '{query}': {e}")
        return self._dedup(jobs)

    async def _search(self, client: httpx.AsyncClient, query: str) -> List[Dict]:
        url = f"{self.BASE}/Job/jobs.htm"
        params = {
            "suggestCount": "0",
            "suggestChosen": "false",
            "clickSource": "searchBtn",
            "typedKeyword": query,
            "sc.keyword": query,
            "locT": "C",
            "locId": DELHI_LOC_ID,
        }
        r = await client.get(url, params=params)
        if r.status_code in (403, 429, 503):
            logger.warning(f"Glassdoor blocked ({r.status_code}) for '{query}'")
            return []
        if r.status_code != 200:
            return []
        return self._parse(r.text, query)

    def _parse(self, html: str, query: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        selectors = [
            "li.react-job-listing",
            "article.JobCard",
            "[data-test='jobListing']",
            ".JobCard",
            "[id^='job-listing']",
        ]
        cards = []
        for sel in selectors:
            cards = soup.select(sel)
            if cards:
                break
        for card in cards[:8]:
            try:
                title = self._text(card, [
                    "[data-test='job-title']", "[class*='jobTitle']",
                    ".job-title", "a[class*='title']",
                ])
                company = self._text(card, [
                    "[data-test='employer-name']", "[class*='employerName']",
                    ".employer-name",
                ])
                location = self._text(card, [
                    "[data-test='emp-location']", "[class*='location']",
                    ".location",
                ]) or "Delhi NCR"
                link = card.select_one("a[href*='/job-listing/'], a[href*='/partner/'], a[href*='/Jobs/']")
                href = (link["href"] if link and link.get("href") else "") or ""
                url = href if href.startswith("http") else f"{self.BASE}{href}"
                if not title:
                    continue
                job_id = "gd_" + hashlib.md5(f"{title}{company}".encode()).hexdigest()[:10]
                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": "Not disclosed",
                    "posted_date": "Recent",
                    "url": url or f"{self.BASE}/Jobs/index.htm",
                    "source": "Glassdoor",
                    "description": f"{query} {title} {company}",
                })
            except Exception:
                continue
        return jobs

    def _text(self, card, selectors: list) -> str:
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return ""

    def _dedup(self, jobs: List[Dict]) -> List[Dict]:
        seen, out = set(), []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                out.append(j)
        return out
