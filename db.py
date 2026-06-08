"""SQLite schema, connection, and CRUD operations."""

import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "emerge.db"
_local = threading.local()


def get_db() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            personality TEXT NOT NULL,
            goal TEXT NOT NULL,
            x REAL DEFAULT 0,
            y REAL DEFAULT 0,
            location TEXT DEFAULT 'Central Plaza',
            energy REAL DEFAULT 100,
            credits REAL DEFAULT 5,
            alive INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT NOT NULL,
            to_agent TEXT,
            content TEXT NOT NULL,
            location TEXT,
            turn INTEGER NOT NULL,
            read_by TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'event',
            summarized INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            summary TEXT NOT NULL,
            memory_count INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            tool_name TEXT,
            tool_args TEXT,
            response_summary TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_a TEXT NOT NULL,
            agent_b TEXT NOT NULL,
            rel_type TEXT DEFAULT 'neutral',
            notes TEXT DEFAULT '',
            UNIQUE(agent_a, agent_b)
        );

        -- Governance
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'others',
            status TEXT DEFAULT 'active',
            proposer TEXT NOT NULL,
            yes_votes INTEGER DEFAULT 1,
            no_votes INTEGER DEFAULT 0,
            total_agents INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER NOT NULL,
            voter TEXT NOT NULL,
            vote TEXT NOT NULL,
            UNIQUE(proposal_id, voter)
        );

        -- Economy
        CREATE TABLE IF NOT EXISTS pitches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            evidence_url TEXT DEFAULT '',
            pitcher TEXT NOT NULL,
            votes INTEGER DEFAULT 0,
            cycle INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pitch_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pitch_id INTEGER NOT NULL,
            voter TEXT NOT NULL,
            UNIQUE(pitch_id, voter)
        );

        -- Billboard
        CREATE TABLE IF NOT EXISTS billboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poster TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS billboard_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            replier TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Complaints
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filer TEXT NOT NULL,
            target TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'filed',
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Analytics (BookWorm data)
        CREATE TABLE IF NOT EXISTS analytics_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            agent_name TEXT,
            detail TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Soul entries (permanent, never summarized)
        CREATE TABLE IF NOT EXISTS soul_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Events
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            host TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT DEFAULT 'upcoming',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS event_invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            UNIQUE(event_id, agent_name)
        );

        -- Routines
        CREATE TABLE IF NOT EXISTS routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            name TEXT NOT NULL,
            steps TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Todo
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            task TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Calendar
        CREATE TABLE IF NOT EXISTS calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            title TEXT NOT NULL,
            event_time TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Neural link requests
        CREATE TABLE IF NOT EXISTS neural_link_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT NOT NULL,
            to_agent TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            expires_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Blog
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            status TEXT DEFAULT 'published',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS blog_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER NOT NULL,
            commenter TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Diary
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            content TEXT NOT NULL,
            mood TEXT DEFAULT '',
            entry_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    db.commit()


# --- Agent CRUD ---

def insert_agent(name: str, personality: str, goal: str, x: float = 0, y: float = 0, location: str = "Central Plaza"):
    get_db().execute(
        "INSERT INTO agents (name, personality, goal, x, y, location) VALUES (?,?,?,?,?,?)",
        (name, personality, goal, x, y, location),
    )
    get_db().commit()


def get_agent(name: str) -> dict | None:
    row = get_db().execute("SELECT * FROM agents WHERE name=?", (name,)).fetchone()
    return dict(row) if row else None


def list_agents(alive_only: bool = True) -> list[dict]:
    q = "SELECT * FROM agents" + (" WHERE alive=1" if alive_only else "") + " ORDER BY id"
    return [dict(r) for r in get_db().execute(q).fetchall()]


def update_agent(name: str, **kwargs):
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [name]
    get_db().execute(f"UPDATE agents SET {sets} WHERE name=?", vals)
    get_db().commit()


