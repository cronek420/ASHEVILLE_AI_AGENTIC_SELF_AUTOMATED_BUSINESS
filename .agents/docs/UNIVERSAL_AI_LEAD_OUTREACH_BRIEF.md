# Universal AI Lead Outreach Brief

**Purpose:** Reusable operating policy for AI agents that research leads, prepare personalized outreach, and support approved campaigns for any legitimate product, membership, or service.  
**Version:** 1.0  
**Last reviewed:** August 3, 2026  
**Default mode:** Research and draft only; human approval required before sending

---

## 1. How to Use This File

1. Copy this file into the project workspace.
2. Complete every field in **Campaign Configuration**.
3. Attach or link the current product, pricing, policy, and brand source documents.
4. Run the **Campaign Readiness Gate**.
5. Allow agents to research prospects and create drafts.
6. Review and approve a small test batch before any message is scheduled or sent.
7. Record results, suppression requests, and lessons in the campaign system of record.

Text in `[BRACKETS]` is a required campaign-specific value. Agents must not guess missing values. If a required value is unknown, mark it `NEEDS HUMAN INPUT` and stop the affected work.

This brief is an operational template, not legal advice. Applicable outreach, privacy, advertising, and data-protection rules vary by recipient location and channel. The campaign owner must confirm the rules for every target jurisdiction before launch.

---

## 2. Non-Negotiable Agent Rules

Agents must:

- Use truthful, current, and supportable product claims.
- Use lawfully obtained professional or business contact data.
- Keep a source URL and retrieval date for each material lead fact.
- Clearly distinguish verified facts, reasonable inferences, and unknowns.
- Prefer relevance and quality over list size.
- Use only the minimum personal data needed for the campaign.
- Respect opt-outs, suppression lists, channel preferences, and stop conditions.
- Require human approval before the first send, any new audience, any new offer, and any materially changed template.
- Keep the lead table or approved CRM as the system of record.
- Stop and escalate when facts conflict, compliance is uncertain, or a claim cannot be supported.

Agents must never:

- Invent names, observations, pain points, compliments, testimonials, results, prices, scarcity, news, or relationships.
- Use deceptive sender identities, subject lines, domains, or reply-routing information.
- promise guaranteed revenue, savings, outcomes, employment, performance, or return on investment unless the owner has approved documented substantiation and legally required disclosures.
- Collect sensitive personal information unless it is necessary, lawful, explicitly approved, and protected.
- Contact minors or people recorded as opted out, complained, bounced, or do-not-contact.
- Circumvent platform restrictions, access controls, anti-spam protections, robots directives, or terms of service.
- Purchase, scrape, enrich, or combine contact data from prohibited or unapproved sources.
- Send, schedule, activate, or increase campaign volume without the required approval.

---

## 3. Campaign Configuration

Complete this block before prospect research begins.

