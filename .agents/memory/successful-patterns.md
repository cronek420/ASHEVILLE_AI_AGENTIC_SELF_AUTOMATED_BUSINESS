# Proven Successful Execution Patterns

This repository contains verified, high-performing operational patterns, checklists, and templates.

## Pattern Index

1. [Single-Writer Command Center Sync](#1-single-writer-command-center-sync)
2. [Truthful Local Business Audit Checklist](#2-truthful-local-business-audit-checklist)
3. [G2 Outreach Payload Drafting Pattern](#3-g2-outreach-payload-drafting-pattern)

---

### 1. Single-Writer Command Center Sync

- **Applicability:** All state-changing operations targeting the Google Sheet Command Center.
- **Preconditions:** Active `run_id`, single active offer verified in `Start Here` tab, change packet validated against schema, secret redaction passed.
- **Execution Steps:**
  1. Specialist agent prepares structured change packet (read-only execution).
  2. Packet submitted to `Atlas-Orchestrator`.
  3. `Atlas-Orchestrator` verifies identity, evidence, and absence of external side effects.
  4. `Atlas-Orchestrator` acquires single-writer lock and applies changes to targeted spreadsheet tabs.
  5. Append entry to `Activity Log`.
- **Non-Applicability:** Specialist agents writing directly; unvalidated packets; actions lacking empirical evidence.

---

### 2. Truthful Local Business Audit Checklist

- **Applicability:** `Scout-Research` and `Proof-Builder` local business analysis for Asheville & Buncombe County, NC.
- **Preconditions:** Publicly accessible business URL or Google Maps listing.
- **Verification Checklist:**
  - [ ] Verify physical location in Asheville or Buncombe County, NC.
  - [ ] Check target name and contact against Do-Not-Contact (DNC) list.
  - [ ] Check target name against existing `Prospect Tracker` records (duplicate check).
  - [ ] Inspect mobile layout, menu links, SSL certificate, page load speed, and contact form functionality.
  - [ ] Document exact URL and observable defect (e.g., broken link, non-responsive viewport, missing local schema).
- **Non-Applicability:** Non-local prospects; estimated/assumed defects; unverified third-party claims.

---

### 3. G2 Outreach Payload Drafting Pattern

- **Applicability:** `Outreach-Drafter` preparing cold email/message drafts.
- **Preconditions:** Verified audit defect; approved active offer.
- **Structure:**
  - **Subject Line:** Short, friendly, interesting, and explicitly establishing Tom as a real local resident in Asheville (e.g. "Hey Its Tom from Asheville. Quick Question." or "Tom from Asheville, a quick question.re:your Website and your online presence."). Avoid automated/corporate robotic phrasing.
  - Factual, polite explanation of observed issue (with proof screenshot/link).
  - Clear value proposition tied to 48-Hour Optimization offer.
  - Explicit sender identity (Tom Gronek, Asheville resident Digital Reputation Strategist)
  - **No automated sending** — formatted as draft packet for Tom Gronek's G2 review.

---

### 4. Safe Gmail Deliverability & Anti-Spam Sending Pattern

- **Applicability:** All outbound email dispatches via Gmail SMTP (`smtp.gmail.com`).
- **Preconditions:** G2 explicit written approval for each recipient & payload; `SMTP_USER` and App Password loaded securely from `.env`.
- **Execution Checklist:**
  1. **Plain-Text Formatting:** Send purely as `text/plain` MIME type without HTML markup, tracking pixels, or rich text links.
  2. **Paced Pacing & Delay:** Insert 30 to 90 seconds of randomized delay between individual dispatches to simulate human typing and prevent bot signature detection.
  3. **Unique Personalization:** Include domain-specific factual findings (`load_time_ms`, missing viewport, missing H1) to ensure unique content hashes.
  4. **Humanized Headers:** Standardized `From: Tom Gronek <lexiconatlas@gmail.com>` and `Reply-To: lexiconatlas@gmail.com`.
  5. **Clear Opt-Out:** Footer must contain explicit, polite opt-out instructions ("Reply REMOVE at any time to be removed").
  6. **Daily Cap:** Max 20 cold outreach dispatches per 24-hour period for new/warming accounts.

---