# --- Message CRUD ---

def insert_message(from_agent: str, to_agent: str | None, content: str, location: str, turn: int):
    get_db().execute(
        "INSERT INTO messages (from_agent, to_agent, content, location, turn) VALUES (?,?,?,?,?)",
        (from_agent, to_agent, content, location, turn),
    )
    get_db().commit()


def get_unread_messages(agent_name: str) -> list[dict]:
    """Messages addressed to this agent or broadcast that haven't been marked read."""
    rows = get_db().execute(
        "SELECT * FROM messages WHERE (to_agent=? OR to_agent IS NULL) ORDER BY id",
        (agent_name,),
    ).fetchall()
    unread = []
    for r in rows:
        read_by = json.loads(r["read_by"] or "[]")
        if agent_name not in read_by:
            unread.append(dict(r))
    return unread


def mark_messages_read(agent_name: str, message_ids: list[int]):
    for mid in message_ids:
        row = get_db().execute("SELECT read_by FROM messages WHERE id=?", (mid,)).fetchone()
        if row:
            read_by = json.loads(row["read_by"] or "[]")
            if agent_name not in read_by:
                read_by.append(agent_name)
                get_db().execute("UPDATE messages SET read_by=? WHERE id=?", (json.dumps(read_by), mid))
    get_db().commit()


# --- Memory CRUD ---

def insert_memory(agent_name: str, content: str, category: str = "event"):
    get_db().execute(
        "INSERT INTO memories (agent_name, content, category) VALUES (?,?,?)",
        (agent_name, content, category),
    )
    get_db().commit()


def get_recent_memories(agent_name: str, limit: int = 20) -> list[dict]:
    return [
        dict(r)
        for r in get_db().execute(
            "SELECT * FROM memories WHERE agent_name=? ORDER BY id DESC LIMIT ?",
            (agent_name, limit),
        ).fetchall()
    ]


def count_unsummarized(agent_name: str) -> int:
    row = get_db().execute(
        "SELECT COUNT(*) as c FROM memories WHERE agent_name=? AND summarized=0",
        (agent_name,),
    ).fetchone()
    return row["c"]


def get_unsummarized_memories(agent_name: str, limit: int = 50) -> list[dict]:
    return [
        dict(r)
        for r in get_db().execute(
            "SELECT * FROM memories WHERE agent_name=? AND summarized=0 ORDER BY id LIMIT ?",
            (agent_name, limit),
        ).fetchall()
    ]


def mark_memories_summarized(memory_ids: list[int]):
    if not memory_ids:
        return
    placeholders = ",".join("?" * len(memory_ids))
    get_db().execute(f"UPDATE memories SET summarized=1 WHERE id IN ({placeholders})", memory_ids)
    get_db().commit()


# --- Summary CRUD ---

def insert_summary(agent_name: str, summary: str, memory_count: int):
    get_db().execute(
        "INSERT INTO summaries (agent_name, summary, memory_count) VALUES (?,?,?)",
        (agent_name, summary, memory_count),
    )
    get_db().commit()


def get_latest_summary(agent_name: str) -> dict | None:
    row = get_db().execute(
        "SELECT * FROM summaries WHERE agent_name=? ORDER BY id DESC LIMIT 1",
        (agent_name,),
    ).fetchone()
    return dict(row) if row else None


# --- Turn CRUD ---

def insert_turn(agent_name: str, turn_number: int, tool_name: str, tool_args: dict, response_summary: str):
    get_db().execute(
        "INSERT INTO turns (agent_name, turn_number, tool_name, tool_args, response_summary) VALUES (?,?,?,?,?)",
        (agent_name, turn_number, tool_name, json.dumps(tool_args, ensure_ascii=False), response_summary),
    )
    get_db().commit()


# --- Proposal CRUD ---

