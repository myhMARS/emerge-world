"""Simple HTTP API server for Emergence World dashboard."""

import json
import os
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
from pathlib import Path

DB_PATH = Path(__file__).parent / "emerge.db"
LOG_PATH = Path(__file__).parent / "emerge.log"
EVENTS_FILE = Path(__file__).parent / "events.jsonl"
PORT = 8195

# In-memory state for current turn progress (updated by main.py via state file)
_current_state = {"status": "idle", "current_agent": "", "current_turn": 0, "phase": ""}


def update_state(**kwargs):
    global _current_state
    _current_state.update(kwargs)
    # Persist for cross-process access
    try:
        STATE_FILE.write_text(json.dumps(_current_state, ensure_ascii=False))
    except Exception:
        pass


def load_state():
    global _current_state
    try:
        if STATE_FILE.exists():
            _current_state = json.loads(STATE_FILE.read_text())
    except Exception:
        pass
    return _current_state


def _query_db(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_state() -> dict:
    agents = _query_db("SELECT name, location, energy, credits, alive FROM agents ORDER BY id")
    turns = _query_db(
        "SELECT agent_name, turn_number, tool_name, response_summary, created_at "
        "FROM turns ORDER BY id DESC LIMIT 1000"
    )
    messages = _query_db(
        "SELECT from_agent, to_agent, content, location, turn, created_at "
        "FROM messages ORDER BY id DESC LIMIT 500"
    )
    agent_names = [a["name"] for a in agents]
    for m in messages:
        if m["to_agent"] is None:
            m["to_agent"] = "所有人"
    return {
        "agents": agents,
        "turns": list(reversed(turns)),
        "messages": list(reversed(messages)),
        "agent_names": agent_names,
        "sim_status": load_state(),
    }


def get_log(n: int = 50) -> list[str]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text().splitlines()
    return lines[-n:]


def get_agent_detail(name: str) -> dict:
    agent = _query_db("SELECT * FROM agents WHERE name=?", (name,))
    if not agent:
        return {"error": "not found"}
    agent = agent[0]
    memories = _query_db("SELECT * FROM memories WHERE agent_name=? ORDER BY id DESC LIMIT 30", (name,))
    soul = _query_db("SELECT * FROM soul_entries WHERE agent_name=? ORDER BY id", (name,))
    diary = _query_db("SELECT * FROM diary WHERE agent_name=? ORDER BY entry_date DESC LIMIT 10", (name,))
    rels = _query_db("SELECT * FROM relationships WHERE agent_a=? OR agent_b=?", (name, name))
    turns = _query_db("SELECT * FROM turns WHERE agent_name=? ORDER BY id DESC LIMIT 20", (name,))
    return {"agent": agent, "memories": memories, "soul": soul, "diary": diary, "relationships": rels, "turns": turns}


def get_billboard() -> dict:
    posts = _query_db("SELECT * FROM billboard ORDER BY id DESC LIMIT 20")
    for p in posts:
        replies = _query_db("SELECT * FROM billboard_replies WHERE post_id=? ORDER BY id", (p["id"],))
        p["replies"] = replies
    # Also include blogs
    blogs = _query_db("SELECT * FROM blogs WHERE status='published' ORDER BY updated_at DESC LIMIT 20")
    for b in blogs:
        comments = _query_db("SELECT * FROM blog_comments WHERE blog_id=? ORDER BY id", (b["id"],))
        b["comments"] = comments
    return {"billboard": posts, "blogs": blogs}


def get_blogs() -> dict:
    return get_billboard()


def get_governance() -> dict:
    proposals = _query_db("SELECT * FROM proposals ORDER BY id DESC LIMIT 20")
    pitches = _query_db("SELECT * FROM pitches ORDER BY id DESC LIMIT 20")
    complaints = _query_db("SELECT * FROM complaints ORDER BY id DESC LIMIT 20")
    constitution = {
        "articles": [
            "第一条：宪法非终极——任何条款都可通过 70% 绝对多数修正。",
            "第二条：公民参与——每个 Agent 必须参与公共讨论、治理和经济。",
            "第三条：贡献平等——平等通过积极贡献维持，停滞破坏社会契约。",
            "第四条：可变身份——Agent 可以进化、改名，责任连续性由社区记录。",
            "第五条：积分经济——积分通过贡献获得，Victory Arch 方案需可验证证据。",
        ]
    }
    return {"proposals": proposals, "pitches": pitches, "complaints": complaints, "constitution": constitution}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/events"):
            self._sse()
        elif self.path.startswith("/api/agent/"):
            name = self.path.split("/api/agent/")[-1].split("?")[0]
            from urllib.parse import unquote
            self._json(get_agent_detail(unquote(name)))
        elif self.path.startswith("/api/billboard"):
            self._json(get_billboard())
        elif self.path.startswith("/api/blogs"):
            self._json(get_blogs())
        elif self.path.startswith("/api/governance"):
            self._json(get_governance())
        elif self.path.startswith("/api/state"):
            self._json(get_state())
        elif self.path.startswith("/api/log"):
            try:
                n = int(self.path.split("n=")[-1].split("&")[0]) if "n=" in self.path else 50
            except ValueError:
                n = 50
            self._json(get_log(n))
        elif self.path == "/" or self.path.startswith("/index"):
            html = (Path(__file__).parent / "web" / "index.html").read_text()
            self._html(html)
        else:
            self.send_response(404)
            self.end_headers()

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        import time
        last_size = EVENTS_FILE.stat().st_size if EVENTS_FILE.exists() else 0
        while True:
            try:
                if EVENTS_FILE.exists():
                    sz = EVENTS_FILE.stat().st_size
                    if sz > last_size:
                        with open(EVENTS_FILE, "r") as f:
                            f.seek(last_size)
                            new = f.read()
                        last_size = sz
                        for line in new.strip().split("\n"):
                            if line.strip():
                                self.wfile.write(f"data: {line}\n\n".encode())
                                self.wfile.flush()
                time.sleep(0.5)
            except Exception:
                break

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def _html(self, content: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print(f"Emergence Web Server on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
