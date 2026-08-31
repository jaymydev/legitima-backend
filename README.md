# Legitima — backend

FastAPI service behind [Legitima](https://github.com/jaymydev/legitima-frontend),
an iOS app that helps someone defend a non-linear career path in a job
interview.

The product mechanism is **narrative → answers**. This service turns a few
lines of career history into a strategic reading of it, names the objection an
interviewer is likely to raise, and writes the answer the user can say out
loud. Output is French only, by design and by validation.

Python 3.11, deployed on Render **from the Dockerfile** at
`https://legitima-backend-ocr.onrender.com`.

The runtime is not a detail. `/cv/parse` drives the `tesseract` binary, which
`pip` does not install — the Dockerfile does. A second Render service ran this
same repository on the native Python runtime, answered every route identically,
and returned `500 OCR engine is not available` the moment a real CV photo
arrived. Render cannot change a service's runtime after creation. `GET /health`
now reports whether OCR can actually run, so the question takes one call
instead of a user complaint.
The full request and response contract is in
[docs/api-contract.md](docs/api-contract.md).

## What it serves

| Route | Does | Limit |
| --- | --- | --- |
| `GET /v3/interview/bank` | the questions to prepare, from the hand-written bank | 120/hour |
| `POST /v3/interview/questions` | the same, personalised by the model | 10/hour |
| `POST /cv/parse` | experience extraction from a PDF or a photo | 20/hour |
| `POST /analyze` | strategic reading of a career path — **no client left** | 10/hour |
| `POST /v2/interview-preparation/*` | the previous guided preparation — **no client left** | 10/hour |

`GET /v3/interview/bank` is the main path and it makes **no model call**: it
answers instantly, costs nothing, and works for someone who has typed nothing.
That is what generation could not do without inventing a career.

`/analyze` and the `v2` preparation are kept until the TestFlight builds still
calling them are replaced. Nothing in the current app touches them.

`/cv/parse` is deterministic: text extraction with `pypdf`, OCR with Tesseract,
no model call and no token cost.

The seven CRUD routers that came from an earlier design — `/contexte`,
`/parcours`, `/elements`, `/zones`, `/requalifications`, `/fil-conducteur`,
`/reponses` — are gone, along with the Supabase dependency and the `X-User-Id`
header they alone required. Nothing ever called them, and in production they
answered `500 Supabase is not configured`.

## Running it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

`OPENAI_API_KEY` is required for anything that generates. `/cv/parse` and
`/health` work without it. Image OCR additionally needs Tesseract on the host;
the Dockerfile installs it, and
[docs/cv-parse-ocr-deployment.md](docs/cv-parse-ocr-deployment.md) covers the
deployment side.

```bash
.venv/bin/python -m pytest        # 154 tests, no network, no API key needed
```

There is no GitHub Actions workflow here, deliberately: the suite runs in
thirteen seconds locally and CI minutes were the binding constraint on the iOS
repository.

## No authentication, and what stands in for it

Anyone who extracts the base URL from the iOS binary can call this service.
That is a deliberate trade — accounts were removed from the product — and it
means the protections have to be real.

**Per-IP rate limiting**, at the numbers in the table above. `GET /health` is
never counted: Render polls it continuously, and counting it would exhaust the
default bucket unaided and take the service down.

Each route has its own counter, so a full preparation — analysis, kickoff,
guided preparation — spends one call from three separate budgets. A request
rejected by schema validation never reaches its handler, so only the 120/hour
default counts it; testing a per-route limit needs a request the handler
actually accepts.

**The address is read from the leftmost `X-Forwarded-For` entry.** This is worth
explaining, because the first version got it wrong in a way no test could catch.

It read from the *right*, reasoning that a caller can only forge entries on the
left and the right-hand end is what our own proxy observed. Render appends a hop
whose address **changes between requests**, so every call opened a fresh bucket
and the limit never fired. The anticipated failure was everyone collapsing into
one bucket — loud, users hitting 429 immediately. The actual failure was the
opposite and silent: counters fragment, nothing ever triggers, everything looks
healthy. The tell was `X-RateLimit-Remaining` climbing back up between requests
instead of descending. It now falls by one per call.

The leftmost entry is the client, and it is stable. It is also forgeable: a
caller who fakes it gets a fresh bucket per request. That weakness is real and
deliberate — the alternative, measured, was a limit that applied to no one. The
backstop against it is the monthly spend cap on the OpenAI account, not this
module. `SKIPPED_FORWARDED_ENTRIES` (default `0`) skips leading entries should a
proxy of our own ever be placed in front.

Counters live in process memory, which is correct for one instance and wrong the
moment there are two — each would keep its own and multiply every limit. That is
the point at which this needs Redis.

## Not leaking anything

`/analyze` used to answer a failed upstream call with
`detail=f"OpenAI API call failed: {exc}"`. OpenAI phrases a rejected credential
as `Incorrect API key provided: sk-...`, and this endpoint takes no
authentication — so it handed the key to whoever asked. An existing test
asserted the interpolated string, which is how it survived: the bug was pinned
in place by its own coverage.

Error responses now carry no upstream text at all. Reasons go to the log.

[tests/test_public_release_readiness.py](tests/test_public_release_readiness.py)
keeps that closed, and is worth running before publishing anything:

- every handler whose source constructs an OpenAI client must declare an
  explicit limit, checked against the source rather than a maintained list, so
  a new generating route cannot quietly inherit the 120/hour default;
- a failing upstream call must not echo the key, and a malformed model reply
  must not echo the reply;
- the 429 body, served to unauthenticated callers by definition, says only that
  a limit was hit;
- no tracked file matches an OpenAI key, a JWT or an `api_key` assignment, and
  no `.env` is tracked — run against `git ls-files`, which is what publishing
  actually exposes;
- the published limits match `docs/api-contract.md`, so the contract cannot
  drift from the code.

## What an error says, and to whom

The app is French-only, and it prints a failed request's `detail` in red,
unchanged, to someone who is about to walk into an interview. For a while that
meant they read *"No exploitable professional experiences were found in this
document"* — English, and phrased about the document rather than about what to
do next.

Every error the five client-facing routes can return now comes from one table,
[app/api/errors.py](app/api/errors.py), and carries two fields:

```json
{ "detail": "Aucun texte n'a pu être extrait de ce PDF. C'est probablement un scan : importez-le comme photo, ou utilisez un PDF au format texte.", "code": "cv_pdf_no_text" }
```

`detail` is the sentence, and it is copy — it can be reworded. `code` is the
contract, and it cannot. Keeping both means the wording stays reviewable in one
place while a client that wants its own phrasing has something stable to branch
on, and it kept the change backward compatible: `detail` is still a plain string
in its usual position, so the shipped app benefits without being rebuilt.

Nothing internal goes in `detail`. `OCR dependencies are not installed` names
which of the two Render services answered, and `Duplicate question_id: x` is
addressed to whoever wrote the client — neither helps the person reading it, so
both stay in the log.

FastAPI's own body validation went the same way. It answers `detail` as an
array of `{"msg": "Field required"}` and the client reads the first `msg`, so a
client bug read as English — and this repository has already shipped one of
those: re-adding `from __future__ import annotations` to the interview
preparation router downgrades its body to a query parameter and answers every
POST with exactly that. The field paths moved to a `fields` key, where they
still serve whoever is debugging the client.

[tests/test_user_facing_errors.py](tests/test_user_facing_errors.py) reads the
source of the three modules those routes go through and fails on a bare
`raise HTTPException(...)`. Asserting the messages in the table would have
proved nothing about the next one someone adds.

## Privacy

Career history, sensitive periods and interview answers are personal data, and
some of what a user writes may be health-related whatever the form invites.
None of it is stored: requests are processed and answered, nothing is persisted.

Logs record shape, never content — counts, durations, use-case identifiers,
whether a field was filled. Two tests exist purely to assert that answers and
context never reach the log. IP addresses are personal data too, so the
forwarded-chain diagnostic logs the number of entries and never the addresses.

What users write is sent to OpenAI, in the United States. The app says so on
its first screen.

## Layout

```
app/
  api/
    errors.py            # every user-facing message, in French, in one table
    health.py            # exempt from rate limiting on purpose
    rate_limit.py        # the key function is the interesting part
    routes/              # analyze, cv, interview_preparation, question_bank
  services/
    cv_parse.py          # pypdf + Tesseract, no model call
    interview_preparation.py   # prompts, validation, use-case catalog
  observability/         # logging and the catch-all error handler
  main.py
docs/
tests/
```

## Licence

Code under the [MIT licence](LICENSE) — read it, change it, reuse it, keep the
copyright line. The name Legitima and the visual identity are not covered.

[AGENTS.md](AGENTS.md) holds the product boundaries: never invent experience or
credentials, never promise hiring success, never hide a sensitive period, and
keep endpoints small with business logic outside the handlers.
