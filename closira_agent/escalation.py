from .models import Escalation
from .sop import SOP


EXPLICIT_HANDOFF = ("human", "agent", "manager", "representative", "call me")
ANGRY_WORDS = ("angry", "upset", "furious", "ridiculous", "complaint", "complain", "terrible", "unacceptable")
MEDICAL_TERMS = ("safe", "side effect", "pregnant", "allergy", "medical", "doctor", "pain", "infection", "diagnosis")
NEGOTIATION_TERMS = ("discount", "negotiate", "cheaper", "match price", "lower price", "deal")


def detect_escalation(message: str, unanswered_count: int, sop: SOP) -> Escalation:
    lowered = message.lower()
    reasons: list[str] = []

    if any(term in lowered for term in EXPLICIT_HANDOFF):
        reasons.append("Customer requested a human handoff.")
    if any(term in lowered for term in ANGRY_WORDS):
        reasons.append("Customer sentiment indicates frustration or a complaint.")
    if any(term in lowered for term in MEDICAL_TERMS):
        reasons.append("Customer asked a medical question, which the SOP marks for escalation.")
    if any(term in lowered for term in NEGOTIATION_TERMS):
        reasons.append("Customer is negotiating pricing, which the SOP marks for escalation.")
    if unanswered_count > 2:
        reasons.append("More than two questions could not be answered from the SOP.")

    return Escalation(should_escalate=bool(reasons), reasons=reasons)