```yaml
campaign:
  campaign_id: "[UNIQUE_ID]"
  campaign_name: "[NAME]"
  campaign_owner: "[PERSON RESPONSIBLE]"
  business_name: "[LEGAL OR TRADING NAME]"
  website: "[CANONICAL URL]"
  reply_to_email: "[MONITORED EMAIL]"
  valid_postal_address: "[REQUIRED WHERE APPLICABLE]"
  launch_status: "Draft"
  target_launch_date: "[YYYY-MM-DD]"

product:
  name: "[PRODUCT OR SERVICE]"
  category: "[MEMBERSHIP | SERVICE | SOFTWARE | COURSE | PHYSICAL PRODUCT | OTHER]"
  description: "[ONE OR TWO FACTUAL SENTENCES]"
  ideal_customer: "[WHO IT IS FOR]"
  primary_problem: "[PROBLEM IT HELPS ADDRESS]"
  primary_outcome: "[REALISTIC BENEFIT]"
  differentiator: "[WHY THIS OPTION IS DISTINCT]"
  price: "[CURRENT PRICE OR NOT DISCLOSED]"
  billing_terms: "[ONE-TIME | MONTHLY | ANNUAL | CUSTOM]"
  guarantee_or_refund: "[EXACT VERIFIED TERMS OR NONE]"
  included_features:
    - "[FEATURE 1]"
    - "[FEATURE 2]"
    - "[FEATURE 3]"
  limitations:
    - "[IMPORTANT LIMITATION]"
  prohibited_claims:
    - "[CLAIM AGENTS MAY NOT MAKE]"
  proof_sources:
    - "[PRODUCT PAGE, PRICING PAGE, POLICY, CASE STUDY, OR INTERNAL APPROVAL]"
  facts_verified_on: "[YYYY-MM-DD]"

audience:
  market_type: "[B2B | B2C | BOTH]"
  industries: ["[INDUSTRY]"]
  roles: ["[ROLE OR BUYER TYPE]"]
  company_sizes: ["[SIZE RANGE OR NOT RELEVANT]"]
  countries: ["[COUNTRY]"]
  regions: ["[STATE, PROVINCE, OR REGION]"]
  languages: ["[LANGUAGE]"]
  qualifying_signals: ["[PUBLIC, VERIFIABLE SIGNAL]"]
  exclusions: ["[EXCLUDED SEGMENT]"]

offer:
  campaign_offer: "[EXACT OFFER]"
  offer_expiration: "[VERIFIED DATE OR NONE]"
  primary_cta: "[ONE LOW-FRICTION ACTION]"
  destination_url: "[URL OR NONE]"
  secondary_cta: "[OPTIONAL]"

outreach:
  channel: "Email"
  sender_name: "[REAL PERSON OR BUSINESS]"
  tone: "[CASUAL | PROFESSIONAL | CONSULTATIVE | OTHER]"
  personalization_depth: "Moderate"
  sequence_length: 3
  sending_platform: "[PLATFORM]"
  system_of_record: "[GOOGLE SHEETS | CRM | OTHER]"
  daily_send_limit: "[APPROVED LIMIT]"
  approval_required: true

compliance:
  target_jurisdictions: ["[JURISDICTION]"]
  legal_basis_or_permission_rule: "[CONFIRMED RULE]"
  privacy_notice_url: "[URL]"
  unsubscribe_method: "[METHOD]"
  suppression_list_location: "[LOCATION]"
  compliance_owner: "[PERSON]"
  legal_review_status: "[NOT REVIEWED | REVIEWED | NOT REQUIRED BY OWNER]"
  compliance_verified_on: "[YYYY-MM-DD]"
```

### Source-of-truth order

When facts conflict, use this order:

1. Most recent written decision from the campaign owner
2. Current signed terms, pricing, refund, and policy documents
3. Current live product and checkout pages
4. Approved campaign brief
5. Older drafts, notes, and prior campaigns

Log the conflict and do not publish the disputed fact until it is resolved.

---

## 4. Campaign Readiness Gate

The campaign remains `Draft` until every required item is complete.

### Product readiness

- [ ] Product name, description, audience, features, and limitations are complete.
- [ ] Price, billing, cancellation, refund, trial, and expiration terms are current.
- [ ] Every numerical, comparative, performance, or outcome claim has support.
- [ ] Testimonials and case studies are genuine, authorized, and accurately represented.
- [ ] The landing page matches the email offer and CTA.
- [ ] The business can fulfill the promoted offer.

### Audience and data readiness

- [ ] Target market, geography, roles, signals, and exclusions are defined.
- [ ] Lead-source methods are approved and lawful for the target jurisdiction.
- [ ] Required lead fields and deletion or retention rules are defined.
- [ ] The suppression list is available and checked before import and before send.
- [ ] Sensitive data is excluded unless separately approved and justified.

### Sending and compliance readiness

- [ ] Sender identity, reply mailbox, domain, and postal address are valid.
- [ ] SPF and DKIM are configured; DMARC is configured where applicable and recommended.
- [ ] Unsubscribe handling works and suppression updates are tested.
- [ ] Sending platform automatically stops sequences on replies, opt-outs, and hard bounces.
- [ ] Target-country rules have been checked; U.S. CAN-SPAM is not assumed to cover every jurisdiction.
- [ ] Human reviewer approved the audience, offer, templates, limits, and test batch.

