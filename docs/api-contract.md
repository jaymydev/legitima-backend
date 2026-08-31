# Contrat d'API — backend Legitima

## Scope

Ce document décrit les routes réellement montées dans [app/main.py](../app/main.py).
Rien d'autre ne fait partie du contrat.

Le produit part désormais du **type d'entretien**, pas du parcours : la banque de
questions écrite à la main sert le chemin principal, et le modèle n'intervient
que pour personnaliser quand la personne a fourni de la matière.

## Base URL

Local development:

```text
http://localhost:8000
```

## Current authentication and headers

### Supported headers

- `Content-Type: application/json` for `POST` requests with JSON bodies

No route takes any authentication. The `X-User-Id` header and the Supabase JWT
were required only by the CRUD routers, which are gone.

## Rate limiting

Every route is rate limited per client IP address, read from the **leftmost**
`X-Forwarded-For` entry. Render appends a hop whose address changes between
requests, so keying on the right-hand end gave every call a fresh bucket and
the limits never fired. `SKIPPED_FORWARDED_ENTRIES` (default `0`) ignores that
many leading entries, should a proxy of our own ever be put in front.

A caller who forges the leading entry gets a fresh quota per request. That is
a known weakness of keying on the client end; the backstop against it is the
monthly spend cap on the OpenAI account, not this limit.

| Scope | Limit |
| --- | --- |
| `POST /analyze` | 10 / hour |
| `POST /v2/interview-preparation/analyze` | 10 / hour |
| `POST /v2/interview-preparation/kickoff` | 10 / hour |
| `POST /v3/interview/questions` | 10 / hour |
| `POST /cv/parse` | 20 / hour |
| every other route | 120 / hour |
| `GET /health` | not counted |

Each scope has its own counter, so one full preparation — analyse, kickoff,
guided preparation — spends one call from three separate budgets.

A request rejected by schema validation never reaches its handler, so the
per-route limit above does not count it — only the 120/hour default does. The
routes that cost money are reached only by well-formed requests, which are
counted. Testing a per-route limit therefore needs a request the handler
actually accepts.

Exceeding a limit returns `429` with a `Retry-After` header in seconds and:

```json
{ "error": "Rate limit exceeded: 10 per 1 hour" }
```

Successful responses carry `X-RateLimit-Limit`, `X-RateLimit-Remaining` and
`X-RateLimit-Reset`.

Counters live in the process memory of a single instance. Running more than
one instance gives each its own counters and multiplies every limit by the
instance count; that is the point at which this needs shared storage.

## Error responses

The five routes the iOS client calls answer a failure with two fields:

```json
{
  "detail": "Aucun texte n'a pu être lu sur cette photo. Reprenez-la à plat, bien éclairée et sans reflet, ou importez votre CV en PDF.",
  "code": "cv_image_no_text"
}
```

`detail` is French prose meant to be shown to the user unchanged — the iOS app
displays it as written. It is copy, and it may be reworded at any time.

`code` is the stable half of the contract. A client that wants to phrase the
error itself, or branch on what happened, matches on `code` and never on the
sentence. Codes are added, not renamed.

`detail` remains a plain string in its usual position, so a client that only
reads `detail` — every version shipped so far — keeps working unchanged.

| `code` | Status | Raised when |
| --- | --- | --- |
| `invalid_request` | 422 | the request body failed validation; see `fields` |
| `service_unavailable` | 500 | the service cannot reach its model provider |
| `cv_unsupported_file_type` | 415 | the upload is not a PDF, a JPEG or a PNG |
| `cv_file_too_large` | 413 | the upload exceeds 10 MiB |
| `cv_image_unreadable` | 422 | the image could not be decoded |
| `cv_image_no_text` | 422 | OCR ran and found no text |
| `cv_ocr_unavailable` | 500 | the deployed service has no working OCR engine |
| `cv_pdf_expected` | 422 | the content type reached the PDF branch without being a PDF |
| `cv_pdf_unreadable` | 422 | the PDF could not be opened |
| `cv_pdf_no_text` | 422 | the PDF carries no extractable text, typically a scan |
| `cv_no_experiences` | 422 | text was extracted but no experience row was recognised |
| `analysis_generation_failed` | 500 | the analysis call failed, or its answer could not be read |
| `analysis_invalid_model_response` | 422 | the model's answer did not match the output schema |
| `analysis_quality_insufficient` | 500 | the answer still failed the French quality rules after one retry |
| `preparation_context_too_thin` | 422 | the submitted context holds too little to build an answer |
| `preparation_invalid_request` | 422 | unknown or duplicate question, or a stale questionnaire version |
| `preparation_generation_failed` | 500 | the guided preparation call failed |
| `kickoff_generation_failed` | 500 | the kickoff call failed |
| `unknown_use_case` | 404 | `use_case_id` is not in the catalog |

