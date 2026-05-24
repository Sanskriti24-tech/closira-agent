import json
import os
from typing import Any

from pydantic import BaseModel, Field

from .models import ConversationState
from .prompts import RESPONSE_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT
from .sop import SOP


DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


class AgentDecision(BaseModel):
    response: str = Field(description="Customer-facing assistant reply.")
    intent: str = Field(description="Short label for the customer's latest intent.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence that response is fully supported by the SOP.")
    sop_citations: list[str] = Field(default_factory=list, description="Specific SOP fields or facts that support the response.")
    should_escalate: bool = Field(description="Whether the session should be handed to a human.")
    escalation_reasons: list[str] = Field(default_factory=list, description="Reasons for human handoff.")
    sop_gaps: list[str] = Field(default_factory=list, description="Customer requests not answerable from the SOP.")


class ConversationSummary(BaseModel):
    customer_intent: str
    key_details_collected: dict[str, str] = Field(default_factory=dict)
    sop_gaps_identified: list[str] = Field(default_factory=list)
    escalation_required: bool
    escalation_reasons: list[str] = Field(default_factory=list)
    recommended_next_action: str


def _state_payload(state: ConversationState) -> dict[str, Any]:
    return {
        "messages": state.messages,
        "qualification": state.qualification,
        "unanswered_count": state.unanswered_count,
        "sop_gaps": state.sop_gaps,
        "escalation_log": state.escalation_log,
        "last_intent": state.last_intent,
    }


class LangChainConversationAgent:
    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.provider = self._resolve_provider(provider)
        self.model = model or self._default_model(self.provider)
        self._chat_model = self._build_chat_model(self.provider, self.model)
        self._fallback_chat_model = self._build_fallback_model()

    @staticmethod
    def is_anthropic_configured() -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def decide_response(self, sop: SOP, state: ConversationState, customer_message: str) -> AgentDecision:
        return self._invoke_with_optional_fallback(
            schema=AgentDecision,
            prompt_text=RESPONSE_PROMPT,
            payload={
                "sop_json": json.dumps(sop.data, indent=2),
                "state_json": json.dumps(_state_payload(state), indent=2),
                "customer_message": customer_message,
            },
        )

    def summarize(self, sop: SOP, state: ConversationState) -> ConversationSummary:
        return self._invoke_with_optional_fallback(
            schema=ConversationSummary,
            prompt_text=SUMMARY_PROMPT,
            payload={
                "sop_json": json.dumps(sop.data, indent=2),
                "state_json": json.dumps(_state_payload(state), indent=2),
            },
        )

    def _invoke_with_optional_fallback(self, schema: type[BaseModel], prompt_text: str, payload: dict[str, str]):
        try:
            return self._invoke(self._chat_model, schema, prompt_text, payload)
        except Exception:
            if self._fallback_chat_model is None:
                raise
            return self._invoke(self._fallback_chat_model, schema, prompt_text, payload)

    @staticmethod
    def _invoke(chat_model, schema: type[BaseModel], prompt_text: str, payload: dict[str, str]):
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", prompt_text),
            ]
        )
        chain = prompt | chat_model.with_structured_output(schema)
        return chain.invoke(payload)

    def _build_chat_model(self, provider: str, model: str):
        try:
            from dotenv import load_dotenv
        except ImportError as exc:
            raise RuntimeError("python-dotenv is missing. Install dependencies with: pip install -r requirements.txt") from exc

        load_dotenv()
        if provider == "anthropic":
            return self._build_anthropic_model(model)
        if provider == "ollama":
            return self._build_ollama_model(model)
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _build_anthropic_model(model: str):
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise RuntimeError("langchain-anthropic is missing. Install dependencies with: pip install -r requirements.txt") from exc

        if not LangChainConversationAgent.is_anthropic_configured():
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your environment or a .env file.")

        return ChatAnthropic(
            model=model,
            temperature=0,
            max_tokens=800,
        )

    @staticmethod
    def _build_ollama_model(model: str):
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise RuntimeError("langchain-ollama is missing. Install dependencies with: pip install -r requirements.txt") from exc

        return ChatOllama(
            model=model,
            base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            temperature=0,
        )

    def _build_fallback_model(self):
        fallback_enabled = os.getenv("OLLAMA_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}
        if self.provider != "anthropic" or not fallback_enabled:
            return None
        try:
            return self._build_ollama_model(os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL))
        except RuntimeError:
            return None

    @classmethod
    def _resolve_provider(cls, provider: str | None) -> str:
        selected = (provider or os.getenv("LLM_PROVIDER", "auto")).lower()
        if selected == "auto":
            return "anthropic" if cls.is_anthropic_configured() else "ollama"
        if selected in {"anthropic", "ollama"}:
            return selected
        raise RuntimeError("LLM provider must be one of: auto, anthropic, ollama.")

    @staticmethod
    def _default_model(provider: str) -> str:
        if provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
        return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


class ClaudeLangChainAgent(LangChainConversationAgent):
    def __init__(self, model: str | None = None) -> None:
        super().__init__(provider="anthropic", model=model)
