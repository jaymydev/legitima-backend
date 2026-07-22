# CV Parse Error Testing

This document describes controlled ways to validate frontend error handling for `POST /cv/parse`.

These scenarios are for local development and staging validation only. Do not enable forced errors in production.

## Endpoint

```text
POST /cv/parse
Content-Type: multipart/form-data
```

Multipart field:

- `file`: required uploaded file

## Reproduce `415 Unsupported Media Type`

Send a file with an unsupported MIME type.

```bash
printf "not a cv" > /tmp/legitima-not-a-cv.txt

curl -i \
  -X POST "$LEGITIMA_BACKEND_URL/cv/parse" \
  -F "file=@/tmp/legitima-not-a-cv.txt;type=text/plain"
```

Expected response:

```json
{
  "detail": "Unsupported file type. Supported types: application/pdf, image/jpeg, image/png"
}
```

## Reproduce `422 Unprocessable Entity`

Send an unreadable PDF payload.

```bash
printf "%s\n" "%PDF-1.4 invalid test payload" > /tmp/legitima-unreadable.pdf

curl -i \
  -X POST "$LEGITIMA_BACKEND_URL/cv/parse" \
  -F "file=@/tmp/legitima-unreadable.pdf;type=application/pdf"
```

Expected response:

```json
{
  "detail": "The PDF could not be read"
}
```

Alternative `422` scenario with an unreadable image payload:

```bash
printf "fake image payload" > /tmp/legitima-cv.png

curl -i \
  -X POST "$LEGITIMA_BACKEND_URL/cv/parse" \
  -F "file=@/tmp/legitima-cv.png;type=image/png"
```

Expected response:

```json
{
  "detail": "The image could not be read"
}
```

Readable JPEG/PNG CV images now use classic OCR. If the image is readable but no exploitable professional experiences are found, `/cv/parse` returns `422`.

## Reproduce `500 Internal Server Error`

Forced `500` responses are disabled by default.

To enable this in a staging or local environment, set:

```text
ENABLE_CV_PARSE_TEST_ERRORS=true
```

Then send:

```bash
printf "not a cv" > /tmp/legitima-trigger-500.txt

curl -i \
  -X POST "$LEGITIMA_BACKEND_URL/cv/parse" \
  -H "X-CV-Parse-Test-Error: 500" \
  -F "file=@/tmp/legitima-trigger-500.txt;type=text/plain"
```

Expected response when the environment flag is enabled:

```json
{
  "detail": "Forced /cv/parse test error"
}
```

If `ENABLE_CV_PARSE_TEST_ERRORS` is missing or not set to `true`, the header is ignored and `/cv/parse` follows the normal contract.

## Production Rule

- Do not set `ENABLE_CV_PARSE_TEST_ERRORS=true` in production.
- Do not use real CVs for error simulation.
- Do not log CV contents, career history, or interview preparation data while testing.
- `/cv/parse` remains deterministic and does not call OpenAI.
- `/analyze` is not involved in these tests.