Nothing internal appears in `detail`: not an upstream message, not a missing
environment variable, not which question was malformed. Those go to the log.

A failed body validation is the one case that carries a third field. FastAPI
answers those with `detail` as an array of `{"msg": "Field required"}`, and the
client reads the first `msg` — so a malformed request read as English. It now
answers `invalid_request` like everything else, with the offending paths kept
under `fields`:

```json
{
  "detail": "La demande envoyée n'a pas pu être traitée. Mettez l'application à jour, puis réessayez.",
  "code": "invalid_request",
  "fields": ["body.input.meta.language"]
}
```

The rate limiter is the only response outside this shape: `429` answers
`{"error": "Rate limit exceeded: ..."}`, deliberately, since it is served to
unauthenticated callers and says only that a limit was hit.

The catalog is [app/api/errors.py](../app/api/errors.py); every message lives in
that one table.

## Health endpoint

### `GET /health`

Health check endpoint.

Response `200`

```json
{
  "status": "ok"
}
```

## Interview questions V3

The pivot. The interview type carries the preparation; the career path is
optional material rather than the subject. No analysis runs first.

### `GET /v3/interview/bank`

The main path: the hand-written question bank. No model call — the response is
instant, costs nothing, and is useful to someone who typed nothing at all.

Query parameters: `use_case_id` (required, one of the six types),
`metier` (optional vertical: `developpement_back`, `commerce`, `comptabilite` —
see `GET /v3/interview/metiers`), `seen` (comma-separated ids already served,
capped at 200; recently seen questions are excluded so a second preparation
brings new ones).

Response `200`:

```json
{
  "use_case_id": "recruitment",
  "questions": [
    {"id": "", "question": "", "answer": "", "follow_up": "", "avoid": ""}
  ],
  "action_plan": ["Relisez l'annonce une dernière fois : …"]
}
```

Eight questions, most probable first — the order of the bank IS the data.
`answer` and `follow_up` are templates with `<BALISE>` slots, delivered intact:
they are filled **on the device**, which is what lets someone put their salary
in an answer without it ever reaching the server.

`action_plan` is the "before entering" block, hand-written per interview type,
read as-is with five minutes and a corridor: one to three gestures, no slots.
When a personalised preparation exists, its own `action_plan` — more specific —
replaces this one on the client. An unknown `use_case_id` answers `404`
`unknown_use_case`.

### `GET /v3/interview/use-cases`

Six types, questionnaire version `2.1`. There is no "not sure yet" entry: someone
who cannot name their interview is not who this is for.

### `POST /v3/interview/questions`

Rate limited to 10/hour — it spends tokens.

```json
{
  "use_case_id": "internal_mobility",
  "questionnaire_version": "2.1",
  "answers": [{"question_id": "current_role", "answer": "Cheffe de projet"}],
  "experiences": [{"title": "", "company": "", "period": ""}],
  "cv_text": ""
}
```

`cv_text` is the raw text `/cv/parse` returned as `raw_text`, sent back verbatim
when the person asked for personalisation. It is refused above 12 000 characters:
the field lands verbatim in a token-costing prompt on an unauthenticated route,
so the honest client's 6 000-character cap cannot be the only bound.

`answers` and `experiences` may both be empty. A performance review needs neither,
and still returns a usable page — that is the property the pivot exists for, and
`tests/test_interview_questions.py` asserts it.

`experiences` is read by two use cases only, and differently: a recruitment may
use the whole list, an internal move only the **last three roles**. Every other
type ignores it entirely — the manager already knows the person's history, so
replaying it is noise.

Response:

```json
{
  "use_case_id": "internal_mobility",
  "title": "",
  "questions": [{"question": "", "intent": "", "answer": "", "kind": "sentence"}],
  "action_plan": [""]
}
```

Between 5 and 8 questions, most likely first. `intent` says in one sentence what
the interviewer is checking, so the reader can improvise when the question comes
out differently; it is capped at 80 characters because it sits between the
question and the answer, and is read on the way to the thing the reader came
for. Answers are capped at 420 characters. Both are bounded **in code**, cut at a
sentence boundary — asking the model for brevity works most of the time, and the
page has to hold every time. The whole thing is meant to be read in five minutes,
in the corridor.

