# app/run.py
from .main import build_travel_graph
from .state import initial_state
from app.utils import is_travel_intent


WELCOME = "Welcome from Travel Planner Committee. How can I assist you today?"
HELP = """\
Commands:
  help   - show this message
  reset  - clear session state
  quit   - exit the planner

Examples:
  • plan a 4-day Bali trip under SGD 2000 in June
  • 7-day Japan (Tokyo/Kyoto) in December for 2 pax, ~SGD 3500
  • 5 days in Paris this spring, food + museums focus, ~10000
"""


def print_result(result: dict):
    print("\n Final Itinerary Suggestion:\n")
    print(result.get("raw_itinerary", "Planner agent did not return a result."))

    print("\n Agent Summary:")
    print(f"- Advice:  {result.get('advice_notes')}")
    print(f"- Cost:    {result.get('cost_analysis')}")
    print(f"- Loyalty: {result.get('loyalty_status') or 'N/A'}")
    if result.get("loyalty_discount"):
        print(f"- Perks:   {result.get('loyalty_discount')}")
    last_log = (result.get("conversation_log") or [])[-1:] or [""]
    print(f"- Log:     {last_log[0]}")


def run_chat():
    # Build once (main.py can visualize the graph)
    graph = build_travel_graph()

    print("\n Travel Planner Committee \n")
    print(WELCOME)
    print("(type 'help' for examples)\n")

    # Keep a working state for the session
    state = initial_state.copy()
    state.setdefault("conversation_log", [])

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n Have a nice day, Goodbye!\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("quit", "exit"):
            print("\n Have a nice day, Goodbye!\n")
            break
        if cmd == "help":
            print("\n" + HELP + "\n")
            continue
        if cmd == "reset":
            state = initial_state.copy()
            state.setdefault("conversation_log", [])
            print("↺ Session state reset.\n")
            continue

        # Guardrail: only handle travel-related queries
        if not is_travel_intent(user_input):
            print("\n This app focuses on travel planning (itineraries, budgets, packages, tips).")
            print("   Try: “Plan a 4-day Bali trip under SGD 2000.”\n")
            continue

        # Feed state and run
        state["user_preferences"] = user_input
        state["conversation_log"].append(f"User → {user_input}")
        state.pop("assistant_question", None)

        result = graph.invoke(state)

        # If the graph asks for one clarification, gather once and re-run
        if result.get("assistant_question"):
            print("\n Clarification needed:")
            print(result["assistant_question"])
            followup = input("You (details): ").strip()
            state["user_preferences"] = followup
            state["conversation_log"].append(f"User → {followup}")
            result = graph.invoke(state)

        print_result(result)
        print()  # spacing


if __name__ == "__main__":
    run_chat()
