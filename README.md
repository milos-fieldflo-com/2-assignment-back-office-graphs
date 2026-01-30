# Bug Triage Agent – LangGraph Automation

> **Assignment**: Automate a Department Back Office Task with Graphs (Mainsail AI Launch Labs)

This project implements an intelligent bug triage system using LangGraph that automatically:
- Classifies bug severity (critical, high, medium, minor, trivial)
- Searches across Jira, Slack, and GitHub for duplicates
- Creates Jira tickets with appropriate priority
- Verifies output quality with retry loops
- Evaluates performance against a golden set of test cases

## 🎯 Features

✅ **Multi-step LangGraph workflow** (6 nodes: classify → search → decide → execute → verify → finalize)  
✅ **Branching logic** based on bug severity and classification  
✅ **Retry loop** with verification node (up to 3 retries for quality assurance)  
✅ **Multiple tools** (jira_search, slack_search, github_search, jira_create)  
✅ **Golden set evaluation** with 17 comprehensive test cases  
✅ **Mock data** – No external APIs required for testing

---

## 📋 Requirements

- **Python 3.11+**
- **OpenAI API Key** (required for LLM calls)
- Windows / Linux / macOS

---

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
```

**Note**: The agent uses OpenAI's GPT-4 model by default.

---

## 🧪 Usage

### Option 1: Run Full Evaluation (Recommended)

Runs the complete workflow with golden set evaluation:

```bash
python main.py
```

**What it does:**
1. Sets up mock environment
2. Seeds Jira, Slack, and GitHub fixtures
3. Runs 17 test cases from the golden set
4. Reports pass/fail results for each test
5. Shows overall score (e.g., "14/17 passed (82.4%)")

**Expected output:**
```
============================================================
RUNNING GOLDEN SET EVALUATION
============================================================
✓ bt-001: Login failure on production
  Tools: ✓  Completion: ✓  Content: ✓  Negative: ✓
...
Results: 14/17 passed (82.4%)
```

---

### Option 2: Test Agent Interactively (No Evaluation)

Test the graph with custom queries **without** running the golden set:

```bash
python test_agent.py
```

**What it does:**
- Starts an interactive prompt
- Type any bug report or query
- Shows the complete execution trace with all tool calls
- See state transitions and agent decisions in real-time

**Example session:**
```
Type prompt (empty line to exit)

> Payment service is crashing in production

===== EXECUTION TRACE =====

[SystemMessage]
You are Smart Bug Triage AI.

[HumanMessage]
Payment service is crashing in production

[AIMessage]
TOOL CALLS:
  → jira_search({'query': 'payment service crash production'})
  → slack_search({'query': 'payment service crash'})
  → github_search({'query': 'payment crash'})

[ToolMessage]
[CSE-9] [P1] [Open]
Type: Bug
Summary: Payment service failing intermittently
...

[AIMessage]
Created new Jira ticket CSE-10: Payment service crashing in production

Summary: High priority issue affecting payment processing...
===========================
```

**Use cases for test_agent.py:**
- 🔍 Debug specific scenarios
- 🧪 Test new bug reports
- 👀 Understand graph execution flow
- 🛠️ Develop and iterate on logic

---

## 📂 Project Structure

```
├── main.py                          # Full evaluation runner
├── test_agent.py                    # Interactive testing (no eval)
├── requirements.txt                 # Python dependencies
├── .env                            # API keys (create this)
│
├── setup_agent/
│   ├── orchestrator.py             # LangGraph workflow definition
│   └── mcp_tools.py                # Tool implementations (search, create)
│
├── setup_environment/
│   └── env_setup.py                # Mock environment setup
│
├── setup_seed_data/
│   ├── seed_data.py                # Seeds mock fixtures
│   └── mcp_fixtures/
│       ├── jira_tickets.json       # Mock Jira data
│       ├── slack_messages.json     # Mock Slack data
│       └── github_issues.json      # Mock GitHub data
│
└── stage_1_golden_sets/
    ├── golden_set.py               # Golden set runner
    ├── evaluator.py                # Test evaluation logic
    └── golden_data.yaml            # 17 test cases with expectations