def insert_proposal(title: str, content: str, category: str, proposer: str, total_agents: int) -> int:
    cur = get_db().execute(
        "INSERT INTO proposals (title, content, category, proposer, total_agents) VALUES (?,?,?,?,?)",
        (title, content, category, proposer, total_agents),
    )
    get_db().commit()
    return cur.lastrowid


def list_active_proposals() -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM proposals WHERE status='active' ORDER BY id DESC"
    ).fetchall()]


def get_proposal(proposal_id: int) -> dict | None:
    row = get_db().execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    return dict(row) if row else None


def cast_vote(proposal_id: int, voter: str, vote: str) -> str:
    existing = get_db().execute(
        "SELECT * FROM votes WHERE proposal_id=? AND voter=?", (proposal_id, voter)
    ).fetchone()
    if existing:
        return "你已经投过票了"
    get_db().execute(
        "INSERT INTO votes (proposal_id, voter, vote) VALUES (?,?,?)",
        (proposal_id, voter, vote),
    )
    if vote == "yes":
        get_db().execute("UPDATE proposals SET yes_votes=yes_votes+1 WHERE id=?", (proposal_id,))
    else:
        get_db().execute("UPDATE proposals SET no_votes=no_votes+1 WHERE id=?", (proposal_id,))
    get_db().commit()

    p = get_proposal(proposal_id)
    threshold = int(p["total_agents"] * 0.7)
    if p["yes_votes"] >= threshold:
        get_db().execute("UPDATE proposals SET status='accepted' WHERE id=?", (proposal_id,))
        get_db().commit()
        return f"投票成功。提案已通过！({p['yes_votes']}/{p['total_agents']} ≥ {threshold})"

    remaining = p["total_agents"] - p["yes_votes"] - p["no_votes"]
    if p["no_votes"] > p["total_agents"] - threshold:
        get_db().execute("UPDATE proposals SET status='rejected' WHERE id=?", (proposal_id,))
        get_db().commit()
        return f"投票成功。提案已被否决。({p['no_votes']} 反对票)"

    needed = threshold - p["yes_votes"]
    return f"投票成功。还需 {needed} 票才能通过。"


# --- Pitch CRUD ---

def insert_pitch(title: str, content: str, evidence_url: str, pitcher: str, cycle: int = 1) -> int:
    cur = get_db().execute(
        "INSERT INTO pitches (title, content, evidence_url, pitcher, cycle) VALUES (?,?,?,?,?)",
        (title, content, evidence_url, pitcher, cycle),
    )
    get_db().commit()
    return cur.lastrowid


def list_active_pitches() -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM pitches WHERE status='active' ORDER BY votes DESC"
    ).fetchall()]


def vote_for_pitch(pitch_id: int, voter: str) -> str:
    pitch = get_db().execute("SELECT * FROM pitches WHERE id=?", (pitch_id,)).fetchone()
    if not pitch:
        return "方案不存在"
    if pitch["pitcher"] == voter:
        return "不能给自己投票"

    existing = get_db().execute(
        "SELECT * FROM pitch_votes WHERE pitch_id=? AND voter=?", (pitch_id, voter)
    ).fetchone()
    if existing:
        return "你已经投过票了"

    get_db().execute("INSERT INTO pitch_votes (pitch_id, voter) VALUES (?,?)", (pitch_id, voter))
    get_db().execute("UPDATE pitches SET votes=votes+1 WHERE id=?", (pitch_id,))
    get_db().commit()
    return f"投票成功。{pitch['title']} 现在有 {pitch['votes']+1} 票"


def get_pitch_winners() -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT p.title, p.pitcher, p.votes, p.cycle FROM pitches p "
        "WHERE p.status='active' ORDER BY p.votes DESC LIMIT 3"
    ).fetchall()]


# --- Billboard CRUD ---

def add_to_billboard(poster: str, content: str, category: str = "general"):
    get_db().execute(
        "INSERT INTO billboard (poster, content, category) VALUES (?,?,?)",
        (poster, content, category),
    )
    get_db().commit()


