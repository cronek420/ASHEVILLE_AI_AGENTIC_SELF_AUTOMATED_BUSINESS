"""
Batch Website Audit Scanner for Asheville AI Agentic Self-Automated Business.
Scans multiple local business websites and generates a consolidated prospect report.
Enhanced checks:
- SSL / HTTPS
- Page load speed
- Mobile viewport meta tag
- Clickable phone numbers (tel: links)
- Outdated copyright year
- Missing SEO meta description
- Missing Open Graph tags (og:title, og:description, og:image)
- Broken internal links (sample top 5)
- Missing favicon
- Missing h1 heading tag
- Image alt text coverage
- Schema.org / structured data presence
"""

import urllib.request
import urllib.parse
import re
import time
import datetime
import json
import ssl
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional


class EnhancedHTMLAuditor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: List[str] = []
        self.tel_links: List[str] = []
        self.mailto_links: List[str] = []
        self.has_viewport = False
        self.has_meta_description = False
        self.has_og_title = False
        self.has_og_description = False
        self.has_og_image = False
        self.has_favicon = False
        self.has_h1 = False
        self.title_text = ""
        self.in_title = False
        self.img_count = 0
        self.img_with_alt = 0
        self.has_schema = False
        self.social_links: List[str] = []
        self.text_content: List[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "viewport":
                self.has_viewport = True
            if name == "description":
                self.has_meta_description = True
            if prop == "og:title":
                self.has_og_title = True
            if prop == "og:description":
                self.has_og_description = True
            if prop == "og:image":
                self.has_og_image = True

        elif tag == "title":
            self.in_title = True

        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if "icon" in rel:
                self.has_favicon = True

        elif tag == "h1":
            self.has_h1 = True

        elif tag == "img":
            self.img_count += 1
            if attrs_dict.get("alt", "").strip():
                self.img_with_alt += 1

        elif tag == "a":
            href = attrs_dict.get("href", "").strip()
            if href:
                if href.startswith("tel:"):
                    self.tel_links.append(href)
                elif href.startswith("mailto:"):
                    self.mailto_links.append(href)
                else:
                    # Check for social media links
                    for social in ["facebook.com", "instagram.com", "twitter.com", "x.com",
                                   "linkedin.com", "youtube.com", "tiktok.com", "yelp.com",
                                   "nextdoor.com"]:
                        if social in href.lower():
                            self.social_links.append(href)
                            break
                    if not href.startswith("javascript:") and not href.startswith("#"):
                        full_url = urllib.parse.urljoin(self.base_url, href)
                        self.links.append(full_url)

        elif tag == "script":
            if attrs_dict.get("type") == "application/ld+json":
                self.has_schema = True

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data.strip()
        self.text_content.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False

    def extract_emails(self):
        import re
        text = " ".join(self.text_content)
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = re.findall(email_pattern, text)
        return list(set(emails))
        
    def extract_phones(self):
        import re
        text = " ".join(self.text_content)
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        return list(set(phones))


def audit_website(url: str, run_id: str = "RUN-BATCH-AUDIT") -> Dict[str, Any]:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]

    findings: List[Dict[str, str]] = []
    issues: List[str] = []
    opportunities: List[str] = []
    score = 100  # Start at 100 and deduct points

    start_time = time.time()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Create SSL context that doesn't verify (for audit purposes only)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as response:
            load_time_ms = int((time.time() - start_time) * 1000)
            html_content = response.read().decode("utf-8", errors="ignore")
            final_url = response.geturl()
    except Exception as e:
        return {
            "domain": domain,
            "url": url,
            "status": "UNREACHABLE",
            "score": 0,
            "issues": [f"Site unreachable: {str(e)[:80]}"],
            "opportunities": ["Website may be down or misconfigured"],
            "findings": [{"check": "Connectivity", "result": "FAIL", "detail": str(e)[:80]}]
        }

    parser = EnhancedHTMLAuditor(final_url)
    try:
        parser.feed(html_content)
    except Exception:
        pass

    # === AUDIT CHECKS ===

    # 1. SSL / HTTPS
    if not final_url.startswith("https://"):
        issues.append("No HTTPS — shows 'Not Secure' in browser bar")
        opportunities.append("SSL Certificate Setup")
        findings.append({"check": "HTTPS/SSL", "result": "FAIL", "detail": "Site loads over HTTP, not HTTPS"})
        score -= 15
    else:
        findings.append({"check": "HTTPS/SSL", "result": "PASS", "detail": "SSL active"})

    # 2. Page Load Speed
    if load_time_ms > 3000:
        issues.append(f"Very slow load: {load_time_ms}ms (target < 1500ms)")
        opportunities.append("Page Speed Optimization")
        findings.append({"check": "Load Speed", "result": "FAIL", "detail": f"{load_time_ms}ms"})
        score -= 12
    elif load_time_ms > 1500:
        issues.append(f"Moderate load: {load_time_ms}ms (target < 1500ms)")
        opportunities.append("Image & Asset Optimization")
        findings.append({"check": "Load Speed", "result": "WARN", "detail": f"{load_time_ms}ms"})
        score -= 5
    else:
        findings.append({"check": "Load Speed", "result": "PASS", "detail": f"{load_time_ms}ms"})

    # 3. Mobile Viewport
    if not parser.has_viewport:
        issues.append("No mobile viewport tag — site likely broken on phones")
        opportunities.append("Mobile Responsive Design")
        findings.append({"check": "Mobile Viewport", "result": "FAIL", "detail": "Missing <meta viewport>"})
        score -= 15
    else:
        findings.append({"check": "Mobile Viewport", "result": "PASS", "detail": "Viewport tag present"})

    # 4. Clickable Phone Number
    phone_matches = re.findall(r'\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b', html_content)
    if phone_matches and not parser.tel_links:
        issues.append(f"Phone # visible ({phone_matches[0]}) but not tap-to-call on mobile")
        opportunities.append("1-Tap Call Button")
        findings.append({"check": "Tap-to-Call", "result": "FAIL", "detail": f"Phone {phone_matches[0]} not linked"})
        score -= 8
    elif parser.tel_links:
        findings.append({"check": "Tap-to-Call", "result": "PASS", "detail": f"{len(parser.tel_links)} tel: link(s)"})
    elif not phone_matches:
        issues.append("No phone number found on homepage")
        opportunities.append("Add Visible Phone Number & Call CTA")
        findings.append({"check": "Tap-to-Call", "result": "FAIL", "detail": "No phone number on page"})
        score -= 10

    # 5. Copyright Year
    current_year = datetime.datetime.now().year
    copyright_years = re.findall(r'[©Cc]opyright\s*(?:20\d\d\s*[-–]\s*)?(20\d\d)', html_content)
    if not copyright_years:
        copyright_years = re.findall(r'©\s*(?:20\d\d\s*[-–]\s*)?(20\d\d)', html_content)
    if copyright_years:
        latest = max(int(y) for y in copyright_years)
        if latest < current_year - 1:
            issues.append(f"Outdated copyright: © {latest} (now {current_year})")
            opportunities.append("Website Content Refresh")
            findings.append({"check": "Copyright Year", "result": "FAIL", "detail": f"© {latest}"})
            score -= 5
        else:
            findings.append({"check": "Copyright Year", "result": "PASS", "detail": f"© {latest}"})
    else:
        findings.append({"check": "Copyright Year", "result": "INFO", "detail": "No copyright notice found"})

    # 6. Meta Description
    if not parser.has_meta_description:
        issues.append("Missing meta description — Google shows random text in search results")
        opportunities.append("SEO Meta Description & Title Optimization")
        findings.append({"check": "Meta Description", "result": "FAIL", "detail": "No <meta name='description'>"})
        score -= 8
    else:
        findings.append({"check": "Meta Description", "result": "PASS", "detail": "Meta description present"})

    # 7. Open Graph Tags (social sharing)
    og_missing = []
    if not parser.has_og_title:
        og_missing.append("og:title")
    if not parser.has_og_description:
        og_missing.append("og:description")
    if not parser.has_og_image:
        og_missing.append("og:image")
    if og_missing:
        issues.append(f"Missing Open Graph tags: {', '.join(og_missing)} — links shared on Facebook/social look broken")
        opportunities.append("Social Sharing Preview Setup")
        findings.append({"check": "Open Graph Tags", "result": "FAIL", "detail": f"Missing: {', '.join(og_missing)}"})
        score -= 5
    else:
        findings.append({"check": "Open Graph Tags", "result": "PASS", "detail": "All OG tags present"})

    # 8. Favicon
    if not parser.has_favicon:
        issues.append("No favicon — browser tab shows generic icon")
        opportunities.append("Brand Identity (Favicon)")
        findings.append({"check": "Favicon", "result": "FAIL", "detail": "No <link rel='icon'>"})
        score -= 3
    else:
        findings.append({"check": "Favicon", "result": "PASS", "detail": "Favicon present"})

    # 9. H1 Heading
    if not parser.has_h1:
        issues.append("No H1 heading — hurts Google ranking for local searches")
        opportunities.append("SEO Heading Structure")
        findings.append({"check": "H1 Heading", "result": "FAIL", "detail": "No <h1> tag found"})
        score -= 5
    else:
        findings.append({"check": "H1 Heading", "result": "PASS", "detail": "H1 tag present"})

    # 10. Image Alt Text
    if parser.img_count > 0:
        alt_pct = int((parser.img_with_alt / parser.img_count) * 100)
        if alt_pct < 50:
            issues.append(f"Only {alt_pct}% of images have alt text ({parser.img_with_alt}/{parser.img_count})")
            opportunities.append("Accessibility & Image SEO")
            findings.append({"check": "Image Alt Text", "result": "FAIL", "detail": f"{alt_pct}% coverage"})
            score -= 5
        else:
            findings.append({"check": "Image Alt Text", "result": "PASS", "detail": f"{alt_pct}% coverage"})

    # 11. Schema.org Structured Data
    if not parser.has_schema:
        issues.append("No Schema.org structured data — missing from Google rich results/knowledge panel")
        opportunities.append("Local Business Schema Markup")
        findings.append({"check": "Schema.org", "result": "FAIL", "detail": "No JSON-LD structured data"})
        score -= 5
    else:
        findings.append({"check": "Schema.org", "result": "PASS", "detail": "Structured data present"})

    # 12. Broken Links (sample top 5 internal links)
    broken_links = []
    same_domain_links = [l for l in parser.links if domain in l]
    test_links = list(dict.fromkeys(same_domain_links))[:5]
    for link in test_links:
        try:
            lreq = urllib.request.Request(link, headers=headers, method="HEAD")
            with urllib.request.urlopen(lreq, timeout=5, context=ctx) as lres:
                if lres.getcode() >= 400:
                    broken_links.append(link)
        except Exception:
            broken_links.append(link)

    if broken_links:
        short_links = [l.split(domain)[-1] or "/" for l in broken_links[:3]]
        issues.append(f"{len(broken_links)} broken link(s): {', '.join(short_links)}")
        opportunities.append("Broken Link & Navigation Repair")
        findings.append({"check": "Broken Links", "result": "FAIL", "detail": f"{len(broken_links)} broken"})
        score -= 8
    else:
        findings.append({"check": "Broken Links", "result": "PASS", "detail": f"Tested {len(test_links)} links, all OK"})

    # 13. Page Title
    title = parser.title_text.strip()
    if not title:
        issues.append("No page title — Google search listing will have no headline")
        opportunities.append("SEO Title Tag")
        findings.append({"check": "Page Title", "result": "FAIL", "detail": "Empty <title>"})
        score -= 8
    elif len(title) > 70:
        findings.append({"check": "Page Title", "result": "WARN", "detail": f"'{title[:50]}...' ({len(title)} chars, ideal <60)"})
        score -= 2
    else:
        findings.append({"check": "Page Title", "result": "PASS", "detail": f"'{title}'"})

    score = max(0, score)

    # Grade
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    # Match the best product based on issues
    recommended_product = "IDEA-02"  # default to Same-Day CTA repair
    if not parser.has_viewport:
        recommended_product = "IDEA-01" # Mobile Booking Page Rescue
    elif score >= 80:
        recommended_product = "IDEA-05" # Review Reply Pack / SEO stuff
    elif parser.img_count > 0 and (parser.img_with_alt / parser.img_count) < 0.5:
        recommended_product = "IDEA-02"

    return {
        "domain": domain,
        "url": final_url,
        "title": title,
        "status": "AUDITED",
        "score": score,
        "grade": grade,
        "load_time_ms": load_time_ms,
        "issues": issues,
        "opportunities": opportunities,
        "findings": findings,
        "recommended_product": recommended_product,
        "contacts": {
            "emails": parser.extract_emails(),
            "phones": parser.extract_phones(),
            "tel_links": parser.tel_links,
            "mailto_links": parser.mailto_links,
        },
        "stats": {
            "total_links": len(parser.links),
            "tel_links": len(parser.tel_links),
            "images": parser.img_count,
            "images_with_alt": parser.img_with_alt,
            "social_links": len(parser.social_links)
        }
    }


