import json
from pathlib import Path

FIXTURES_PATH = Path(__file__).parent / 'mcp_fixtures'

def seed_data():
    FIXTURES_PATH.mkdir(exist_ok=True)

    jira_mock = {
        "tickets": [
            {"key": "CSE-1", "summary": "Login failure on production", "description": "Cannot login after update", "status": "Open", "priority": "P0", "type": "Bug", "assignee": None, "labels": ["backend"], "component": None, "team": None, "client": None},
            {"key": "CSE-2", "summary": "Minor dashboard UI glitch", "description": "Misaligned buttons", "status": "Open", "priority": "P1", "type": "Bug", "assignee": None, "labels": ["frontend"], "component": None, "team": None, "client": None}
        ]
    }
    with open(FIXTURES_PATH / 'jira_tickets.json', 'w') as f:
        json.dump(jira_mock, f)

    slack_mock = {
        "channels": ["#bugs"],
        "messages": [
            {"channel": "#bugs", "thread": [{"user": "alice", "text": "Login failure reported by client X", "ts": "2026-01-25T12:00:00"}]},
            {"channel": "#bugs", "thread": [{"user": "bob", "text": "Minor dashboard UI glitch", "ts": "2026-01-25T12:05:00"}]} 
        ]
    }
    with open(FIXTURES_PATH / 'slack_messages.json', 'w') as f:
        json.dump(slack_mock, f)

    github_mock = {
        "issues": [
            {"id": 101, "title": "Login failure on production"},
            {"id": 102, "title": "Minor dashboard UI glitch"}
        ]
    }
    with open(FIXTURES_PATH / 'github_issues.json', 'w') as f:
        json.dump(github_mock, f)

    print("Seeded mock Jira tickets, Slack messages, and GitHub issues")


if __name__ == "__main__":
    seed_data()
