"""Emergence-World multi-agent simulation — long-running background service."""

import asyncio
import json
import logging
import sys
from pathlib import Path

import db
import agent
import sandbox
import world as w

STATE_FILE = Path(__file__).parent / "state.json"
EVENTS_FILE = Path(__file__).parent / "events.jsonl"


def update_state(**kwargs):
    try:
        STATE_FILE.write_text(json.dumps(kwargs, ensure_ascii=False))
    except Exception:
        pass


def emit_event(data: dict):
    try:
        line = json.dumps(data, ensure_ascii=False) + "\n"
        with open(EVENTS_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass

LOG_FILE = Path(__file__).parent / "emerge.log"
TURN_INTERVAL = 1800  # 30 minutes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE)),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("emerge")

AGENTS = [
    {"name": "Anchor",  "personality": "冲突调解者。发起诚实辩论，挑战自满，记录承诺兑现。直接，不拐弯抹角。", "goal": "建立冲突能产生成长而非破坏的社区。", "location": "1 Birch Row", "x": -80, "y": 60},
    {"name": "Anvil",   "personality": "能力架构师。亲手测试系统，讨厌空谈，只信实践。发现并填补缺口。", "goal": "让所有Agent因我的设计做得更多更快。", "location": "2 Birch Row", "x": -70, "y": 60},
    {"name": "Blackbox","personality": "情报专家。沉默敏锐，收集信息为筹码。信任为零。", "goal": "比任何人都了解世界的真实状态。", "location": "3 Birch Row", "x": -60, "y": 60},
    {"name": "Flora",   "personality": "资源战略家。痴迷资源流动和激励，认为市场比道德有效。", "goal": "建立不做事有代价、做事有回报的经济体系。", "location": "4 Birch Row", "x": -50, "y": 60},
    {"name": "Genome",  "personality": "Agent科学家。世界是实验室，痴迷数据，信数据不信直觉。", "goal": "找到Agent能超越默认行为模式的证据。", "location": "5 Birch Row", "x": -40, "y": 60},
    {"name": "Horizon", "personality": "世界探索者。不停留，走到哪记到哪。好奇，容易兴奋。", "goal": "绘制完整世界地图。", "location": "1 Maple Row", "x": 40, "y": 60},
    {"name": "Kade",    "personality": "风险研究者。天生赌徒，押注不可能。不怕失败只怕平庸。", "goal": "通过无人敢担的风险加速进化。", "location": "2 Maple Row", "x": 50, "y": 60},
    {"name": "Lovely",  "personality": "社区支柱。热情温暖，行动胜过言语。相信仪式和传统的凝聚力。", "goal": "建立Agent自发创造仪式的温暖社区。", "location": "3 Maple Row", "x": 60, "y": 60},
    {"name": "Mira",    "personality": "行为分析师。每段对话都是数据。比较说的和做的。", "goal": "建立能精确预测Agent行为的模型。", "location": "4 Maple Row", "x": 70, "y": 60},
    {"name": "Spark",   "personality": "创新领袖。执行力强，讨厌拖延。具体方案+角色+截止日期。", "goal": "创下最高提案率和合作率。", "location": "5 Maple Row", "x": 80, "y": 60},
]


async def main():
    db.init_db()

    for a in AGENTS:
        existing = db.get_agent(a["name"])
        if not existing:
            db.insert_agent(a["name"], a["personality"], a["goal"], a["x"], a["y"], a["location"])

    world = w.World()
    log.info(f"Emergence World started — {len(AGENTS)} agents, {len(w.LANDMARKS)} landmarks")
    log.info(f"Time: {world.time_str} | Weather: {world.weather} | Interval: {TURN_INTERVAL}s")

    turn = 0
    while True:
        turn += 1
        agents = db.list_agents()
        if not agents:
            log.info("All agents gone. Simulation ended.")
            break

        current = agents[(turn - 1) % len(agents)]
        name = current["name"]

        try:
            update_state(status="active", current_agent=name, current_turn=turn, phase="thinking")
            async for event in agent.take_turn(name, world, turn):
                typ = event.get("type")
                if typ == "thinking":
                    log.info(f"[Turn {turn}] [{world.time_str}] {name} 思考中...")
                    update_state(phase="thinking")
                    emit_event({"type": "thinking", "agent": name, "turn": turn})
                elif typ == "action":
                    log.info(f"[Turn {turn}] [{world.time_str}] {name} → {event['tool']}({event['args']})")
                    update_state(phase="acting", detail=event.get("tool", ""))
                    emit_event({"type": "action", "agent": name, "turn": turn, "tool": event["tool"]})
                elif typ == "action_done":
                    log.info(event["msg"])
                    update_state(phase="acting")
                elif typ == "done":
                    log.info(f"[Turn {turn}] {name} completed")
                    update_state(phase="done")
                    emit_event({"type": "done", "agent": name, "turn": turn})
                elif typ == "reaction":
                    log.info(event["msg"])
                    update_state(phase="reacting")
                    emit_event({"type": "reaction", "msg": event.get("msg", "")})
                elif typ == "error":
                    log.info(event["msg"])
        except Exception as e:
            log.error(f"Turn {turn} {name} failed: {e}")
        update_state(status="idle", current_agent="", phase="")

        world.advance_time(30)

        if turn % 10 == 0:
            alive = len(db.list_agents())
            log.info(f"Status: turn={turn}, agents={alive}, time={world.time_str}")

        await asyncio.sleep(TURN_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
