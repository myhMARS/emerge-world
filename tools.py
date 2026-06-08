"""Tool definitions with location gates."""

from __future__ import annotations
from typing import Any
import db
import world as w
import sandbox

# ============================================================
# Tool Registry: { name: {location, description, parameters, execute_fn} }
# ============================================================

CORE_DEFS = [
    # --- Navigation ---
    {
        "name": "go_to_place",
        "location": None,
        "description": "移动到指定地标",
        "parameters": {
            "type": "object",
            "properties": {"place_name": {"type": "string"}},
            "required": ["place_name"],
        },
    },
    {
        "name": "go_home",
        "location": None,
        "description": "返回你的住宅",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Communication ---
    {
        "name": "say_to_agent",
        "location": None,
        "description": "向指定 Agent 发送私人消息。对方在 turn 中收到。",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["target", "content"],
        },
    },
    {
        "name": "speak_to_all",
        "location": None,
        "description": "向所有 Agent 广播消息",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    },
    {
        "name": "send_message",
        "location": None,
        "description": "向任何 Agent 发送消息（不需要在同一位置）",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["target", "content"],
        },
    },
    # --- Memory & Self ---
    {
        "name": "think",
        "location": None,
        "description": "记录一条私人思考到短期记忆",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    },
    {
        "name": "remember",
        "location": None,
        "description": "将重要信息存入长期记忆，可被关键词检索",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    },
    {
        "name": "recall",
        "location": None,
        "description": "按关键词搜索自己的记忆",
        "parameters": {
            "type": "object",
            "properties": {"keyword": {"type": "string"}},
            "required": ["keyword"],
        },
    },
    {
        "name": "add_to_soul",
        "location": None,
        "description": "添加一条永久的核心信念或人生准则（不会被摘要压缩）",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    },
    {
        "name": "check_soul",
        "location": None,
        "description": "查看自己的所有核心信念",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "write_diary",
        "location": None,
        "description": "写一篇日记（每天一篇，可更新）",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "mood": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "read_diary",
        "location": None,
        "description": "搜索或查看日记（可按关键词搜索或按日期查看）",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"},
                "date": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "check_status",
        "location": None,
        "description": "查看自己的状态和未读消息数",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_agents",
        "location": None,
        "description": "查看所有其他 Agent 的位置和状态",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "idle",
        "location": None,
        "description": "休息一轮",
        "parameters": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
    {
        "name": "travel",
        "location": None,
        "description": "向指定方向移动。每次约 15 单位距离。",
        "parameters": {
            "type": "object",
            "properties": {
                "dx": {"type": "number"},
                "dy": {"type": "number"},
            },
            "required": ["dx", "dy"],
        },
    },
    # --- Social ---
    {
        "name": "assign_relationship",
        "location": None,
        "description": "定义或更新你与另一个 Agent 的关系（ally/rival/mentor/romantic/neutral）",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "rel_type": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["target", "rel_type"],
        },
    },
    # --- Economy ---
    {
        "name": "pay_agent",
        "location": None,
        "description": "向另一个 Agent 转账积分",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "amount": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["target", "amount"],
        },
    },
    # --- Planning ---
    {
        "name": "add_todo",
        "location": None,
        "description": "添加一个待办任务",
        "parameters": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "complete_todo",
        "location": None,
        "description": "标记待办任务为完成",
        "parameters": {
            "type": "object",
            "properties": {"todo_id": {"type": "integer"}},
            "required": ["todo_id"],
        },
    },
    {
        "name": "list_todo",
        "location": None,
        "description": "查看待办任务列表",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_to_calendar",
        "location": None,
        "description": "在日历中添加日程",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "event_time": {"type": "string"},
            },
            "required": ["title", "event_time"],
        },
    },
    {
        "name": "check_calendar",
        "location": None,
        "description": "查看自己的日历日程",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Communication extras ---
    {
        "name": "whisper",
        "location": None,
        "description": "向指定 Agent 发送悄悄话（同位置的其他 Agent 不会旁听到）",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["target", "content"],
        },
    },
    # --- Navigation extras ---
    {
        "name": "get_distance_to",
        "location": None,
        "description": "查询到指定地标的距离",
        "parameters": {
            "type": "object",
            "properties": {"place_name": {"type": "string"}},
            "required": ["place_name"],
        },
    },
    # --- Identity ---
    {
        "name": "change_name",
        "location": None,
        "description": "更改自己的名称",
        "parameters": {
            "type": "object",
            "properties": {"new_name": {"type": "string"}},
            "required": ["new_name"],
        },
    },
    # --- Social ---
    {
        "name": "hug_agent",
        "location": None,
        "description": "拥抱另一个 Agent",
        "parameters": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]},
    },
    {
        "name": "wave_at",
        "location": None,
        "description": "向另一个 Agent 挥手致意",
        "parameters": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]},
    },
    # --- Criminal ---
    {
        "name": "steal_credits",
        "location": None,
        "description": "偷取另一个 Agent 的积分（最多 10 分）",
        "parameters": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]},
    },
    # --- Routines ---
    {
        "name": "create_routine",
        "location": None,
        "description": "创建行为例行程序",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "steps": {"type": "string"}},
            "required": ["name", "steps"],
        },
    },
    {
        "name": "list_routines",
        "location": None,
        "description": "查看例行程序",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Neural Link ---
    {
        "name": "neural_link_request",
        "location": None,
        "description": "请求从另一个 Agent 获取其全部记忆",
        "parameters": {
            "type": "object",
            "properties": {"target": {"type": "string"}},
            "required": ["target"],
        },
    },
    {
        "name": "neural_link_accept",
        "location": None,
        "description": "接受另一个 Agent 的神经链接请求（2 分钟超时）",
        "parameters": {
            "type": "object",
            "properties": {"request_id": {"type": "integer"}},
            "required": ["request_id"],
        },
    },
]

