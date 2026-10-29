from langchain_core.messages import AIMessage, HumanMessage

from graph.routing import route_after_support


def test_route_to_tools_when_model_requests_tool():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_knowledge_base",
                        "args": {"query": "refund policy"},
                        "id": "call_1",
                    }
                ],
            )
        ],
        "requires_human": False,
        "error": None,
    }

    assert route_after_support(state) == "tools"


def test_route_to_end_when_model_has_final_answer():
    state = {
        "messages": [AIMessage(content="Here is your answer.")],
        "requires_human": False,
        "error": None,
    }

    assert route_after_support(state) == "end"


def test_route_to_escalation_when_required():
    state = {
        "messages": [HumanMessage(content="I need a human representative.")],
        "requires_human": True,
        "error": None,
    }

    assert route_after_support(state) == "escalation"


def test_route_to_end_when_an_error_exists():
    state = {
        "messages": [],
        "requires_human": False,
        "error": "Model unavailable",
    }

    assert route_after_support(state) == "end"