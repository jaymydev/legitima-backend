---
name: tech-patterns
description: API endpoints, OCR patterns, architectural rules, gotchas
metadata:
  type: reference
---

## Backend API Endpoints

### CV Parsing (Stable)
- `POST /cv/parse` → returns `Experience[]` (max 5, chronological)
  - Input: file (PDF/JPEG/PNG, ≤10MB)
  - Output: `[{company, role, startDate, endDate}, ...]`
  - OCR: French lang model (CV_PARSE_OCR_LANG=fra)
  - 100% non-LLM (Tesseract OCR + regex parsing only)

### Interview Preparation (New - just merged)
- `POST /interview-preparation/use-cases` → list interview scenarios
  - Input: `{targetRole: str}`
  - Output: `{useCases: [{scenario: str, description: str}, ...]}`

- `POST /interview-preparation/context` → premium recruitment context
  - Input: `{targetRole: str, experiences: Experience[], sensitiveZone: str?}`
  - Output: Premium context for interview prep

- `POST /interview-preparation/suggestions` → answer suggestions
  - Input: `{question: str, context: str}`
  - Output: `{suggestions: [str, ...]}`

- `POST /interview-preparation/analyze-paragraph` → deduped premium analysis
  - Uses `/analyze` internally (see gotchas)

### Sensitive Analysis (Stable - HIGH-RISK)
- `POST /analyze` — Sensitive period reframing
  - Powers premium recruitment flow
  - **Never modify without explicit validation**
  - Input: `{text: str}` (sensitive period description)
  - Output: `{reframed: str}` (professional narrative)

## OCR Configuration

### CV Parsing Hardening (just merged)
1. Image optimization (resize, convert to RGB)
2. Sparse OCR mode for multi-column CVs (PSM 11)
3. Automatic page segmentation (PSM 3)
4. Sidebar layout detection
5. OCR noise cleanup (regex patterns)
6. Month fragment handling (split date parsing)
7. Chronological sorting (by startDate DESC)
8. Timeout hardening (retry + fallback)

### Production Setting
```bash
CV_PARSE_OCR_LANG=fra  # French language model
```

## Architecture Patterns

### Service Layer
- `app/services/cv_parse.py` — CV parsing logic (OCR + structure)
- `app/services/interview_preparation.py` — Interview prep workflows
- `app/services/analyze.py` — Sensitive period analysis (LLM-based, restricted)

### Route Layer
- `app/api/routes/cv.py` — CV parsing endpoint
- `app/api/routes/analyze.py` — Sensitive analysis endpoint
- `app/api/routes/interview_preparation.py` — Interview prep endpoints

### Testing
- `tests/test_cv_parse.py` — CV parsing unit + integration tests
- `tests/test_interview_preparation.py` — Interview prep tests
- `tests/test_analyze.py` — Sensitive analysis tests

## AI Rules (Critical)

**Never invent:**
- Experience records
- Diplomas or certifications
- Skills or achievements
- Companies or job titles
- Interview scenarios (fabricated)

**Always:**
- Help users explain real paths with clarity
- Keep tone professional, grounded, non-judgmental
- Respect sensitive periods (don't hide, help reframe)
- Use user input as foundation (don't hallucinate)

## Common Gotchas

### /analyze endpoint
1. **High-risk** — Powers sensitive period reframing
2. **Never modify without validation** — User explicitly forbids changes
3. **LLM-based** — Uses language model, not deterministic
4. **Premium-only** — Only in premium recruitment flow

### /cv/parse endpoint
1. **100% non-LLM** — Tesseract OCR + regex only, no hallucinations
2. **Max 5 experiences** — Always truncates to 5 most recent
3. **Chronological only** — Sorted by startDate DESC, no reordering
4. **French language** — CV_PARSE_OCR_LANG=fra (non-negotiable)
5. **File size limit** — 10MB max input

### Interview Prep (New)
1. **Uses /analyze internally** — Inherits /analyze restrictions
2. **Test scenarios** — Use case suggestions are LLM-based, validate before prod
3. **Answer suggestions** — Validate quality before merging to main

### Local Testing
1. **test_payload.json** — For manual endpoint testing, ignore in commits
2. **Poetry** — Use for dependency management
3. **Tests** — Run pytest before every commit

## Contract & Documentation

- **docs/api-contract.md** — Source of truth for request/response schemas
- **Update together** — Code changes + docs + tests (never separate)
- **Frontend dependency** — Frontend calls these endpoints, breaking changes = production bugs
