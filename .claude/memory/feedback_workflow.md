---
name: workflow-rules
description: Strict workflow rules for Legitima repos (frontend + backend)
metadata:
  type: feedback
---

## Global Rules (both repos)

**Rule 1:** Always create a new branch for each task — never work on main
**Why:** Clean history, easy to review, reversible
**How to apply:** `git checkout -b codex/<task-name>` before coding

**Rule 2:** One PR = one commit
**Why:** Clean history, easy to revert if needed
**How to apply:** Before push: verify with `git log main..HEAD --oneline`, squash if needed

**Rule 3:** Always verify commit count before creating PR
**Why:** Catch multi-commit branches before pushing
**How to apply:** `git log main..HEAD --oneline` — must show exactly 1 commit

**Rule 4:** Never work directly on main
**Why:** Prevents accidental commits to main
**How to apply:** Always branch first, PR for review

**Rule 5:** Always read AGENTS.md before modifying a repo
**Why:** Respects product boundaries and technical constraints
**How to apply:** Read AGENTS.md in the target repo before any changes

## Backend-specific rules

**Rule 6:** Never modify `/analyze` endpoint without explicit validation
**Why:** High-risk endpoint, powers sensitive period reframing, can break premium flow
**How to apply:** Always ask before touching analyze logic — this is restricted

**Rule 7:** Never log personal user data (CV content, career info, answers)
**Why:** Privacy/compliance
**How to apply:** Review all logging statements for sensitive data before commit

**Rule 8:** Never invent experience, diplomas, or skills in responses
**Why:** Core product principle: help users explain real paths, not fake ones
**How to apply:** All generation is user-centric, never hallucinate
[[reference_tech.md#AI-rules]]

**Rule 9:** Run pytest before commit
**Why:** Catch logic errors early
**How to apply:** Always run before staging for backend changes

**Rule 10:** Keep `/cv/parse` 100% non-LLM (OCR only)
**Why:** Deterministic parsing, no hallucinations
**How to apply:** Never add LLM logic to /cv/parse, only OCR + structure

**Rule 11:** Preserve unrelated local changes
**Why:** Don't accidentally commit something you weren't working on
**How to apply:** When branching, check `git status` first; ignore test_payload.json

## Global Rules (Data/Integration)

**Rule 12:** Never invent backend endpoints
**Why:** Frontend can't call them; breaks contract
**How to apply:** Follow docs/api-contract.md strictly

**Rule 13:** Update docs/api-contract.md when behavior changes
**Why:** Frontend depends on accurate contract
**How to apply:** Always update contract + tests together
