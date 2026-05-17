import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASS", "")
        self.vikas_email = os.getenv("VIKAS_EMAIL", "vikaspandita1@gmail.com")
        self.diksha_email = os.getenv("DIKSHA_EMAIL", "dikshakoul88@gmail.com")

    def send_daily_digest(self, vikas_jobs: List[Dict], diksha_jobs: List[Dict]):
        if not self.user or not self.password:
            logger.warning("SMTP not configured — skipping email digest")
            return

        today = datetime.today().strftime("%d %b %Y")

        if vikas_jobs:
            self._send(
                to=self.vikas_email,
                subject=f"JobHuntAI — {len(vikas_jobs)} new Delhi cybersecurity roles — {today}",
                html=self._build_html("Vikas", vikas_jobs, "vikas"),
            )

        if diksha_jobs:
            self._send(
                to=self.diksha_email,
                subject=f"JobHuntAI — {len(diksha_jobs)} new Delhi cloud engineering roles — {today}",
                html=self._build_html("Diksha", diksha_jobs, "diksha"),
            )

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
                </div>
                <div style="text-align:center;min-width:60px;">
                  <div style="background:{score_color};color:#fff;border-radius:50%;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:15px;margin:0 auto;">{score}</div>
                  <p style="margin:4px 0;font-size:11px;color:#6b7280;">Match</p>
                </div>
              </div>
              <div style="margin-top:12px;">
                <a href="{j.get('url','#')}" style="background:#1e3a5f;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;margin-right:8px;">View & Apply &rarr;</a>
                <a href="http://localhost:8000/cover-letter/{j.get('job_id','')}/{profile}" style="background:#f3f4f6;color:#374151;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;">Generate Cover Letter</a>
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
              <strong>{len(jobs)} new matching roles</strong> found across Naukri, LinkedIn, Indeed &amp; Shine &mdash; Delhi NCR
            </div>
            <div style="padding:8px 0;">{cards}</div>
            <div style="background:#f3f4f6;padding:16px;border-radius:0 0 12px 12px;text-align:center;font-size:12px;color:#9ca3af;">
              JobHuntAI &bull; Pune &rarr; Delhi Relocation 2025 &bull; <a href="http://localhost:8000" style="color:#6b7280;">Open Dashboard</a>
            </div>
          </div>
        </body></html>"""

    def _send(self, to: str, subject: str, html: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.user
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, to, msg.as_string())
            logger.info(f"Email sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