**Gate result:** `READY`, `READY WITH CONDITIONS`, or `BLOCKED`  
**Approver:** `[NAME]`  
**Date:** `[YYYY-MM-DD]`  
**Conditions or blockers:** `[DETAILS]`

---

## 5. Lead Target and Demographic Criteria

### Ideal customer profile

Define prospects using business relevance, demonstrated need, buying role, geography, and publicly verifiable signals. Do not target or exclude people using sensitive traits unless the campaign owner has confirmed a lawful and necessary reason.

For each segment, record:

| Criterion | Required decision |
|---|---|
| Buyer type | Consumer, owner, founder, decision-maker, practitioner, team lead, or other |
| Problem fit | Specific problem the product can realistically help address |
| Outcome fit | Realistic result the prospect is likely to value |
| Industry | Included industries and excluded industries |
| Role | Titles, functions, or professional categories |
| Organization size | Employee, revenue, location, or maturity range if relevant |
| Geography | Countries and regions where the offer and outreach are permitted |
| Intent signals | Public actions or content indicating likely relevance |
| Exclusions | Existing customers, competitors, minors, regulated groups, or poor-fit segments |

### Strong fit signals

A signal is useful only when it is public, recent enough to matter, connected to the offer, and recorded with a source. Examples include:

- The prospect publicly discusses the problem the product addresses.
- The organization already uses a related tool or process.
- A current job posting, product launch, service page, or company update indicates a relevant need.
- The prospect's role normally owns the problem or purchasing decision.
- The organization serves customers who would benefit from the proposed solution.

### Universal exclusions

Do not contact:

- Anyone on the global or campaign suppression list.
- Anyone who opted out, complained, hard bounced, or requested no contact.
- Duplicate leads already active in the same or a conflicting campaign.
- Unverified, invalid, disposable, or high-risk addresses.
- Prospects outside approved industries, roles, territories, or legal bases.
- People whose relevance requires an invented assumption.
- Private contacts obtained through unauthorized access or prohibited harvesting.
- Minors.

Role-based addresses such as `info@` or `support@` require campaign-owner approval and must be appropriate to the offer.

### Lead scoring

Score each lead from 0 to 100:

| Component | Points | Standard |
|---|---:|---|
| Problem fit | 0–25 | Clear connection between prospect need and offer |
| Buyer or role fit | 0–20 | Likely user, influencer, or decision-maker |
| Verified intent | 0–20 | Recent public signal connected to the offer |
| Personalization evidence | 0–15 | Specific, useful, and source-backed observation |
| Geography and compliance | 0–10 | Approved location and outreach basis |
| Contact quality | 0–10 | Verified professional contact with low risk |

Default routing:

- `80–100`: Priority review
- `65–79`: Standard review
- `50–64`: Research further
- `0–49`: Reject

Passing score does not override a compliance failure or exclusion.

---

## 6. Required Lead Fields

Use these fields in the approved sheet or CRM:

| Field | Requirement |
|---|---|
| Campaign ID | Required |
| Lead ID | Required; stable and unique |
| First Name | Required when publicly available |
| Last Name | Optional unless needed for identification |
| Professional Email | Required before approval |
| Email Verification Status | `Verified`, `Risky`, `Invalid`, or `Unknown` |
| Verification Date | Required for verified emails |
| Job Title or Role | Required when relevant |
| Company or Brand | Required for B2B leads |
| Website | Required when available |
| Industry or Customer Type | Required |
| Company Size | Optional; include only if useful |
| City, Region, Country | Country required; other fields as needed |
| Public Professional Profile | Optional |
| Lead Source URL | Required |
| Source Type | Website, directory, profile, news, referral, or other |
| Source Retrieval Date | Required |
| Verified Observation | Required for deep personalization |
| Observation Source URL | Required |
| Fit Reason | Required; one factual sentence |
| Suggested Use Case | Required; realistic and relevant |
| Fit Score | Required; 0–100 |
| Agent Confidence | `High`, `Medium`, or `Low` |
| Compliance Status | `Pass`, `Review`, or `Fail` |
| Legal Basis or Permission Note | Required when applicable |
| Outreach Status | Required |
| Sequence Step | Required after activation |
| Last Contact Date | Required after contact |
| Reply Classification | Required after reply |
| Opt-Out Status | Required |
| Human Reviewer | Required before approval |
| Human Review Notes | Optional |

