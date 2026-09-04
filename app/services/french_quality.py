"""Is a piece of model output actually written in French?

The app is French only, and the prompts say so. Saying so is not enough: on
4 September 2026 a personalisation shipped an "Avant d'entrer" plan written
entirely in English, on screen and in the exported PDF. A control that
promises an effect has to have it.

Two rules were already here, in the legacy `/analyze` route, and they are
kept: a count of English marker words, and French words that must carry their
accents. Measured against the three lines that actually shipped, they catch
two of them and miss "Think about specific examples when discussing team
management" — which contains no marker at all. Enumerating English is a losing
game; every miss is a word nobody thought to list.

So the third rule reverses the question. Rather than asking whether the text
looks English, it asks whether it looks French: past a certain length, a
French sentence always contains one of a handful of function words. An English
sentence contains none. That rule alone catches all three shipped lines, and
none of the 25 fields of a real French generation.

This module carries the rules rather than the policy: `/analyze` and the v3
route compose them differently, and it outlives `/analyze`, which is due for
deletion once the TestFlight builds are replaced.
"""

from __future__ import annotations

import re

#: English words common enough in this domain that two of them together mean
#: the answer switched language. Kept from `/analyze`, where it was written.
ENGLISH_MARKERS = (
    "the",
    "and",
    "with",
    "for",
    "strong",
    "skills",
    "experience",
    "interview",
    "candidate",
    "role",
    "leadership",
    "career",
    "technical",
    "summary",
    "narrative",
    "positioning",
    "alignment",
    "core",
    "thread",
)

#: French words whose unaccented spelling is either English or careless. The
#: accent is what separates "experience" from "expérience".
REQUIRED_FRENCH_ACCENTS = {
    "experimente": "expérimenté",
    "experimentee": "expérimentée",
    "experimentees": "expérimentées",
    "experimentes": "expérimentés",
    "developpement": "développement",
    "developpeur": "développeur",
    "developpeuse": "développeuse",
    "coherent": "cohérent",
    "coherente": "cohérente",
    "coherents": "cohérents",
    "coherentes": "cohérentes",
    "competences": "compétences",
    "experience": "expérience",
}

#: Function words a French sentence of any length reaches for. Chosen so that
#: none is also an English word: "on" and "or" are French but read as English,
#: and are left out for that reason.
FRENCH_MARKERS = (
    "le", "la", "les", "de", "des", "du", "un", "une", "vous", "votre", "vos",
    "et", "que", "qui", "quoi", "pour", "dans", "avec", "sur", "au", "aux",
    "ce", "cet", "cette", "est", "sont", "ne", "pas", "plus", "son", "sa",
    "ses", "leur", "comme", "mais", "par", "en", "se", "sans", "chez", "tout",
    "toute", "vers", "avant", "après", "puis", "lorsque", "afin",
)

#: Below this, a French line can legitimately hold no function word at all —
#: "Relisez l'annonce." is three words and none of them is in the list. The
#: positive rule only applies past it.
MIN_LENGTH_FOR_FRENCH_MARKER = 40


def contains_english_markers(text: str) -> bool:
    """Two marker words or more: the answer changed language."""
    lowered = text.lower()
    matches = sum(1 for marker in ENGLISH_MARKERS if re.search(rf"\b{re.escape(marker)}\b", lowered))
    return matches >= 2


def contains_missing_required_accents(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in REQUIRED_FRENCH_ACCENTS)


def reads_as_french(text: str) -> bool:
    """Does a long enough line carry at least one French function word?

    The rule that catches what enumerating English misses. Short lines are
    exempt: below the threshold, an ordinary French imperative can contain no
    function word and would be failed for being terse.
    """
    if len(text) <= MIN_LENGTH_FOR_FRENCH_MARKER:
        return True
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(marker)}\b", lowered) for marker in FRENCH_MARKERS)


def is_french(text: str) -> bool:
    """The v3 policy: all three rules, any one of them enough to reject."""
    if not text.strip():
        return True
    if contains_english_markers(text):
        return False
    if contains_missing_required_accents(text):
        return False
    return reads_as_french(text)
