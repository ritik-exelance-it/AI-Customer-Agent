from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from graph.nodes import support_node
from graph.workflow import support_graph


@patch("graph.nodes.llm")
def test_support_node_returns_response(mock_llm):
    mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(
        content="Hello! How can I help you?"
    )

    state = {
        "messages": [HumanMessage(content="How can I get support?")],
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

    mock_llm.bind_tools.return_value.invoke.assert_called_once()


def test_standalone_greeting_does_not_call_model():
    with patch("graph.nodes.llm") as mock_llm:
        result = support_graph.invoke(
            {"messages": [HumanMessage(content="Hi!")]}
        )

    assert result["messages"][-1].content == "Hi! How can I help you today?"
    assert result["error"] is None
    mock_llm.bind_tools.assert_not_called()


def test_out_of_scope_question_is_refused_without_calling_model():
    with patch("graph.nodes.llm") as mock_llm:
        result = support_graph.invoke(
            {"messages": [HumanMessage(content="What is the capital of France?")]}
        )

    assert "customer-support questions" in result["messages"][-1].content
    assert result["error"] is None
    mock_llm.bind_tools.assert_not_called()


def test_bill_statement_request_explains_missing_billing_integration():
    with patch("graph.nodes.llm") as mock_llm:
        result = support_graph.invoke(
            {"messages": [HumanMessage(content="Can you show me my bills?")]}
        )

    answer = result["messages"][-1].content
    assert "isn't connected to billing statements" in answer
    assert "billing-policy questions" in answer
    assert result["error"] is None
    mock_llm.bind_tools.assert_not_called()


@patch("graph.nodes.llm")
def test_customer_name_is_allowed_after_support_clarification(mock_llm):
    mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(
        content="Thanks. Please provide the customer ID to look up the account."
    )
    history = [
        HumanMessage(content="Can you look up my account?"),
        AIMessage(content="What is your customer ID or name?"),
        HumanMessage(content="I am Alex Morgan"),
    ]

    result = support_node({"messages": history})

    assert result["messages"][0].content.startswith("Thanks.")
    mock_llm.bind_tools.return_value.invoke.assert_called_once()


@patch("graph.nodes.llm")
def test_customer_id_is_allowed_after_support_clarification(mock_llm):
    mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(
        content="I couldn't find that customer ID. Please check the ID and try again."
    )
    history = [
        HumanMessage(content="Can you look up my account?"),
        AIMessage(content="What is your customer ID?"),
        HumanMessage(content="my id is cust-001"),
    ]

    result = support_node({"messages": history})

    assert "couldn't find" in result["messages"][0].content
    mock_llm.bind_tools.return_value.invoke.assert_called_once()


@patch("graph.nodes.llm")
def test_support_question_uses_model(mock_llm):
    mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(
        content="You can reset it using the password reset link."
    )

    result = support_graph.invoke(
        {"messages": [HumanMessage(content="How do I reset my password?")]}
    )

    assert "reset it" in result["messages"][-1].content
    mock_llm.bind_tools.return_value.invoke.assert_called_once()


@patch("graph.nodes.llm")
def test_greeting_with_a_support_request_uses_model(mock_llm):
    mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(
        content="I can help with your ticket."
    )

    result = support_node(
        {"messages": [HumanMessage(content="Hi, can you check my ticket?")]}
    )

    assert result["messages"][0].content == "I can help with your ticket."
    mock_llm.bind_tools.return_value.invoke.assert_called_once()


def test_support_node_handles_empty_messages():
    result = support_node({"messages": []})

    assert result["error"] == "No messages were provided."