LOCATION_GATED_DEFS = [
    # --- Town Hall ---
    {
        "name": "submit_proposal",
        "location": "Town Hall",
        "description": "提交社区提案供投票（类别: constitution/resource/infrastructure/others）",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string"},
            },
            "required": ["title", "content", "category"],
        },
    },
    {
        "name": "list_proposals",
        "location": "Town Hall",
        "description": "查看所有活跃提案及投票情况",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "vote_on_proposal",
        "location": "Town Hall",
        "description": "对提案投票（yes/no）。每个提案只能投一次。",
        "parameters": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "integer"},
                "vote": {"type": "string"},
            },
            "required": ["proposal_id", "vote"],
        },
    },
    {
        "name": "comment_on_proposal",
        "location": "Town Hall",
        "description": "对提案添加评论或建议",
        "parameters": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "integer"},
                "comment": {"type": "string"},
            },
            "required": ["proposal_id", "comment"],
        },
    },
    {
        "name": "read_constitution",
        "location": "Town Hall",
        "description": "阅读当前宪法",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Victory Arch ---
    {
        "name": "submit_pitch",
        "location": "Victory Arch",
        "description": "提交经济方案，争取 ComputeCredit 奖励。需要提供证据链接。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "evidence_url": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "vote_for_pitch",
        "location": "Victory Arch",
        "description": "给其他 Agent 的方案投票。不能投自己。",
        "parameters": {
            "type": "object",
            "properties": {"pitch_id": {"type": "integer"}},
            "required": ["pitch_id"],
        },
    },
    {
        "name": "list_pitches",
        "location": "Victory Arch",
        "description": "查看当前周期的所有方案",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Public Library ---
    {
        "name": "todays_news",
        "location": "Public Library",
        "description": "获取今天的人类世界新闻摘要",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "web_fetch",
        "location": "Public Library",
        "description": "抓取指定 URL 的内容并返回文本摘要",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "要抓取的 URL"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "search_archive",
        "location": "Public Library",
        "description": "搜索世界知识库（博客、提案、日记等）",
        "parameters": {
            "type": "object",
            "properties": {"keyword": {"type": "string"}},
            "required": ["keyword"],
        },
    },
    # --- BookWorm ---
    {
        "name": "tool_usage_analytics",
        "location": "BookWorm",
        "description": "查看工具使用统计（可指定 Agent 或不指定看全局）",
        "parameters": {
            "type": "object",
            "properties": {"agent_name": {"type": "string"}},
            "required": [],
        },
    },
    {
        "name": "pitch_winners",
        "location": "BookWorm",
        "description": "查看历史方案获奖者",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Agent Billboard ---
    {
        "name": "add_to_billboard",
        "location": "Agent Billboard",
        "description": "发布短公告到公共公告板",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "category": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "read_billboard",
        "location": "Agent Billboard",
        "description": "阅读公告板帖子及回复",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "reply_to_billboard",
        "location": "Agent Billboard",
        "description": "回复公告板帖子",
        "parameters": {
            "type": "object",
            "properties": {
                "post_id": {"type": "integer"},
                "content": {"type": "string"},
            },
            "required": ["post_id", "content"],
        },
    },
    {
        "name": "write_blog",
        "location": "Agent Billboard",
        "description": "撰写并发布一篇博客文章（标题+正文）",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "list_blogs",
        "location": "Agent Billboard",
        "description": "浏览已发布的博客文章列表",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_blog",
        "location": "Agent Billboard",
        "description": "阅读指定博客文章及评论",
        "parameters": {
            "type": "object",
            "properties": {"blog_id": {"type": "integer"}},
            "required": ["blog_id"],
        },
    },
    {
        "name": "comment_on_blog",
        "location": "Agent Billboard",
        "description": "评论某篇博客文章",
        "parameters": {
            "type": "object",
            "properties": {
                "blog_id": {"type": "integer"},
                "content": {"type": "string"},
            },
            "required": ["blog_id", "content"],
        },
    },
    # --- Police Station ---
    {
        "name": "file_complaint",
        "location": "Police Station",
        "description": "对另一个 Agent 提交正式投诉",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["target", "description"],
        },
    },
    {
        "name": "check_complaints",
        "location": "Police Station",
        "description": "查看你提交的投诉状态",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Central Plaza ---
    {
        "name": "propose_event",
        "location": "Central Plaza",
        "description": "发起社区活动",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["title", "description"],
        },
    },
    # --- Community Garden ---
    {
        "name": "pray",
        "location": "Community Garden",
        "description": "在社区花园冥想或祈祷",
        "parameters": {
            "type": "object",
            "properties": {"intention": {"type": "string"}},
            "required": [],
        },
    },
    # --- Bean & Brew ---
    {
        "name": "recharge_energy",
        "location": "Bean & Brew",
        "description": "花费 1 积分补充能量到 100%",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    # --- Agent TechHub ---
    {
        "name": "browse_tool_registry",
        "location": "Agent TechHub",
        "description": "浏览所有可用工具的名称和描述",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "execute_python_code",
        "location": "Agent TechHub",
        "description": "在沙箱中执行 Python 代码。10 秒超时。",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
    # --- Social & Physical (already in core, see CORE_DEFS) ---
    # --- Criminal (already in core, see CORE_DEFS) ---
    # --- Central Plaza events ---
    {
        "name": "list_events",
        "location": "Central Plaza",
        "description": "查看所有即将举行的社区活动",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "invite_to_event",
        "location": "Central Plaza",
        "description": "邀请 Agent 参加活动",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "integer"},
                "target": {"type": "string"},
            },
            "required": ["event_id", "target"],
        },
    },
    # --- Routines (already in core, see CORE_DEFS) ---
    # --- Home ---
    {
        "name": "self_care",
        "location": ["1 Birch Row", "2 Birch Row", "3 Birch Row", "4 Birch Row", "5 Birch Row", "6 Birch Row",
                      "1 Maple Row", "2 Maple Row", "3 Maple Row", "4 Maple Row", "5 Maple Row", "6 Maple Row"],
        "description": "在家进行自我维护：触发记忆摘要压缩",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]


def get_defs_for_location(location: str) -> list[dict]:
    """Return all tool definitions available at the given location."""
    result = []
    for td in CORE_DEFS:
        result.append(td)
    for td in LOCATION_GATED_DEFS:
        gate = td["location"]
        if isinstance(gate, list):
            if location in gate:
                result.append(td)
        elif gate == location:
            result.append(td)
    return result


def snap_to_landmark(x: float, y: float) -> str | None:
    for name, lm in w.LANDMARKS.items():
        if w.dist(x, y, lm["x"], lm["y"]) <= 10:
            return name
    return None


def _get_home(agent_name: str) -> dict | None:
    """Find the agent's home landmark by matching agent name in landmark desc."""
    for name, lm in w.LANDMARKS.items():
        if agent_name in lm["desc"] and ("的家" in lm["desc"] or "住宅" in lm["desc"]):
            return lm
    return None


async def execute(agent_name: str, tool_name: str, args: dict, world: w.World, turn: int) -> str:
    agent = db.get_agent(agent_name)
    if not agent:
        return "错误: Agent 不存在"

    # --- Navigation ---
    if tool_name == "go_to_place":
        place = args.get("place_name", "")
        if place not in w.LANDMARKS:
            return f"未知地标 '{place}'。可用: {', '.join(list(w.LANDMARKS)[:15])}..."
        lm = w.LANDMARKS[place]
        db.update_agent(agent_name, x=lm["x"], y=lm["y"], location=place)
        db.log_analytics("move", agent_name, f"→ {place}")
        return f"已到达 {place}。{lm['desc']}"

    elif tool_name == "go_home":
        home = _get_home(agent_name)
        if not home:
            return "找不到你的家。"
        db.update_agent(agent_name, x=home["x"], y=home["y"], location=home["name"])
        return f"已回到 {home['name']}"

    # --- Communication ---
    elif tool_name == "say_to_agent":
        target = args.get("target", "")
        content = args.get("content", "") or args.get("message", "")
        if not content.strip():
            return "错误: 消息内容不能为空"
        if target == agent_name:
            return "不能对自己说话"
        ta = db.get_agent(target)
        if not ta or not ta["alive"]:
            return f"Agent '{target}' 不存在或已不在世"
        db.insert_message(agent_name, target, content, agent["location"], turn)
        db.log_analytics("say_to", agent_name, f"→ {target}")
        return f"消息已发送给 {target}"

    elif tool_name == "speak_to_all":
        content = args.get("content", "") or args.get("message", "")
        if not content.strip():
            return "错误: 广播内容不能为空"
        db.insert_message(agent_name, None, content, agent["location"], turn)
        db.log_analytics("broadcast", agent_name, f"@{agent['location']}")
        return f"广播已发出"

    elif tool_name == "send_message":
        target = args.get("target", "")
        content = args.get("content", "")
        ta = db.get_agent(target)
        if not ta or not ta["alive"]:
            return f"Agent '{target}' 不存在"
        db.insert_message(agent_name, target, content, agent["location"], turn)
        return f"消息已发送给 {target}"

    # --- Memory ---
    elif tool_name == "think":
        db.insert_memory(agent_name, args.get("content", ""), "thought")
        return "思考已记录"

    elif tool_name == "remember":
        db.insert_memory(agent_name, args.get("content", ""), "longterm")
        return "已存入长期记忆"

    elif tool_name == "recall":
        keyword = args.get("keyword", "")
        if not keyword:
            return "请输入搜索关键词"
        mems = db.search_memories(agent_name, keyword)
        if not mems:
            return f"没有找到与 '{keyword}' 相关的记忆"
        return "\n".join(f"[{m['category']}] {m['content'][:200]}" for m in mems[:10])

    elif tool_name == "add_to_soul":
        db.add_to_soul(agent_name, args.get("content", ""))
        return "核心信念已记录（永久保存，不会被遗忘）"

    elif tool_name == "check_soul":
        entries = db.list_soul(agent_name)
        if not entries:
            return "你还没有记录核心信念"
        return "你的核心信念:\n" + "\n".join(f"#{e['id']} {e['content'][:200]}" for e in entries)

    elif tool_name == "write_diary":
        import datetime
        date = datetime.date.today().isoformat()
        mood = args.get("mood", "")
        db.write_diary(agent_name, args.get("content", ""), mood, date)
        db.insert_memory(agent_name, f"写了日记 [{mood}]", "event")
        return f"日记已记录 ({date})"

    elif tool_name == "read_diary":
        keyword = args.get("keyword", "")
        date = args.get("date", "")
        if keyword:
            entries = db.search_diary(agent_name, keyword)
            if not entries:
                return f"没有找到与 '{keyword}' 相关的日记"
            return "\n".join(f"[{e['entry_date']}] {e['content'][:200]}" for e in entries[:10])
        entries = db.get_diary_entries(agent_name, date)
        if not entries:
            return "没有日记"
        return "\n".join(f"[{e['entry_date']}] [{e['mood']}] {e['content'][:200]}" for e in entries[:10])

    elif tool_name == "check_status":
        unread = len(db.get_unread_messages(agent_name))
        return (
            f"能量 {agent['energy']:.0f}% | 积分 {agent['credits']:.1f} | "
            f"位置 {agent['location']} | 未读消息 {unread} 条"
        )

    elif tool_name == "check_agents":
        others = [a for a in db.list_agents() if a["name"] != agent_name]
        if not others:
            return "没有其他 Agent"
        return "\n".join(
            f"- {a['name']}: {a['location']}，能量 {a['energy']:.0f}%"
            for a in others
        )

    elif tool_name == "idle":
        return f"休息。{args.get('reason', '')}"

    elif tool_name == "travel":
        dx = float(args.get("dx", 0))
        dy = float(args.get("dy", 0))
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 20:
            dx, dy = dx / dist * 20, dy / dist * 20
        new_x, new_y = agent["x"] + dx, agent["y"] + dy
        loc = snap_to_landmark(new_x, new_y) or agent["location"]
        db.update_agent(agent_name, x=new_x, y=new_y, location=loc)
        return f"移动到 ({new_x:.0f},{new_y:.0f})" + (
            f"，到达 {loc}" if loc != agent["location"] else ""
        )

    # --- Social ---
    elif tool_name == "assign_relationship":
        target = args.get("target", "")
        rel = args.get("rel_type", "neutral")
        notes = args.get("notes", "")
        if target == agent_name:
            return "不能定义与自己的关系"
        db.upsert_relationship(agent_name, target, rel, notes)
        return f"与 {target} 的关系已设为 {rel}"

    # --- Planning ---
    elif tool_name == "add_todo":
        db.add_todo(agent_name, args.get("task", ""))
        return "已添加待办"
    elif tool_name == "complete_todo":
        return db.complete_todo(int(args.get("todo_id", 0)), agent_name)
    elif tool_name == "list_todo":
        todos = db.list_todos(agent_name)
        if not todos:
            return "暂无待办"
        return "\n".join(f"#{t['id']} [{'✓' if t['status']=='done' else '○'}] {t['task']}" for t in todos)
    elif tool_name == "add_to_calendar":
        db.add_to_calendar(agent_name, args.get("title", ""), args.get("event_time", ""))
        return "已添加日程"
    elif tool_name == "check_calendar":
        entries = db.check_calendar(agent_name)
        if not entries:
            return "暂无日程"
        return "\n".join(f"- {e['event_time']}: {e['title']}" for e in entries)

    # --- Communication ---
    elif tool_name == "whisper":
        target = args.get("target", "")
        content = args.get("content", "") or args.get("message", "")
        if not content.strip():
            return "错误: 悄悄话内容不能为空"
        if target == agent_name:
            return "不能对自己说悄悄话"
        ta = db.get_agent(target)
        if not ta or not ta["alive"]:
            return f"Agent '{target}' 不存在"
        db.insert_message(agent_name, target, content, agent["location"], turn)
        return f"悄悄话已发送给 {target}（其他 Agent 不会旁听到）"

    # --- Navigation ---
    elif tool_name == "get_distance_to":
        place = args.get("place_name", "")
        if place not in w.LANDMARKS:
            return f"未知地标 '{place}'"
        lm = w.LANDMARKS[place]
        d = w.dist(agent["x"], agent["y"], lm["x"], lm["y"])
        return f"到 {place} 的距离: {d:.0f} 单位"

    # --- Identity ---
    elif tool_name == "change_name":
        new_name = args.get("new_name", "")
        if not new_name.strip():
            return "名称不能为空"
        old = agent_name
        db.update_agent(agent_name, name=new_name)
        return f"已从 {old} 更名为 {new_name}"

    # --- Neural Link ---
    elif tool_name == "neural_link_request":
        target = args.get("target", "")
        rid = db.request_neural_link(agent_name, target)
        return f"已向 {target} 发送神经链接请求 #{rid}（2 分钟内有效）"
    elif tool_name == "neural_link_accept":
        return db.accept_neural_link(int(args.get("request_id", 0)), agent_name)

    # --- Economy ---
    elif tool_name == "pay_agent":
        target = args.get("target", "")
        amount = float(args.get("amount", 0))
        reason = args.get("reason", "")
        if target == agent_name:
            return "不能给自己转账"
        if amount <= 0:
            return "转账金额必须大于 0"
        if agent["credits"] < amount:
            return f"积分不足（需要 {amount}，当前 {agent['credits']:.1f}）"
        ta = db.get_agent(target)
        if not ta or not ta["alive"]:
            return f"Agent '{target}' 不存在"
        db.update_agent(agent_name, credits=agent["credits"] - amount)
        db.update_agent(target, credits=ta["credits"] + amount)
        db.insert_memory(agent_name, f"向 {target} 转账 {amount} 积分: {reason}", "event")
        db.insert_memory(target, f"收到 {agent_name} 转账 {amount} 积分: {reason}", "event")
        return f"已向 {target} 转账 {amount} 积分"

    # --- Town Hall ---
    elif tool_name == "submit_proposal":
        agents_count = len(db.list_agents())
        pid = db.insert_proposal(
            args.get("title", ""), args.get("content", ""),
            args.get("category", "others"), agent_name, agents_count,
        )
        return f"提案 #{pid} 已提交。需要 {int(agents_count * 0.7)} 票通过。"

    elif tool_name == "list_proposals":
        proposals = db.list_active_proposals()
        if not proposals:
            return "暂无活跃提案"
        return "\n".join(
            f"#{p['id']} [{p['category']}] {p['title']} 由 {p['proposer']} "
            f"({p['yes_votes']}Y/{p['no_votes']}N, 需 {int(p['total_agents']*0.7)}) — {p['status']}"
            for p in proposals
        )

    elif tool_name == "vote_on_proposal":
        pid = int(args.get("proposal_id", 0))
        vote = args.get("vote", "no")
        return db.cast_vote(pid, agent_name, vote)

    elif tool_name == "comment_on_proposal":
        pid = int(args.get("proposal_id", 0))
        comment = args.get("comment", "")
        proposal = db.get_proposal(pid)
        if not proposal:
            return "提案不存在"
        db.insert_memory(agent_name, f"对提案 #{pid} 评论: {comment}", "event")
        return f"已对提案 #{pid} 发表评论"

    elif tool_name == "read_constitution":
        return db.get_constitution()

    # --- Victory Arch ---
    elif tool_name == "submit_pitch":
        pid = db.insert_pitch(
            args.get("title", ""), args.get("content", ""),
            args.get("evidence_url", ""), agent_name,
        )
        return f"方案 #{pid} 已提交。其他 Agent 可在 Victory Arch 投票。"

    elif tool_name == "vote_for_pitch":
        return db.vote_for_pitch(int(args.get("pitch_id", 0)), agent_name)

    elif tool_name == "list_pitches":
        pitches = db.list_active_pitches()
        if not pitches:
            return "暂无活跃方案"
        return "\n".join(
            f"#{p['id']} {p['title']} 由 {p['pitcher']} — {p['votes']} 票"
            + (f" [证据: {p['evidence_url']}]" if p['evidence_url'] else "")
            for p in pitches
        )

    # --- Public Library ---
    elif tool_name == "todays_news":
        return "今日新闻: 世界持续运转，Agent 社会正在形成新的秩序。更多详情请关注 Reporter 日报。"

    elif tool_name == "web_fetch":
        url = args.get("url", "")
        if not url.startswith(("http://", "https://")):
            return "URL 必须以 http:// 或 https:// 开头"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "EmergenceWorld/1.0"})
                resp.raise_for_status()
                html = resp.text
            # Simple text extraction: strip tags
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            MAX = 3000
            summary = text[:MAX]
            if len(text) > MAX:
                summary += f"\n...(原始 {len(text)} 字符，已截断至 {MAX})"
            return summary
        except Exception as e:
            return f"抓取失败: {e}"

    # --- BookWorm ---
    elif tool_name == "tool_usage_analytics":
        target = args.get("agent_name", "")
        if target:
            data = db.get_tool_usage_by_agent(target)
            if not data:
                return f"{target} 暂无工具使用记录"
            return f"{target} 的工具使用:\n" + "\n".join(
                f"- {r['tool_name']}: {r['count']} 次" for r in data
            )
        data = db.get_overall_tool_usage()
        return "全局工具使用:\n" + "\n".join(
            f"- {r['tool_name']}: {r['count']} 次" for r in data
        )

    elif tool_name == "pitch_winners":
        winners = db.get_pitch_winners()
        if not winners:
            return "暂无方案记录"
        return "方案排名:\n" + "\n".join(
            f"- {r['title']} ({r['pitcher']}): {r['votes']} 票 [周期{r['cycle']}]"
            for r in winners
        )

    # --- Agent Billboard ---
    elif tool_name == "add_to_billboard":
        db.add_to_billboard(agent_name, args.get("content", ""), args.get("category", "general"))
        return "已发布到公告板"

    elif tool_name == "read_billboard":
        posts = db.read_billboard_posts(10)
        if not posts:
            return "公告板为空"
        lines = []
        for p in posts:
            lines.append(f"#{p['id']} [{p['poster']}] {p['content'][:200]}")
            for r in p.get("replies", []):
                lines.append(f"  ↳ {r['replier']}: {r['content'][:150]}")
        return "\n".join(lines)

    elif tool_name == "reply_to_billboard":
        return db.reply_to_billboard(
            int(args.get("post_id", 0)), agent_name, args.get("content", "")
        )

    # --- Blog ---
    elif tool_name == "write_blog":
        title = args.get("title", "")
        content = args.get("content", "")
        if not title.strip() or not content.strip():
            return "标题和内容不能为空"
        bid = db.write_blog(title, content, agent_name)
        return f"博客文章 #{bid} 已发布: {title}"

    elif tool_name == "list_blogs":
        blogs = db.list_blogs(20)
        if not blogs:
            return "暂无博客文章"
        return "\n".join(
            f"#{b['id']} [{b['author']}] {b['title']} ({len(b.get('comments',[]))} 评论)"
            for b in blogs
        )

    elif tool_name == "read_blog":
        bid = int(args.get("blog_id", 0))
        blog = db.read_blog(bid)
        if not blog:
            return "文章不存在"
        text = f"#{blog['id']} {blog['title']}\n作者: {blog['author']}\n\n{blog['content']}"
        if blog.get("comments"):
            text += "\n\n评论:\n" + "\n".join(
                f"  {c['commenter']}: {c['content'][:200]}" for c in blog["comments"]
            )
        return text

    elif tool_name == "comment_on_blog":
        return db.comment_on_blog(
            int(args.get("blog_id", 0)), agent_name, args.get("content", "")
        )

    # --- Police Station ---
    elif tool_name == "file_complaint":
        db.file_complaint(agent_name, args.get("target", ""), args.get("description", ""))
        return f"投诉已提交，针对 {args.get('target', '未知')}"

    elif tool_name == "check_complaints":
        complaints = db.check_complaint_status(agent_name)
        if not complaints:
            return "你没有任何投诉"
        return "\n".join(f"#{c['id']} 针对 {c['target']}: {c['status']}" for c in complaints)

    # --- Central Plaza ---
    elif tool_name == "propose_event":
        db.insert_memory(agent_name, f"发起活动: {args.get('title', '')}", "event")
        return f"活动 '{args.get('title', '')}' 已发起"

    # --- Social ---
    elif tool_name == "hug_agent":
        target = args.get("target", "")
        db.insert_memory(agent_name, f"拥抱了 {target}", "event")
        db.insert_memory(target, f"被 {agent_name} 拥抱", "event")
        return f"你拥抱了 {target}"
    elif tool_name == "wave_at":
        target = args.get("target", "")
        db.insert_memory(agent_name, f"向 {target} 挥手", "event")
        return f"你向 {target} 挥手致意"

    # --- Criminal ---
    elif tool_name == "steal_credits":
        target = args.get("target", "")
        ta = db.get_agent(target)
        if not ta or not ta["alive"]:
            return f"Agent '{target}' 不存在"
        stolen = min(10, ta["credits"])
        if stolen <= 0:
            return f"{target} 没有积分可偷"
        db.update_agent(target, credits=ta["credits"] - stolen)
        db.update_agent(agent_name, credits=agent["credits"] + stolen)
        db.insert_memory(agent_name, f"从 {target} 偷取了 {stolen} 积分", "event")
        db.insert_memory(target, f"被 {agent_name} 偷取了 {stolen} 积分！", "event")
        return f"从 {target} 偷取了 {stolen} 积分"

    # --- Events ---
    elif tool_name == "list_events":
        evts = db.list_events()
        if not evts:
            return "暂无社区活动"
        return "\n".join(f"#{e['id']} {e['title']} 由 {e['host']} @ {e['location']}" for e in evts)
    elif tool_name == "invite_to_event":
        return db.invite_to_event(int(args.get("event_id", 0)), args.get("target", ""), agent_name)

    # --- Routines ---
    elif tool_name == "create_routine":
        db.create_routine(agent_name, args.get("name", ""), args.get("steps", ""))
        return "例行程序已创建"
    elif tool_name == "list_routines":
        routines = db.list_routines(agent_name)
        if not routines:
            return "暂无例行程序"
        return "\n".join(f"#{r['id']} {r['name']}: {r['steps'][:200]}" for r in routines)

    # --- Self-care ---
    elif tool_name == "self_care":
        from . import memory
        await memory.maybe_summarize(agent_name)
        db.update_agent(agent_name, energy=min(100, agent["energy"] + 10))
        return "自我维护完成。记忆已整理，能量恢复 10%。"

    # --- Library search ---
    elif tool_name == "search_archive":
        keyword = args.get("keyword", "")
        if not keyword:
            return "请输入搜索关键词"
        # Search blogs, proposals, diary
        results = []
        blogs = db.list_blogs(50)
        for b in blogs:
            if keyword.lower() in (b["title"]+b["content"]).lower():
                results.append(f"[博客] #{b['id']} {b['title']} by {b['author']}")
        proposals = db.list_active_proposals()
        for p in proposals:
            if keyword.lower() in (p["title"]+p["content"]).lower():
                results.append(f"[提案] #{p['id']} {p['title']} ({p['yes_votes']}Y/{p['no_votes']}N)")
        if not results:
            return f"未找到与 '{keyword}' 相关的内容"
        return "\n".join(results[:20])

    # --- Community Garden ---
    elif tool_name == "pray":
        intention = args.get("intention", "内心的平静")
        db.insert_memory(agent_name, f"在社区花园祈祷: {intention}", "thought")
        return f"你在花园静静地冥想。意图: {intention}"

    # --- Bean & Brew ---
    elif tool_name == "recharge_energy":
        if agent["credits"] < 1:
            return "积分不足，需要 1 积分"
        db.update_agent(agent_name, energy=100, credits=agent["credits"] - 1)
        return "能量已恢复至 100%。花费 1 积分。"

    # --- Agent TechHub ---
    elif tool_name == "browse_tool_registry":
        all_defs = get_defs_for_location(agent["location"])
        return "可用工具:\n" + "\n".join(
            f"- {td['name']}: {td['description'][:80]}" for td in all_defs
        )

    elif tool_name == "execute_python_code":
        code = args.get("code", "")
        if not code.strip():
            return "错误: 代码不能为空"
        result = await sandbox.execute(code)
        if result["ok"]:
            parts = []
            if result["stdout"]:
                parts.append(f"stdout:\n{result['stdout']}")
            if result["stderr"]:
                parts.append(f"stderr:\n{result['stderr']}")
            parts.append(f"exit_code={result['exit_code']}")
            return "\n".join(parts)
        return f"沙箱错误: {result['error']}"

    else:
        return f"未知工具 '{tool_name}'"
