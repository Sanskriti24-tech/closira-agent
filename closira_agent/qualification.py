from .models import ConversationState
from .sop import SOP


def next_question(state: ConversationState, sop: SOP) -> dict[str, str] | None:
    for question in sop.qualification_questions():
        if question["id"] not in state.qualification:
            return question
    return None


def store_answer(state: ConversationState, answer: str, sop: SOP) -> bool:
    question = next_question(state, sop)
    if not question:
        return False
    state.qualification[question["id"]] = answer.strip()
    return True


def qualification_summary(state: ConversationState) -> dict[str, str]:
    return dict(state.qualification)

