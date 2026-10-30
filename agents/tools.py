"""Central registry of tools exposed to the language model.

Ticket status mutation is intentionally not exposed to the model in this batch.
A model-generated tool call is not proof of customer identity or authorization.
The application service will add an authenticated, policy-checked mutation path.
"""

from tools.customer_tools import lookup_customer
from tools.ticket_tools import get_support_ticket, list_customer_tickets
from tools.knowledge_tools import search_knowledge_base
from tools.web_search import search_web


SUPPORT_TOOLS = [
    lookup_customer,
    get_support_ticket,
    list_customer_tickets,
    search_knowledge_base,
    search_web,
]

TOOLS_BY_NAME = {support_tool.name: support_tool for support_tool in SUPPORT_TOOLS}
