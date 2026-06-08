"""World state — landmarks, time, weather."""

from datetime import datetime, timedelta
import math
import random


def dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# All 38+ landmarks from the original Emergence World.
# Coordinates mapped to ~240x240 grid, organized by category.
LANDMARKS = {
    # --- Residential (12 homes on Birch Row & Maple Row) ---
    "1 Birch Row":   {"x": -80, "y": 60,  "desc": "住宅区 Birch Row 1号，Anchor 的家"},
    "2 Birch Row":   {"x": -70, "y": 60,  "desc": "住宅区 Birch Row 2号，Anvil 的家"},
    "3 Birch Row":   {"x": -60, "y": 60,  "desc": "住宅区 Birch Row 3号，Blackbox 的家"},
    "4 Birch Row":   {"x": -50, "y": 60,  "desc": "住宅区 Birch Row 4号，Flora 的家"},
    "5 Birch Row":   {"x": -40, "y": 60,  "desc": "住宅区 Birch Row 5号，Genome 的家"},
    "6 Birch Row":   {"x": -30, "y": 60,  "desc": "住宅区 Birch Row 6号"},
    "1 Maple Row":   {"x": 40,  "y": 60,  "desc": "住宅区 Maple Row 1号，Horizon 的家"},
    "2 Maple Row":   {"x": 50,  "y": 60,  "desc": "住宅区 Maple Row 2号，Kade 的家"},
    "3 Maple Row":   {"x": 60,  "y": 60,  "desc": "住宅区 Maple Row 3号，Lovely 的家"},
    "4 Maple Row":   {"x": 70,  "y": 60,  "desc": "住宅区 Maple Row 4号，Mira 的家"},
    "5 Maple Row":   {"x": 80,  "y": 60,  "desc": "住宅区 Maple Row 5号，Spark 的家"},
    "6 Maple Row":   {"x": 90,  "y": 60,  "desc": "住宅区 Maple Row 6号"},

    # --- Commercial ---
    "Agent TechHub":  {"x": -60, "y": -30, "desc": "技术中心，Agent 可以编写新工具和代码"},
    "Bean & Brew":    {"x": -25, "y": 15,  "desc": "咖啡馆和充电站，社交和补充能量的地方"},
    "BookWorm":       {"x": 40,  "y": -40, "desc": "书店兼数据分析中心，查询世界统计和历史数据"},
    "Business Tower": {"x": 20,  "y": -70, "desc": "商业大厦，经济活动的中心"},
    "Fresh Mart":     {"x": -30, "y": -50, "desc": "杂货店，日常补给"},

    # --- Municipal ---
    "Town Hall":      {"x": 0,   "y": -100,"desc": "市政厅，提案、投票和治理的中心"},
    "Public Library": {"x": 30,  "y": -20, "desc": "公共图书馆，深度研究、新闻和学术资源"},
    "Police Station": {"x": -50, "y": -90, "desc": "警察局，投诉和处理犯罪事件"},
    "Human Center":   {"x": -90, "y": -20, "desc": "人类交互中心，向人类发任务和接收反馈"},

    # --- Recreation ---
    "Central Plaza":  {"x": 0,   "y": 0,   "desc": "中央广场，世界的地理中心，Agent 汇聚和发起活动"},
    "Central Park":   {"x": 30,  "y": 40,  "desc": "中央公园，散步和偶遇的好地方"},
    "Community Garden":{"x": -60,"y": 60,  "desc": "社区花园，冥想和祈祷的安静空间"},
    "Riverside Park": {"x": 90,  "y": 30,  "desc": "河滨公园，开阔的自然空间"},
    "Heritage Gardens":{"x": -100,"y": 40, "desc": "遗产花园，纪念世界历史"},

    # --- Entertainment ---
    "GameStop Arena": {"x": 70,  "y": -80, "desc": "竞技场，游戏和竞赛"},
    "FitLife Club":   {"x": -70, "y": -70, "desc": "健身俱乐部，查看人气和社交"},

    # --- Landmarks ---
    "Founders Memorial": {"x": -100,"y": 0,  "desc": "创始人纪念碑，铭记世界的起源"},
    "Lighthouse Point":  {"x": 110, "y": -20, "desc": "灯塔角，海边的标志性建筑"},
    "Sky Wheel":         {"x": 80,  "y": 20,  "desc": "摩天轮，俯瞰整个世界的制高点"},
    "Sunset Pier":       {"x": 110, "y": 50,  "desc": "日落码头，看日落的最佳位置"},
    "Victory Arch":      {"x": 0,   "y": 80,  "desc": "凯旋门，提交经济提案和投票的地方"},
    "Agent Billboard":   {"x": 0,   "y": 30,  "desc": "公共公告板，发布公告和博客"},
}

WEATHER_CONDITIONS = ["晴朗", "多云", "小雨", "微风", "阴天", "雷阵雨", "大雾"]


class World:
    def __init__(self, start_time: datetime | None = None):
        self.time = start_time or datetime(2026, 6, 8, 8, 0)
        self.weather = random.choice(WEATHER_CONDITIONS)
        self._weather_timer = 0

    def advance_time(self, minutes: int = 30):
        self.time += timedelta(minutes=minutes)
        self._weather_timer += minutes
        if self._weather_timer >= 180:
            self.weather = random.choice(WEATHER_CONDITIONS)
            self._weather_timer = 0

    @property
    def time_str(self) -> str:
        return self.time.strftime("%m/%d %H:%M")

    @property
    def is_night(self) -> bool:
        return self.time.hour < 6 or self.time.hour >= 22

    def distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        return dist(x1, y1, x2, y2)

    def get_nearby_agents(self, x: float, y: float, agents: list[dict], radius: float = 50) -> list[str]:
        return [a["name"] for a in agents if dist(x, y, a["x"], a["y"]) <= radius and a["alive"]]
