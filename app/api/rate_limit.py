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

from app.observability.logging import logger

#: Set once the shape of the forwarded chain has been reported, so the line
#: appears a handful of times after a deploy rather than on every request.
_reported_chain_lengths: set[int] = set()

#: Calls that cost an OpenAI completion.
#:
#: This was `10/hour`, which is about one person's own pace — the one place a
#: limit should not sit. It did not reach who it was written for: the leading
#: `X-Forwarded-For` entry is forgeable, so a loop mints a fresh bucket per
#: request, which a test pins as a known weakness. It did reach people it was
#: never aimed at — someone trying several of the six interview types, and
#: everyone behind one shared exit IP, an office or a carrier's NAT, who all
#: count against a single bucket.
#:
#: `30/hour` keeps the stated job of stopping an unsophisticated loop, two
#: orders of magnitude below one, while clearing any human pace. Against a
#: determined caller the backstop is the monthly spend cap on the OpenAI
#: account, not this module.
AI_GENERATION_LIMIT = "30/hour"

#: OCR costs CPU rather than tokens, and a real user imports a CV once or
#: twice. This mostly keeps a single client from occupying the worker.
CV_PARSE_LIMIT = "20/hour"

#: Blanket ceiling for everything else, applied by the middleware. Well above
#: any human pace; it only catches indiscriminate scraping.
DEFAULT_LIMIT = "120/hour"


def _skipped_leading_entries() -> int:
    """How many leading entries to ignore, if a proxy is ever put in front."""
    try:
        return max(0, int(os.environ.get("SKIPPED_FORWARDED_ENTRIES", "0")))
    except ValueError:
        return 0


def client_ip(request: Request) -> str:
    """The address to count against: the *leftmost* `X-Forwarded-For` entry.

    `get_remote_address` reads the socket peer, which behind Render's proxy is
    the proxy itself — every user on earth would share one bucket and the app
    would start refusing real traffic within minutes. So the address comes from
    the header.

    This first read from the right, on the theory that entries a caller can
    forge sit on the left and the rightmost is what our own proxy observed.
    Measured against the deployed service, that was wrong in a way no test
    caught: Render appends a hop whose address *changes between requests*, so
    every call landed in a fresh bucket. The tell was `X-RateLimit-Remaining`
    climbing back up between requests instead of descending; it now falls by
    one per call.

    The leftmost entry is the real client, stable across requests, and is what
    Render documents. A determined caller can forge it and mint a new bucket
    per request; that is a real weakness, and the honest backstop against it is
    the monthly spend cap on the OpenAI account, not this module. The trade is
    a limit that works on everyone versus a limit that worked on no one.

    `SKIPPED_FORWARDED_ENTRIES` ignores that many leading entries, for the day
    a proxy of our own is put in front and starts prepending.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]

    # The count, never the addresses: an IP address is personal data. One line
    # per distinct length is enough to see how many hops the platform adds,
    # which is exactly the fact whose absence hid the bug above.
    if len(chain) not in _reported_chain_lengths:
        _reported_chain_lengths.add(len(chain))
        logger.info("Forwarded chain observed entry_count=%d", len(chain))

    if chain:
        return chain[min(_skipped_leading_entries(), len(chain) - 1)]
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_ip,
    default_limits=[DEFAULT_LIMIT],
    headers_enabled=True,
)
