# AGENTS.md — Backend FastAPI

## Mission

This repository contains the FastAPI backend for Legitima, an app that prepares
someone for the interview ahead of them.

**The main path calls no model.** It serves a hand-written question bank of 300
entries: eight questions for the interview type, with written answers whose
`<BALISE>` slots are filled on the device. It is instant, costs nothing, and is
useful to someone who typed nothing at all — which is the whole point, and what
generation could not do without inventing a career.

A single optional path calls a language model: the personalisation, which
adapts the preparation to a pasted job offer. Its output goes through a
separate verification pass that can only downgrade a claim, never add one.

The app is free, has no account, and stores nothing server-side.

## Product boundaries

The backend must support:
- the question bank: eight questions per interview type, plus the hand-written
  "Avant d'entrer" action plan;
- the métier verticals and their catalog, so the app displays choices it does
  not hardcode;
- the management filter, for questions that only make sense to someone who
  leads a team;
- personalised questions from a job offer, a told achievement and a CV, always
  verified against what the person wrote;
- CV parsing by OCR, with no model involved.

The backend must not support without explicit human approval:
- fake experience generation;
- CV generation as the main feature;
- job matching or recruiter scraping;
- payment, subscription, or marketplace;
- social features;
- heavy authentication;
- server-side storage of user work;
- complex multi-service architecture.

## Standing decisions

These were decided, not stumbled into. Re-open them with a reason.

- **The order of the entries IS the data.** The bank is sorted by decreasing
  probability, and selecting means taking the first of each source. Anything
  that reorders must justify itself in those terms — a rank is a claim about
  how likely a question is.
- **Hand-written for the main path, generation for personalisation only.** One
  prompt cannot reliably both authorise and forbid invention; the check is a
  separate pass.
- **`<PLANCHER>` never appears in a spoken sentence.** Knowing your own floor
  changes how you negotiate; saying it costs you the negotiation. The app
  declares the slot — it serves the person, not their answer — and the bank
  currently emits it nowhere at all.
- **The métier applies only to interviews that assess a skill for a role** —
  `TYPES_EVALUATION`. Its questions are written to screen ("vendez-moi ce
  stylo"); in a review, none of them would be asked. The catalog publishes that
  list as `applies_to` so no client has to hardcode it.
- **Management entries stay in the drawer** until the client says the person
  leads a team — and when it does, they move to the head of their source,
  because for that person they are the likeliest of their category.
- **The word "objection" is banned**: the recruiter is not an opponent. A test
  enforces it across everything the person reads — the four text fields of all
  300 entries, and the action plans.
- **`POST /analyze` and the `v2` routes stay mounted** for TestFlight builds
  that still call them. No current client uses them. Removing them before those
  builds are replaced would break testers.

## Technical rules

- Use FastAPI idioms. Keep endpoints small and explicit, business logic outside
  route handlers, request bodies validated with Pydantic.
- **Never add `from __future__ import annotations` to a router with a POST
  body.** Under postponed evaluation FastAPI cannot resolve the body model
  through slowapi's decorator wrapper and silently downgrades it to a query
  parameter — every POST then answers 422. This cost a production outage once.
- Rate limits are per IP: `10/hour` on model routes, `20/hour` on `/cv/parse`,
  `120/hour` by default, `/health` exempt. The counters live in one process's
  memory: correct for a single instance, wrong the moment there are two.
- Do not hardcode secrets. Do not commit `.env`.
- Do not log personal user data — logs record the shape of a request, never its
  content, and a test enforces it.
- Do not add dependencies without justification.
- Do not change public API contracts without updating `docs/api-contract.md`,
  including the "known limits" section.
- Add or update tests when behavior changes. `.venv/bin/python -m pytest` runs
  191 tests with no network and no key.

## AI rules

- Never invent experience, diplomas, skills, companies, or achievements.
- Never promise hiring success.
- Never hide or falsify a difficult period.
- Help the user explain their path with clarity and legitimacy.
- Keep the tone serious and warm: someone is preparing for a stressful moment.
- Vouvoiement everywhere.

## Definition of Done

A backend task is complete only if:
- endpoint behavior is implemented;
- request and response schemas are clear;
- tests pass — and a **new test has been seen failing without the fix**, or it
  proves nothing. A test that only checks a page is the right size once let a
  switch ship that added no question at all;
- privacy rules are respected;
- `docs/api-contract.md` is updated when needed;
- the PR explains what changed and how to test it.