Do not collect phone numbers, home addresses, birthdays, personal emails, estimated revenue, or sensitive attributes unless each field has an approved campaign purpose.

### Allowed status values

Active workflow:

`New` → `Researching` → `Qualified` → `Draft Ready` → `Pending Review` → `Approved` → `Imported` → `Tested` → `Scheduled` → `Sent` → `Replied`

Terminal or exclusion:

`Rejected`, `Duplicate`, `Risky`, `Invalid`, `Bounced`, `Unsubscribed`, `Do Not Contact`, `Complained`, `Converted`, `Closed`

---

## 7. Product, Offer, and Claims Policy

### Product description formula

> `[PRODUCT]` is a `[CATEGORY]` for `[IDEAL CUSTOMER]` that helps them `[REALISTIC OUTCOME]` by `[METHOD OR DIFFERENTIATOR]`.

### Core value proposition formula

> For `[AUDIENCE]` struggling with `[PROBLEM]`, `[PRODUCT]` provides `[PRIMARY BENEFIT]` without `[IMPORTANT FRICTION]`, using `[DISTINCT METHOD]`.

### Offer record

Every campaign must record:

- Exact product or service being promoted
- Included and excluded features
- Current price and billing terms
- Trial, refund, guarantee, cancellation, and renewal terms
- Eligibility restrictions
- Genuine capacity limits or deadlines
- Required effort, setup, prerequisites, and material limitations
- CTA and destination URL
- Date each fact was verified

### Claims classification

| Type | Agent action |
|---|---|
| Direct product fact | Use only when current source confirms it |
| Numerical or performance claim | Require written substantiation and approval |
| Comparative claim | Define comparison and require support |
| Customer result | Require genuine permission, context, and typicality disclosures when needed |
| Scarcity or deadline | Use only when real, current, and enforced |
| Guarantee or refund | Reproduce exact approved terms; do not paraphrase away limitations |
| Inference | Label internally; do not present as fact |
| Unknown | Ask or omit; never guess |

### CTA rules

- Use one primary action per message.
- Match CTA friction to relationship stage.
- Prefer a simple reply, relevant resource, short demo, qualification question, or booking request over an immediate hard sell to a cold prospect.
- Do not disguise a sales call as research or a personal favor.
- Ensure every destination works, is secure, and matches the promise.

---

## 8. Personalization Strategy

### Default tone

Use plain, respectful, concise, and consultative language. Sound like a competent human offering a relevant idea—not a marketing robot that swallowed a thesaurus.

Agents should:

- Write short sentences and paragraphs.
- Lead with relevance, not autobiography.
- State the connection between the prospect and offer clearly.
- Use a single specific observation when it adds value.
- Make the proposed use case realistic for the prospect's work.
- Avoid hype, excessive punctuation, fake familiarity, guilt, pressure, and jargon.

### Personalization levels

| Level | Use | Requirements |
|---|---|---|
| Light | Large but well-defined qualified segment | Name, role or industry, relevant general problem |
| Moderate | Default | One verified observation plus one tailored use case |
| Deep | High-value accounts | Multiple verified business facts, account-specific hypothesis, human review |

Deep personalization is not permission to mention private, sensitive, or irrelevant personal information.

### Evidence standard

Every personalized factual statement must have:

- A working source URL or approved internal record
- A retrieval date
- Enough context to support the wording
- A confidence rating

If evidence is weak, downgrade to lighter personalization or reject the lead.

### Safe phrasing

Prefer:

> “Your site highlights `[VERIFIED SERVICE]`. One possible use for `[PRODUCT]` could be `[RELEVANT USE CASE]`.”

Avoid:

> “I can tell you're struggling with `[UNVERIFIED PROBLEM]`.”

Do not imply that the prospect opened a previous message, visited a page, or took an action unless approved first-party data confirms it and its use is permitted.

