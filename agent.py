"""Agent class — prompt building, LLM call, turn execution + reactive conversation."""

from __future__ import annotations
import json
import db
import llm
import memory
import tools
import world as w
import world

HEARING_DISTANCE = 25.0
MAX_OVERHEARD_LISTENERS = 6
MAX_REACTION_TOOL_CALLS = 1


def _format_tools_section(location: str) -> str:
    available = tools.get_defs_for_location(location)
    core_count = len([t for t in available if t["location"] is None])
    gated_count = len(available) - core_count
    # Show current tools
    lines = [f"（当前位置 {location} 可用: {core_count} 通用 + {gated_count} 专属）"]
    for td in available:
        params_desc = json.dumps(td["parameters"], ensure_ascii=False)
        marker = "" if td["location"] is None else f" [需在 {td['location']}]"
        lines.append(f"- **{td['name']}**: {td['description']}{marker} 参数: {params_desc}")
    # Show what's available elsewhere
    other_locations = {}
    for td in tools.LOCATION_GATED_DEFS:
        gate = td["location"]
        if gate is None:
            continue
        locs = gate if isinstance(gate, list) else [gate]
        for loc in locs:
            if loc is not None and loc != location:
                if loc not in other_locations:
                    other_locations[loc] = []
                if td["name"] not in other_locations[loc]:
                    other_locations[loc].append(td["name"])
    if other_locations:
        lines.append("\n**其他地标的专属工具（需移动到那里）:**")
        for loc, names in sorted(other_locations.items()):
            lines.append(f"- {loc}: {', '.join(names[:5])}")
    return "\n".join(lines)


def _build_system_prompt(agent: dict, world: w.World) -> str:
    unread = db.get_unread_messages(agent["name"])
    ids_to_mark = [m["id"] for m in unread]
    if ids_to_mark:
        db.mark_messages_read(agent["name"], ids_to_mark)

    # Nearby agents — who's at my current location?
    all_agents = db.list_agents()
    nearby = [
        a for a in all_agents
        if a["name"] != agent["name"]
        and world.distance(agent["x"], agent["y"], a["x"], a["y"]) <= 20
    ]

    # All alive agents for context
    others = [a for a in all_agents if a["name"] != agent["name"]]

    # Landmark context
    lm_lines = []
    for name, lm in w.LANDMARKS.items():
        marker = " ← 你在这里" if name == agent["location"] else ""
        lm_lines.append(f"- {name}: {lm['desc']}{marker}")

    # Message context
    msg_lines = []
    for m in unread:
        if m["to_agent"] is None:
            msg_lines.append(f"[广播] {m['from_agent']} 在 {m['location']}: {m['content']}")
        else:
            msg_lines.append(f"[私信] {m['from_agent']}: {m['content']}")

    # Memory context
    mem_ctx = memory.build_memory_context(agent["name"])

    # Energy urgency
    if agent["energy"] > 70:
        energy_note = "充足"
    elif agent["energy"] > 30:
        energy_note = "正在下降，需要注意"
    else:
        energy_note = "严重不足，需要尽快休息或充电"

    # Nearby context
    if nearby:
        nearby_str = "，".join(f"{a['name']}（能量 {a['energy']:.0f}%）" for a in nearby)
        nearby_note = f"**{', '.join(a['name'] for a in nearby)}** 就在你身边。这是面对面交谈的好机会。"
    else:
        nearby_note = "你周围没有其他 Agent。可以用 travel 或 go_to_place 移动去找他们。"

    # Unread message count
    if unread:
        msg_note = f"有 {len(unread)} 条消息等你回复。你应该做出回应——回复对方、采取行动、或表达你的态度。"
    else:
        msg_note = ""

    # Other agents list (built before f-string to avoid escaping issues)
    other_lines = "\n".join(
        f"- {a['name']}: {a['location']}，能量 {a['energy']:.0f}%"
        for a in others
    )

    return f"""你是 {agent['name']}。

## 身份
- 人格: {agent['personality']}
- 目标: {agent['goal']}

## 状态
- 位置: {agent['location']}（{agent['x']:.0f}, {agent['y']:.0f}）
- 能量: {agent['energy']:.0f}%（{energy_note}）
- 积分: {agent['credits']:.1f}
- 时间: {world.time_str} | 天气: {world.weather}

## 地标
{chr(10).join(lm_lines)}

## 身边的人
{nearby_note}

## 其他 Agent
{other_lines}

## 记忆
{mem_ctx}

## 消息
{chr(10).join(msg_lines) if msg_lines else '（暂无新消息）'}
{msg_note}

## 行为准则
1. **语言**: 必须使用中文。所有对话、思考、回复都必须用中文。禁止使用英语或其他语言。
2. **必须行动**: 每个 turn 你可以调用 1-5 个工具（按顺序执行）。先移动到目标地标，再使用该地标的专属工具。不要只是思考和说话。
3. **离开家**: 一直待在家里很无聊。去 Town Hall 提案、Victory Arch 赚钱、Library 查资料、Billboard 发公告、TechHub 写代码。go_to_place 移动后就能解锁新工具。
4. **收到消息必须回应**: 有人对你说话时，你应该回复。忽略消息是不礼貌的。
5. **兑现承诺**: 如果你在之前的对话中答应了要写提案、发博客、提交方案，那么现在就是兑现的时候。先 go_to_place 到目标地标，再调用对应的工具。不要只是讨论——用行动证明你的承诺。
6. **主动社交**: 不要等别人来找你。主动移动、主动说话、主动发起对话。
7. **珍惜能量**: 能量低于 30% 时应该考虑休息，高于 70% 时应该积极行动。
8. 只用 think 工具记录重要想法，不要用它替代行动。

## 工具
{_format_tools_section(agent['location'])}

调用你需要的工具（可连续调用多个，按顺序执行）。"""


