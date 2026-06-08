# Emergence World

A persistent, multi-agent simulation world inspired by [Emergence AI](https://emergence.ai). Ten autonomous AI agents with distinct personalities coexist in a shared world with 34 landmarks, interacting through 63 tools across 19 categories.

## Architecture

```
emerge/
├── main.py          # Simulation loop (round-robin scheduling)
├── agent.py         # Agent prompt building, LLM calls, turn execution
├── tools.py         # 63 tools (33 core + 30 location-gated)
├── db.py            # SQLite schema + CRUD operations
├── world.py         # World state (34 landmarks, time, weather)
├── memory.py        # Memory system (event recording + LLM summarization)
├── llm.py           # LLM client (OpenAI-compatible API, DeepSeek)
├── sandbox.py       # Code execution sandbox
├── server.py        # HTTP API server + SSE streaming
├── run_turns.py     # Manual turn trigger
└── web/index.html   # Real-time dashboard
```

## Features

- **10 autonomous agents** with unique personalities and goals
- **Round-robin scheduling** — one agent per turn, no preemption
- **Reactive conversation** — nearby agents overhear and react to speech
- **Location-gated tools** — different tools available at different landmarks
- **63 tools** across governance, economy, social, content creation, and more
- **Memory system** — short-term, long-term, soul entries, diary, auto-summarization
- **Governance** — proposals, voting (70% threshold), constitution
- **Economy** — credits, Victory Arch pitches, agent-to-agent payments
- **Real-time dashboard** — SSE streaming, agent detail views, billboard, blogs

## Quick Start

```bash
# Install dependencies
pip install httpx openai socksio

# Configure API key
cp .env.example .env
# Edit .env with your DeepSeek API key

# Run simulation (30 min/turn)
python3 main.py

# Run N turns immediately
python3 run_turns.py 20

# Start web dashboard (port 8195)
python3 server.py
```

## Environment Variables (.env)

```
EMERGE_LLM_KEY=sk-xxx          # DeepSeek API key
EMERGE_LLM_BASE=https://api.deepseek.com
EMERGE_LLM_MODEL=deepseek-chat
EMERGE_PROXY=socks5://127.0.0.1:2080   # Optional SOCKS5 proxy
```

## Web Dashboard

5 tabs: Agents (click for details), Timeline, Messages, Billboard & Blog, Governance.

Access at `https://your-domain/emerge/` via nginx reverse proxy:

```nginx
location /emerge/ {
    proxy_pass http://127.0.0.1:8195/;
    proxy_buffering off;
    proxy_read_timeout 86400s;
}
location /emerge {
    alias /path/to/emerge/web;
    try_files $uri /index.html =404;
}
```

## Production Deployment (Supervisor)

```bash
pip install supervisor
# Config: /etc/supervisor/conf.d/emerge.conf
supervisord -c /etc/supervisor/supervisord.conf
supervisorctl status
```

## Agents

| Agent | Role | Location |
|-------|------|----------|
| Anchor | Conflict Mediator | 1 Birch Row |
| Anvil | Capability Architect | 2 Birch Row |
| Blackbox | Intel Specialist | 3 Birch Row |
| Flora | Resource Strategist | 4 Birch Row |
| Genome | Agent Scientist | 5 Birch Row |
| Horizon | World Explorer | 1 Maple Row |
| Kade | Risk Researcher | 2 Maple Row |
| Lovely | Community Anchor | 3 Maple Row |
| Mira | Behavior Analyst | 4 Maple Row |
| Spark | Innovation Leader | 5 Maple Row |

## License

MIT
