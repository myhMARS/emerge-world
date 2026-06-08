"""Manually trigger N turns without waiting for the 30-minute interval."""
import asyncio
import sqlite3
import sys
import db
import agent
import world as w

async def main(turns: int = 30):
    db.init_db()
    conn = sqlite3.connect(str(db.DB_PATH))
    conn.row_factory = sqlite3.Row
    last = conn.execute("SELECT MAX(turn_number) as t FROM turns").fetchone()["t"] or 0
    conn.close()

    world = w.World()
    print(f"Starting from turn {last + 1} (last was {last})")

    for turn in range(last + 1, last + turns + 1):
        agents = db.list_agents()
        if not agents:
            break
        current = agents[(turn - 1) % len(agents)]
        name = current["name"]
        try:
            async for event in agent.take_turn(name, world, turn):
                typ = event.get("type")
                if typ == "thinking":
                    print(f"[Turn {turn}] [{world.time_str}] {name} 思考中...")
                elif typ == "action":
                    print(f"[Turn {turn}] [{world.time_str}] {name} → {event['tool']}({event['args']})")
                elif "msg" in event:
                    print(event["msg"])
        except Exception as e:
            print(f"Turn {turn} {name} failed: {e}")
        world.advance_time(30)

    print(f"Done. {turns} turns. World time: {world.time_str}")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    asyncio.run(main(n))
