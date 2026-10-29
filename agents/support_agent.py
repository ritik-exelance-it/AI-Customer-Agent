
"""Customer support agent initialization."""

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda

from agents.prompts import CUSTOMER_SUPPORT_SYSTEM_PROMPT
from model import llm


def get_support_agent():
    """Return a runnable that applies the support system prompt."""

    def invoke_with_system_prompt(messages):
        return llm.invoke(
            [
                SystemMessage(content=CUSTOMER_SUPPORT_SYSTEM_PROMPT),
                *messages,
            ]
        )

    return RunnableLambda(invoke_with_system_prompt)