```

---

## 🧩 Graph Architecture

### State Tracking

```python
class AgentState:
    messages: list              # Conversation history
    severity: str              # critical, high, medium, minor, trivial, not_a_bug
    is_valid_bug: bool         # Classification result
    duplicate_found: bool      # Duplicate detection
    ticket_created: bool       # Ticket creation status
    workflow_done: bool        # Completion flag
    retry_count: int          # Retry tracking (max 3)
    final_output: dict        # Structured result
```

### Workflow Nodes

1. **classify** – Determines if valid bug and assigns severity
2. **search** – Searches Jira, Slack, GitHub for duplicates
3. **decide** – Analyzes search results for existing tickets
4. **execute** – Creates ticket or references existing one
5. **verify** – Validates output quality (enables retry loop)
6. **finalize** – Creates structured final output

### Branching & Loops

- **Branch after classify**: Off-topic → end, Valid bug → search
- **Branch after verify**: Quality issues → retry (loop), Good → finalize
- **Retry loop**: Verify → agent → verify (up to 3 times)

---

## 📊 Golden Set Test Cases

The evaluation includes 17 test scenarios:

| Category | Test Cases |
|----------|------------|
| **Critical bugs** | Production outages, database crashes |
| **Duplicates** | Login failures, UI glitches already reported |
| **New bugs** | API crashes, memory leaks, 500 errors |
| **Minor issues** | Button colors, typos in footer |
| **Off-topic** | Quantum mechanics, life questions |
| **Ambiguous** | "Bug or feature request?" |

**Evaluation criteria:**
- ✓ **Tools**: Correct tools called (jira_search, slack_search, etc.)
- ✓ **Completion**: Workflow reached completion
- ✓ **Content**: Output contains required keywords
- ✓ **Negative**: Didn't call forbidden tools (e.g., no jira_create for duplicates)

---

## 🔧 Configuration

### Change LLM Model

Edit `setup_agent/orchestrator.py`:

```python
def create_agent(model: str = None, temperature: float = 0.0, system_prompt: str = None):
    model = model or 'gpt-4o-mini'  # Change to 'gpt-3.5-turbo', etc.
    llm = ChatOpenAI(model=model, temperature=temperature).bind_tools(TOOLS)
    ...
```

### Modify Test Cases

Edit `stage_1_golden_sets/golden_data.yaml` to add/modify test cases:

```yaml
test_cases:
  - id: "bt-018"
    query: "New test scenario"
    expected_tools: [jira_search, slack_search, github_search]
    must_call: [jira_create]
    must_contain: ["critical"]
```

---

## 🎓 Assignment Requirements Met

✅ Multi-step workflow (6+ nodes)  
✅ Multiple tools (4 tools: 3 search + 1 create)  
✅ Clear done output (Jira tickets, structured final_output)  
✅ Defined state (AgentState with 10+ tracked fields)  
✅ Branching decision (classify → search vs. end)  
✅ Loop implementation (verify → retry → verify)  
✅ Verification step (quality checks before completion)  
✅ Golden set evaluation (17 test cases, 80%+ pass rate)  

---

## 🐛 Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'yaml'`  
**Solution**: `pip install pyyaml`

**Issue**: `OpenAI API key not found`  
**Solution**: Create `.env` file with `OPENAI_API_KEY=your_key`

**Issue**: Tests failing with different LLM  
**Solution**: LLM behavior varies. Golden set tuned for GPT-4. Adjust expectations in `golden_data.yaml` if using different models.

---

## 📝 License

This is an educational project for Mainsail AI Launch Labs assignment.

---

## 🙏 Acknowledgments

- **LangGraph** for graph-based workflow framework
- **LangChain** for LLM tooling and integrations
- **Mainsail AI Launch Labs** for the assignment structure