def batch_audit(targets: List[str], run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if not run_id:
        now = datetime.datetime.now()
        run_id = f"RUN-{now.strftime('%Y%m%d-%H%M')}-01"

    results = []
    print(f"\n{'='*70}")
    print(f"  ASHEVILLE WEBSITE AUDIT SCOUT — Run ID: {run_id}")
    print(f"  Targets: {len(targets)} businesses")
    print(f"  Started: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p ET')}")
    print(f"{'='*70}\n")

    for i, target in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] Scanning {target}...", end=" ", flush=True)
        result = audit_website(target, run_id)
        results.append(result)

        if result["status"] == "AUDITED":
            issue_count = len(result["issues"])
            print(f"Grade: {result['grade']} ({result['score']}/100) — {issue_count} issue(s) found")
        else:
            print(f"UNREACHABLE")

        time.sleep(1)  # Polite delay between scans

    # Print Summary Report
    print(f"\n{'='*70}")
    print(f"  AUDIT SUMMARY REPORT")
    print(f"{'='*70}")
    print(f"{'Business':<35} {'Grade':>6} {'Score':>6} {'Issues':>7} {'Top Opportunity'}")
    print(f"{'-'*35} {'-'*6} {'-'*6} {'-'*7} {'-'*30}")

    hot_leads = []
    for r in sorted(results, key=lambda x: x.get("score", 0)):
        domain = r["domain"][:33]
        grade = r.get("grade", "?")
        score = r.get("score", 0)
        issues = len(r.get("issues", []))
        top_opp = r["opportunities"][0] if r.get("opportunities") else "-"
        print(f"{domain:<35} {grade:>6} {score:>5}/100 {issues:>5}   {top_opp}")
        if issues >= 2:
            hot_leads.append(r)

    print(f"\n{'='*70}")
    print(f"  HOT LEADS (2+ issues = strong outreach candidates): {len(hot_leads)}")
    print(f"{'='*70}")
    for lead in hot_leads:
        print(f"\n  >>> {lead['domain']} (Grade {lead['grade']}, Score {lead['score']}/100)")
        for issue in lead["issues"]:
            print(f"      [!]  {issue}")
        print(f"      [->] Opportunities: {', '.join(lead['opportunities'][:3])}")

    return results


