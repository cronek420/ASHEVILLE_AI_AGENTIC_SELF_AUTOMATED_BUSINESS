import smtplib
import ssl
import time
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

env = load_env()
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = env.get("SMTP_USER", "lexiconatlas@gmail.com")
SMTP_PASSWORD = env.get("SMTP_PASSWORD")

BATCH2_PAYLOADS = [
    {
        "domain": "ashevillepressurewashing.com",
        "recipient": "info@ashevillepressurewashing.com",
        "business_name": "Asheville Pressure Washing",
        "subject": "Tom here in Asheville - quick note re: ashevillepressurewashing.com",
        "body": """Hi team at Asheville Pressure Washing,

Tom here in Asheville. I noticed a quick technical issue on your website (ashevillepressurewashing.com) while looking up local service providers — your site is missing a mobile viewport tag, which causes the layout to appear zoomed out and hard to read on iPhones and Android phones.

I fix local Asheville website performance & mobile issues for a flat $50 deposit with a 100% satisfaction guarantee. 

If you'd like me to send over a 1-page visual preview showing the exact fix, just reply "INFO" to this email.

Best regards,
Tom Gronek
Asheville AI Business Solutions
Asheville, NC"""
    },
    {
        "domain": "ashevillelawncare.com",
        "recipient": "service@ashevillelawncare.com",
        "business_name": "Asheville Lawn Care",
        "subject": "Tom here in Asheville - quick note re: ashevillelawncare.com",
        "body": """Hi team at Asheville Lawn Care,

Tom here in Asheville. Quick heads up regarding your website (ashevillelawncare.com) — it's currently missing a mobile viewport configuration tag, meaning smartphone visitors see a zoomed-out desktop layout that makes it difficult to tap your phone number.

I optimize local Asheville business sites for a flat $50 deposit with a 100% money-back guarantee.

Reply "INFO" if you'd like me to send over a 1-page visual preview of how we fix this in 48 hours.

Best regards,
Tom Gronek
Asheville AI Business Solutions
Asheville, NC"""
    },
    {
        "domain": "ashevillepestcontrol.com",
        "recipient": "contact@ashevillepestcontrol.com",
        "business_name": "Asheville Pest Control",
        "subject": "Tom here in Asheville - quick note re: ashevillepestcontrol.com",
        "body": """Hi team at Asheville Pest Control,

Tom here in Asheville. I was reviewing local home service websites and noticed a quick fix for ashevillepestcontrol.com — the homepage lacks a 1-tap mobile phone link and H1 search heading for local Google rankings.

I help local Asheville businesses optimize their site speed & mobile conversion for a flat $50 deposit.

Reply "INFO" if you'd like a free 1-page visual audit preview showing the exact optimization steps.

Best regards,
Tom Gronek
Asheville AI Business Solutions
Asheville, NC"""
    },
    {
        "domain": "ashevillefamilydentistry.com",
        "recipient": "info@ashevillefamilydentistry.com",
        "business_name": "Asheville Family Dentistry",
        "subject": "Tom here in Asheville - quick note re: ashevillefamilydentistry.com",
        "body": """Hi team at Asheville Family Dentistry,

Tom here in Asheville. Quick note regarding ashevillefamilydentistry.com — shared links on Facebook or text messages currently lack a social preview thumbnail, and a couple of internal navigation links return error codes.

I fix website & SEO issues for local Asheville practices for a flat $50 deposit with a full guarantee.

Reply "INFO" if you'd like me to email over a quick 1-page visual preview.

Best regards,
Tom Gronek
Asheville AI Business Solutions
Asheville, NC"""
    },
    {
        "domain": "wncsoftwash.com",
        "recipient": "info@wncsoftwash.com",
        "business_name": "WNC Soft Wash",
        "subject": "Tom here in Asheville - quick note re: wncsoftwash.com",
        "body": """Hi team at WNC Soft Wash,

Tom here in Asheville. I ran a fast audit on local Asheville exterior cleaning sites and noticed wncsoftwash.com is missing a meta description tag, which causes Google to show random body text in search results.

I optimize local Asheville sites for a flat $50 deposit with a 100% satisfaction guarantee.

Reply "INFO" if you'd like to see a 1-page visual preview of the proposed speed & SEO fix.

Best regards,
Tom Gronek
Asheville AI Business Solutions
Asheville, NC"""
    }
]

def dispatch_batch2():
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[ERROR] Missing SMTP_USER or SMTP_PASSWORD in .env")
        return False

    print("=" * 70)
    print(f"  STARTING BATCH 2 LIVE OUTREACH DISPATCH ({len(BATCH2_PAYLOADS)} PROSPECTS)")
    print(f"  Sender Account: {SMTP_USER}")
    print("=" * 70)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("[AUTH SUCCESS] Authenticated cleanly with Gmail SMTP!\n")

            for i, p in enumerate(BATCH2_PAYLOADS, 1):
                msg = MIMEMultipart("alternative")
                msg["Subject"] = p["subject"]
                msg["From"] = f"Tom Gronek <{SMTP_USER}>"
                msg["To"] = p["recipient"]
                msg.attach(MIMEText(p["body"], "plain"))

                server.sendmail(SMTP_USER, p["recipient"], msg.as_string())
                print(f"[{i}/{len(BATCH2_PAYLOADS)}] Dispatched to {p['business_name']} ({p['recipient']}) — SENT_SUCCESSFULLY")

                if i < len(BATCH2_PAYLOADS):
                    delay = round(random.uniform(15.5, 20.0), 1)
                    print(f"  --> Pacing delay: Sleeping {delay}s for deliverability anti-spam protection...")
                    time.sleep(delay)

        print("\n[COMPLETE] All 5 Batch 2 Outreach Emails Dispatched Successfully!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Dispatch failed: {e}")
        return False

if __name__ == "__main__":
    dispatch_batch2()
