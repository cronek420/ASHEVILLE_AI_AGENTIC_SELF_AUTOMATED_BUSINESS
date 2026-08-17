---
name: privacy-and-data-handling
description: Handle project data, identities, and credentials safely.
---

# Privacy and Data Handling

- Inventory sensitive data before modifying or sharing it.
- Never copy raw secrets to logs, examples, fixtures, archives, or version control.
- Use placeholders and `.env.example` for configuration examples.
- Keep production, sample, synthetic, and archived data clearly labeled.
- Quarantine irrelevant non-sensitive supplied files in `OLD_FILES_TO_DELETE/`; do not permanently delete them without approval.
- Report suspected credential exposure and recommend rotation without revealing values.
