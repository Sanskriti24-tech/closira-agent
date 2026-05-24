from .models import ConversationState


def build_summary(state: ConversationState) -> dict[str, object]:
    escalation_reasons = [
        reason
        for entry in state.escalation_log
        for reason in entry.get("reasons", [])
    ]
    next_action = "Continue automated support"
    if escalation_reasons:
        next_action = "Hand off to a human agent with escalation context"
    elif len(state.qualification) >= 3:
        next_action = "Send qualified lead to booking follow-up"

    return {
        "customer_intent": state.last_intent,
        "key_details_collected": dict(state.qualification),
        "sop_gaps_identified": state.sop_gaps,
        "escalation_required": bool(escalation_reasons),
        "escalation_reasons": escalation_reasons,
        "recommended_next_action": next_action,
    }

