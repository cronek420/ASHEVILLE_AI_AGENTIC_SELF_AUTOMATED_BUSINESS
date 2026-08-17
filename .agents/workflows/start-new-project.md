# Start a New Project

Do not implement anything until this workflow is complete.

1. Read `GEMINI.md`, `.agent/rules/00-project-governance.md`, and `PROJECT_ONBOARDING.md`.
2. Ask the user to complete the onboarding questionnaire. Ask only focused follow-ups for material gaps.
3. Inspect every supplied file, folder, repository instruction, dependency manifest, test, asset, and existing implementation.
4. Create a capability inventory: installed skills, tools, connectors, permissions, integrations, credentials required, and missing capabilities. Read selected skill instructions before acting.
5. Keep relevant files in place. Move irrelevant, obsolete, duplicate, or unrelated supplied files into `OLD_FILES_TO_DELETE/`, preserving their relative paths when practical. Do not move credentials into that folder; report them as sensitive and ask the user how they should be handled.
6. Update `PROJECT_CONTEXT.md`, `PROJECT_REQUIREMENTS.md`, `BUILD_PLAN.md`, and `BUILD_STATUS.md` with verified information only.
7. Report: project understanding, retained files, moved files and reasons, source-of-truth hierarchy, feature status, risks, missing inputs, recommended skills, and a dependency-aware plan with acceptance criteria.
8. Wait for approval before consequential implementation, external actions, or permanent deletions.