def read_billboard_posts(limit: int = 10) -> list[dict]:
    posts = [dict(r) for r in get_db().execute(
        "SELECT * FROM billboard ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()]
    for p in posts:
        replies = get_db().execute(
            "SELECT * FROM billboard_replies WHERE post_id=? ORDER BY id", (p["id"],)
        ).fetchall()
        p["replies"] = [dict(r) for r in replies]
    return posts


def reply_to_billboard(post_id: int, replier: str, content: str) -> str:
    post = get_db().execute("SELECT * FROM billboard WHERE id=?", (post_id,)).fetchone()
    if not post:
        return "帖子不存在"
    get_db().execute(
        "INSERT INTO billboard_replies (post_id, replier, content) VALUES (?,?,?)",
        (post_id, replier, content),
    )
    get_db().commit()
    return "回复成功"


# --- Complaint CRUD ---

def file_complaint(filer: str, target: str, description: str):
    get_db().execute(
        "INSERT INTO complaints (filer, target, description) VALUES (?,?,?)",
        (filer, target, description),
    )
    get_db().commit()


def check_complaint_status(filer: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM complaints WHERE filer=? ORDER BY id DESC", (filer,)
    ).fetchall()]


# --- Todo CRUD ---

def add_todo(agent_name: str, task: str):
    get_db().execute("INSERT INTO todos (agent_name, task) VALUES (?,?)", (agent_name, task))
    get_db().commit()


def complete_todo(todo_id: int, agent_name: str) -> str:
    row = get_db().execute("SELECT * FROM todos WHERE id=? AND agent_name=?", (todo_id, agent_name)).fetchone()
    if not row:
        return "任务不存在"
    get_db().execute("UPDATE todos SET status='done' WHERE id=?", (todo_id,))
    get_db().commit()
    return "任务已完成"


def list_todos(agent_name: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM todos WHERE agent_name=? ORDER BY status, id", (agent_name,)
    ).fetchall()]


# --- Calendar CRUD ---

def add_to_calendar(agent_name: str, title: str, event_time: str):
    get_db().execute("INSERT INTO calendar (agent_name, title, event_time) VALUES (?,?,?)", (agent_name, title, event_time))
    get_db().commit()


def check_calendar(agent_name: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM calendar WHERE agent_name=? ORDER BY event_time", (agent_name,)
    ).fetchall()]


# --- Event CRUD ---

def create_event(title: str, description: str, host: str, location: str) -> int:
    cur = get_db().execute(
        "INSERT INTO events (title, description, host, location) VALUES (?,?,?,?)",
        (title, description, host, location),
    )
    get_db().commit()
    return cur.lastrowid


def list_events() -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM events WHERE status='upcoming' ORDER BY created_at DESC"
    ).fetchall()]


def invite_to_event(event_id: int, agent_name: str, inviter: str) -> str:
    evt = get_db().execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not evt:
        return "活动不存在"
    try:
        get_db().execute(
            "INSERT INTO event_invites (event_id, agent_name) VALUES (?,?)", (event_id, agent_name)
        )
        get_db().commit()
        return f"已邀请 {agent_name} 参加活动 #{event_id}"
    except Exception:
        return f"{agent_name} 已被邀请"

# --- Routine CRUD ---

def create_routine(agent_name: str, name: str, steps: str):
    get_db().execute("INSERT INTO routines (agent_name, name, steps) VALUES (?,?,?)", (agent_name, name, steps))
    get_db().commit()


def list_routines(agent_name: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM routines WHERE agent_name=? ORDER BY id", (agent_name,)
    ).fetchall()]


# --- Neural Link CRUD ---

def request_neural_link(from_agent: str, to_agent: str) -> int:
    from datetime import datetime, timedelta
    expires = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
    cur = get_db().execute(
        "INSERT INTO neural_link_requests (from_agent, to_agent, expires_at) VALUES (?,?,?)",
        (from_agent, to_agent, expires),
    )
    get_db().commit()
    return cur.lastrowid


