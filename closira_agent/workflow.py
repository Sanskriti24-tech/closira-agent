from .llm import LangChainConversationAgent
from .models import ConversationState
from .qualification import next_question, store_answer
from .sop import SOP


class CustomerSupportWorkflow:
    def __init__(self, sop: SOP | None = None, llm_agent: LangChainConversationAgent | None = None) -> None:
        self.sop = sop or SOP.load()
        self.state = ConversationState()
        self.llm_agent = llm_agent or LangChainConversationAgent()

    def handle_customer_message(self, message: str) -> str:
        self.state.add_message("customer", message)

        if self._looks_like_qualification_answer(message):
            store_answer(self.state, message, self.sop)
            response = self._qualification_response()
            self.state.add_message("assistant", response)
            return response

        decision = self.llm_agent.decide_response(self.sop, self.state, message)
        self.state.last_intent = decision.intent

        if decision.sop_gaps:
            self.state.unanswered_count += len(decision.sop_gaps)
            self.state.sop_gaps.extend(decision.sop_gaps)

        should_escalate = decision.should_escalate or decision.confidence < 0.70
        escalation_reasons = list(decision.escalation_reasons)
        if decision.confidence < 0.70:
            escalation_reasons.append("Claude confidence was below the 0.70 handoff threshold.")

        if should_escalate:
            self.state.escalation_log.append({"message": message, "reasons": escalation_reasons})

        response = decision.response
        if not should_escalate and not decision.sop_gaps and next_question(self.state, self.sop) and "?" not in response:
            response = f"{response} {self._lead_prompt()}"
        self.state.add_message("assistant", response)
        return response

    def summary(self) -> dict[str, object]:
        summary = self.llm_agent.summarize(self.sop, self.state).model_dump()
        escalation_reasons = [
            reason
            for entry in self.state.escalation_log
            for reason in entry.get("reasons", [])
        ]
        summary["key_details_collected"] = dict(self.state.qualification)
        summary["sop_gaps_identified"] = list(self.state.sop_gaps)
        summary["escalation_required"] = bool(escalation_reasons)
        summary["escalation_reasons"] = escalation_reasons
        if escalation_reasons:
            summary["recommended_next_action"] = "Hand off to a human agent with escalation context"
        elif len(self.state.qualification) >= 3:
            summary["recommended_next_action"] = "Send qualified lead to booking follow-up"
        return summary

    def _lead_prompt(self) -> str:
        question = next_question(self.state, self.sop)
        if not question:
            return "I have the key qualification details needed for follow-up."
        return question["question"]

    def _qualification_response(self) -> str:
        question = next_question(self.state, self.sop)
        if question:
            return f"Thanks. {question['question']}"
        return "Thanks, I have captured the qualification details for the clinic team."

    def _looks_like_qualification_answer(self, message: str) -> bool:
        if not next_question(self.state, self.sop):
            return False
        if not self.state.messages:
            return False
        if len(self.state.messages) < 2:
            return False
        previous_assistant = next(
            (m["content"] for m in reversed(self.state.messages[:-1]) if m["role"] == "assistant"),
            "",
        )
        return "?" in previous_assistant and len(message.split()) <= 18
