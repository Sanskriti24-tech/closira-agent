from dataclasses import dataclass, field
from typing import Any


@dataclass
class Escalation:
    should_escalate: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class ConversationState:
    messages: list[dict[str, str]] = field(default_factory=list)
    qualification: dict[str, str] = field(default_factory=dict)
    unanswered_count: int = 0
    sop_gaps: list[str] = field(default_factory=list)
    escalation_log: list[dict[str, Any]] = field(default_factory=list)
    last_intent: str = "general enquiry"

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