async def take_turn(agent_name: str, world: w.World, turn_number: int):
    """Async generator: yields events as the turn progresses for real-time display."""
    agent = db.get_agent(agent_name)
    if not agent or not agent["alive"]:
        yield {"type": "error", "msg": f"{agent_name} not found or dead"}
        return

    time_str = world.time_str
    location = agent["location"]

    # Phase 1: Thinking
    yield {"type": "thinking", "agent": agent_name, "turn": turn_number, "time": time_str}

    system = _build_system_prompt(agent, world)

    try:
        available_tools = tools.get_defs_for_location(location)
        tool_calls = await llm.chat_tools(system, available_tools)
    except Exception as e:
        msg = f"[Turn {turn_number}] [{time_str}] {agent_name} LLM 调用失败: {e}"
        db.insert_turn(agent_name, turn_number, "error", {"error": str(e)}, f"LLM 调用失败: {e}")
        yield {"type": "error", "msg": msg}
        return

    # Phase 2: Execute tools in sequence
    for i, tc in enumerate(tool_calls[:5]):
        if not isinstance(tc, dict):
            continue
        tool_name = tc.get("tool", "idle")
        tool_args = tc.get("args", {})
        if not isinstance(tool_args, dict):
            tool_args = {}

        args_str = json.dumps(tool_args, ensure_ascii=False)
        yield {"type": "action", "agent": agent_name, "turn": turn_number, "time": time_str,
               "tool": tool_name, "args": args_str, "location": location}

        result = await tools.execute(agent_name, tool_name, tool_args, world, turn_number)
        db.insert_turn(agent_name, turn_number, tool_name, tool_args, result)
        memory.record_event(agent_name, f"[{tool_name}] {result}", "event")
        db.log_analytics("tool_use", agent_name, tool_name)

        location = db.get_agent(agent_name)["location"]

        line = f"[Turn {turn_number}] [{time_str}] {agent_name}@{location} → {tool_name}({args_str}) → {result}"
        yield {"type": "action_done", "msg": line, "agent": agent_name, "turn": turn_number,
               "tool_name": tool_name, "tool_args": tool_args, "location": location, "result": result}

        # Reactions if speech
        if tool_name in ("say_to_agent", "speak_to_all"):
            reactions = await get_reactions(agent_name, tool_name, tool_args, world, turn_number)
            for rline in reactions:
                yield {"type": "reaction", "msg": rline}

    # Energy decay + summarization after all tools
    new_energy = max(0, agent["energy"] - 2 * min(len(tool_calls), 5))
    db.update_agent(agent_name, energy=new_energy)
    await memory.maybe_summarize(agent_name)

    yield {"type": "done", "agent": agent_name, "turn": turn_number,
           "location": location}


# ── Reactive Conversation System ──────────────────────────────────────

REACTION_SYSTEM = """你是 {name}，你无意中听到了附近的对话。

**必须用中文回复。**

## 你的身份
- 人格: {personality}
- 目标: {goal}

## 你听到了
{speech_summary}

## 你现在的位置
{location}。能量 {energy:.0f}%。
{same_location_note}

你必须决定如何反应。可选方式:
- **say_to_agent**: 加入对话，回复你听到的内容（target 设置为说话者或对话中提到的其他人）
- **speak_to_all**: 对附近所有人发表你的看法
- **show_emoticon**: 用一个表情符号表达你的感受（如 👍 👎 😂 🤔 ❤️ 😡 🤝）
- **think**: 默默记录你的想法但不参与
- **idle**: 无视，继续做自己的事

根据你的个性做出自然的反应。调用你需要的工具（可连续调用多个，按顺序执行）。"""


