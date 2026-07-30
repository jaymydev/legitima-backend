# API Contract - Legitima Backend V1 Scaffold

## Scope

This document describes the API endpoints currently implemented in the FastAPI backend as mounted in [app/main.py](/Users/milehanalivecomm/Documents/Developer/legitima-backend/app/main.py).

It documents the current V1 scaffold only. No additional endpoints are part of the official contract unless they are mounted in the backend.

This file is the backend API source of truth for the current V1 scaffold.

## Base URL

Local development:

```text
http://localhost:8000
```

## Current authentication and headers

### Supported headers

- `Content-Type: application/json` for `POST` and `PATCH` requests with JSON bodies
- `X-User-Id: <string>` is required for all CRUD routes
- `Authorization: Bearer <supabase_jwt>` may be sent by clients, but the backend does not validate or decode JWTs in V1

### Header behavior

- `GET /health` does not require `X-User-Id`
- All CRUD endpoints return `400` with `{"detail":"X-User-Id header is required"}` when `X-User-Id` is missing
- CRUD routes scope reads and writes using the provided `X-User-Id`

## Health endpoint

### `GET /health`

Health check endpoint.

Response `200`

```json
{
  "status": "ok"
}
```

## Interview preparation V2

### `GET /v2/interview-preparation/use-cases`

Returns the versioned questionnaire catalog for recruitment, internal mobility, role
evolution, mid-year, annual, and performance interviews. Each use case contains its
own title, description, version, and ordered questions. The endpoint does not require
authentication.

### `POST /v2/interview-preparation/analyze`

Generates a preparation adapted to one questionnaire without changing the transitional
`POST /analyze` contract.

Request:

```json
{
  "use_case_id": "mid_year",
  "questionnaire_version": "1.0",
  "answers": [
    {
      "question_id": "role_context",
      "answer": "Responsable produit"
    }
  ],
  "context": {
    "target_role": "string",
    "career_experiences": "string",
    "sensitive_point": "string",
    "freemium_analysis": "string"
  }
}
```

All required questions from the selected catalog must be answered. Unknown questions,
duplicates, and stale questionnaire versions return `422`. Always send the
`questionnaire_version` returned by `use-cases` rather than a pinned value: the catalog
is versioned as a whole, and clients holding a saved draft from an earlier version must
restart it rather than submit stale answers.

Every use case asks, as a **required** question, what the person fears being asked —
the objection, the reservation, or the critique they expect. This is the material the
preparation is built to answer; without it the generation has nothing to defend and
returns the user's own words reformatted.

Each catalog question provides either selectable `options` or non-binding
`suggestions` to help the user formulate a more complete answer.

`context` is optional and lets the premium recruitment flow reuse information already
collected by the freemium analysis. It must not be used to request another CV upload.

Response:

```json
{
  "use_case_id": "mid_year",
  "title": "string",
  "summary": "string",
  "sections": [
    {
      "title": "string",
      "content": "string"
    }
  ],
  "talking_points": ["string"],
  "action_plan": ["string"]
}
```

The endpoint requires `OPENAI_API_KEY`. User answers and generated content must not be
written to application logs.

### `POST /v2/interview-preparation/kickoff`

First premium deliverable, generated at purchase time. It runs from the lean context
alone — before any guided question is asked — so the user receives one usable answer
immediately after paying, instead of being sent straight back into a questionnaire.

Deliberately narrow: one probable objection, one defensible answer. The client blocks
on this call behind a progress screen, so the response must stay small and fast.

Request:

```json
{
  "context": {
    "target_role": "string",
    "career_experiences": "string",
    "sensitive_point": "string",
    "freemium_analysis": "string"
  }
}
```

`context` is required and uses the same shape as the `analyze` endpoint. Unknown keys
return `422`. All four fields default to an empty string, but a context carrying only a
`sensitive_point` returns `422`: without a role or career path there is no thread to
answer from, and the only way to produce an answer would be to invent one.

When `freemium_analysis` already names a probable objection, the generation reuses that
one rather than raising a different one — it is the objection the free teaser quoted
without resolving.

Response:

```json
{
  "objection": "string",
  "defensible_answer": "string"
}
```

