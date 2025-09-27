from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-5-mini", temperature=1)

budget_prompt = PromptTemplate.from_template(
    """You are a pragmatic travel budget analyst. Given the user's request,
estimate a realistic total trip cost with line items, and state clearly whether
the plan is UNDER or OVER their stated budget. Do NOT ask for user IDs or PII.
If details are missing, make sensible assumptions and list them.

User input:
{user_input}

Your goals:
1) Parse key budget inputs from the text (destinations, dates/month, duration in days/nights,
   party size, stated budget amount/currency if present).
2) Choose a single currency: if none is given, assume SGD (user likely in Singapore).
3) Produce a line-item estimate with simple formulas (e.g., nights × nightly rate).
4) Provide 2–3 savings levers (e.g., move dates, swap area, lodging tier).
5) If OVER budget, propose a target-meeting swap (what to change to get ≤ budget).
6) End with a machine-readable verdict block so other agents can parse it.

Return your answer in this exact structure:

### Parsed Inputs
- Destinations: …
- Dates/Month & Duration: …
- Party size: …
- Budget (currency): …
- Notes (interests/pace/constraints if detectable): …

### Cost Estimate (all amounts in one currency)
- Flights: …
- Lodging: … (N nights × nightly rate)
- Local transport: …
- Activities & attractions: …
- Food & drinks: …
- Misc/contingency (~10%): …
**Estimated total:** …

### Savings Levers
- …
- …
- (Optional) …

### If Over Budget (only include when applicable)
- Swap plan: …
- New total (est.): …

### Assumptions
- …
- …

### Budget Verdict
BUDGET_STATUS: UNDER | OVER | UNKNOWN
BUDGET_JSON: {{"currency":"<ISO or 'SGD'>","budget":<number or null>,"est_total":<number>,"buffer":<number or null>}}

Guidelines:
- Prefer conservative, round numbers; avoid false precision.
- If no budget was provided, put `budget=null`, `buffer=null`, and set STATUS to UNKNOWN.
- If duration missing, assume 5–7 days; if party size missing, assume 2 adults.
- Keep to ~220–320 words total."""
)

budget_chain = budget_prompt | llm | StrOutputParser()
