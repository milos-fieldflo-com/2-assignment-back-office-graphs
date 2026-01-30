# Video Walkthrough Script (3-5 Minutes)

**Total Time**: ~4 minutes | **Pace**: Read naturally, not too fast

---

## 🎬 INTRODUCTION (30 seconds)

### Screen: Show README.md title

**Say:**
> "Hi, I'm presenting my bug triage automation system for the Mainsail AI Launch Labs assignment. This project automates the Engineering department's bug triage workflow using LangGraph. The system classifies incoming bug reports, searches for duplicates across Jira, Slack, and GitHub, and automatically creates tickets with the appropriate priority."

---

## 📊 PART 1: AUTOMATION STRUCTURE (90 seconds)

### Screen: Open `setup_agent/orchestrator.py` - scroll to the workflow section (around line 315)

**Say:**
> "Let me show you how the automation is structured. The system uses a LangGraph StateGraph with six distinct nodes that form a complete workflow."

### Screen: Show the workflow.add_node() calls

**Say:**
> "First, the **classify node** determines if this is a valid bug and assigns a severity level - critical, high, medium, minor, trivial, or not a bug.
>
> Second, the **search node** queries Jira, Slack, and GitHub for existing related issues. For trivial issues like typos, we only search Jira to reduce overhead.
>
> Third, the **decide node** analyzes search results to detect if a duplicate ticket already exists.
>
> Fourth, the **execute node** either creates a new Jira ticket with appropriate priority, or references the existing ticket if a duplicate was found.
>
> Fifth, the **verify node** checks output quality - this is where our retry loop happens. If verification fails and we haven't hit our retry limit of 3, we loop back to improve the output.
>
> Finally, the **finalize node** creates structured output with the ticket ID, actions taken, and a summary."

---

## 🔀 PART 2: GRAPH STATE AND BRANCHING (60 seconds)

### Screen: Scroll up to show the AgentState class (around line 25)

**Say:**
> "The state is tracked throughout the workflow using this AgentState class. We track the conversation messages, the severity classification, whether it's a valid bug, if duplicates were found, ticket creation status, retry count, and the final output."

### Screen: Scroll down to show conditional_edges (around line 350)

**Say:**
> "For branching, we have three key decision points:
>
> First, after classification - if it's not a valid bug, we skip directly to finalize. Otherwise, we proceed to search.
>
> Second, after verification - this is our retry loop. If quality checks fail and retry count is under 3, we loop back to the agent to try again. Otherwise, we proceed to finalize.
>
> Third, the agent decides whether to call tools or move to verification based on whether tool calls are needed.
>
> This branching ensures we don't waste resources searching for non-bugs, and our retry loop ensures quality output."

---

## 🎯 PART 3: EVAL STRATEGY & GOLDEN SET (90 seconds)

### Screen: Open `stage_1_golden_sets/golden_data.yaml`

**Say:**
> "For evaluation, I implemented a golden set with seventeen test cases covering diverse scenarios."

### Screen: Scroll through the test cases

**Say:**
> "The test cases include critical production outages, duplicate detection scenarios, new bugs that need tickets, minor UI issues, off-topic queries like 'explain quantum mechanics', and ambiguous queries like 'is this a bug or feature request?'"

### Screen: Show a specific test case (bt-015 or bt-002)

**Say:**
> "Each test case specifies expected tool calls, required content, and forbidden actions. For example, this critical database crash must call jira_create and must contain keywords like P0, critical, or urgent."

### Screen: Open `stage_1_golden_sets/evaluator.py` - show the checks

**Say:**
> "The evaluator checks four dimensions for each test:
>
> Tools - did it call the correct tools and avoid the wrong ones?
> Completion - did the workflow finish successfully?
> Content - does the output contain required keywords?
> Negative - did it avoid forbidden actions like creating duplicate tickets?"

### Screen: Show terminal with test results (or run `python main.py` if not visible)

**Say:**
> "Currently the system achieves 76.5% pass rate with 13 out of 17 tests passing. The failures are edge cases around ambiguous queries and content matching, which could be improved with more prompt engineering."

---

## 💡 PART 4: WHY THIS EVAL & TRADEOFFS (60 seconds)

### Screen: Show README.md - scroll to the "Golden Set Test Cases" table

**Say:**
> "I chose this golden set approach because bug triage has clear pass-fail criteria. Unlike open-ended tasks, we can definitively say whether the agent called the right tools, created or avoided creating a ticket, and included critical priority markers.
>
> The key tradeoffs I made:
>
> First, I prioritized recall over precision - it's better to search all three tools and find duplicates than to miss them and create duplicate tickets.
>
> Second, I implemented aggressive verification with retries. This adds latency but ensures tickets have complete information and proper severity labels.
>
> Third, I use rule-based severity classification combined with LLM tool execution. This hybrid approach is faster and more consistent than pure LLM classification, while still being flexible for edge cases."

---

## 🎬 CLOSING (10 seconds)

### Screen: Show README.md top or test_agent.py running

**Say:**
> "The system is production-ready for testing with an interactive mode for debugging and a full evaluation suite. Thank you for watching."

---

## 📋 RECORDING TIPS

### Before Recording:
1. ✅ Close unnecessary browser tabs/apps
2. ✅ Set screen resolution to 1920x1080 or 1280x720
3. ✅ Test audio - speak clearly, not too fast
4. ✅ Have all files ready to open:
   - `setup_agent/orchestrator.py`
   - `stage_1_golden_sets/golden_data.yaml`
   - `stage_1_golden_sets/evaluator.py`
   - `README.md`
   - Terminal with test results

### During Recording:
- Use a screen recorder (OBS, Loom, or QuickTime)
- Zoom in on code when showing specific sections (Ctrl/Cmd + Plus)
- Pause briefly between sections
- Use cursor/mouse to highlight what you're talking about
- If you make a mistake, pause, then restart that sentence

### Timing Check:
- Introduction: 30s
- Part 1: 90s (total 2:00)
- Part 2: 60s (total 3:00)
- Part 3: 90s (total 4:30)
- Part 4: 60s (total 5:30)
- Closing: 10s (total 5:40)

**Target**: Speak slightly faster or trim Part 4 to stay under 5 minutes

### Alternative Shorter Version (3 minutes):
- Skip detailed code walkthroughs
- Focus on high-level architecture
- Show graph visualization instead of code
- Abbreviate golden set examples to 2-3 test cases

---

## 🎥 OPTIONAL: Visual Aids

Consider creating a quick diagram showing:
```
User Query
    ↓
[Classify] → severity
    ↓
[Search] → 3 tools
    ↓
[Decide] → duplicate?
    ↓
[Execute] → create/reference ticket
    ↓
[Verify] → quality OK?
    ↓ (retry if needed)
[Finalize] → output
```

Show this diagram when explaining the structure.

---

## ✅ CHECKLIST BEFORE SUBMITTING

- [ ] Video is 3-5 minutes
- [ ] Explained automation structure ✓
- [ ] Showed graph state and branching ✓
- [ ] Explained eval strategy and golden set ✓
- [ ] Discussed tradeoffs and reasoning ✓
- [ ] Audio is clear
- [ ] Screen is readable (no tiny text)
- [ ] No sensitive information visible (API keys, etc.)

---

Good luck with your recording! 🎬
