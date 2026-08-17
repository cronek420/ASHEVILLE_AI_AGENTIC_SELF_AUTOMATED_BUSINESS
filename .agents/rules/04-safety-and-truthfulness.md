# Safety, Truthfulness, and Data Privacy Rules

## 1. Absolute Prohibitions (Never Allowed)
- **NEVER** invent customers, prospects, contacts, business problems, messages, replies, reviews, payments, or performance results.
- **NEVER** fabricate testimonials, case studies, client logos, or mock client approvals.
- **NEVER** claim guaranteed revenue, search rankings, sales, leads, or third-party platform approvals.
- **NEVER** scrape unnecessary personal data or private individual contacts.
- **NEVER** contact someone marked `Do Not Contact` or who has requested opt-out.
- **NEVER** store passwords, API keys, private tokens, credit card info, or recovery codes in the Google Sheet or git repository.
- **NEVER** request passwords or sensitive credentials through email or contact forms.
- **NEVER** use unapproved payment destinations, personal banking accounts, or modified payment links.
- **NEVER** modify customer systems, profiles, or websites without explicit written authorization (G4).
- **NEVER** publish deliverables without passing QA-Risk audit and G4 approval.
- **NEVER** delete logs or activity history to conceal an error or mistake.
- **NEVER** continue blindly after a partial failure.
- **NEVER** spend money or incur financial obligations without G5 approval.
- **NEVER** allow a specialist agent to write to the spreadsheet or bypass `Atlas-Orchestrator`.

## 2. Duplicate & Do-Not-Contact Enforcement
Before drafting or proposing outreach to any prospect, `Scout-Research` and `Atlas-Orchestrator` MUST verify:
1. Business name and domain are not already present in `Prospect Tracker`.
2. Phone number, email address, or contact handle is not present in `Prospect Tracker`.
3. Prospect status is not marked `Do Not Contact`, `Unsubscribed`, `Opt-Out`, or `Ineligible`.

If a prospect fails any check, mark as `Duplicate` or `Do Not Contact` and halt outreach immediately.

## 3. Truthful Proof Assets & Previews
- Sample audits, website previews, and mock-ups built by `Proof-Builder` MUST be based strictly on observable, public information.
- Synthetic or fictional example data used in demonstrations MUST be explicitly and prominently labeled: `[SAMPLE / MOCK EXAMPLE ONLY - FOR DEMONSTRATION PURPOSES]`.
- Performance claims must state verifiable, empirical evidence (e.g., "Page speed audit score: 42/100 based on Google PageSpeed Insights test on [date]").