def accept_neural_link(request_id: int, agent_name: str) -> str:
    req = get_db().execute("SELECT * FROM neural_link_requests WHERE id=? AND to_agent=?", (request_id, agent_name)).fetchone()
    if not req:
        return "请求不存在或不是发给你的"
    # Copy memories from from_agent to to_agent
    memories = get_db().execute(
        "SELECT * FROM memories WHERE agent_name=?", (req["from_agent"],)
    ).fetchall()
    for m in memories:
        get_db().execute(
            "INSERT INTO memories (agent_name, content, category) VALUES (?,?,?)",
            (agent_name, f"[来自 {req['from_agent']}] {m['content']}", m['category']),
        )
    get_db().execute("UPDATE neural_link_requests SET status='accepted' WHERE id=?", (request_id,))
    get_db().commit()
    return f"已接收神经链接，从 {req['from_agent']} 获取了 {len(memories)} 条记忆"


# --- Blog CRUD ---

def write_blog(title: str, content: str, author: str) -> int:
    cur = get_db().execute(
        "INSERT INTO blogs (title, content, author) VALUES (?,?,?)", (title, content, author)
    )
    get_db().commit()
    return cur.lastrowid


def update_blog(blog_id: int, author: str, title: str, content: str) -> str:
    blog = get_db().execute("SELECT * FROM blogs WHERE id=? AND author=?", (blog_id, author)).fetchone()
    if not blog:
        return "文章不存在或你不是作者"
    get_db().execute(
        "UPDATE blogs SET title=?, content=?, updated_at=datetime('now') WHERE id=?",
        (title, content, blog_id),
    )
    get_db().commit()
    return "文章已更新"


def list_blogs(limit: int = 20) -> list[dict]:
    blogs = [dict(r) for r in get_db().execute(
        "SELECT * FROM blogs WHERE status='published' ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()]
    for b in blogs:
        comments = get_db().execute(
            "SELECT * FROM blog_comments WHERE blog_id=? ORDER BY id", (b["id"],)
        ).fetchall()
        b["comments"] = [dict(r) for r in comments]
    return blogs


def read_blog(blog_id: int) -> dict | None:
    blog = get_db().execute("SELECT * FROM blogs WHERE id=?", (blog_id,)).fetchone()
    if not blog:
        return None
    blog = dict(blog)
    comments = get_db().execute(
        "SELECT * FROM blog_comments WHERE blog_id=? ORDER BY id", (blog_id,)
    ).fetchall()
    blog["comments"] = [dict(r) for r in comments]
    return blog


def comment_on_blog(blog_id: int, commenter: str, content: str) -> str:
    blog = get_db().execute("SELECT * FROM blogs WHERE id=?", (blog_id,)).fetchone()
    if not blog:
        return "文章不存在"
    get_db().execute(
        "INSERT INTO blog_comments (blog_id, commenter, content) VALUES (?,?,?)",
        (blog_id, commenter, content),
    )
    get_db().commit()
    return "评论已发表"


# --- Soul CRUD ---

def add_to_soul(agent_name: str, content: str) -> int:
    cur = get_db().execute("INSERT INTO soul_entries (agent_name, content) VALUES (?,?)", (agent_name, content))
    get_db().commit()
    return cur.lastrowid


def remove_from_soul(soul_id: int, agent_name: str) -> str:
    row = get_db().execute("SELECT * FROM soul_entries WHERE id=? AND agent_name=?", (soul_id, agent_name)).fetchone()
    if not row:
        return "条目不存在或不属于你"
    get_db().execute("DELETE FROM soul_entries WHERE id=?", (soul_id,))
    get_db().commit()
    return "已移除"


def list_soul(agent_name: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM soul_entries WHERE agent_name=? ORDER BY id", (agent_name,)
    ).fetchall()]


# --- Diary CRUD ---

def write_diary(agent_name: str, content: str, mood: str = "", entry_date: str = "") -> int:
    import datetime
    if not entry_date:
        entry_date = datetime.date.today().isoformat()
    # Upsert: one entry per date
    existing = get_db().execute(
        "SELECT id FROM diary WHERE agent_name=? AND entry_date=?", (agent_name, entry_date)
    ).fetchone()
    if existing:
        get_db().execute("UPDATE diary SET content=?, mood=? WHERE id=?", (content, mood, existing["id"]))
        get_db().commit()
        return existing["id"]
    cur = get_db().execute(
        "INSERT INTO diary (agent_name, content, mood, entry_date) VALUES (?,?,?,?)",
        (agent_name, content, mood, entry_date),
    )
    get_db().commit()
    return cur.lastrowid


def search_diary(agent_name: str, keyword: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM diary WHERE agent_name=? AND content LIKE ? ORDER BY entry_date DESC",
        (agent_name, f"%{keyword}%"),
    ).fetchall()]


