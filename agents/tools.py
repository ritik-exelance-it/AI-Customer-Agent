from tools.customer_tools import lookup_customer
from tools.ticket_tools import (
    get_support_ticket,
    list_customer_tickets,
    update_support_ticket_status,
)
from tools.knowledge_tools import search_knowledge_base
from tools.web_search import search_web


SUPPORT_TOOLS = [
    lookup_customer,
    get_support_ticket,
    list_customer_tickets,
    update_support_ticket_status,
    search_knowledge_base,
    search_web,
]

TOOLS_BY_NAME = {
    support_tool.name: support_tool
    for support_tool in SUPPORT_TOOLS
}