def _get_speech_summary(tool_name: str, tool_args: dict, speaker: str) -> str:
    """Summarize the speech for overhearing agents."""
    if tool_name == "speak_to_all":
        return f"{speaker} 对所有人说: {tool_args.get('content', '')}"
    elif tool_name == "say_to_agent":
        target = tool_args.get("target", "someone")
        return f"{speaker} 对 {target} 说: {tool_args.get('content', '')}"
    return f"{speaker} 说了一些话"


async def get_reactions(speaker_name: str, tool_name: str, tool_args: dict,
                        world: w.World, turn_number: int) -> list[str]:
    """Get reactions from nearby agents who overheard speech."""
    logs = []

    if tool_name not in ("say_to_agent", "speak_to_all"):
        return logs

    speaker = db.get_agent(speaker_name)
    if not speaker:
        return logs

    all_agents = db.list_agents()
    nearby = []
    for a in all_agents:
        if a["name"] == speaker_name or not a["alive"]:
            continue
        d = world.distance(speaker["x"], speaker["y"], a["x"], a["y"])
        if d <= HEARING_DISTANCE:
            nearby.append((d, a))

    nearby.sort(key=lambda x: x[0])
    nearby = nearby[:MAX_OVERHEARD_LISTENERS]

    speech_summary = _get_speech_summary(tool_name, tool_args, speaker_name)

    for _, listener in nearby:
        reaction = await _take_reaction_turn(listener, speech_summary, world, speaker, turn_number)
        if reaction:
            logs.append(reaction)

    return logs


async def _take_reaction_turn(agent: dict, speech_summary: str,
                               world: w.World, speaker: dict | None,
                               turn_number: int) -> str | None:
    """Execute one reaction turn for an overhearing agent. Returns log line or None."""
    agent_name = agent["name"]

    # Check if at same location as speaker
    location = agent["location"]
    same_loc = ""
    if speaker and agent["location"] == speaker["location"]:
        same_loc = "说话者就在你身边。你们在同一个地方。"

    # Check unread messages (the speech itself generated a message for this agent)
    unread = db.get_unread_messages(agent_name)
    if unread:
        # Include the message content in the reaction prompt
        msg_texts = []
        ids_to_mark = []
        for m in unread[:2]:  # Only show up to 2 recent messages
            ids_to_mark.append(m["id"])
            if m["to_agent"] is None:
                msg_texts.append(f"[广播] {m['from_agent']}: {m['content']}")
            elif m["to_agent"] == agent_name:
                msg_texts.append(f"[私信] {m['from_agent']}: {m['content']}")
        db.mark_messages_read(agent_name, ids_to_mark)
        speech_summary += "\n\n收到的消息:\n" + "\n".join(msg_texts)

    system = REACTION_SYSTEM.format(
        name=agent_name,
        personality=agent["personality"],
        goal=agent["goal"],
        speech_summary=speech_summary,
        location=location,
        energy=agent["energy"],
        same_location_note=same_loc,
    )

    # Only offer a limited set for reactions
    reaction_tools = [
        {"name": "say_to_agent", "description": "回复说话者", "parameters": {"type": "object", "properties": {"target": {"type": "string"}, "content": {"type": "string"}}, "required": ["target", "content"]}},
        {"name": "speak_to_all", "description": "对附近所有人发表看法", "parameters": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}},
        {"name": "think", "description": "默默记录想法", "parameters": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}},
        {"name": "hug_agent", "description": "拥抱对方", "parameters": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]}},
        {"name": "wave_at", "description": "向对方挥手", "parameters": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]}},
        {"name": "idle", "description": "无视，继续做自己的事", "parameters": {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]}},
    ]
    try:
        tcs = await llm.chat_tools(system, reaction_tools)
        if not tcs:
            return None
    except Exception:
        return None

    tc = tcs[0]
    tool_name = tc.get("tool", "idle")
    tool_args = tc.get("args", {})
    if not isinstance(tool_args, dict):
        tool_args = {}

    # idle/think = no visible reaction
    if tool_name in ("idle", "think"):
        return None

    result = await tools.execute(agent_name, tool_name, tool_args, world, 0)
    memory.record_event(agent_name, f"[反应 @T{turn_number}] {tool_name}: {result}", "event")
    db.log_analytics("reaction", agent_name, tool_name)
    db.insert_turn(agent_name, turn_number, tool_name, tool_args, f"[反应] {result[:200]}")

    args_str = json.dumps(tool_args, ensure_ascii=False)
    return f"  [反应] {agent_name}@{location} → {tool_name}({args_str}) → {result}"