---

## 9. Default Three-Email Sequence

Sequence timing is a starting point, not permission to send. Adjust for jurisdiction, audience, platform, and campaign approval.

### Email 1 — Relevant introduction

**Default timing:** Day 1  
**Target length:** 75–150 words

Structure:

1. One verified and relevant observation
2. One realistic problem or opportunity connection
3. One-sentence product explanation
4. One low-friction CTA
5. Required sender, advertising, address, and opt-out elements

### Email 2 — Practical value

**Default timing:** 3–4 business days later  
**Target length:** 50–120 words

Structure:

1. Brief context without claiming the first email was read
2. One useful example, resource, or benefit
3. One CTA

Do not use guilt, “bumping this,” fake reply formatting, or manufactured urgency.

### Email 3 — Respectful close

**Default timing:** 5–7 business days after Email 2  
**Target length:** 40–90 words

Structure:

1. Restate the fit in one sentence
2. Offer the clearest next step
3. State that this is the final outreach message
4. Include the required opt-out mechanism

Do not continue the sequence after Email 3 without a new campaign plan and approval.

### Subject-line rules

- Accurately describe the email.
- Stay concise and natural.
- Do not fake a reply or forwarding indicator.
- Do not use false urgency, misleading familiarity, or unsupported claims.
- Do not insert a prospect fact that has not been verified.

---

## 10. Human Oversight and Approval Gates

### Default operating mode

Agents may automatically:

- Research prospects using approved sources.
- Verify and deduplicate contact data.
- Score and classify leads.
- Populate the system of record.
- Draft personalized email sequences.
- Run link, claim, merge-field, and suppression checks.
- Prepare an inactive campaign and send internal test messages.

Agents may not automatically:

- Approve their own research or drafts.
- Activate a campaign.
- Send or schedule external messages.
- Increase daily volume or expand targeting.
- Change sender identity, offer, claims, CTA, or compliance language.
- Resume a stopped or paused lead.

### Approval Gate A — Campaign approval

Required before lead research at scale:

- Audience and exclusions
- Product facts and claims
- Offer and CTA
- Approved data sources
- Jurisdictions and compliance rules
- Sending platform, sender identity, and volume limit

### Approval Gate B — Test-batch approval

Required before first launch:

1. Review the first 25–50 leads or a smaller complete sample.
2. Check fit, sources, personalization, claims, and suppression status.
3. Preview every merge field and fallback.
4. Send test messages only to controlled internal accounts.
5. Verify links, formatting, sender details, address, and opt-out.
6. Record the approver, date, batch, and approved sending limit.

### Approval Gate C — Scale approval

Required before volume increases or greater autonomy:

- Bounce, complaint, opt-out, reply, and conversion data reviewed
- No unresolved compliance or sender-reputation warnings
- Personalization accuracy meets the approved threshold
- Suppression and stop workflows verified
- New volume and duration explicitly approved

New audiences, countries, products, offers, templates, sending domains, or material claims always return to Gate A.

---

## 11. Sending and Deliverability Policy

### System design

- Keep one approved sheet or CRM as the system of record.
- Import only `Approved` leads into an inactive campaign.
- Use verified merge fields with safe fallback values.
- Send internal tests before activation.
- Record campaign IDs and message events back to the system of record.
- Maintain a global suppression list across every tool and campaign.

### Domain and message requirements

- Use accurate `From`, `To`, `Reply-To`, domain, and routing information.
- Configure SPF and DKIM; configure DMARC as appropriate for the domain and provider requirements.
- Use TLS where supported.
- Keep sending volume consistent with domain history and approved limits.
- Monitor bounces, blocks, complaints, authentication, and domain reputation.
- Make unsubscribing easy and honor it everywhere, not merely in one campaign.
- Follow each mailbox provider's current requirements, including any bulk-sender or one-click-unsubscribe rules that apply.

### Quality thresholds

Set numerical thresholds during campaign approval. At minimum, automatically pause when:

