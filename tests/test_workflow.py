from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from graph.nodes import support_node


@patch("graph.nodes.llm")
def test_support_node_returns_response(mock_llm):
    # Configure the model's response explicitly.
    mock_llm.invoke.return_value = AIMessage(
        content="Hello! How can I help you?"
    )

    state = {
        "messages": [HumanMessage(content="Hello")],
        "customer_id": None,
        "ticket_id": None,
        "intent": None,
        "requires_human": False,
        "sources": [],
        "error": None,
    }

    result = support_node(state)

    assert result["messages"][0].content == "Hello! How can I help you?"
    assert result["error"] is None

    mock_llm.invoke.assert_called_once()