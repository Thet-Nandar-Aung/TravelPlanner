
"""
Utility helpers for TravelPlanner.

- update_state(state, key, value): mutate state and append a concise log line
- mentions_loyalty(text): heuristic to detect loyalty/miles/status mentions
- is_travel_intent(text): guardrail to accept only travel-related queries
- last_ai_text(messages): extract the last AI message text (if any)
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

try:
    from langchain_core.messages import AIMessage, BaseMessage  # type: ignore
except Exception:
    # Fallback typing shim if langchain_core isn't available at import time
    class BaseMessage:  # type: ignore
        content: Any
    class AIMessage(BaseMessage):  # type: ignore
        pass


# --- Logging helper -----------------------------------------------------------

def update_state(state: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """
    Set state[key] = value and append a short preview to `conversation_log`.

    The preview is truncated to keep logs readable.
    """
    state[key] = value
    try:
        preview = _preview_value(value)
        state.setdefault("conversation_log", []).append(f"{key} → {preview}")
    except Exception:
        # Never fail the graph due to logging
        pass
    return state


def _preview_value(value: Any, max_len: int = 240) -> str:
    """Return a single-line, truncated preview for logs."""
    if isinstance(value, str):
        txt = " ".join(value.split())  # collapse whitespace/newlines
        return (txt[: max_len - 1] + "…") if len(txt) > max_len else txt
    return "✅"


# --- Router heuristics --------------------------------------------------------

LOYALTY_KEYWORDS = [
    "loyalty", "miles", "status", "tier", "perk", "perks",
    "elite", "krisflyer", "skywards", "oneworld", "star alliance",
    "priority pass", "lounge", "upgrade",
]

def mentions_loyalty(text: Optional[str]) -> bool:
    """Return True if the user text mentions loyalty/status concepts."""
    t = (text or "").lower()
    return any(k in t for k in LOYALTY_KEYWORDS)


# --- Intent guard (accept only travel queries) --------------------------------

TRAVEL_KEYWORDS = [
    "trip", "travel", "itinerary", "flight", "flights",
    "hotel", "hotels", "stay", "booking", "book", "reservation",
    "budget", "cost", "visa", "tour", "tours", "package", "packages",
    "day", "days", "plan", "planner", "vacation", "holiday",
    "destination", "city", "cities", "airport", "train",
    "jr pass", "rail pass", "metro", "museum", "beach", "temple",
    "island", "cruise", "car rental", "transport", "transfer",
]

_MATH_TOKEN_RE = re.compile(r"\b\d+\s*(?:[+\-*/]|plus|minus|times|x|÷|divided|mod)\s*\d+\b")
_ONLY_MATH_CHARS_RE = re.compile(r"^[\s\d+\-*/().=x÷,%]+$")
_CODEY_RE = re.compile(r"\b(print|def|class|var|let|const|SELECT|INSERT|UPDATE|DELETE)\b", re.I)

def is_travel_intent(text: Optional[str]) -> bool:
    """
    True iff the text looks like a travel request.
    Rejects obvious math/code and accepts messages containing travel keywords.
    """
    t = (text or "").strip().lower()
    if not t:
        return False

    # Quick rejection: math-like or code-like
    if _MATH_TOKEN_RE.search(t):
        return False
    if _ONLY_MATH_CHARS_RE.match(t):
        return False
    if _CODEY_RE.search(t):
        return False

    # Accept if at least one travel keyword appears
    if any(k in t for k in TRAVEL_KEYWORDS):
        return True

    # Soft accept: common travel phrasing without keywords (e.g., "Paris in May", "Bali 5 days")
    if re.search(r"\b(\d+\s*day|\d+\s*nights?)\b", t):
        return True
    if re.search(r"\b(spring|summer|autumn|fall|winter|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", t):
        return True
    if re.search(r"\b(paris|tokyo|kyoto|osaka|bali|london|rome|barcelona|seoul|taipei|bangkok|singapore|dubai|nyc|new york|sydney|cape town)\b", t):
        return True

    return False


# --- Messages helper ----------------------------------------------------------

def last_ai_text(messages: Optional[List[BaseMessage]]) -> Optional[str]:
    """Return the last AI message text, if available."""
    if not messages:
        return None
    m = messages[-1]
    if isinstance(m, AIMessage) and isinstance(m.content, str):
        txt = m.content.strip()
        return txt or None
    return None


__all__ = [
    "update_state",
    "mentions_loyalty",
    "is_travel_intent",
    "last_ai_text",
]
