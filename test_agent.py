from setup_agent.orchestrator import DEFAULT_SYSTEM_PROMPT, agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

def pretty(msg):
    name = msg.__class__.__name__
    content = getattr(msg, "content", "")
    print(f"\n[{name}]")
    if content:
        print(content)

    if hasattr(msg, "tool_calls") and msg.tool_calls:
        print("TOOL CALLS:")
        for tc in msg.tool_calls:
            print(f"  → {tc['name']}({tc['args']})")

print("Type prompt (empty line to exit)\n")

while True:
    q = input("> ").strip()
    if not q:
        break

    state = {
        "messages": [
            SystemMessage(content=DEFAULT_SYSTEM_PROMPT),
            HumanMessage(content=q),
        ]
    }

    result = agent.invoke(state)

    print("\n===== EXECUTION TRACE =====")
    for m in result["messages"]:
        pretty(m)
    print("\n===========================\n")