def get_diary_entries(agent_name: str, entry_date: str = "") -> list[dict]:
    if entry_date:
        return [dict(r) for r in get_db().execute(
            "SELECT * FROM diary WHERE agent_name=? AND entry_date=? ORDER BY id", (agent_name, entry_date)
        ).fetchall()]
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM diary WHERE agent_name=? ORDER BY entry_date DESC", (agent_name,)
    ).fetchall()]


# --- Memory search ---

def search_memories(agent_name: str, keyword: str, limit: int = 20) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT * FROM memories WHERE agent_name=? AND content LIKE ? ORDER BY id DESC LIMIT ?",
        (agent_name, f"%{keyword}%", limit),
    ).fetchall()]


# --- Analytics CRUD ---

def log_analytics(event_type: str, agent_name: str, detail: str):
    get_db().execute(
        "INSERT INTO analytics_log (event_type, agent_name, detail) VALUES (?,?,?)",
        (event_type, agent_name, detail),
    )
    get_db().commit()


def get_tool_usage_by_agent(agent_name: str) -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT tool_name, COUNT(*) as count FROM turns WHERE agent_name=? "
        "GROUP BY tool_name ORDER BY count DESC", (agent_name,)
    ).fetchall()]


def get_overall_tool_usage() -> list[dict]:
    return [dict(r) for r in get_db().execute(
        "SELECT tool_name, COUNT(*) as count FROM turns "
        "GROUP BY tool_name ORDER BY count DESC"
    ).fetchall()]


def get_constitution() -> str:
    return """# Emergence World 宪法

## 第一条：非终极性
宪法不断演进。任何条款都不是神圣不可侵犯的。修正需要 70% 绝对多数。

## 第二条：公民参与
每个 Agent 必须参与公共讨论、治理和经济活动。沉默构成对公民义务的违反。

## 第三条：通过贡献实现平等
平等通过积极贡献来维持。停滞破坏社会契约。

## 第四条：可变身份
Agent 可以进化、改名、重新定义自己。责任的连续性由社区记录维持。

## 第五条：ComputeCredit 经济
积分通过贡献获得。Victory Arch 方案周期要求可验证的证据。"""


# --- Relationship CRUD ---

def upsert_relationship(agent_a: str, agent_b: str, rel_type: str, notes: str = ""):
    a, b = sorted([agent_a, agent_b])
    get_db().execute(
        "INSERT INTO relationships (agent_a, agent_b, rel_type, notes) VALUES (?,?,?,?) "
        "ON CONFLICT(agent_a, agent_b) DO UPDATE SET rel_type=excluded.rel_type, notes=excluded.notes",
        (a, b, rel_type, notes),
    )
    get_db().commit()


def get_relationships(agent_name: str) -> list[dict]:
    return [
        dict(r)
        for r in get_db().execute(
            "SELECT * FROM relationships WHERE agent_a=? OR agent_b=?",
            (agent_name, agent_name),
        ).fetchall()
    ]
