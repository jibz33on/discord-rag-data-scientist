# backend/llm.py

import traceback
from openai import AzureOpenAI
import config   # load env vars

# =========================
# 1. Azure Client Setup
# =========================
try:
    client = AzureOpenAI(
        api_key=config.AZURE_OPENAI_KEY,
        base_url=config.AZURE_OPENAI_ENDPOINT,
        api_version=config.AZURE_API_VERSION
    )
    print(f"✅ Azure OpenAI client initialized (deployment={config.AZURE_DEPLOYMENT_NAME})")
except Exception as e:
    print("❌ Failed to initialize Azure client:", str(e))
    client = None


# =========================
# 2. Prompt Templates
# =========================
SYSTEM_PROMPT = (
    "You are an assistant that answers user questions using ONLY the provided CONTEXT. "
    "Cite sources inline using [source:doc_X]. "
    "If the answer cannot be found in the context, say 'I don't know' and do not hallucinate."
)

USER_PROMPT_TEMPLATE = (
    "CONTEXT:\n{context}\n\n"
    "QUESTION:\n{question}\n\n"
    "INSTRUCTIONS:\n"
    "- Answer based only on the CONTEXT above.\n"
    "- Keep the answer concise and include source tags like [source:doc_1].\n"
    "- If context doesn't contain the answer, reply: 'I don't know'.\n\n"
    "ANSWER:"
)


# =========================
# 3. Helper Functions
# =========================
def call_azure_chat(system_prompt, user_prompt, max_tokens=350, temperature=0.0, debug=False):
    """
    Calls Azure OpenAI chat completion and returns the assistant response.
    """
    if not client:
        return "[LLM_ERROR] Azure client not initialized"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if debug:
            print("🟡 Debug - Sending to Azure:")
            print("SYSTEM:", system_prompt[:200])
            print("USER:", user_prompt[:500])

        response = client.chat.completions.create(
            model=config.AZURE_DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        if debug:
            traceback.print_exc()
        return f"[LLM_ERROR] {str(e)}"


def build_user_prompt(context, question):
    """
    Fills in USER_PROMPT_TEMPLATE with context and question.
    """
    return USER_PROMPT_TEMPLATE.format(context=context, question=question)


# =========================
# 4. Demo
# =========================
if __name__ == "__main__":
    test_context = "[source:doc_1] Python is a programming language created by Guido van Rossum in 1991."
    test_question = "Who created Python and when?"

    user_prompt = build_user_prompt(test_context, test_question)
    answer = call_azure_chat(SYSTEM_PROMPT, user_prompt, debug=True)

    print("\n=== TEST ANSWER ===")
    print(answer)
