import argparse
import json
import sys

from .workflow import CustomerSupportWorkflow


DEMO_SCENARIOS = {
    "in_sop_question": ["What are your Botox prices?"],
    "out_of_scope_question": ["Do you offer laser hair removal?"],
    "escalation_trigger": ["I am really upset. This is a complaint and I want a human."],
    "lead_qualification": [
        "What are your filler prices?",
        "Fillers",
        "Next Friday afternoon",
        "WhatsApp",
    ],
    "conversation_summary": [
        "How do I book a consultation?",
        "Consultation",
        "Tomorrow morning",
        "Email",
    ],
}


def run_demo(provider: str | None = None, model: str | None = None) -> None:
    for name, messages in DEMO_SCENARIOS.items():
        print(f"\n## {name}")
        workflow = CustomerSupportWorkflow(llm_agent=_agent(provider, model))
        for message in messages:
            print(f"Customer: {message}")
            print(f"AI: {workflow.handle_customer_message(message)}")
        print("Summary:")
        print(json.dumps(workflow.summary(), indent=2, ensure_ascii=False))


def run_ask(message: str, provider: str | None = None, model: str | None = None) -> None:
    workflow = CustomerSupportWorkflow(llm_agent=_agent(provider, model))
    print(workflow.handle_customer_message(message))
    print(json.dumps(workflow.summary(), indent=2, ensure_ascii=False))


def run_chat(provider: str | None = None, model: str | None = None) -> None:
    workflow = CustomerSupportWorkflow(llm_agent=_agent(provider, model))
    print("Bloom Aesthetics Clinic assistant. Type 'summary' for session summary or 'quit' to exit.")
    while True:
        message = input("Customer: ").strip()
        if message.lower() in {"quit", "exit"}:
            break
        if message.lower() == "summary":
            print(json.dumps(workflow.summary(), indent=2, ensure_ascii=False))
            continue
        print(f"AI: {workflow.handle_customer_message(message)}")


def _agent(provider: str | None, model: str | None):
    from .llm import LangChainConversationAgent

    return LangChainConversationAgent(provider=provider, model=model)


def main() -> None:
    parser = argparse.ArgumentParser(description="Closira customer support workflow prototype")
    parser.add_argument("--model", help="Provider model ID. Defaults to ANTHROPIC_MODEL, OLLAMA_MODEL, or project defaults.")
    parser.add_argument(
        "--provider",
        choices=["auto", "anthropic", "ollama"],
        help="LLM provider. Defaults to LLM_PROVIDER or auto.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="Handle a single customer message")
    ask_parser.add_argument("message")
    subparsers.add_parser("chat", help="Start an interactive chat")
    subparsers.add_parser("demo", help="Run assignment demo scenarios")

    args = parser.parse_args()
    try:
        if args.command == "ask":
            run_ask(args.message, args.provider, args.model)
        elif args.command == "chat":
            run_chat(args.provider, args.model)
        elif args.command == "demo":
            run_demo(args.provider, args.model)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
