# API Contract - Legitima Backend V1 Scaffold

## Scope

This document describes the API endpoints currently implemented in the FastAPI backend as mounted in [app/main.py](/Users/milehanalivecomm/Documents/Developer/legitima-backend/app/main.py).

It documents the current V1 scaffold only. No additional endpoints are part of the official contract unless they are mounted in the backend.

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

## Explicitly unsupported endpoint

### `POST /analyze`

`POST /analyze` is not currently implemented in the backend.

The frontend must not call `POST /analyze` until that endpoint is added to the backend and then added to this official API contract.

## Known limitations

- The backend currently exposes only scaffold CRUD operations plus `GET /health`.
- The route-level request and response schemas are simple `name`-based payloads; domain-specific fields are not implemented yet.
- CRUD ownership is based only on the `X-User-Id` header value supplied by the client.
- JWTs are not validated or decoded by the backend in V1.
- If `SUPABASE_URL` or `SUPABASE_ANON_KEY` is missing, CRUD routes return `500` with `{"detail":"Supabase is not configured"}`.
- Persistence errors from Supabase are not normalized into a dedicated public error contract yet.
- No `POST /analyze` route exists.
- No AI orchestration is part of the current backend contract.
