from langchain_core.messages import HumanMessage

from agents.support_agent import get_support_agent


def main():
    agent = get_support_agent()

    response = agent.invoke(
        [HumanMessage(content="Hello! What can you help me with?")]
    )

    print(response.content)


if __name__ == "__main__":
    main()