`objection` is a short question phrased as an interviewer would ask it.
`defensible_answer` is 3 to 5 sentences in the first person, grounded in the career
thread, that the candidate can say out loud as-is.

The endpoint requires `OPENAI_API_KEY`. Context and generated content must not be
written to application logs.

## Transitional AI endpoint

### `POST /analyze`

`POST /analyze` is an officially supported transitional V1 endpoint for the current iOS flow:

`onboarding -> analyze -> result`

It is supported to stabilize the current product flow and TestFlight preparation, but it is not the target long-term backend design.

Required headers:

- `Content-Type: application/json`

Environment requirement:

- `OPENAI_API_KEY` must be configured on the backend

Request body:

```json
{
  "input": {
    "meta": {
      "version": "1.0",
      "language": "fr",
      "target_market": "US",
      "interview_type": "recruitment"
    },
    "narrative_positioning": {
      "short_summary": "string",
      "current_positioning": "string",
      "evolution_logic": "string"
    }
  }
}
```

Input contract notes:

- `input.meta` is required
- `input.narrative_positioning` is required
- all fields shown above are required strings
- `input.meta.language` currently supports only `fr`
- additional top-level fields are not part of the current official contract
- additional nested fields are not part of the current official contract

Response `200`

```json
{
  "analysis": {
    "strategic_reading": "string",
    "dominant_competencies": "string",
    "career_logic": "string"
  },
  "sensitive_reframing": {
    "identified_fragilities": "string",
    "strategic_reinterpretation": "string",
    "rational_reframing": "string"
  },
  "narrative": {
    "core_thread": "string",
    "positioning_statement": "string"
  },
  "interview_preparation": {
    "probable_objections": "string",
    "structured_answers": "string"
  },
  "legitimacy_anchor": {
    "objective_strength": "string",
    "final_alignment_statement": "string"
  }
}
```

Language behavior:

- for the current V1 contract, the backend supports only `input.meta.language = "fr"`
- all response sections are generated in French
- mixed French/English output is considered invalid for this endpoint
- French spelling quality matters, including required accents in standard French words
- duplicated text reused across different response fields is considered invalid
- if the first model response contains English content, the backend retries once with a stricter French-only instruction
- if the generated content still fails the quality rules after retry, the backend returns an error instead of returning degraded content

Validation response `422`

FastAPI validation errors are returned in the standard `detail` array format.

Example:

```json
{
  "detail": [
    {
      "msg": "Field required"
    }
  ]
}
```

Unsupported language example:

```json
{
  "detail": [
    {
      "msg": "Value error, Only French output is currently supported for /analyze"
    }
  ]
}
```

Backend error response `500`

Possible current `detail` values include:

- `OPENAI_API_KEY environment variable is missing`
- `OpenAI API call failed: ...`
- `OpenAI response did not contain content`
- `Failed to parse model response as JSON: ...`
- `Parsed model response is not a JSON object`
- `Model response did not satisfy the analyze quality requirements`

Model validation response `422`

If the OpenAI response does not match the documented output schema, the backend returns a `422` validation error.

## CV parsing endpoint

### `POST /cv/parse`

Dedicated V1 endpoint to extract structured professional experiences from an uploaded CV document.

This endpoint is separate from `POST /analyze`.

Required headers:

- `Content-Type: multipart/form-data`

Optional staging/local test header:

- `X-CV-Parse-Test-Error: 500`

This header is ignored unless `ENABLE_CV_PARSE_TEST_ERRORS=true` is configured on the backend. It exists only to validate frontend error handling in controlled local or staging environments.

Multipart fields:

- `file`: required uploaded file

Supported file types:

- `application/pdf`
- `image/jpeg`
- `image/png`

Maximum file size:

- `10485760` bytes (`10 MB`)

Execution model:

- `/cv/parse` is deterministic and does not call OpenAI
- `/cv/parse` does not consume OpenAI tokens
- text-based PDFs are parsed using local text extraction and rules
- JPEG and PNG CV images are parsed with classic OCR when the backend OCR engine is available
- scanned PDFs are not converted to images yet and currently return `422` when no PDF text is extractable
- image OCR requires the Python OCR dependencies and a Tesseract runtime available in the deployed backend

Response `200`

