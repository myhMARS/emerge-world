"""LLM client — OpenAI-compatible API via SOCKS5 proxy.

Loads configuration from .env file in project root.
"""

import json
import os
from pathlib import Path
import httpx
from openai import AsyncOpenAI

# Load .env from project directory
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            if key not in os.environ:
                os.environ[key] = value

LLM_CONFIG = {
    "base_url": os.environ["EMERGE_LLM_BASE"],
    "api_key": os.environ["EMERGE_LLM_KEY"],
    "model": os.environ.get("EMERGE_LLM_MODEL", "deepseek-chat"),
    "proxy": os.environ.get("EMERGE_PROXY", ""),
}


def _build_client() -> AsyncOpenAI:
    kwargs = {"base_url": LLM_CONFIG["base_url"], "api_key": LLM_CONFIG["api_key"]}
    if LLM_CONFIG["proxy"]:
        kwargs["http_client"] = httpx.AsyncClient(proxy=LLM_CONFIG["proxy"])
    return AsyncOpenAI(**kwargs)


_client: AsyncOpenAI | None = None


async def chat_json(
    system: str,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> dict:
    """Send chat request with JSON mode enabled, return parsed response dict."""
    global _client
    if _client is None:
        _client = _build_client()

    response = await _client.chat.completions.create(
        model=model or LLM_CONFIG["model"],
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


async def chat_tools(
    system: str,
    tools: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
) -> list[dict]:
    """Send chat request with native function calling. Returns list of tool calls."""
    global _client
    if _client is None:
        _client = _build_client()

    openai_tools = []
    for t in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}, "required": []}),
            },
        })

    response = await _client.chat.completions.create(
        model=model or LLM_CONFIG["model"],
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
        ],
        tools=openai_tools,
        tool_choice="auto",
    )

    msg = response.choices[0].message
    if msg.tool_calls:
        return [
            {"tool": tc.function.name, "args": json.loads(tc.function.arguments)}
            for tc in msg.tool_calls
        ]
    if msg.content:
        try:
            parsed = json.loads(msg.content)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "tool" in parsed:
                return [parsed]
        except json.JSONDecodeError:
            pass
    return [{"tool": "idle", "args": {"reason": msg.content[:100] if msg.content else "no response"}}]


async def chat_text(
    system: str,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    """Send chat request, return text response (for summarization)."""
    global _client
    if _client is None:
        _client = _build_client()

    response = await _client.chat.completions.create(
        model=model or LLM_CONFIG["model"],
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""
