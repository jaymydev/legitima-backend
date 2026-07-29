---
name: project-state
description: Current Legitima backend state, active routes, deployment status
metadata:
  type: project
---

## Backend Status (FastAPI)

### Stable Endpoints
- **POST /cv/parse** — CV parsing with OCR (français), returns 5 max experiences, chronological order
  - Input: file (PDF/JPEG/PNG, ≤10MB)
  - Output: `Experience[]` with company, role, dates
  - OCR: CV_PARSE_OCR_LANG=fra (production setting)
  - Status: Working, tested with French CV samples

### Premium & Interview Prep (New - just merged)
- **POST /interview-preparation/use-cases** — Interview scenario suggestions
- **POST /interview-preparation/context** — Premium recruitment context (new endpoint)
- **POST /interview-preparation/suggestions** — Answer suggestions for questions
- **POST /interview-preparation/analyze-paragraph** — (uses /analyze internally, see gotchas)
- Status: Just merged `e1f74d3` (13 commits squashed)

### Sensitive Analysis (Stable)
- **POST /analyze** — Sensitive period reframing (HIGH-RISK)
  - Powers premium recruitment flow
  - Status: Stable but restricted (never modify without validation)

## Deployment
- **Current:** Render (temporary)
- **Next:** VPS migration planned
- **Language:** Python 3.9+, FastAPI, Pydantic, Tesseract OCR

## Recent Merge
- **PR #26 `e1f74d3`** — "Add interview answer suggestions" (today)
  - Squashed 13 commits: CV parsing hardening + interview prep workflows
  - Added routes: use-cases, context, suggestions
  - Updated docs/api-contract.md

## Local State
- `test_payload.json` — Manual testing payload, ignore in commits
- Tests passing in `test_interview_preparation.py`, `test_cv_parse.py`

## Next Steps
- Create project memory documentation (current task)
- Monitor /analyze stability (high-risk)
- Plan VPS migration from Render
