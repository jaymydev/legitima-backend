import json
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = "Return strictly valid JSON only. No explanations. No markdown. No text outside JSON."


class AnalyzeRequest(BaseModel):
    input: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    analysis: Dict[str, Any]


app = FastAPI()


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing")

    client = OpenAI(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload.input)},
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI API call failed: {exc}") from exc

    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        raise HTTPException(status_code=500, detail="OpenAI response did not contain content")

    try:
        parsed = json.loads(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse model response as JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=500, detail="Parsed model response is not a JSON object")

    return AnalyzeResponse(analysis=parsed)
