# backend/discord_bot.py
"""
Clean, user-friendly Discord RAG bot (prefix-based).
Sends only a single tidy answer string back to the user.
"""

import asyncio
import ast
import time
from functools import lru_cache
import os
import re
import discord
import traceback
from dotenv import load_dotenv
from backend.RAG_pipeline import run_rag_pipeline

# ---------- config ----------
PREFIXES = ("!ask", "$ask", "/ask")   # commands the bot listens to
CACHE_SIZE = 128                      # LRU cache size for demo
COOLDOWN_SECONDS = 3                  # per-user cooldown (demo-friendly)
MIN_WORDS = 2                         # ignore tiny messages
MAX_MESSAGE_CHARS = 1900
# ----------------------------

# Customize your knowledge domain here
CONTEXT_DESCRIPTION = "Python, Machine Learning, Web Development, and Discord"
EXAMPLE_QUERIES = [
    "How do I create a virtual environment in Python?",
    "What's overfitting in machine learning?",
    "How do I create a REST API with Flask?",
    "How do I add slash commands to a Discord bot?"
]

# Fallback response when question is outside the knowledge base
FALLBACK_RESPONSE = (
    "I couldn’t find an answer to that. 🤔\n\n"
    f"My knowledge base contains information about **{CONTEXT_DESCRIPTION}**.\n"
    "Please ask something related to these topics. For example:\n"
    f"- {EXAMPLE_QUERIES[0]}\n"
    f"- {EXAMPLE_QUERIES[1]}\n"
    f"- {EXAMPLE_QUERIES[2]}"
)

# simple in-memory cooldown store (demo use)
_user_cooldowns = {}

# Load env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Discord client + intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Cached wrapper around the (blocking) pipeline
@lru_cache(maxsize=CACHE_SIZE)
def cached_run_rag_pipeline(question: str):
    # returns whatever your pipeline returns (we will robustly extract the answer)
    return run_rag_pipeline(question)

def _clean_answer_text(s: str) -> str:
    """Remove source tokens and noisy lines, and trim whitespace."""
    if not isinstance(s, str):
        s = str(s)
    # remove `[source:...]` tokens
    s = re.sub(r"\s*\[source:[^\]]*\]", "", s)
    # remove common "Sources:" lines or trailing "Sources: ..." fragments
    s = re.sub(r"\n?Sources?:.*$", "", s, flags=re.IGNORECASE | re.DOTALL)
    # remove repeated whitespace
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()

def _try_parse_stringified_dict(s: str):
    """
    If a pipeline accidentally returned a repr(dict) string, try to parse it.
    Returns dict or None.
    """
    if not isinstance(s, str):
        return None
    s_strip = s.strip()
    # quick heuristic: starts with "{" or "{" single-quote patterns
    if not s_strip.startswith("{"):
        return None
    try:
        # ast.literal_eval is safe for Python literals (dict/list/str/nums)
        return ast.literal_eval(s_strip)
    except Exception:
        return None

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    # ignore self and other bots
    if message.author == client.user:
        return
    if message.author.bot:
        return

    content = (message.content or "").strip()
    if not content:
        return

    # only handle configured prefixes for demo
    prefix_used = None
    for p in PREFIXES:
        if content.lower().startswith(p.lower()):
            prefix_used = p
            break
    if not prefix_used:
        return

    # apply per-user cooldown
    now = time.time()
    last = _user_cooldowns.get(message.author.id, 0)
    if now - last < COOLDOWN_SECONDS:
        # gentle rate-limit; avoid spamming LLM and keep demo smooth
        await message.channel.send("Please wait a few seconds before asking again.")
        return
    _user_cooldowns[message.author.id] = now

    # extract question text after prefix
    question = message.content[len(prefix_used):].strip()
    if not question or len(question.split()) < MIN_WORDS:
        await message.channel.send(" Please provide a short question (at least a couple of words). E.g. `!ask Who created Python?`")
        return

    try:
        # typing indicator while we run the pipeline
        async with message.channel.typing():
            loop = asyncio.get_running_loop()
            # run pipeline in background thread; cached wrapper short-circuits repeated queries
            result = await loop.run_in_executor(None, cached_run_rag_pipeline, question)

        # --- Robustly extract answer only ---
        answer = None

        # If pipeline returned a dict
        if isinstance(result, dict):
            answer = (result.get("answer")
                      or result.get("text")
                      or result.get("response")
                      or result.get("output")
                      or result.get("final"))
        # If pipeline returned tuple/list (common pattern)
        elif isinstance(result, (tuple, list)):
            if len(result) >= 1:
                answer = result[0]
        # If pipeline returned a string
        elif isinstance(result, str):
            answer = result
        else:
            # fallback stringify
            answer = str(result)

        # If 'answer' is still none and result was a string that looks like a dict, try parsing it
        if answer is None and isinstance(result, str):
            parsed = _try_parse_stringified_dict(result)
            if isinstance(parsed, dict):
                answer = (parsed.get("answer")
                          or parsed.get("text")
                          or parsed.get("response")
                          or parsed.get("output")
                          or parsed.get("final"))

        # final fallback
        if answer is None:
            # Use fallback redirect instead of "I don't know."
            answer_text = FALLBACK_RESPONSE
        else:
            # Clean the answer text (strip source tokens, remove 'Sources:' lines, trim)
            answer_text = _clean_answer_text(str(answer))

            # Heuristic: treat very short / generic "I don't know" style replies as out-of-context
            lower_ans = answer_text.lower().strip()
            weak_responses = {
                "i don't know", "i don't know.", "i am not sure", "i'm not sure",
                "no idea", "sorry, i don't know", "i don't have that information"
            }
            # if answer is too short or matches weak patterns, replace with FALLBACK_RESPONSE
            if (len(answer_text) < 5) or (lower_ans in weak_responses):
                answer_text = FALLBACK_RESPONSE

        # safety truncation
        if len(answer_text) > MAX_MESSAGE_CHARS:
            answer_text = answer_text[:MAX_MESSAGE_CHARS] + "\n\n...(truncated)"

        # Send only the clean, user-friendly answer
        await message.channel.send(answer_text)

    except Exception as e:
        # terminal-only debug so you can inspect failures during demo
        traceback.print_exc()
        # user-friendly error
        await message.channel.send("⚠️ Sorry — something went wrong while answering. Check the server logs.")

# Run the bot
client.run(TOKEN)
