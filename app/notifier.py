import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

DASHBOARD_URL = "https://vikaspandita12.github.io/JobHuntAI-Delhi/"


class EmailNotifier:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))

        # Vikas sends from vikaspandita111@gmail.com (secret: JOB)
        self.vikas_smtp_user = os.getenv("VIKAS_SMTP_USER", "")
        self.vikas_smtp_pass = os.getenv("VIKAS_SMTP_PASS", "")
        self.vikas_email     = os.getenv("VIKAS_EMAIL", "vikaspandita1@gmail.com")

        # Diksha sends from dikshakoul88@gmail.com (secret: DIKSHASECRET)
        self.diksha_smtp_user = os.getenv("DIKSHA_SMTP_USER", "")
        self.diksha_smtp_pass = os.getenv("DIKSHA_SMTP_PASS", "")
        self.diksha_email     = os.getenv("DIKSHA_EMAIL", "dikshakoul88@gmail.com")

    def send_daily_digest(self, vikas_jobs: List[Dict], diksha_jobs: List[Dict]):
        today = datetime.today().strftime("%d %b %Y")
        senders = [(self.vikas_smtp_user, self.vikas_smtp_pass), (self.diksha_smtp_user, self.diksha_smtp_pass)]
        senders = [(u, p) for u, p in senders if u and p]
        if not senders:
            logger.warning("No SMTP credentials set (secrets JOB / DIKSHASECRET) — skipping email")
            return

        if vikas_jobs:
            self._send_any(senders, self.vikas_email,
                           f"JobHuntAI — {len(vikas_jobs)} new Delhi cybersecurity roles — {today}",
                           self._build_html("Vikas", vikas_jobs, "vikas"))
        if diksha_jobs:
            # Her own address first; if Gmail rejects it, send from Vikas's account instead
            self._send_any(list(reversed(senders)), self.diksha_email,
                           f"JobHuntAI — {len(diksha_jobs)} new Delhi cloud engineering roles — {today}",
                           self._build_html("Diksha", diksha_jobs, "diksha"))

    def _send_any(self, senders, to: str, subject: str, html: str) -> bool:
        for user, password in senders:
            if self._send(user, password, to, subject, html):
                return True
        logger.error(f"Every sender failed for {to} — regenerate the Gmail App Password secrets")
        return False

    def _build_html(self, name: str, jobs: List[Dict], profile: str) -> str:
        score_key = f"{profile}_score"
        today = datetime.today().strftime("%d %b %Y")
        cards = ""
        for j in jobs[:20]:
            score = j.get(score_key, 0)
            score_color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#6b7280"
            cards += f"""
            <div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px;margin:12px 0;background:#fff;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <h3 style="margin:0 0 4px;color:#1e3a5f;font-size:16px;">{j.get('title','')}</h3>
                  <p style="margin:0;color:#374151;font-weight:600;">{j.get('company','')}</p>
                  <p style="margin:4px 0;color:#6b7280;font-size:13px;">{j.get('location','')} &bull; {j.get('source','')} &bull; {j.get('salary','Not disclosed')}</p>
                  <p style="margin:4px 0;color:#9ca3af;font-size:12px;">Posted: {j.get('posted_date','Recent')}</p>
                  <p style="margin:6px 0 0;color:#166534;font-size:12px;">{'<br>'.join('✓ ' + r for r in (j.get(f'{profile}_fit') or {}).get('reasons', [])[:2])}</p>
                  <p style="margin:2px 0 0;color:#b45309;font-size:12px;">{'<br>'.join('⚠ ' + r for r in (j.get(f'{profile}_fit') or {}).get('red_flags', [])[:2])}</p>
                </div>
                <div style="text-align:center;min-width:60px;">
                  <div style="background:{score_color};color:#fff;border-radius:50%;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:15px;margin:0 auto;">{score}</div>
                  <p style="margin:4px 0;font-size:11px;color:#6b7280;">Match</p>
                </div>
              </div>
              <div style="margin-top:12px;">
                <a href="{j.get('url','#')}" style="background:#1e3a5f;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;margin-right:8px;">View &amp; Apply &rarr;</a>
                <a href="{DASHBOARD_URL}" style="background:#f3f4f6;color:#374151;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;">Open Dashboard</a>
              </div>
            </div>"""

        return f"""
        <html><head><meta charset="UTF-8"></head>
        <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f9fafb;padding:20px;">
          <div style="max-width:680px;margin:0 auto;">
            <div style="background:#1e3a5f;color:#fff;padding:24px;border-radius:12px 12px 0 0;">
              <h1 style="margin:0;font-size:22px;">JobHuntAI Delhi</h1>
              <p style="margin:6px 0 0;opacity:0.8;">Hi {name}! Your daily job digest &mdash; {today}</p>
            </div>
            <div style="background:#e8f0fe;padding:14px 24px;">
              <strong>{len(jobs)} new matching roles</strong> found across company career pages, LinkedIn, HN, RemoteOK and more &mdash; Delhi NCR
            </div>
            <div style="padding:8px 0;">{cards}</div>
            <div style="background:#f3f4f6;padding:16px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#9ca3af;">
              JobHuntAI &bull; Pune &rarr; Delhi NCR Relocation &bull; <a href="{DASHBOARD_URL}" style="color:#6b7280;">Open Mobile Dashboard</a>
            </div>
          </div>
        </body></html>"""

    def _send(self, smtp_user: str, smtp_pass: str, to: str, subject: str, html: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to, msg.as_string())
            logger.info(f"Email sent to {to} from {smtp_user}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to} from {smtp_user}: {e}")
            return False
