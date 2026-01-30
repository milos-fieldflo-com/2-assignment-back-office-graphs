import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import yaml
from setup_agent.orchestrator import agent
from langchain_core.messages import SystemMessage, HumanMessage

def run_eval():
    with open("stage_1_golden_sets/golden_data.yaml") as f:
        tests = yaml.safe_load(f)["test_cases"]

    passed = 0

    for t in tests:
        state = {
            "messages": [
                SystemMessage(content="You are Smart Bug Triage AI."),
                HumanMessage(content=t["query"]),
            ]
        }

        result = agent.invoke(state)
        messages = result["messages"]

        tool_calls = [
            tc["name"]
            for m in messages
            if hasattr(m, "tool_calls")
            for tc in m.tool_calls
        ]

        checks = {
            "tools": True,
            "completion": True,
            "content": True,
            "negative": True,
        }

        for tool in t.get("expected_tools", []):
            if tool not in tool_calls:
                checks["tools"] = False

        for tool in t.get("must_call", []):
            if tool not in tool_calls:
                checks["tools"] = False

        for tool in t.get("must_not_call", []):
            if tool in tool_calls:
                checks["tools"] = False

        has_output = bool(result.get("final_output", {}).get("status"))
        if t.get("expected_tools") and not has_output:
            checks["completion"] = False
            
        response_text = " ".join(
            m.content if hasattr(m, "content") else "" for m in messages
        )
            
        for phrase in t.get("must_contain", []):
            if re.search(re.escape(phrase), response_text, re.IGNORECASE) is None:
                checks["content"] = False

        for phrase in t.get("must_not_call", []):
            if re.search(re.escape(phrase), response_text, re.IGNORECASE):
                checks["negative"] = False
            
        ok = all(checks.values())

        status = "✓" if ok else "✗"
        print(f"{status} {t['id']}: {t['query']}")
        print(
            f"  Tools: {'✓' if checks['tools'] else '✗'}"
            f"  Completion: {'✓' if checks['completion'] else '✗'}"
            f"  Content: {'✓' if checks['content'] else '✗'}"
            f"  Negative: {'✓' if checks['negative'] else '✗'}"
        )
        print()

        if ok:
            passed += 1

    pct = passed / len(tests) * 100
    print("-" * 40)
    print(f"Results: {passed}/{len(tests)} passed ({pct:.1f}%)")

if __name__ == "__main__":
    run_eval()
