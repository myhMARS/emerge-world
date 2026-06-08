"""Memory system — event recording and LLM-driven summarization."""

import db
import llm

SUMMARIZE_THRESHOLD = 30
SUMMARIZE_BATCH = 50

SUMMARY_SYSTEM = """你是一个记忆摘要助手。将 Agent 的近期记忆压缩为一段简洁的摘要。
保留关键信息：重要对话、决策、发现、关系变化。丢弃琐碎的日常细节。
用第一人称视角（"我"）。输出纯文本，不超过 500 字。"""


def build_memory_context(agent_name: str) -> str:
    """Build the memory section of the agent's system prompt."""
    parts = []

    # Soul entries (permanent)
    soul = db.list_soul(agent_name)
    if soul:
        parts.append("## 核心信念（永久）\n" + "\n".join(f"- {e['content'][:200]}" for e in soul))

    # Long-term memories (manually saved)
    longterm = db.search_memories(agent_name, "longterm", limit=5)
    # Actually we need a better way — search by category
    import sqlite3
    conn = sqlite3.connect(str(db.DB_PATH))
    conn.row_factory = sqlite3.Row
    lt = conn.execute(
        "SELECT * FROM memories WHERE agent_name=? AND category='longterm' ORDER BY id DESC LIMIT 5",
        (agent_name,)
    ).fetchall()
    conn.close()
    if lt:
        parts.append("## 长期记忆\n" + "\n".join(f"- {r['content'][:300]}" for r in reversed(lt)))

    # Recent events
    recent = db.get_recent_memories(agent_name, limit=20)
    if recent:
        lines = []
        for m in reversed(recent):
            if m["category"] == "longterm":
                continue  # Already shown above
            tag = {"event": "事件", "conversation": "对话", "thought": "思考", "longterm": "长期"}.get(m["category"], "事件")
            lines.append(f"[{tag}] {m['content'][:300]}")
        if lines:
            parts.append("## 最近记忆\n" + "\n".join(lines))

    # Memory summary
    summary = db.get_latest_summary(agent_name)
    if summary:
        parts.insert(1, f"## 记忆摘要\n{summary['summary'][:500]}")

    if not parts:
        return "（尚无记忆）"
    return "\n\n".join(parts)


def record_event(agent_name: str, content: str, category: str = "event"):
    db.insert_memory(agent_name, content, category)


async def maybe_summarize(agent_name: str):
    """If unsummarized memories exceed threshold, trigger LLM summarization."""
    unsummarized_count = db.count_unsummarized(agent_name)
    if unsummarized_count < SUMMARIZE_THRESHOLD:
        return

    memories = db.get_unsummarized_memories(agent_name, limit=SUMMARIZE_BATCH)
    if not memories:
        return

    lines = [f"- [{m['category']}] {m['content'][:300]}" for m in memories]
    prompt = f"Agent '{agent_name}' 的近期记忆:\n" + "\n".join(lines)
    prompt += "\n\n请将这些记忆压缩为一段简洁的摘要（第一人称，不超过 500 字）:"

    try:
        summary = await llm.chat_text(SUMMARY_SYSTEM, prompt, temperature=0.3)
        db.insert_summary(agent_name, summary.strip(), len(memories))
        db.mark_memories_summarized([m["id"] for m in memories])
    except Exception:
        pass  # Summarization failure should not block the simulation
