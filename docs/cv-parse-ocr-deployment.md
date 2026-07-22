# CV Parse OCR Deployment

`POST /cv/parse` supports JPEG and PNG CV images through classic OCR.

This OCR path is non-LLM:

- no OpenAI call
- no token consumption
- local text extraction from the uploaded image
- deterministic parsing after OCR text extraction

## Runtime Requirements

The Python dependencies are declared in `requirements.txt`:

- `Pillow`
- `pytesseract`

The deployed runtime must also provide the Tesseract binary and OCR languages:

- `tesseract`
- French language data
- English language data

The backend uses:

```text
CV_PARSE_OCR_LANG=fra+eng
```

by default.

## Render Note

On Render, the current Python web service environment may not include the system `tesseract` binary by default.

If OCR image parsing returns:

```json
{
  "detail": "OCR engine is not available or failed to process the image"
}
```

then the Python code is deployed, but the Render runtime is missing Tesseract or the required OCR language data.

Recommended production deployment options:

- use the repository `Dockerfile` for the Render service; it installs `tesseract-ocr`, `tesseract-ocr-fra`, and `tesseract-ocr-eng`
- or configure an equivalent Render environment that provides the same system packages

Do not fall back to OpenAI for `/cv/parse`.

## Render Docker Setup

Create or update the Render web service with these settings:

- **Environment:** `Docker`
- **Dockerfile Path:** `./Dockerfile`
- **Docker Context:** `.`
- **Environment Variable:** `CV_PARSE_OCR_LANG=fra+eng` (optional; this is already the image default)

When using the Docker environment, leave Render's build and start command fields empty so the
image's `CMD` is used. Render provides the `PORT` variable at runtime and the container binds
Uvicorn to it automatically.

After deployment, verify `/health`, then upload a JPEG or PNG CV to `/cv/parse`. A successful
OCR deployment must return the normal `experiences` response instead of the missing-engine `500`.

## Timeout Diagnostics

The PDF extraction and image OCR work runs in a threadpool so it does not block FastAPI's event
loop or delay concurrent `/health` requests. Each successful parse logs only operational metadata:

- MIME type
- file size in bytes
- extraction duration in milliseconds
- total duration in milliseconds
- number of extracted experiences

The CV content, filename, and extracted text are never logged. Compare `total_duration_ms` with
the request duration shown by Render. If `/health` is also slow while no parse is running, the
remaining likely causes are a Render cold start or service resource pressure rather than the OCR
parser itself.

Tesseract also has a 20-second internal timeout. If it exceeds that limit, the request returns a
controlled `500` instead of keeping a worker occupied indefinitely.

## Supported Uploads

Supported:

- text-based PDFs
- JPEG CV images
- PNG CV images

Not yet supported:

- scanned PDF pages that require PDF-to-image conversion before OCR

## Frontend Contract

The response schema does not change:

```json
{
  "experiences": [
    {
      "title": "string",
      "company": "string",
      "period": "string"
    }
  ]
}
```

If OCR succeeds but no exploitable professional experiences are found, `/cv/parse` returns `422`.
