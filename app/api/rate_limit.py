"""Per-IP rate limiting.

The iOS client used to hold a daily quota in `UserDefaults`. It protected
nothing — a reinstall reset it — and it has been removed now that the app
ships free. This module is the replacement, and it is the only thing standing
between an automated loop and the OpenAI account.

Storage is in-memory, which is correct for a single Render instance. Running
more than one instance would give each its own counters and multiply every
limit by the instance count; that is the point at which this needs Redis.
"""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

#: Calls that cost an OpenAI completion. Generous for someone iterating on
#: their own career text, ruinous for nobody.
AI_GENERATION_LIMIT = "10/hour"

#: OCR costs CPU rather than tokens, and a real user imports a CV once or
#: twice. This mostly keeps a single client from occupying the worker.
CV_PARSE_LIMIT = "20/hour"

#: Blanket ceiling for everything else, applied by the middleware. Well above
#: any human pace; it only catches indiscriminate scraping.
DEFAULT_LIMIT = "120/hour"


def _trusted_proxy_hops() -> int:
    """How many proxies sit in front of us, from the right of the header."""
    try:
        return max(1, int(os.environ.get("TRUSTED_PROXY_HOPS", "1")))
    except ValueError:
        return 1


def client_ip(request: Request) -> str:
    """The address to count against, read from the right of `X-Forwarded-For`.

    `get_remote_address` reads the socket peer, which behind Render's proxy is
    the proxy itself — every user on earth would share one bucket and the app
    would start refusing real traffic within minutes.

    The header is a comma-separated chain, appended to by each hop, so the
    entries a client can forge sit on the *left*. Reading from the right takes
    what our own proxy observed. If Render ever adds a hop, everyone collapses
    into a single bucket again — visible immediately as users hitting 429 — and
    `TRUSTED_PROXY_HOPS` is the dial for that.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]
    if chain:
        return chain[-min(_trusted_proxy_hops(), len(chain))]
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_ip,
    default_limits=[DEFAULT_LIMIT],
    headers_enabled=True,
)
