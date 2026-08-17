"""
G3 Proposal & $50 Deposit Engine for Asheville AI Agentic Business.
Generates personalized, high-converting 1-page client proposals and deposit payment payloads.
Enforces G3 approval governance prior to customer delivery.
"""

import os
import json
import datetime
from typing import Dict, Any

import os
import json
import datetime
from typing import Dict, Any

# Map of the 7 Idea Library products
PRODUCTS = {
    "IDEA-01": {
        "name": "24-Hour Mobile Booking-Page Rescue",
        "total": 149,
        "deposit": 75,
        "desc": "mobile booking page rescue"
    },
    "IDEA-02": {
        "name": "Same-Day 3-CTA Repair",
        "total": 75,
        "deposit": 40,
        "desc": "same-day website and CTA repair"
    },
    "IDEA-03": {
        "name": "One-Offer Promo Sprint",
        "total": 99,
        "deposit": 50,
        "desc": "promotional content pack"
    },
    "IDEA-04": {
        "name": "Google Profile Accuracy Session",
        "total": 99,
        "deposit": 50,
        "desc": "Google Business Profile accuracy session"
    },
    "IDEA-05": {
        "name": "Local Voice Review Reply Pack",
        "total": 75,
        "deposit": 40,
        "desc": "professional review response pack"
    },
    "IDEA-06": {
        "name": "Never-Lose-a-Lead Starter Form",
        "total": 149,
        "deposit": 75,
        "desc": "lead-capture form and follow-up system"
    },
    "IDEA-07": {
        "name": "One-Workflow Automation Sprint",
        "total": 149,
        "deposit": 75,
        "desc": "business automation workflow setup"
    }
}

# Stripe links for different deposit amounts
STRIPE_DEPOSIT_LINKS = {
    40: "https://buy.stripe.com/aFadR8ceZ1YS7X93EX7g40c",
    50: "https://buy.stripe.com/8x28wObaVdHA7X9cbt7g409",
    75: "https://buy.stripe.com/fZu8wOgvf5b40uHgrJ7g406"
}

STRIPE_FULL_LINKS = {
    75: "https://buy.stripe.com/eVq14m3It6f87X95N57g40b",
    99: "https://buy.stripe.com/00wbJ0gvf5b47X97Vd7g408",
    149: "https://buy.stripe.com/8x25kC92N1YSfpBejB7g405"
}

STRIPE_BALANCE_LINKS = {
    35: "https://buy.stripe.com/eVq14m6UF6f8b9lgrJ7g40d",
    49: "https://buy.stripe.com/dRmfZgbaV9rkb9l5N57g40a",
    74: "https://buy.stripe.com/cNi6oG2EpeLE2CPfnF7g407"
}

PROPOSAL_TEMPLATE = """======================================================================
  G3 PROPOSAL PACKET — FOR TOM GRONEK APPROVAL
======================================================================
Client Business: {domain}
Audit Score: {score}/100 (Grade {grade})
Recommended Service: {product_name}
----------------------------------------------------------------------
Proposed Scope of Work (48-Hour Delivery):
{issues_list}

Investment & Payment Options:
- Total Service Fee: ${total}.00 USD

Option 1: Pay Full Amount Upfront
  👉 ${total} Full Payment Link: {stripe_full_link}?client_reference_id={domain}

Option 2: 50% Deposit Now, Balance on Completion
  👉 ${deposit} Deposit Link: {stripe_deposit_link}?client_reference_id={domain}
  (Remaining ${balance} will be billed via {stripe_balance_link})

- Money-Back Guarantee: 100% Satisfaction Guarantee

----------------------------------------------------------------------
PROPOSED EMAIL RESPONSE PAYLOAD:

Subject: Re: 48-Hour {desc} for {domain}

Hi there,

Thanks for reaching out! Here is the 1-page visual audit summary for {domain}:
Audit Grade: {grade} ({score}/100)

Key Optimizations We Will Fix:
{issues_list}

We complete this {desc} within 48 hours for a flat ${total} investment. We offer a 100% satisfaction guarantee.

You can lock in your 48-hour slot using one of the payment options below:
Option 1: ${deposit} Deposit to Start, ${balance} upon completion
👉 {stripe_deposit_link}?client_reference_id={domain}

Option 2: ${total} Paid in Full
👉 {stripe_full_link}?client_reference_id={domain}

Once the initial payment is received, we begin work immediately and deliver your update within 48 hours.

Best regards,
Tom Gronek
Asheville AI Business Solutions
======================================================================
"""

def generate_proposals(tenant):
    audit_file = f"audit_results_{tenant}.json"
    if not os.path.exists(audit_file):
        print(f"[ERROR] {audit_file} not found. Run batch_audit_scanner.py first.")
        return

    with open(audit_file, "r") as f:
        audits = json.load(f)

    out_dir = os.path.join(os.path.dirname(__file__), f"proposals_{tenant}")
    os.makedirs(out_dir, exist_ok=True)

    generated = 0
    for a in audits:
        if a.get("status") == "AUDITED":
            domain = a["domain"]
            score = a.get("score", 0)
            grade = a.get("grade", "F")
            issues = a.get("issues", [])
            product_id = a.get("recommended_product", "IDEA-02")
            
            prod = PRODUCTS.get(product_id, PRODUCTS["IDEA-02"])
            issues_formatted = "\n".join([f"  • {issue}" for issue in issues]) if issues else "  • Routine digital checkup and repair"
            
            balance = prod["total"] - prod["deposit"]
            stripe_deposit = STRIPE_DEPOSIT_LINKS.get(prod["deposit"], "https://buy.stripe.com/MISSING")
            stripe_full = STRIPE_FULL_LINKS.get(prod["total"], "https://buy.stripe.com/MISSING")
            stripe_balance = STRIPE_BALANCE_LINKS.get(balance, "https://buy.stripe.com/MISSING")

            proposal_text = PROPOSAL_TEMPLATE.format(
                domain=domain,
                score=score,
                grade=grade,
                product_name=prod["name"],
                issues_list=issues_formatted,
                total=prod["total"],
                deposit=prod["deposit"],
                balance=balance,
                desc=prod["desc"],
                stripe_deposit_link=stripe_deposit,
                stripe_full_link=stripe_full,
                stripe_balance_link=stripe_balance
            )

            out_file = os.path.join(out_dir, f"{domain.replace('.', '_')}_proposal.txt")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(proposal_text)
            
            generated += 1

    print(f"[SUCCESS] Generated {generated} personalized, multi-product proposal packets for {tenant}!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="asheville", help="Tenant ID")
    args = parser.parse_args()
    
    generate_proposals(args.tenant)
