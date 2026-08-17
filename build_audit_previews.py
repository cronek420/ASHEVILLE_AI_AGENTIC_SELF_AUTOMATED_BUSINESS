"""
Proof-Builder Visual Audit Asset Generator for Asheville AI Agentic Business.
Generates responsive, professional 1-page HTML visual audit previews for our 5 outreach prospects.
Uses modern CSS tokens, Google Fonts, glassmorphism UI cards, empirical metrics, and clear optimization roadmaps.
"""

import os
import json

PROSPECTS = [
    {
        "filename": "wardph_audit.html",
        "domain": "wardph.com",
        "business_name": "Ward Plumbing, Heating, and Air",
        "niche": "Plumbing & HVAC • Asheville, NC",
        "score": 85,
        "grade": "B",
        "load_time_ms": 2569,
        "issues": [
            {"title": "Mobile Load Latency", "detail": "Currently 2.57 seconds (Target: < 1.5 seconds)", "severity": "WARN"},
            {"title": "Missing <h1> Search Heading", "detail": "Homepage lacks an H1 tag for local Asheville keyword ranking", "severity": "FAIL"},
            {"title": "0% Image Alt Text Coverage", "detail": "0 of 4 images contain alt text attributes for accessibility & image search", "severity": "FAIL"}
        ],
        "passes": [
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "Tap-to-Call Phone Link Active",
            "Schema.org Structured Data Present",
            "Open Graph Social Preview Tags Active"
        ],
        "optimization_steps": [
            "1. Image & Asset Compression: Sub-1.5s load target",
            "2. Local SEO H1 Heading Tag Setup: Asheville plumbing keyword optimization",
            "3. Complete Image Alt Text Tagging: Screen-reader and image search compliance"
        ]
    },
    {
        "filename": "whiteandwilliams_audit.html",
        "domain": "whiteandwilliams.com",
        "business_name": "White & Williams Co.",
        "niche": "Contracting & HVAC • Asheville, NC",
        "score": 36,
        "grade": "F",
        "load_time_ms": 1612,
        "issues": [
            {"title": "Missing Mobile Viewport Tag", "detail": "Website layout appears broken and zoomed-out on mobile devices", "severity": "CRITICAL"},
            {"title": "No Tap-to-Call Phone Link", "detail": "Homepage lacks a 1-tap phone link for mobile visitors to call instantly", "severity": "FAIL"},
            {"title": "Missing H1 & Page Title Tags", "detail": "Google search listings lack a primary headline and keyword structure", "severity": "FAIL"},
            {"title": "Missing Meta Description", "detail": "Google displays random body snippet in search results", "severity": "WARN"}
        ],
        "passes": [
            "HTTPS / SSL Security Active",
            "Favicon Present"
        ],
        "optimization_steps": [
            "1. Responsive Mobile Viewport Tag Setup: 100% mobile-friendly layout",
            "2. Sticky 1-Tap Mobile Call CTA Button: Instant customer calls",
            "3. Full SEO Meta & Heading Structure: Title, Meta Description, and H1 tags"
        ]
    },
    {
        "filename": "ashevilleelectrician_audit.html",
        "domain": "ashevilleelectrician.com",
        "business_name": "Asheville Electrician",
        "niche": "Electrical Contractors • Asheville, NC",
        "score": 76,
        "grade": "B",
        "load_time_ms": 6243,
        "issues": [
            {"title": "High Mobile Load Latency", "detail": "Takes 6.24 seconds to load on mobile networks (Target: < 1.5s)", "severity": "FAIL"},
            {"title": "Outdated Footer Copyright", "detail": "Displays © 2023 copyright date (gives impression site is unmaintained)", "severity": "WARN"},
            {"title": "Missing Social Preview Image", "detail": "Shared links on Facebook/messaging lack a preview thumbnail", "severity": "WARN"}
        ],
        "passes": [
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "Tap-to-Call Link Active",
            "H1 Heading Tag Present"
        ],
        "optimization_steps": [
            "1. Code & Asset Optimization: Speed up mobile load time from 6.2s to sub-1.5s",
            "2. Automated Copyright Year Update: Dynamic © 2026 footer script",
            "3. Open Graph og:image Social Card Setup: High-converting social previews"
        ]
    },
    {
        "filename": "ashevilletreeservice_audit.html",
        "domain": "ashevilletreeservice.com",
        "business_name": "Asheville Tree Service",
        "niche": "Tree Care & Landscaping • Asheville, NC",
        "score": 85,
        "grade": "B",
        "load_time_ms": 1794,
        "issues": [
            {"title": "Missing Local Schema.org Markup", "detail": "Missing structured data for Google Knowledge Panel & local map rich results", "severity": "FAIL"},
            {"title": "Missing Social Card Thumbnail", "detail": "Links shared on Facebook or text messages show generic placeholder", "severity": "WARN"},
            {"title": "Moderate Mobile Load Latency", "detail": "1.79 seconds mobile load time (Target: < 1.5s)", "severity": "WARN"}
        ],
        "passes": [
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "Tap-to-Call Phone Link Active",
            "H1 Heading Tag Present"
        ],
        "optimization_steps": [
            "1. Local Business Schema.org Tagging: Rich Snippets for Google Maps & Knowledge Panel",
            "2. Open Graph Social Card Setup: High-impact social thumbnail link previews",
            "3. Sub-1.5s Page Latency Compression"
        ]
    },
    {
        "filename": "bakerroofing_audit.html",
        "domain": "bakerroofing.com",
        "business_name": "Baker Roofing",
        "niche": "Roofing Contractors • Asheville, NC",
        "score": 87,
        "grade": "B",
        "load_time_ms": 912,
        "issues": [
            {"title": "Non-Clickable Mobile Phone Number", "detail": "Phone number (833-338-1915) is plain text, requiring manual dialing on phones", "severity": "FAIL"},
            {"title": "34% Image Alt Text Coverage", "detail": "38 of 58 images lack alt text attributes for accessibility & image search", "severity": "WARN"}
        ],
        "passes": [
            "Fast Sub-1s Mobile Load Speed (912ms)",
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "H1 Heading Tag Present",
            "Schema.org Structured Data Active"
        ],
        "optimization_steps": [
            "1. 1-Tap Mobile Call Button: Convert plain text phone numbers into direct tel: call links",
            "2. Complete Image Alt Tag Coverage: 100% search & accessibility compliance"
        ]
    },
    # --- BATCH 2 PROSPECTS ---
    {
        "filename": "ashevillepressurewashing_audit.html",
        "domain": "ashevillepressurewashing.com",
        "business_name": "Asheville Pressure Washing",
        "niche": "Exterior Cleaning • Asheville, NC",
        "score": 41,
        "grade": "D",
        "load_time_ms": 1820,
        "issues": [
            {"title": "Missing Mobile Viewport Tag", "detail": "Layout renders zoomed-out on smartphones, making text illegible", "severity": "CRITICAL"},
            {"title": "No Direct Phone Call CTA Link", "detail": "Homepage lacks a 1-tap mobile call button for instant leads", "severity": "FAIL"},
            {"title": "Missing Search Meta Description & Title", "detail": "Google displays random page text in local search results", "severity": "FAIL"},
            {"title": "Missing Social Preview Open Graph Tags", "detail": "Links shared on Facebook/text messages show broken thumbnails", "severity": "WARN"}
        ],
        "passes": [
            "HTTPS / SSL Security Active"
        ],
        "optimization_steps": [
            "1. Responsive Mobile Viewport Tag Setup: 100% mobile smartphone optimization",
            "2. Sticky 1-Tap Mobile Call CTA Button: High-converting lead generation",
            "3. Full Local SEO & Social Card Setup: Title, Meta Description, og:image"
        ]
    },
    {
        "filename": "ashevillelawncare_audit.html",
        "domain": "ashevillelawncare.com",
        "business_name": "Asheville Lawn Care",
        "niche": "Lawn Care & Landscaping • Asheville, NC",
        "score": 41,
        "grade": "D",
        "load_time_ms": 1950,
        "issues": [
            {"title": "Missing Mobile Viewport Tag", "detail": "Site appears unformatted and zoomed-out on mobile devices", "severity": "CRITICAL"},
            {"title": "No Tap-to-Call Phone Link", "detail": "Mobile visitors cannot tap to call for lawn maintenance quotes", "severity": "FAIL"},
            {"title": "Missing H1 Search Heading Tag", "detail": "Lacks primary H1 tag for local Asheville lawn care keyword ranking", "severity": "FAIL"}
        ],
        "passes": [
            "HTTPS / SSL Security Active"
        ],
        "optimization_steps": [
            "1. Smartphone Mobile Viewport Integration: Clean responsive layout",
            "2. Sticky 1-Tap Quote Request Call Link",
            "3. Local SEO H1 & Meta Description Optimization"
        ]
    },
    {
        "filename": "ashevillepestcontrol_audit.html",
        "domain": "ashevillepestcontrol.com",
        "business_name": "Asheville Pest Control",
        "niche": "Pest & Termite Control • Asheville, NC",
        "score": 64,
        "grade": "C",
        "load_time_ms": 1420,
        "issues": [
            {"title": "Missing Homepage Phone Link", "detail": "No direct 1-tap phone button for emergency pest control calls", "severity": "FAIL"},
            {"title": "Missing H1 Search Heading", "detail": "Missing primary headline for Google local search indexing", "severity": "WARN"},
            {"title": "Missing Schema.org Local Business Data", "detail": "Lacks structured data for Google Knowledge Panel & map rich results", "severity": "WARN"}
        ],
        "passes": [
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "Fast Sub-1.5s Load Speed (1420ms)"
        ],
        "optimization_steps": [
            "1. 1-Tap Emergency Mobile Call Button Setup",
            "2. Local Business Schema.org Rich Snippet Tagging",
            "3. Local SEO H1 & Open Graph Social Card Setup"
        ]
    },
    {
        "filename": "ashevillefamilydentistry_audit.html",
        "domain": "ashevillefamilydentistry.com",
        "business_name": "Asheville Family Dentistry",
        "niche": "Dental Practice • Asheville, NC",
        "score": 79,
        "grade": "B",
        "load_time_ms": 1280,
        "issues": [
            {"title": "Missing Social Preview Card Image", "detail": "Shared links on messaging/Facebook lack a branded preview image", "severity": "WARN"},
            {"title": "5 Broken Navigation Links", "detail": "Internal links to /about and /testimonials return error codes", "severity": "FAIL"}
        ],
        "passes": [
            "Fast Sub-1.5s Mobile Load Time (1280ms)",
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "Tap-to-Call Phone Link Active"
        ],
        "optimization_steps": [
            "1. Broken Internal Link Repairs: Fix /about & /testimonials routing",
            "2. Open Graph og:image Branded Social Card Setup",
            "3. Favicon & Search Title Polish"
        ]
    },
    {
        "filename": "wncsoftwash_audit.html",
        "domain": "wncsoftwash.com",
        "business_name": "WNC Soft Wash",
        "niche": "Exterior Soft Washing • Asheville, NC",
        "score": 85,
        "grade": "B",
        "load_time_ms": 1566,
        "issues": [
            {"title": "Moderate Load Latency", "detail": "Currently 1.57 seconds (Target: < 1.5 seconds)", "severity": "WARN"},
            {"title": "Missing Meta Description Tag", "detail": "Google displays unformatted snippet text in local search results", "severity": "WARN"}
        ],
        "passes": [
            "HTTPS / SSL Security Active",
            "Mobile Viewport Tag Present",
            "Tap-to-Call Phone Link Active",
            "H1 Heading Tag Present"
        ],
        "optimization_steps": [
            "1. Sub-1.5s Image & Asset Compression",
            "2. Meta Description Optimization for Local Asheville Search Conversion"
        ]
    }
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>48-Hour AI Optimization Audit — {business_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #0f172a;
      --card-bg: #1e293b;
      --accent-blue: #38bdf8;
      --accent-green: #22c55e;
      --accent-yellow: #eab308;
      --accent-red: #ef4444;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
    body {{ background: var(--bg-dark); color: var(--text-main); line-height: 1.6; padding: 40px 20px; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid var(--border); border-radius: 16px; padding: 32px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }}
    .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; }}
    .grade-A {{ background: rgba(34, 197, 94, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }}
    .grade-B {{ background: rgba(234, 179, 8, 0.15); color: var(--accent-yellow); border: 1px solid var(--accent-yellow); }}
    .grade-F {{ background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid var(--accent-red); }}
    .score-circle {{ width: 90px; height: 90px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(56, 189, 248, 0.1); border: 2px solid var(--accent-blue); }}
    .score-num {{ font-size: 1.8rem; font-weight: 800; color: var(--accent-blue); }}
    .score-label {{ font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; }}
    .section {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 28px; margin-bottom: 24px; }}
    .section-title {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 16px; color: var(--accent-blue); display: flex; align-items: center; gap: 8px; }}
    .issue-card {{ background: rgba(15, 23, 42, 0.6); border-left: 4px solid var(--accent-yellow); border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
    .issue-card.critical {{ border-left-color: var(--accent-red); }}
    .issue-title {{ font-weight: 700; font-size: 1rem; margin-bottom: 4px; display: flex; justify-content: space-between; }}
    .issue-detail {{ font-size: 0.9rem; color: var(--text-muted); }}
    .pass-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
    .pass-item {{ background: rgba(15, 23, 42, 0.4); border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-size: 0.88rem; color: #cbd5e1; display: flex; align-items: center; gap: 8px; }}
    .pass-icon {{ color: var(--accent-green); font-weight: 700; }}
    .step-item {{ background: rgba(56, 189, 248, 0.05); border: 1px dashed var(--accent-blue); border-radius: 8px; padding: 14px; margin-bottom: 10px; font-size: 0.95rem; font-weight: 600; color: #e2e8f0; }}
    .footer-cta {{ background: linear-gradient(135deg, #0284c7, #2563eb); border-radius: 16px; padding: 32px; text-align: center; margin-top: 32px; }}
    .footer-cta h3 {{ font-size: 1.5rem; font-weight: 800; margin-bottom: 8px; }}
    .footer-cta p {{ font-size: 0.95rem; color: #e0f2fe; margin-bottom: 20px; }}
    .btn {{ display: inline-block; background: #ffffff; color: #0284c7; padding: 12px 28px; border-radius: 30px; font-weight: 700; text-decoration: none; font-size: 0.95rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <span class="badge grade-{grade}">Audit Grade: {grade}</span>
        <h1 style="font-size: 1.8rem; font-weight: 800; margin-top: 8px;">{business_name}</h1>
        <p style="color: var(--text-muted); font-size: 0.9rem;">{niche} • <a href="https://{domain}" target="_blank" style="color: var(--accent-blue);">{domain}</a></p>
      </div>
      <div class="score-circle">
        <span class="score-num">{score}</span>
        <span class="score-label">out of 100</span>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title">⚠️ Identified Performance & SEO Bottlenecks</h2>
      {issues_html}
    </div>

    <div class="section">
      <h2 class="section-title">✅ Verified Site Assets & Passing Checks</h2>
      <div class="pass-list">
        {passes_html}
      </div>
    </div>

    <div class="section">
      <h2 class="section-title">🚀 Proposed 48-Hour Optimization Roadmap</h2>
      {steps_html}
    </div>

    <div class="footer-cta">
      <h3>Ready to optimize {domain} in 48 Hours?</h3>
      <p>Fixed for a $50 deposit with a 100% satisfaction guarantee. Local Asheville support.</p>
      <div style="font-size: 0.9rem; color: #e0f2fe; margin-top: 8px;">Contact: Tom Gronek • Asheville AI Business Solutions</div>
    </div>
  </div>
</body>
</html>
"""

def generate_previews():
    out_dir = os.path.join(os.path.dirname(__file__), "audit_previews")
    os.makedirs(out_dir, exist_ok=True)

    generated_files = []

    for p in PROSPECTS:
        issues_html = ""
        for issue in p["issues"]:
            is_crit = "critical" if issue["severity"] in ["CRITICAL", "FAIL"] else ""
            issues_html += f"""
      <div class="issue-card {is_crit}">
        <div class="issue-title">
          <span>{issue['title']}</span>
          <span style="font-size: 0.75rem; color: var(--accent-red);">{issue['severity']}</span>
        </div>
        <div class="issue-detail">{issue['detail']}</div>
      </div>"""

        passes_html = ""
        for item in p["passes"]:
          passes_html += f"""
        <div class="pass-item">
          <span class="pass-icon">✓</span>
          <span>{item}</span>
        </div>"""

        steps_html = ""
        for step in p["optimization_steps"]:
          steps_html += f"""
      <div class="step-item">{step}</div>"""

        content = HTML_TEMPLATE.format(
            business_name=p["business_name"],
            domain=p["domain"],
            niche=p["niche"],
            score=p["score"],
            grade=p["grade"],
            issues_html=issues_html,
            passes_html=passes_html,
            steps_html=steps_html
        )

        filepath = os.path.join(out_dir, p["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        generated_files.append(filepath)
        print(f"Generated visual audit report: {filepath}")

    return generated_files

if __name__ == "__main__":
    files = generate_previews()
    print(f"\nSuccessfully generated {len(files)} visual audit preview assets in 'audit_previews/'.")
