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

- use a Docker-based Render service that installs `tesseract-ocr`, `tesseract-ocr-fra`, and `tesseract-ocr-eng`
- or configure an equivalent Render environment that provides the same system packages

Do not fall back to OpenAI for `/cv/parse`.

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