`kind` says whether `answer` is a sentence to say (`sentence`) or a directive on
how to answer (`guidance`). It is the honest half of the response: with no
material about the person, every answer is guidance, because the alternative is
inventing a career. `cv_text` and the optional open question on each use case
exist to earn sentences.

A second model call verifies every answer that asserts anything — whatever the
model labelled it — against the material the person supplied, and rewrites the
unsupported ones as directives. Prompt wording alone was measured unstable:
tightened it produced no usable sentence, loosened it produced "je suis à l'aise
en anglais professionnel" from an offer that merely listed English as a plus.
The pass only ever downgrades, and a failure in it leaves the generation as
written rather than dropping the page.

Errors follow the shape under [Error responses](#error-responses):
`unknown_use_case`, `preparation_invalid_request`, `service_unavailable`,
`preparation_generation_failed`.

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

A malformed body answers `invalid_request`; see
[Error responses](#error-responses). A `meta.language` other than `fr` is
rejected the same way, with `fields` reporting `body.input.meta.language`.

Backend error responses

See [Error responses](#error-responses) for the shape. `/analyze` raises
`service_unavailable`, `analysis_generation_failed`,
`analysis_invalid_model_response` and `analysis_quality_insufficient`.

Note that `analysis_invalid_model_response` is a `422` describing the *model's*
answer, not the caller's request — the status code is a historical accident kept
because 1.0 shipped against it.

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
  ],
  "raw_text": "Senior Backend Engineer — Legitima\n- refonte du site, équipe de 8\n…"
}
```

Response contract notes:

- each item of `experiences` contains exactly `title`, `company`, and `period`
- values are strings
- missing values may be returned as empty strings
- the backend must not invent missing experiences
- `raw_text` is the extracted text before it was reduced to rows, capped at
  6 000 characters on a line boundary. The rows answer "who are you" and nothing
  else; the bullets are the material personalised answers are built from. The
  client keeps it **on the device** and sends it back as `cv_text` only when
  the person asks for personalisation.

Validation and error responses, all in the shape described under
[Error responses](#error-responses):

- `415` `cv_unsupported_file_type` — the file is not a PDF, a JPEG or a PNG
- `413` `cv_file_too_large` — the file exceeds the maximum size
- `422` `cv_image_unreadable` / `cv_image_no_text` — the photo could not be decoded, or OCR found nothing
- `422` `cv_pdf_unreadable` / `cv_pdf_no_text` — the PDF could not be opened, or carries no text
- `422` `cv_no_experiences` — text was extracted, no experience row recognised
- `500` `cv_ocr_unavailable` — the deployed service has no working OCR engine

A malformed multipart body or a missing `file` field answers `422`
`invalid_request`. One response carries no `code` at all:
`X-CV-Parse-Test-Error: 500` with `ENABLE_CV_PARSE_TEST_ERRORS=true` answers a
deliberate `500` used to exercise the client's error path outside production.

Known limitations:

- the current deterministic parser supports text-based PDFs and JPEG/PNG CV images
- scanned PDFs require a future PDF-page-to-image OCR integration
- extraction is rule-based and may return `422` when the CV layout does not expose recognizable experience headings and periods
- a heading counts when it is at most four words made only of career vocabulary, in French or English — `EXPÉRIENCES PROFESSIONNELLES`, `EXPÉRIENCE PROFESSIONNELLE`, `PARCOURS PROFESSIONNEL`, `WORK EXPERIENCE`, `EMPLOYMENT HISTORY` and the like all open the section
- month names are recognised in both languages, so `Mar 2018 - Dec 2020` sorts and parses like `mars 2018 - décembre 2020`
- parsing is intended as prefill; `/analyze` remains the only V1 endpoint that uses AI for strategic interview preparation
- this endpoint extracts only structured experience rows for now; it does not return skills, education, summary, or full CV content
- this endpoint is intended to support a staged frontend migration from local parsing to backend parsing

Controlled error testing:

- see `docs/cv-parse-error-testing.md`
- do not enable forced `/cv/parse` errors in production

OCR deployment requirements:

- see `docs/cv-parse-ocr-deployment.md`

## Limites connues

- La banque est écrite à la main : sa couverture est celle de ce qui y a été
  rédigé, pas de tout ce qui peut être demandé en entretien.
- Trois verticales métier existent — développement back, commerce, comptabilité.
  Les autres métiers ne reçoivent que le transversal.
- Les compteurs de limitation vivent en mémoire d'un seul processus : corrects
  pour une instance, faux dès qu'il y en a deux.
- `POST /analyze` et les routes `v2` restent montées pour les builds TestFlight
  qui les appellent encore. Aucun client actuel ne les utilise.

