from langchain_core.tools import tool
import re

@tool("get_travel_cost")
def get_travel_cost(itinerary: str) -> str:
    """Estimate a rough travel cost from a free-text itinerary (dest, days, travelers)."""
    base_rates = {
        "tokyo": 250,
        "seoul": 220,
        "taipei": 200,
        "bangkok": 180,
        "singapore": 300,
    }

    destination = "unknown"
    days = 5
    travelers = 1

    lower = itinerary.lower()
    for city in base_rates:
        if city in lower:
            destination = city
            break

    numbers = [int(n) for n in re.findall(r"\d+", lower)]
    if numbers:
        if len(numbers) == 1:
            days = numbers[0]
        elif len(numbers) >= 2:
            days, travelers = numbers[:2]

    if destination == "unknown":
        return " Unable to estimate cost: destination not recognized."

    total = base_rates[destination] * days * travelers
    return (
        f" Destination: {destination.title()}\n"
        f" Duration: {days} day(s)\n"
        f" Travelers: {travelers}\n"
        f" Estimated Cost: ${total}"
    )