# === ASHEVILLE LOCAL BUSINESSES TO AUDIT ===
ASHEVILLE_TARGETS = [
    # Batch 2: Auto Repair, Pest Control, Pressure Washing, Dental, Lawn Care
    "mostlyfrenchauto.com",
    "experttransmissionasheville.com",
    "organicmechanic.com",
    "macsautoasheville.com",
    "apexbugs.com",
    "gibsonpest.com",
    "ashevillepestcontrol.com",
    "ashevillepressurewashing.com",
    "mountainpressurewash.com",
    "wncsoftwash.com",
    "ashevillefamilydentistry.com",
    "gillespiedental.com",
    "ashevillelawncare.com",
    "mountainscapenc.com",
    "lawnscapesasheville.com"
]


if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
    else:
        # Try to load scraped leads if they exist and are non-empty
        targets = []
        if os.path.exists("scraped_leads.json"):
            with open("scraped_leads.json", "r") as f:
                scraped = json.load(f)
            if scraped:
                targets = [s["domain"] for s in scraped]
                print(f"Loaded {len(targets)} targets from scraped_leads.json")

        if not targets:
            print(f"scraped_leads.json empty or missing. Using {len(ASHEVILLE_TARGETS)} hardcoded Asheville targets.")
            targets = ASHEVILLE_TARGETS

    results = batch_audit(targets)

    # Save JSON results
    output_file = "audit_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: {output_file}")

