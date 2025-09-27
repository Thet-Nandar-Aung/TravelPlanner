from langchain_core.tools import tool
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

# Thompsons regions we can scrape reliably
THOMPSONS_REGION_SLUGS = {
    "asia": ["far-east"],
    "europe": ["europe"],
    "africa": ["africa"],
    "americas": ["americas"],
    "middle-east": ["middle-east"],
    "indian-ocean": ["indian-ocean"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TravelPlanner/1.0; +https://example.com)"
}


def _fetch_thompsons(slug: str) -> List[Tuple[str, str, str]]:
    """Scrape a Thompsons region page. Returns (title, desc, source)."""
    url = f"https://www.thompsons.co.za/our-destinations/{slug}"
    out: List[Tuple[str, str, str]] = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        cards = soup.select(".package-card") or soup.select(".card, article")
        for c in cards:
            title_el = c.select_one(".package-title") or c.select_one("h3, h2, a")
            desc_el  = c.select_one(".package-description") or c.select_one("p")
            title = (title_el.get_text(strip=True) if title_el else "").strip()
            desc  = (desc_el.get_text(strip=True)  if desc_el  else "").strip()
            if title:
                out.append((title, desc, f"Thompsons – {slug.replace('-', ' ').title()}"))
    except requests.exceptions.RequestException:
        return []
    return out


def _sample_fallback(region: str) -> List[Tuple[str, str, str]]:
    """Offline-safe examples so the planner never stalls."""
    region_title = region.title() if region != "worldwide" else "Worldwide"
    return [
        (f"{region_title} Highlights 7D6N", "City tour + 2 day trips + free day; 3★ hotels incl. breakfast.", "Sample"),
        (f"{region_title} Essentials 10D9N", "Signature landmarks + local food walk + optional add-ons.", "Sample"),
        (f"{region_title} Family Fun 5D4N", "Kid-friendly pace, short transfers, flexible downtime.", "Sample"),
    ]


@tool("get_holiday_packages")
def get_holiday_packages(region: str = "worldwide", query: str = "", max_results: int = 8) -> str:
    """
    Fetch current holiday packages by region (worldwide support).

    Args:
        region: one of "worldwide", "asia", "europe", "africa", "americas", "middle-east", "indian-ocean".
                "worldwide" aggregates multiple regions.
        query:  optional keyword to filter titles/descriptions.
        max_results: max items to return.

    Returns:
        str: A formatted list: "🌍 Holiday Packages (Region):\\n- Title — snippet [Source]\\n..."
    """
    region_key = (region or "worldwide").strip().lower()
    results: List[Tuple[str, str, str]] = []

    # Which pages to scan
    if region_key == "worldwide":
        slugs = [s for lst in THOMPSONS_REGION_SLUGS.values() for s in lst]
    else:
        slugs = THOMPSONS_REGION_SLUGS.get(region_key, [])

    # Scrape provider pages
    for slug in slugs:
        items = _fetch_thompsons(slug)
        results.extend(items)
        if len(results) >= max_results:
            break

    # Fallback if nothing scraped
    if not results:
        results = _sample_fallback(region_key)

    # Filter by query
    q = query.strip().lower()
    if q:
        results = [r for r in results if q in (r[0].lower() + " " + r[1].lower())]

    results = results[:max_results]
    if not results:
        return f"⚠️ No matching packages found for region='{region_key}', query='{query}'."

    lines = [f"🌍 Holiday Packages ({region_key.title()}):"]
    for title, desc, src in results:
        desc_part = f" — {desc}" if desc else ""
        lines.append(f"- {title}{desc_part}  [{src}]")
    return "\n".join(lines)


# --- Backward compatibility for your existing code ---
@tool("get_east_asia_packages")
def get_east_asia_packages(query: str = "", max_results: int = 5) -> str:
    """
    Back-compat wrapper: returns Asia packages (previous tool name).
    """
    return get_holiday_packages(region="asia", query=query, max_results=max_results)