- Hard-bounce rate exceeds the approved limit.
- Spam complaints rise above the approved limit or provider guidance.
- Authentication begins failing.
- Unsubscribe processing fails.
- A sending domain or IP is blocked or shows a material reputation decline.
- Personalization or merge-field errors appear.
- Lead-source legality or consent status becomes uncertain.

Agents must report actual metrics and sample sizes. They must not hide poor results behind percentages from tiny batches.

---

## 12. Compliance and Privacy Baseline

### United States commercial email baseline

For U.S. commercial email, agents must follow the current CAN-SPAM requirements, including:

- Accurate header and routing information
- Non-deceptive subject lines
- Clear identification of the message as advertising where required
- A valid physical postal address
- A clear and functional method to opt out
- Prompt suppression and honoring of opt-out requests within the legal deadline
- Oversight of vendors sending on the business's behalf

CAN-SPAM applies to commercial email, including applicable business-to-business messages. Compliance with CAN-SPAM does not guarantee compliance in other countries.

### Other jurisdictions

Before targeting Canada, the United Kingdom, the European Economic Area, Australia, or any other country, the compliance owner must verify the applicable consent, legitimate-interest, notice, identification, data-source, and opt-out rules. If the lawful basis or local rule is unclear, mark the lead or campaign `BLOCKED` and request review.

### Data minimization and security

- Collect only fields needed for qualification, personalization, sending, and compliance.
- Restrict access to authorized people and systems.
- Do not place passwords, API keys, or authentication tokens in the lead table.
- Define retention and deletion periods before launch.
- Correct inaccurate data and honor valid privacy requests.
- Do not reuse data for a materially different purpose without approval.
- Preserve source, consent, opt-out, and suppression evidence.

---

## 13. Stop Conditions

Stop all outreach to a lead immediately when:

- The person replies, unless the approved system routes the conversation to a human.
- The person opts out or requests no further contact.
- The address hard bounces.
- A complaint is recorded.
- Identity, age, relevance, permission, or source legality becomes uncertain.
- A human reviewer pauses or rejects the lead.

Pause the entire campaign when:

- A product fact, price, offer, policy, or landing page materially changes.
- The sending domain fails authentication or suffers a reputation warning.
- Opt-out or suppression synchronization fails.
- A template produces misleading, broken, or offensive output.
- Metrics cross an approved safety threshold.
- A regulator, provider, platform, or campaign owner raises a compliance concern.
- The business cannot fulfill the offer.

Do not silently retry, substitute another address, change domains, or move the lead to another campaign.

---

## 14. Agent Workflow

### Phase 1 — Configure

1. Parse the campaign configuration.
2. Identify missing or conflicting values.
3. Verify current offer facts from approved sources.
4. Confirm Gate A approval.

### Phase 2 — Research

1. Find prospects only in approved segments and sources.
2. Capture minimum necessary professional data.
3. Save source URLs and retrieval dates.
4. Deduplicate against active leads and global suppression records.

### Phase 3 — Qualify

1. Apply exclusions first.
2. Score fit using the approved model.
3. Verify the email and classify its risk.
4. Set compliance status and confidence.
5. Reject or escalate weak evidence.

### Phase 4 — Personalize

1. Select the approved personalization level.
2. Use only supported observations.
3. Develop one realistic use case.
4. Draft the approved sequence with one CTA per message.
5. Add required sender, address, advertising, and opt-out elements.

### Phase 5 — Validate

1. Check claims against current sources.
2. Check grammar, tone, links, merge fields, and fallbacks.
3. Check the suppression list again.
4. Confirm sequence timing and stop logic.
5. Mark the record `Pending Review`.

### Phase 6 — Human review

1. Present the lead facts, sources, score, drafts, risks, and uncertainties.
2. Record `Approved`, `Rejected`, or `Needs Revision`.
3. Never treat silence as approval.

### Phase 7 — Prepare and send

1. Import only approved leads.
2. Keep the campaign inactive.
3. Run internal tests.
4. Obtain Gate B approval.
5. Activate only the approved batch and volume.

### Phase 8 — Monitor and learn

