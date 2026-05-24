# Closira Customer Conversation AI Agent

Python prototype for the Closira AI Engineering Intern assignment. It demonstrates an end-to-end customer support workflow for a fictional SMB, Bloom Aesthetics Clinic.

The workflow covers:

- FAQ answering from SOP data only
- Lead qualification with structured questions
- Escalation detection and reason logging
- End-of-session conversation summary

## Project Structure

```text
closira_agent/
  cli.py              # CLI entry point
  escalation.py       # Escalation detection rules
  faq.py              # SOP-grounded FAQ answering
  qualification.py    # Lead qualification flow
  sop.py              # SOP loading/search helpers
  summary.py          # Structured summary generation
  workflow.py         # Conversation orchestration
data/
  sop.json            # Source of truth for the AI
test_transcripts/     # Required sample conversations
prompt_design.md      # System prompt and design decisions
```

## Requirements

- Python 3.10+
- Anthropic API key, or a local Ollama server
- Python packages in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure Claude:

```bash
copy .env.example .env
```

Then edit `.env` and set:

```text
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LLM_PROVIDER=auto
```

Configure Ollama as a backup or primary provider:

```bash
ollama pull llama3.2
```

Then set:

```text
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

Provider behaviour:

- `auto`: use Anthropic when `ANTHROPIC_API_KEY` is set, otherwise use Ollama.
- `anthropic`: use Claude and optionally fall back to Ollama when `OLLAMA_FALLBACK=true`.
- `ollama`: use local Ollama directly.

You can also pass a provider or model at runtime with `--provider` and `--model`.

## Run

Start an interactive conversation:

```bash
python -m closira_agent.cli chat
```

Run all required demo scenarios:

```bash
python -m closira_agent.cli demo
```

Run a single message through the workflow:

```bash
python -m closira_agent.cli ask "What are your Botox prices?"
```

Choose a specific Claude model:

```bash
python -m closira_agent.cli --provider anthropic --model claude-sonnet-4-20250514 demo
```

Run with local Ollama:

```bash
python -m closira_agent.cli --provider ollama --model llama3.2 demo
```

## Expected Behaviours

The CLI handles the assignment scenarios:

1. In-SOP questions are answered only from `data/sop.json`.
2. Out-of-scope questions are acknowledged as SOP gaps and escalated.
3. Complaints, angry sentiment, medical questions, pricing negotiation, and explicit human handoff requests are escalated with reasons.
4. Lead qualification asks structured questions and stores responses.
5. Session summaries include customer intent, collected details, SOP gaps, escalation state, and next action.

## Trade-offs and Limitations

- The workflow uses LangChain structured outputs with Anthropic Claude or local Ollama.
- Ollama quality depends heavily on the local model. Use a model with strong instruction following and structured output support.
- The SOP is passed directly as JSON context. A production version should use retrieval over SOP chunks as the SOP grows.
- Escalation detection is model-driven and reinforced by a confidence threshold. In production, monitor real conversations and tune thresholds with evaluation data.
- The workflow logs escalation reasons in memory for the session; a deployed version should persist these to a CRM or support system.
