# AGENTS.md — Backend FastAPI

## Mission

This repository contains the FastAPI backend for Legitima.

The backend supports an AI-first interview preparation application for candidates with non-linear, fragmented, or atypical career paths.

## Product boundaries

The backend must support:
- target role clarification;
- strategic career path analysis;
- sensitive period identification;
- sensitive period reframing;
- professional narrative construction;
- difficult interview question preparation;
- final interview preparation summary.

The backend must not support without explicit human approval:
- CV generation as the main feature;
- fake experience generation;
- job matching;
- recruiter scraping;
- payment;
- subscription;
- marketplace;
- social features;
- heavy authentication;
- complex multi-service architecture.

## Technical rules

- Use FastAPI idioms.
- Keep endpoints small and explicit.
- Validate request bodies with Pydantic.
- Keep business logic outside route handlers.
- Do not hardcode secrets.
- Do not commit .env files.
- Do not log personal user data.
- Do not add dependencies without justification.
- Do not change public API contracts without updating docs/api-contract.md.
- Add or update tests when behavior changes.

## AI rules

- Never invent experience, diplomas, skills, companies, or achievements.
- Never promise hiring success.
- Never hide or falsify sensitive periods.
- Help the user explain their path with clarity and legitimacy.
- Keep the tone professional, grounded, and non-judgmental.

## Definition of Done

A backend task is complete only if:
- endpoint behavior is implemented;
- request and response schemas are clear;
- tests pass;
- privacy rules are respected;
- docs/api-contract.md is updated when needed;
- the PR explains what changed and how to test it.
