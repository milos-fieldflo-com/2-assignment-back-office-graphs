import json
from pathlib import Path
from typing import Any
from langchain_core.tools import tool

FIXTURES_PATH = Path(__file__).parent.parent / "setup_seed_data" / "mcp_fixtures"

def load_jira_data() -> dict[str, Any]:
    path = FIXTURES_PATH / "jira_tickets.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"tickets": []}

def load_slack_data() -> dict[str, Any]:
    path = FIXTURES_PATH / "slack_messages.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"channels": [], "messages": []}

def load_github_data() -> dict[str, Any]:
    path = FIXTURES_PATH / "github_issues.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"issues": []}

@tool
def jira_search(query: str) -> str:
    """Search Jira tickets using a natural language query."""
    data = load_jira_data()

    tickets = data.get("tickets", [])
    if not tickets:
        return "No Jira data available."
    query_lower = query.lower()
    matched = []
    for t in tickets:
        searchable = " ".join([t.get("summary", ""), t.get("description", ""), t.get("status", ""), t.get("priority", ""), t.get("type", ""), " ".join(t.get("labels", []))]).lower()
        if any(word in searchable for word in query_lower.split() if len(word) > 3):
            matched.append(t)
    if not matched:
        return "No matching tickets found."
    formatted = []
    for t in matched[:5]:
        formatted.append(f"[{t['key']}] [{t.get('priority','N/A')}] [{t.get('status','Unknown')}]\nType: {t.get('type','Ticket')}\nSummary: {t.get('summary','No summary')}\nAssignee: {t.get('assignee') or 'Unassigned'}\nLabels: {', '.join(t.get('labels',[])) or 'None'}")
    return "\n\n".join(formatted)
    
@tool
def jira_create(summary: str, description: str, priority: str = "P2") -> str:
    """
    Create a new Jira ticket when no existing ticket matches the issue.
    """
    data = load_jira_data()
    tickets = data.setdefault("tickets", [])

    new_id = f"CSE-{len(tickets) + 1}"

    ticket = {
        "key": new_id,
        "summary": summary,
        "description": description,
        "status": "Open",
        "priority": priority,
        "type": "Bug",
        "assignee": None,
        "labels": [],
        "component": None,
        "team": None,
        "client": None,
    }

    tickets.append(ticket)

    path = FIXTURES_PATH / "jira_tickets.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return f"Created new Jira ticket {new_id}: {summary}"

@tool
def slack_search(query: str) -> str:
    """Search Slack messages and threads for relevant discussions."""
    data = load_slack_data()
    messages = data.get("messages", [])
    if not messages:
        return "No Slack data available."
    query_lower = query.lower()
    matched = []
    for thread in messages:
        thread_text = " ".join([m.get("text", "") for m in thread.get("thread", [])]).lower()
        if any(word in thread_text for word in query_lower.split() if len(word) > 3):
            matched.append(thread)
    if not matched:
        return "No matching Slack conversations found."
    formatted = []
    for t in matched[:3]:
        lines = [f"#{t['channel']}\n" + '-'*40]
        for msg in t['thread']:
            lines.append(f"{msg.get('user','Unknown')} ({msg.get('ts','')}):\n{msg.get('text','')}\n")
        formatted.append("\n".join(lines))
    return "\n\n".join(formatted)

@tool
def github_search(query: str) -> str:
    """Search GitHub issues by title."""
    data = load_github_data()
    issues = data.get("issues", [])
    matched = [i for i in issues if query.lower() in i.get('title','').lower()]
    if not matched:
        return "No matching GitHub issues found."
    return "\n".join([f"[{i['id']}] {i['title']}" for i in matched])
