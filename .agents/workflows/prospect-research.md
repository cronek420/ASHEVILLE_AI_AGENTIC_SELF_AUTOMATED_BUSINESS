# Workflow: Prospect Research

```yaml
agent: Scout-Research
governance: .agents/rules/04-safety-and-truthfulness.md
```

## Steps
1. **Target Identification:** Identify local businesses in Asheville / Buncombe County, NC matching active offer criteria using truthful public web information.
2. **Visible Need Verification:** Verify specific, observable problems (e.g. missing mobile optimization, broken links, absent GMB profile details, unpopulated menu/booking system).
3. **Duplicate & Do-Not-Contact Check:**
   - Search `Prospect Tracker` for matching business name, domain, email, or phone.
   - Verify prospect is not marked `Do Not Contact`, `Opt-Out`, or `Ineligible`.
4. **Source Recording:** Record exact public source URL where business data was observed.
5. **Change Packet Generation:** Formulate structured Change Packet for `Atlas-Orchestrator` containing:
   - `prospect_name`, `business_niche`, `city`, `public_source_url`, `observed_need`, `verification_status`.
