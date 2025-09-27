from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage, BaseMessage

from app.agents.advisor_agent import advisor_chain
from app.agents.budget_agent import budget_chain
from app.agents.loyalty_agent import loyalty_chain
from app.agents.planner_agent import make_planner_messages, planner_llm

from app.tools.holiday_package_tool import get_holiday_packages
from app.tools.travel_cost_tool import get_travel_cost
from app.tools.loyalty_tool import get_loyalty_status, apply_loyalty_discount

from app.state import TravelState
from app.utils import update_state, mentions_loyalty


# ---------------- Router ----------------
def route(state: TravelState) -> str:
    """orchestrate: advise -> budget -> (optional) loyalty -> plan"""
    if not state.get("advice_notes"):
        return "advise_preferences"
    if not state.get("cost_analysis"):
        return "estimate_costs"

    if mentions_loyalty(state.get("user_preferences", "")) and not state.get("loyalty_status"):
        return "assess_loyalty"

    # finalize will terminate; we always proceed to plan next
    return "plan_itinerary"


# ---------------- Build Graph ----------------
def build_travel_graph():
    g = StateGraph(TravelState)

    # Entry / no-op node (lets router decide)
    g.add_node("orchestrator", RunnableLambda(lambda s: s))

    # 1) Advise preferences (advisor agent)
    g.add_node(
        "advise_preferences",
        RunnableLambda(
            lambda s: update_state(
                s,
                "advice_notes",
                advisor_chain.invoke({"user_input": s["user_preferences"]}),
            )
        ),
    )

    # 2) Estimate costs (budget agent)
    g.add_node(
        "estimate_costs",
        RunnableLambda(
            lambda s: update_state(
                s,
                "cost_analysis",
                budget_chain.invoke({"user_input": s["user_preferences"]}),
            )
        ),
    )

    # 3) Assess loyalty (only when mentioned by user)
    g.add_node(
        "assess_loyalty",
        RunnableLambda(
            lambda s: update_state(
                s,
                "loyalty_status",
                loyalty_chain.invoke({"user_input": s["user_preferences"]}),
            )
        ),
    )


    BASE_TOOLS = [get_holiday_packages, get_travel_cost]
    planner_llm_with_tools = planner_llm.bind_tools(BASE_TOOLS)

    def planner_step(state: TravelState):
        text = (state.get("user_preferences") or "").lower()
        region = (
            "europe" if any(k in text for k in ["paris","europe","italy","france","spain"]) else
            "asia" if any(k in text for k in ["japan","tokyo","bali","asia","thailand","seoul"]) else
            "americas" if any(k in text for k in ["usa","new york","peru","argentina","america"]) else
            "africa" if any(k in text for k in ["kenya","cape town","marrakech","africa"]) else
            "middle-east" if any(k in text for k in ["dubai","abu dhabi","jordan","lebanon"]) else
            "worldwide"
        )
        pkgs = get_holiday_packages.invoke({"region": region, "query": ""})
        msgs = make_planner_messages(pkgs, state["user_preferences"])
        ai_msg: AIMessage = planner_llm_with_tools.invoke(msgs)
        return {"messages": [ai_msg]}

    g.add_node("plan_itinerary", RunnableLambda(planner_step))

    # Tool execution node for the ReAct loop
    g.add_node("execute_tools", ToolNode(BASE_TOOLS))

    # 5) Finalize plan & post-process loyalty (non-blocking; assume guest if unknown)
    def finalize_step(s: TravelState):
        # Copy last AI message content into raw_itinerary (if present)
        content = None
        if s.get("messages"):
            last: BaseMessage = s["messages"][-1]
            if isinstance(last, AIMessage) and isinstance(last.content, str) and last.content.strip():
                content = last.content.strip()

        s = update_state(s, "raw_itinerary", content or s.get("raw_itinerary") or "Itinerary compiled.")

        # Loyalty enrichment (default to guest; never block)
        if s.get("loyalty_status") is None:
            try:
                status = get_loyalty_status.invoke({"user_id": "guest"})  # or {} if your tool arg is Optional
            except Exception:
                status = "None"
            s["loyalty_status"] = status

            try:
                discount = apply_loyalty_discount.invoke({"status": status})
            except Exception:
                discount = " No discount available for this tier"
            s["loyalty_discount"] = discount

            s["conversation_log"].append(f"loyalty → {status} / {discount}")

        return s

    g.add_node("finalize_plan", RunnableLambda(finalize_step))

    # ---------------- Wiring ----------------
    g.set_entry_point("orchestrator")

    # Router decides next step (note: no END branch here)
    g.add_conditional_edges(
        "orchestrator",
        route,
        {
            "advise_preferences": "advise_preferences",
            "estimate_costs": "estimate_costs",
            "assess_loyalty": "assess_loyalty",
            "plan_itinerary": "plan_itinerary",
        },
    )

    # Bounce back to orchestrator after advisory stages
    g.add_edge("advise_preferences", "orchestrator")
    g.add_edge("estimate_costs", "orchestrator")
    g.add_edge("assess_loyalty", "orchestrator")

    # ReAct loop: tools -> back to planner; else -> finalize
    g.add_conditional_edges(
        "plan_itinerary",
        tools_condition,
        {
            "tools": "execute_tools",
            "__end__": "finalize_plan",
        },
    )
    g.add_edge("execute_tools", "plan_itinerary")

    # Terminate after finalize so END renders at the tail
    g.add_edge("finalize_plan", END)

    # Compile & visualize once
    compiled = g.compile()
    print("\n Travel Planner Workflow:\n")
    try:
        print(compiled.get_graph().draw_ascii())
    except Exception:
        pass
    return compiled