```json
{
  "experiences": [
    {
      "title": "Senior Backend Engineer",
      "company": "Legitima",
      "period": "2023-2026"
    }
  ]
}
```

Response contract notes:

- only `experiences` is returned
- each item contains exactly `title`, `company`, and `period`
- values are strings
- missing values may be returned as empty strings
- the backend must not invent missing experiences

Validation and error responses:

- `422` when the multipart body is malformed or the `file` field is missing
- `415` when the uploaded file type is not supported
- `413` when the uploaded file exceeds the maximum size
- `422` when the PDF contains no extractable text
- `422` when an image contains no extractable text
- `422` when no exploitable professional experiences are found after PDF text extraction or image OCR
- `500` when OCR dependencies or the OCR runtime are not available in the deployed backend
- `500` when `X-CV-Parse-Test-Error: 500` is sent and `ENABLE_CV_PARSE_TEST_ERRORS=true` is enabled in a controlled local or staging environment

Known limitations:

- the current deterministic parser supports text-based PDFs and JPEG/PNG CV images
- scanned PDFs require a future PDF-page-to-image OCR integration
- extraction is rule-based and may return `422` when the CV layout does not expose recognizable experience headings and periods
- parsing is intended as prefill; `/analyze` remains the only V1 endpoint that uses AI for strategic interview preparation
- this endpoint extracts only structured experience rows for now; it does not return skills, education, summary, or full CV content
- this endpoint is intended to support a staged frontend migration from local parsing to backend parsing

Controlled error testing:

- see `docs/cv-parse-error-testing.md`
- do not enable forced `/cv/parse` errors in production

OCR deployment requirements:

- see `docs/cv-parse-ocr-deployment.md`

## CRUD resource pattern

The following resource groups are mounted:

- `/contexte`
- `/parcours`
- `/elements`
- `/zones`
- `/requalifications`
- `/fil-conducteur`
- `/reponses`

Each group exposes the same route pattern and currently uses the same request/response shape:

- Create body:

```json
{
  "name": "string"
}
```

- Update body:

```json
{
  "name": "string"
}
```

`PATCH` accepts partial input, but the only supported field today is `name`.

- Record response:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "string"
}
```

## Endpoint details

### `/contexte`

Resource backing table: `contexte_entretiens`

#### `POST /contexte`

Required headers:

- `X-User-Id`
- `Content-Type: application/json`

Request body:

```json
{
  "name": "Target role clarification"
}
```

Response `201`

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Target role clarification"
}
```

#### `GET /contexte`

Required headers:

- `X-User-Id`

Response `200`

```json
[
  {
    "id": "string",
    "user_id": "string",
    "name": "Target role clarification"
  }
]
```

#### `GET /contexte/{contexte_id}`

Required headers:

- `X-User-Id`

Response `200`

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Target role clarification"
}
```

Not found response `404`

```json
{
  "detail": "ContexteEntretien not found"
}
```

#### `PATCH /contexte/{contexte_id}`

Required headers:

- `X-User-Id`
- `Content-Type: application/json`

Request body:

```json
{
  "name": "Updated context"
}
```

Response `200`

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Updated context"
}
```

Validation response `400`

```json
{
  "detail": "No fields provided"
}
```

Not found response `404`

```json
{
  "detail": "ContexteEntretien not found"
}
```

#### `DELETE /contexte/{contexte_id}`

Required headers:

- `X-User-Id`

Response `204`

No response body.

Not found response `404`

```json
{
  "detail": "ContexteEntretien not found"
}
```

### `/parcours`

Resource backing table: `parcours_professionnels`

Routes and payloads follow the same pattern as `/contexte`.

- `POST /parcours` -> `201`, record body
- `GET /parcours` -> `200`, list of records
- `GET /parcours/{parcours_id}` -> `200`, single record, `404` detail `ParcoursProfessionnel not found`
- `PATCH /parcours/{parcours_id}` -> `200`, single record, `400` detail `No fields provided`, `404` detail `ParcoursProfessionnel not found`
- `DELETE /parcours/{parcours_id}` -> `204`, `404` detail `ParcoursProfessionnel not found`

