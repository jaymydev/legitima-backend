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

Multipart fields:

- `file`: required uploaded file

Supported file types:

- `application/pdf`
- `image/jpeg`
- `image/png`

Maximum file size:

- `10485760` bytes (`10 MB`)

Environment requirement:

- `OPENAI_API_KEY` must be configured on the backend

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
- `422` when a PDF contains no extractable text for the current parser
- `500` when `OPENAI_API_KEY` is missing
- `500` when the OpenAI call fails
- `500` when the OpenAI response cannot be parsed as JSON
- `422` when the OpenAI response does not match the documented schema

Known limitations:

- text-based PDFs are supported; image-only or scanned PDFs are not currently supported by the PDF extraction path
- if a scanned CV is available only as an image-based PDF, the frontend should prefer sending a photo or image export instead
- this endpoint extracts only structured experience rows for now; it does not return skills, education, summary, or full CV content
- this endpoint is intended to support a staged frontend migration from local parsing to backend parsing

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
