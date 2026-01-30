# Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install packages
pip install -r requirements.txt
```

### Step 2: Add Your OpenAI API Key
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your key:
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Run Tests
```bash
# Full evaluation (recommended first time)
python main.py

# Interactive testing (no evaluation)
python test_agent.py
```

---

## 📊 Expected Results

**Full Evaluation (main.py)**
- Runs 17 test cases
- Shows detailed pass/fail for each
- Target: 75%+ pass rate
- Takes ~2-5 minutes

**Interactive Testing (test_agent.py)**
- Type any bug report
- See real-time tool calls
- Watch graph execution
- Press Enter (empty) to exit

---

## 🧪 Example Test Queries

Try these in `test_agent.py`:

```
> Payment service crashing in production
> Button color doesn't match the design
> Random question about quantum physics
> Memory leak in background worker
> Typo in the footer text
```

---

## 📝 What Gets Evaluated?

Each test checks:
- ✓ **Tools** - Did it call the right tools?
- ✓ **Completion** - Did workflow finish?
- ✓ **Content** - Does output have required text?
- ✓ **Negative** - Did it avoid wrong actions?

---

## 🎯 Project Goals

This demonstrates:
1. **Multi-step graph** with 6 nodes
2. **Branching logic** based on severity
3. **Retry loops** for quality control
4. **Tool integration** (search & create)
5. **Golden set evaluation** for reliability

---

## 💡 Tips

- Use GPT-4 for best results (default)
- GPT-3.5-turbo works but scores lower
- Check `.env` if you get API errors
- Run `python test_agent.py` to debug specific cases
- Edit `golden_data.yaml` to add new test cases

---

## 🐛 Common Issues

**Import errors?**
→ Make sure venv is activated

**No API key?**
→ Check `.env` file exists and has your key

**Tests failing?**
→ Normal! Target is 75%+, not 100%

---

## 📚 Learn More

- See [README.md](README.md) for full documentation
- Check [setup_agent/orchestrator.py](setup_agent/orchestrator.py) for graph logic
- View [stage_1_golden_sets/golden_data.yaml](stage_1_golden_sets/golden_data.yaml) for test cases
