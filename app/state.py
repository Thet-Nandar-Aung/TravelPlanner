
from typing import TypedDict, Optional, List, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages  # <- reducer

class TravelState(TypedDict):
    # ReAct/chat history for ToolNode + tools_condition
    messages: Annotated[Sequence[BaseMessage], add_messages]

    user_preferences: Annotated[str, "dynamic"]
    raw_itinerary: Optional[str]
    cost_analysis: Optional[str]
    advice_notes: Optional[str]
    loyalty_status: Optional[str]
    loyalty_discount: Optional[str]
    conversation_log: Annotated[List[str], "input"]

initial_state: TravelState = {
    "messages": [],
    "user_preferences": "5-day winter trip to Japan in December, under $2000, including Kyoto and Tokyo",
    "raw_itinerary": None,
    "cost_analysis": None,
    "advice_notes": None,
    "loyalty_status": None,
    "loyalty_discount": None,
    "conversation_log": [],
}
