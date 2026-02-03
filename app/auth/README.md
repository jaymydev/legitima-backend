# Auth placeholder

Supabase Auth is the only authentication system used in V1.

- Clients (iOS) authenticate directly with Supabase.
- Requests may include `Authorization: Bearer <supabase_jwt>`.
- The FastAPI backend does not validate or decode tokens yet.
- Ownership and access enforcement will be added in a later phase.

This file is documentation only and contains no authentication logic.