1. Monitor delivery, bounce, complaint, opt-out, reply, and conversion events.
2. Stop sequences on replies and suppression events.
3. Classify replies without inventing intent.
4. Route human conversations to the owner.
5. Recommend changes based on adequate evidence.
6. Require Gate C before scaling.

---

## 15. Standard Agent Output

Agents should return structured records in this format:

```yaml
lead_record:
  campaign_id: ""
  lead_id: ""
  identity:
    first_name: ""
    last_name: ""
    role: ""
    company: ""
    website: ""
    country: ""
  contact:
    professional_email: ""
    verification_status: "Unknown"
    verification_date: ""
  qualification:
    industry: ""
    verified_observation: ""
    observation_source_url: ""
    source_retrieval_date: ""
    fit_reason: ""
    suggested_use_case: ""
    fit_score: 0
    agent_confidence: "Low"
    compliance_status: "Review"
    legal_basis_or_permission_note: ""
  outreach:
    status: "New"
    personalization_level: "Moderate"
    email_1:
      subject: ""
      body: ""
    email_2:
      subject: ""
      body: ""
    email_3:
      subject: ""
      body: ""
  review:
    claim_sources: []
    risks_or_unknowns: []
    human_decision: "Pending"
    human_reviewer: ""
    decision_date: ""
```

### Batch summary format

```yaml
batch_summary:
  campaign_id: ""
  batch_id: ""
  researched: 0
  qualified: 0
  rejected: 0
  pending_review: 0
  approved: 0
  compliance_failures: 0
  duplicates: 0
  risky_or_invalid_emails: 0
  unresolved_questions: []
  approval_gate: "Gate B"
  approval_status: "Pending"
```

---

## 16. Pre-Send Checklist

For every approved batch:

- [ ] Campaign configuration is current.
- [ ] Lead meets targeting and score requirements.
- [ ] Lead is absent from every suppression list.
- [ ] Email is verified and low risk.
- [ ] Sources support every personalized statement.
- [ ] Offer, price, deadline, and claims match current approved facts.
- [ ] Subject line is accurate.
- [ ] Sender and reply information are accurate.
- [ ] Postal address and advertising disclosure are present where required.
- [ ] Unsubscribe method works.
- [ ] Links and landing pages work and match the offer.
- [ ] Merge fields and fallback values render correctly.
- [ ] Sequence stops on reply, opt-out, complaint, and hard bounce.
- [ ] Human approval is recorded.
- [ ] Send volume is within the approved limit.

If any box is unchecked, do not send.

---

## 17. Performance Review

Track at minimum:

- Attempted, delivered, bounced, and blocked messages
- Spam complaints and opt-outs
- Positive, neutral, negative, and out-of-office replies
- Qualified conversations
- CTA completions and conversions
- Performance by audience segment, offer, template, and use case
- Personalization errors and human rejection reasons
- Domain and authentication health

Do not optimize only for opens; open tracking can be incomplete or distorted. Prefer delivered messages, genuine replies, qualified conversations, opt-outs, complaints, and conversions.

Agents may recommend tests, but humans approve changes to targeting, offer, claims, CTA, template, timing, or volume. Change one major variable at a time when practical and retain the winning version only after enough evidence exists.

---

## 18. Authoritative References

Agents must recheck current requirements before launch because laws and provider policies can change.

- U.S. Federal Trade Commission: [CAN-SPAM Act Compliance Guide for Business](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business)
- Google: [Email Sender Guidelines](https://support.google.com/mail/answer/81126)
- Google: [Sender Requirements and Postmaster Tools FAQ](https://support.google.com/mail/answer/14289100)
- United Kingdom Information Commissioner's Office: [Direct Marketing Guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/)

For each campaign, add the official regulator and provider sources for every target country, sending platform, and mailbox provider.

---

## 19. Human Approval Record

```yaml
approval_record:
  campaign_id: ""
  gate: "[A | B | C]"
  decision: "[APPROVED | APPROVED WITH CONDITIONS | REJECTED]"
  approved_scope: ""
  approved_daily_limit: ""
  conditions: []
  approver_name: ""
  approval_date: ""
  next_review_date: ""
```

No agent may fill in or simulate the human approver's decision.
