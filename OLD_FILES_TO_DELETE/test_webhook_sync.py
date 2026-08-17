"""
Webhook Live Google Sheets Synchronizer
Syncs local prospects and activity log live to Google Sheets via Webhook URL.
"""

import urllib.request
import urllib.parse
import json
import os

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbz5XbGbGrolMOEVzI3GK4aFstuXz4_lFuXd4QpExvN3OSjyukwdR-S8oRwHF0pB7EskAA/exec"

LOCAL_PROSPECTS = [
    {"name": "Ward Plumbing, Heating, and Air", "domain": "wardph.com", "niche": "Plumbing & HVAC", "score": 85, "grade": "B", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "White & Williams Co.", "domain": "whiteandwilliams.com", "niche": "Contracting & HVAC", "score": 36, "grade": "F", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "Asheville Electrician", "domain": "ashevilleelectrician.com", "niche": "Electrical Contractors", "score": 76, "grade": "B", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "Asheville Tree Service", "domain": "ashevilletreeservice.com", "niche": "Tree Care & Landscaping", "score": 85, "grade": "B", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "Baker Roofing", "domain": "bakerroofing.com", "niche": "Roofing Contractors", "score": 87, "grade": "B", "status": "G2 Approved / Outreach Dispatched"}
]

def sync_via_webhook():
    import requests
    print("=" * 70)
    print("  WEBHOOK LIVE GOOGLE SHEETS SYNCHRONIZER")
    print(f"  Target Webhook URL: {WEBHOOK_URL}")
    print("=" * 70)

    # 1. Sync Prospect Tracker tab
    payload_prospects = {
        "tab": "Prospect Tracker",
        "rows": LOCAL_PROSPECTS
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=payload_prospects, allow_redirects=True, timeout=15)
        print("\n[SUCCESS] Sync Prospect Tracker -> Webhook Response:", resp.text)
    except Exception as e:
        print("\n[ERROR] Prospect Tracker Webhook sync failed:", e)

    # 2. Sync Activity Log tab
    payload_log = {
        "tab": "Activity Log",
        "action": "Live Webhook Sync",
        "evidence": "Synced 5 G2 approved prospects & live outreach dispatches to online Google Sheet"
    }

    try:
        resp_log = requests.post(WEBHOOK_URL, json=payload_log, allow_redirects=True, timeout=15)
        print("[SUCCESS] Sync Activity Log -> Webhook Response:", resp_log.text)
    except Exception as e:
        print("[ERROR] Activity Log Webhook sync failed:", e)

    print("\n[COMPLETE] Webhook sync execution finished!")

if __name__ == "__main__":
    sync_via_webhook()
