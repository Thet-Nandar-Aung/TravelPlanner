from typing import Optional
from langchain_core.tools import tool

@tool("get_loyalty_status")
def get_loyalty_status(user_id: Optional[str] = None) -> str:
    """Return loyalty tier for a user_id; if missing, assume guest."""
    u = (user_id or "guest").lower()
    if u == "121122":
        return "Gold"
    if u.startswith("guest"):
        return "None"
    return "Silver"

@tool("apply_loyalty_discount")
def apply_loyalty_discount(status: Optional[str] = None) -> str:
    """Return perk string for a given tier; if missing, assume None."""
    t = (status or "None").strip().capitalize()
    if t == "Gold":
        return " 10% discount + free lounge access"
    if t == "Silver":
        return " 5% discount on all bookings"
    return " No discount available for this tier"
