# backend/chatbot.py

from typing import Dict, Any, List
from backend.RAG_pipeline import run_rag_pipeline


# =========================
# 1. Conversation Memory
# =========================
conversation_history: List[Dict[str, str]] = []  # each entry: {"role": "user"|"assistant", "content": str}


def _format_history_for_prompt(history, max_turns=6) -> str:
    """
    Format recent conversation history into a string for context.
    """
    if not history:
        return ""
    snippet = history[-max_turns:]
    lines = []
    for h in snippet:
        prefix = "User:" if h["role"] == "user" else "Assistant:"
        content = h["content"].strip().replace("\n", " ")
        lines.append(f"{prefix} {content}")
    return "\n".join(lines)


# =========================
# 2. Chatbot Turn
# =========================
def chatbot_turn(user_input: str, debug: bool = False) -> Dict[str, Any]:
    """
    Handle one chat turn:
      - Store user input
      - Run RAG pipeline
      - Store assistant reply
    Returns structured result from RAG pipeline.
    """
    global conversation_history

    # 1. Save user turn
    conversation_history.append({"role": "user", "content": user_input})

    # 2. Add history snippet to enrich question
    history_snippet = _format_history_for_prompt(conversation_history)
    effective_question = (
        f"Conversation History:\n{history_snippet}\n\nUser question:\n{user_input}"
        if history_snippet else user_input
    )

    # 3. Run RAG pipeline
    result = run_rag_pipeline(effective_question, debug=debug)

    # 4. Save assistant turn
    conversation_history.append({"role": "assistant", "content": result["answer"]})

    return result


# =========================
# 3. Interactive CLI
# =========================
if __name__ == "__main__":
    print("🤖 RAG Chatbot (type 'exit' to quit)\n")
    while True:
        q = input("You: ")
        if q.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        res = chatbot_turn(q, debug=False)
        print("Bot:", res["answer"])
        print("Sources:", res["sources"])
