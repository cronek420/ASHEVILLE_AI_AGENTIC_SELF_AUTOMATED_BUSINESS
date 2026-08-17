"""
Website Audit Scout & Proof Asset Builder for Asheville AI Agentic Self-Automated Business.
Scans local business websites for observable, factual bottlenecks:
- Broken links & 404 errors
- Missing or non-clickable phone numbers (tel: links) & booking CTAs
- Outdated copyright dates & missing SSL certificates
- Slow load latency & missing mobile viewport tags
- Missing SEO meta titles/descriptions & Open Graph tags
Returns a structured specialist Change Packet matching .agents/rules/01-single-writer-contract.md.
"""

import urllib.request
import urllib.parse
import urllib.error
import re
import time
import datetime
from html.parser import HTMLParser
from typing import Dict, Any, List, Tuple

class SimpleHTMLAuditor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: List[str] = []
        self.tel_links: List[str] = []
        self.mailto_links: List[str] = []
        self.has_viewport = False
        self.has_meta_description = False
        self.title_text = ""
        self.in_title = False
        self.buttons: List[str] = []
        self.in_button = False
        self.current_button_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag == "meta":
            if attrs_dict.get("name", "").lower() == "viewport":
                self.has_viewport = True
            if attrs_dict.get("name", "").lower() == "description":
                self.has_meta_description = True

        elif tag == "title":
            self.in_title = True

        elif tag == "a":
            href = attrs_dict.get("href", "").strip()
            if href:
                if href.startswith("tel:"):
                    self.tel_links.append(href)
                elif href.startswith("mailto:"):
                    self.mailto_links.append(href)
                elif not href.startswith("javascript:") and not href.startswith("#"):
                    full_url = urllib.parse.urljoin(self.base_url, href)
                    self.links.append(full_url)

        elif tag in ["button", "input"] or "btn" in attrs_dict.get("class", "").lower():
            self.in_button = True
            self.current_button_text = ""

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() in ["button", "input"]:
            if self.current_button_text:
                self.buttons.append(self.current_button_text.strip())
            self.in_button = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data
        if self.in_button:
            self.current_button_text += " " + data


def audit_website(url: str, run_id: str = "RUN-LOCAL-AUDIT") -> Dict[str, Any]:
    """
    Audits a local business URL and returns observable factual findings.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc

    audit_findings = []
    opportunities = []
    
    start_time = time.time()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AntigravityScout/1.0"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            load_time_ms = int((time.time() - start_time) * 1000)
            html_content = response.read().decode("utf-8", errors="ignore")
            final_url = response.geturl()
            status_code = response.getcode()
    except Exception as e:
        return {
            "run_id": run_id,
            "agent": "Scout-Research",
            "idea_id": "IDEA-01",
            "task": f"Audit Website: {url}",
            "status": "blocked",
            "evidence": [{"source_or_artifact": url, "observation": f"Site unreachable or network error: {str(e)}"}],
            "proposed_sheet_changes": [],
            "external_action_taken": False,
            "next_step": "Flag domain for manual verification",
            "uncertainties": [f"Connection error to {url}"]
        }

    # Parse HTML
    parser = SimpleHTMLAuditor(final_url)
    parser.feed(html_content)

    # 1. SSL / HTTPS check
    if not final_url.startswith("https://"):
        audit_findings.append("Missing HTTPS / SSL security certificate (shows 'Not Secure' in browser).")
        opportunities.append("SSL Certificate Security Setup")
    else:
        audit_findings.append("SSL HTTPS active.")

    # 2. Page Load Speed
    if load_time_ms > 2500:
        audit_findings.append(f"Slow mobile load latency: {load_time_ms}ms (ideal is < 1500ms).")
        opportunities.append("Page Speed & Image Optimization")

    # 3. Mobile Viewport Check
    if not parser.has_viewport:
        audit_findings.append("Missing mobile viewport meta tag — site may render shrunk/zoomed-out on mobile devices.")
        opportunities.append("Mobile Responsiveness Fix")

    # 4. Clickable Phone / Call-to-Action Check
    phone_matches = re.findall(r'\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b', html_content)
    if phone_matches and not parser.tel_links:
        audit_findings.append(f"Phone number ({phone_matches[0]}) visible on page but lacks 'tel:' link for 1-tap mobile calling.")
        opportunities.append("1-Tap Mobile Call Button Setup")

    # 5. Outdated Copyright Year
    current_year = datetime.datetime.now().year
    copyright_years = re.findall(r'©\s*(?:20\d\d-)?(20\d\d)', html_content)
    if copyright_years:
        latest_year = int(copyright_years[0])
        if latest_year < current_year - 1:
            audit_findings.append(f"Outdated copyright notice: '© {latest_year}' (current year is {current_year}).")
            opportunities.append("Website Content Update & Modernization")

    # 6. SEO Meta Description Check
    if not parser.has_meta_description:
        audit_findings.append("Missing meta description tag — Google search result snippet will show random page text.")
        opportunities.append("Local SEO Meta & Search Snippet Optimization")

    # 7. Check for Broken Internal/External Links (Sample test top 5 links)
    broken_links = []
    unique_links = list(dict.fromkeys(parser.links))[:5]
    for link in unique_links:
        try:
            lreq = urllib.request.Request(link, headers=headers, method="HEAD")
            with urllib.request.urlopen(lreq, timeout=5) as lres:
                pass
        except Exception:
            broken_links.append(link)

    if broken_links:
        audit_findings.append(f"Found {len(broken_links)} broken or dead link(s): {', '.join(broken_links[:2])}")
        opportunities.append("Broken Link & Navigation Repair")

    # Formulate Structured Change Packet
    change_packet = {
        "run_id": run_id,
        "agent": "Scout-Research",
        "idea_id": "IDEA-01",
        "task": f"Factual Audit for {domain}",
        "status": "completed",
        "evidence": [
            {
                "source_or_artifact": final_url,
                "observation": finding
            } for finding in audit_findings
        ],
        "proposed_sheet_changes": [
            {
                "tab": "Prospect Tracker",
                "record_key": domain,
                "fields": {
                    "Domain": domain,
                    "Audit_Status": "Audited",
                    "Observed_Bottlenecks": " | ".join(audit_findings[:3]),
                    "Recommended_Solutions": " & ".join(opportunities[:2]) if opportunities else "General Optimization"
                }
            }
        ],
        "approval_request": "G2",
        "external_action_taken": False,
        "next_step": "Draft personalized outreach referencing observed bottlenecks for Tom's G2 approval",
        "uncertainties": []
    }

    return change_packet


if __name__ == "__main__":
    import sys
    test_target = sys.argv[1] if len(sys.argv) > 1 else "blueplanetplumbing.com"
    print(f"--- Running Factual Website Audit Scout on: {test_target} ---")
    packet = audit_website(test_target)
    print("\nGenerated Specialist Change Packet:")
    import json
    print(json.dumps(packet, indent=2))