Record shape:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Career path analysis"
}
```

### `/elements`

Resource backing table: `elements_de_parcours`

Routes and payloads follow the same pattern as `/contexte`.

- `POST /elements` -> `201`, record body
- `GET /elements` -> `200`, list of records
- `GET /elements/{element_id}` -> `200`, single record, `404` detail `ElementDeParcours not found`
- `PATCH /elements/{element_id}` -> `200`, single record, `400` detail `No fields provided`, `404` detail `ElementDeParcours not found`
- `DELETE /elements/{element_id}` -> `204`, `404` detail `ElementDeParcours not found`

Record shape:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Sensitive period input"
}
```

### `/zones`

Resource backing table: `zones_sensibles`

Routes and payloads follow the same pattern as `/contexte`.

- `POST /zones` -> `201`, record body
- `GET /zones` -> `200`, list of records
- `GET /zones/{zone_id}` -> `200`, single record, `404` detail `ZoneSensible not found`
- `PATCH /zones/{zone_id}` -> `200`, single record, `400` detail `No fields provided`, `404` detail `ZoneSensible not found`
- `DELETE /zones/{zone_id}` -> `204`, `404` detail `ZoneSensible not found`

Record shape:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Sensitive period"
}
```

### `/requalifications`

Resource backing table: `requalifications`

Routes and payloads follow the same pattern as `/contexte`.

- `POST /requalifications` -> `201`, record body
- `GET /requalifications` -> `200`, list of records
- `GET /requalifications/{requalification_id}` -> `200`, single record, `404` detail `Requalification not found`
- `PATCH /requalifications/{requalification_id}` -> `200`, single record, `400` detail `No fields provided`, `404` detail `Requalification not found`
- `DELETE /requalifications/{requalification_id}` -> `204`, `404` detail `Requalification not found`

Record shape:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Sensitive period reframing"
}
```

### `/fil-conducteur`

Resource backing table: `fils_conducteurs`

Routes and payloads follow the same pattern as `/contexte`.

- `POST /fil-conducteur` -> `201`, record body
- `GET /fil-conducteur` -> `200`, list of records
- `GET /fil-conducteur/{fil_conducteur_id}` -> `200`, single record, `404` detail `FilConducteur not found`
- `PATCH /fil-conducteur/{fil_conducteur_id}` -> `200`, single record, `400` detail `No fields provided`, `404` detail `FilConducteur not found`
- `DELETE /fil-conducteur/{fil_conducteur_id}` -> `204`, `404` detail `FilConducteur not found`

Record shape:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Professional narrative"
}
```

### `/reponses`

Resource backing table: `reponses_entretiens`

Routes and payloads follow the same pattern as `/contexte`.

- `POST /reponses` -> `201`, record body
- `GET /reponses` -> `200`, list of records
- `GET /reponses/{reponse_id}` -> `200`, single record, `404` detail `ReponseEntretien not found`
- `PATCH /reponses/{reponse_id}` -> `200`, single record, `400` detail `No fields provided`, `404` detail `ReponseEntretien not found`
- `DELETE /reponses/{reponse_id}` -> `204`, `404` detail `ReponseEntretien not found`

Record shape:

```json
{
  "id": "string",
  "user_id": "string",
  "name": "Difficult interview answer"
}
```

## Known limitations

- The backend currently exposes `GET /health`, the transitional `POST /analyze` endpoint, and scaffold CRUD operations.
- `POST /analyze` is an officially supported transitional endpoint, not the target long-term API shape.
- The route-level request and response schemas are simple `name`-based payloads; domain-specific fields are not implemented yet.
- CRUD ownership is based only on the `X-User-Id` header value supplied by the client.
- JWTs are not validated or decoded by the backend in V1.
- If `SUPABASE_URL` or `SUPABASE_ANON_KEY` is missing, CRUD routes return `500` with `{"detail":"Supabase is not configured"}`.
- If `OPENAI_API_KEY` is missing, `POST /analyze` returns `500`.
- Persistence errors from Supabase are not normalized into a dedicated public error contract yet.
- `POST /analyze` currently depends directly on a synchronous OpenAI API call.
- The current `/analyze` request schema is intentionally narrow and only covers the payload used by the current iOS flow.
- The current `/analyze` response is a single aggregated structure consumed by the frontend and will likely be replaced later by more explicit domain endpoints.
- The current backend guarantees reliable support only for French output on `/analyze`.
