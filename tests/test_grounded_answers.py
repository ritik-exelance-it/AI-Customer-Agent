from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from graph.workflow import support_graph


def test_knowledge_search_preserves_source_metadata():
    model_tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_knowledge_base",
                "args": {"query": "refund policy"},
                "id": "call_knowledge_1",
            }
        ],
    )

    final_answer = AIMessage(
        content=(
            "Refund eligibility must be verified against the applicable "
            "refund terms before a refund is promised. [Source: faq.md]"
        )
    )

    with patch("graph.nodes.llm") as mock_llm:
        mock_llm.bind_tools.return_value.invoke.side_effect = [
            model_tool_call,
            final_answer,
        ]

        result = support_graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="What is your refund policy?"
                    )
                ],
                "customer_id": None,
                "ticket_id": None,
                "intent": None,
                "requires_human": False,
                "sources": [],
                "error": None,
            }
        )

    assert result["error"] is None
    assert result["messages"][-1].content == final_answer.content

    assert result["sources"]
    assert any(
        source["source"] == "faq.md"
        for source in result["sources"]
    )

    mock_llm.bind_tools.return_value.invoke.assert_called()