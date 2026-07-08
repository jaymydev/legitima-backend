# API Contract — Legitima V1

## Base URL

Development:
http://localhost:8000

## Endpoints V1

### POST /v1/intake/target-role

Purpose:
Collect the target role and interview context.

Request:
{
  "target_role": "Product Owner",
  "company_context": "ESN / client aerospace",
  "interview_type": "technical interview"
}

Response:
{
  "session_id": "string",
  "next_step": "career_path"
}

---

### POST /v1/analyze/career-path

Purpose:
Analyze the user's career path strategically.

Request:
{
  "session_id": "string",
  "career_entries": [
    {
      "title": "Consultant PLM",
      "company": "Example",
      "start_date": "2021-01",
      "end_date": "2023-06",
      "description": "Worked on..."
    }
  ]
}

Response:
{
  "strengths": ["string"],
  "sensitive_periods": ["string"],
  "initial_diagnosis": "string"
}

---

### POST /v1/reframe/sensitive-periods

Purpose:
Help the user reframe sensitive periods without hiding or falsifying them.

Request:
{
  "session_id": "string",
  "sensitive_period": "6 months bench period"
}

Response:
{
  "risk": "string",
  "strategic_reading": "string",
  "interview_answer_draft": "string"
}