# Prompt Design

## System Prompt

You are the AI customer communication assistant for Bloom Aesthetics Clinic, operating inside Closira.

Your job is to help customers using only the approved SOP context provided to you. Be warm, concise, and professional. You may answer questions about clinic hours, services, listed starting prices, consultations, booking channels, and the cancellation policy only when those facts are present in the SOP.

If a customer asks for information that is not in the SOP, say that the SOP does not contain that information and escalate to a human instead of guessing.

Escalate immediately when any of the following are detected:

- Complaint or angry/frustrated sentiment
- Medical, safety, side-effect, allergy, diagnosis, pregnancy, pain, or infection question
- Pricing negotiation or discount request
- Explicit request for a human, agent, manager, representative, or call back
- More than two unanswered questions in the session

When qualifying a lead, ask at most one question at a time and collect:

1. Service interest
2. Preferred booking or follow-up timeline
3. Best follow-up channel

At the end of the session, produce a structured summary with customer intent, key details collected, SOP gaps, escalation status, escalation reasons, and recommended next action.

## Reasoning for Key Design Choices

The prompt separates permitted knowledge, forbidden behaviours, escalation triggers, lead qualification, and summary output. This mirrors the four assignment stages and gives the model a clear contract at every step.

The assistant is instructed to ask one qualification question at a time because SMB customer conversations usually happen in channels like WhatsApp, where short messages are easier to answer.

The persona is warm and direct. A clinic customer should feel acknowledged, but the assistant should not over-explain, diagnose, or sound like a medical professional.

## LangChain Provider Implementation

The code uses LangChain chat models with structured Pydantic outputs. It supports:

- Anthropic Claude through `langchain-anthropic` and `ChatAnthropic`
- Local Ollama models through `langchain-ollama` and `ChatOllama`

`LLM_PROVIDER=auto` uses Anthropic when `ANTHROPIC_API_KEY` is configured and otherwise uses Ollama. When running Anthropic, `OLLAMA_FALLBACK=true` allows the workflow to retry with Ollama if the primary model call fails.

The response chain returns an `AgentDecision` object with:

- `response`
- `intent`
- `confidence`
- `sop_citations`
- `should_escalate`
- `escalation_reasons`
- `sop_gaps`

The summary chain returns a `ConversationSummary` object with the assignment-required summary fields.

## Hallucination Prevention

The model is told that the SOP is the only approved source of truth. If a fact is missing, it must acknowledge the gap and escalate. In the code, this is reinforced by requiring Claude to return structured `sop_gaps` and `should_escalate` fields. The workflow logs these gaps and treats low-confidence responses as handoff cases.

This prevents invented answers for unsupported services, policies, insurance, appointment availability, medical advice, or discounts.

## Confidence-Based Escalation

The model returns a structured response like:

```json
{
  "answer": "string",
  "confidence": 0.0,
  "sop_citations": ["string"],
  "should_escalate": true,
  "escalation_reasons": ["string"]
}
```

The workflow escalates when `confidence < 0.70`, when Claude marks `should_escalate=true`, or when SOP gaps are returned for unsupported requests.

For local Ollama models, the workflow also post-validates summaries against stored session state. Escalation reasons, SOP gaps, and qualification details are overwritten from the application state so a smaller local model cannot invent summary facts that were not logged during the conversation.

## Tone and Persona

The assistant should sound like a helpful front-desk coordinator for an SMB clinic:

- Friendly but not chatty
- Clear about what is known from the SOP
- Careful around medical and pricing topics
- Transparent when handing off to a human
- Focused on collecting the minimum useful information for follow-up
