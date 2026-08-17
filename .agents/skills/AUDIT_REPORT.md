# Skills Package Audit

## Summary

- Skill files: 256
- Valid YAML frontmatter: 256
- Duplicate YAML names fixed: 4 files across 2 collisions
- Embedded `.git` directory removed
- Index rebuilt from actual skill files
- Risk labels assigned: low, medium, or high
- Files over 500 lines: 31

## Important Notes

The package is usable, but the 31 oversized skills should be shortened or split into reference files. They were not automatically rewritten because bulk compression can silently remove required procedures, examples, or safety constraints.

## Oversized Skills

- `email-sequence/SKILL.md` — 925 lines
- `api-security-best-practices/SKILL.md` — 907 lines
- `github-workflow-automation/SKILL.md` — 846 lines
- `claude-d3js-skill/SKILL.md` — 820 lines
- `social-content/SKILL.md` — 807 lines
- `autonomous-agent-patterns/SKILL.md` — 761 lines
- `llm-app-patterns/SKILL.md` — 760 lines
- `competitor-alternatives/SKILL.md` — 750 lines
- `writing-skills/SKILL.md` — 737 lines
- `kaizen/SKILL.md` — 730 lines
- `voice-ai-engine-development/SKILL.md` — 721 lines
- `loki-mode/SKILL.md` — 721 lines
- `bun-development/SKILL.md` — 691 lines
- `web-performance-optimization/SKILL.md` — 646 lines
- `javascript-mastery/SKILL.md` — 645 lines
- `cc-skill-frontend-patterns/SKILL.md` — 633 lines
- `referral-program/SKILL.md` — 602 lines
- `moodle-external-api-development/SKILL.md` — 597 lines
- `scanning-tools/SKILL.md` — 589 lines
- `cc-skill-backend-patterns/SKILL.md` — 584 lines
- `free-tool-strategy/SKILL.md` — 576 lines
- `paywall-upgrade-cro/SKILL.md` — 570 lines
- `nestjs-expert/SKILL.md` — 552 lines
- `paid-ads/SKILL.md` — 551 lines
- `top-web-vulnerabilities/SKILL.md` — 543 lines
- `production-code-audit/SKILL.md` — 540 lines
- `cc-skill-coding-standards/SKILL.md` — 522 lines
- `linux-shell-scripting/SKILL.md` — 504 lines
- `linux-privilege-escalation/SKILL.md` — 504 lines
- `shodan-reconnaissance/SKILL.md` — 503 lines
- `cloud-penetration-testing/SKILL.md` — 501 lines

## Duplicate Names Corrected

- `internal-comms` → `internal-comms-anthropic` and `internal-comms-community`
- `brand-guidelines` → `brand-guidelines-anthropic` and `brand-guidelines-community`

## Recommended Next Pass

Refactor oversized files using progressive disclosure:

1. Keep `SKILL.md` under 500 lines.
2. Put detailed examples, tables, and reference material in sibling `.md` files.
3. Keep YAML descriptions concise and trigger-focused.
4. Put mandatory workflow, constraints, and verification steps near the top.
5. Remove claims that depend on current market share, vendor leadership, or time-sensitive statistics unless maintained.
