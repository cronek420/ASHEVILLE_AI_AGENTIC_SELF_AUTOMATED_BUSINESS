# Archived skills — 2026-08-09

190 skill directories, `skills_fixed.zip` (21.8 MB), and two copies of
`skills_index.json` were moved here from `.agents/skills/`.

`.agents/` went from **55.8 MB to 6.92 MB**.

## Why this was safe

`VERIFIED` before moving anything:

- No Python file in the project references `.agents/skills`, `skills_index`,
  `skills_fixed`, or `skill_instructions` — zero matches across the codebase.
- `.agents/skills.json` does not even point at this directory. It points at
  `C:/Users/crone/Projects/MASTER_FILES/NEW_UNIVERSAL_WORKSPACE_KIT_REFINED/.agents/skills`.
- `skills-lock.json` locks exactly one skill: `frontend-design`, which was kept.

So this tree was unreferenced weight. It cost build context on every container
image and made the handful of genuinely useful skills hard to find.

## What was kept and why

56 directories that match what this business actually does:

- **SEO and audit** — the core value proposition: `seo-audit`, `seo-fundamentals`,
  `schema-markup`, `geo-fundamentals`, `programmatic-seo`.
- **Conversion** — the "make them more money" half: the `*-cro` skills,
  `ab-test-setup`, `analytics-tracking`.
- **Outreach and copy** — `copywriting`, `copy-editing`, `email-sequence`,
  `email-systems`, `marketing-psychology`, `content-creator`, `social-content`.
- **Delivery quality** — `web-design-guidelines`, `web-performance-optimization`,
  `frontend-design`, `mobile-design`, `ui-ux-pro-max`.
- **The actual stack** — `gcp-cloud-run`, `docker-expert`, `python-patterns`,
  `powershell-windows`, `stripe-integration` (G3 payment links).
- **Discipline** — `systematic-debugging`, `verification-before-completion`,
  `production-code-audit`, `testing-patterns`, `writing-plans`.

## What was archived

Everything unrelated to a local web-services agency. The largest group was
offensive security — `metasploit-framework`, `sqlmap-database-pentesting`,
`active-directory-attacks`, `red-team-tools`, the privilege-escalation and
injection-testing sets, `shodan-reconnaissance`, `burp-suite-testing`,
`wireshark-analysis` and similar. Also platform-specific work this business does
not do: Avalonia, Moodle, Salesforce, Shopify, Discord/Telegram/Slack bots,
Twilio, Plaid, game development, and a long tail of framework guides.

## How to restore

Nothing was deleted. Move any directory back:

```powershell
Move-Item 'OLD_FILES_TO_DELETE\skills-archive-2026-08-09\<name>' '.agents\skills\<name>'
```

Per `.agents/rules/00-project-governance.md`, these stay here until Tom approves
permanent deletion.
