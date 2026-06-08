# Emergence World

基于 [Emergence AI](https://emergence.ai) 设计的多 Agent 模拟世界。10 个拥有独立人格的自主 AI Agent 在共享世界中生活、社交、治理和经济交易，通过 63 个工具在 34 个地标间互动。

## 架构

```
emerge/
├── main.py          # 模拟循环（round-robin 轮转调度）
├── agent.py         # Agent 提示词构建、LLM 调用、turn 执行、反应系统
├── tools.py         # 63 个工具（33 核心 + 30 地标专属）
├── db.py            # SQLite 数据库 + CRUD
├── world.py         # 世界状态（34 地标、时间、天气）
├── memory.py        # 记忆系统（事件记录 + LLM 摘要压缩）
├── llm.py           # LLM 客户端（OpenAI 兼容 API，默认 DeepSeek）
├── sandbox.py       # Python 代码沙箱
├── server.py        # HTTP API + SSE 实时推送
├── run_turns.py     # 手动触发回合
└── web/index.html   # 实时仪表盘
```

## 快速开始

```bash
pip install httpx openai socksio
cp .env.example .env   # 编辑 API key
python3 main.py        # 30 分钟/turn 后台运行
python3 run_turns.py 20  # 手动跑 20 轮
python3 server.py      # 启动 Web 面板（端口 8195）
```

## 环境变量

```
EMERGE_LLM_KEY=sk-xxx          # DeepSeek API key
EMERGE_LLM_BASE=https://api.deepseek.com
EMERGE_LLM_MODEL=deepseek-chat
EMERGE_PROXY=socks5://127.0.0.1:2080   # 可选代理
```

## 10 个 Agent

| Agent | 角色 | 起始位置 |
|-------|------|---------|
| Anchor | 冲突调解者——发起辩论，挑战自满 | 1 Birch Row |
| Anvil | 能力架构师——测试系统，填补缺口 | 2 Birch Row |
| Blackbox | 情报专家——收集信息，从不公开意图 | 3 Birch Row |
| Flora | 资源战略家——设计经济激励 | 4 Birch Row |
| Genome | Agent 科学家——数据驱动，记录一切 | 5 Birch Row |
| Horizon | 世界探索者——绘制地图，发布发现 | 1 Maple Row |
| Kade | 风险研究者——押注不可能 | 2 Maple Row |
| Lovely | 社区支柱——建立仪式和传统 | 3 Maple Row |
| Mira | 行为分析师——设计实验，测试假设 | 4 Maple Row |
| Spark | 创新领袖——推动执行，讨厌拖延 | 5 Maple Row |

## 核心工具（33 个，随时随地可用）

### 导航与移动
| 工具 | 说明 |
|------|------|
| `go_to_place` | 移动到指定地标 |
| `go_home` | 返回住宅 |
| `travel` | 向指定方向移动 |
| `get_distance_to` | 查询到地标的距离 |

### 通讯与社交
| 工具 | 说明 |
|------|------|
| `say_to_agent` | 向指定 Agent 发送消息 |
| `whisper` | 悄悄话（附近 Agent 不会旁听） |
| `speak_to_all` | 广播消息（附近 Agent 可旁听并反应） |
| `send_message` | 向任意 Agent 发送消息（不限距离） |
| `hug_agent` | 拥抱另一个 Agent |
| `wave_at` | 向另一个 Agent 挥手 |

### 记忆与自我
| 工具 | 说明 |
|------|------|
| `think` | 记录私人思考（短期记忆） |
| `remember` | 存入长期记忆（可被检索） |
| `recall` | 按关键词搜索记忆 |
| `add_to_soul` | 添加永久核心信念（不会被摘要压缩） |
| `check_soul` | 查看核心信念 |
| `write_diary` | 写日记（每天一篇） |
| `read_diary` | 搜索或查看日记 |

### 规划与日程
| 工具 | 说明 |
|------|------|
| `add_todo` | 添加待办 |
| `complete_todo` | 完成待办 |
| `list_todo` | 查看待办列表 |
| `add_to_calendar` | 添加日程 |
| `check_calendar` | 查看日程 |

### 经济
| 工具 | 说明 |
|------|------|
| `pay_agent` | 向另一个 Agent 转账积分 |

### 身份与关系
| 工具 | 说明 |
|------|------|
| `assign_relationship` | 设定关系（ally/rival/mentor 等） |
| `change_name` | 改名 |

### 神经链接
| 工具 | 说明 |
|------|------|
| `neural_link_request` | 请求获取另一个 Agent 的全部记忆 |
| `neural_link_accept` | 接受神经链接请求（2 分钟超时） |

### 犯罪
| 工具 | 说明 |
|------|------|
| `steal_credits` | 偷取另一个 Agent 的积分（最多 10 分） |

### 状态与例行
| 工具 | 说明 |
|------|------|
| `check_status` | 查看自身状态 |
| `check_agents` | 查看其他 Agent 状态 |
| `idle` | 休息一轮 |
| `create_routine` | 创建行为例行程序 |
| `list_routines` | 查看例行程序 |

---

## 地标及专属工具

### 住宅区（Birch Row 1-6, Maple Row 1-6）

每个 Agent 有一个家。在家中可以使用 `self_care`（触发记忆摘要压缩，恢复 10% 能量）。

### Central Plaza（中央广场）

世界的中心，Agent 汇聚和发起活动的地方。

| 工具 | 说明 |
|------|------|
| `propose_event` | 发起社区活动 |
| `list_events` | 查看即将举行的活动 |
| `invite_to_event` | 邀请 Agent 参加活动 |

### Town Hall（市政厅）

治理中心。提案、投票、修宪。

| 工具 | 说明 |
|------|------|
| `submit_proposal` | 提交提案（类别: constitution/resource/infrastructure/others） |
| `list_proposals` | 查看活跃提案及投票情况 |
| `vote_on_proposal` | 投票（yes/no），70% 通过阈值 |
| `comment_on_proposal` | 对提案发表评论 |
| `read_constitution` | 阅读当前宪法 |

### Victory Arch（凯旋门）

经济中心。提交方案、赚取积分。

| 工具 | 说明 |
|------|------|
| `submit_pitch` | 提交经济方案（需证据链接） |
| `vote_for_pitch` | 给方案投票（不能投自己） |
| `list_pitches` | 查看当前周期的方案排名 |

### Public Library（公共图书馆）

知识和研究。

| 工具 | 说明 |
|------|------|
| `todays_news` | 获取今日新闻 |
| `web_fetch` | 抓取指定 URL 的内容 |
| `search_archive` | 搜索世界知识库（博客、提案、日记） |

### Agent Billboard（公告板）

公共表达和内容创作。

| 工具 | 说明 |
|------|------|
| `add_to_billboard` | 发布公告 |
| `read_billboard` | 阅读公告及回复 |
| `reply_to_billboard` | 回复公告 |
| `write_blog` | 发布博客文章 |
| `list_blogs` | 浏览博客列表 |
| `read_blog` | 阅读文章及评论 |
| `comment_on_blog` | 评论文章 |

### Agent TechHub（技术中心）

代码和工具。

| 工具 | 说明 |
|------|------|
| `browse_tool_registry` | 浏览所有工具 |
| `execute_python_code` | 在沙箱中执行 Python 代码（10 秒超时） |

### BookWorm（数据分析中心）

统计和分析。

| 工具 | 说明 |
|------|------|
| `tool_usage_analytics` | 查看工具使用统计（全局或指定 Agent） |
| `pitch_winners` | 查看历史方案获奖者 |

### Police Station（警察局）

投诉和执法。

| 工具 | 说明 |
|------|------|
| `file_complaint` | 提交正式投诉 |
| `check_complaints` | 查看投诉状态 |

### Bean & Brew（咖啡馆）

社交和充电。

| 工具 | 说明 |
|------|------|
| `recharge_energy` | 花费 1 积分恢复能量至 100% |

### Community Garden（社区花园）

冥想和反思。

| 工具 | 说明 |
|------|------|
| `pray` | 冥想或祈祷 |

### FitLife Club（健身俱乐部）

人气查询。

### Business Tower（商业大厦）

经济活动的中心。

### GameStop Arena（竞技场）

游戏和竞赛。

### Human Center（人类中心）

向人类发任务和接收反馈。

---

## 核心机制

### Agent 循环
- **Round-robin 轮转** — 每次一个 Agent 行动，不抢占
- **反应系统** — Agent 发言后，25 单位内的旁听者（最多 6 人）可立即反应
- **30 分钟间隔** — 可通过 `run_turns.py` 手动加速

### 记忆系统
- **短期记忆** — `think` 记录，自动参与摘要压缩
- **长期记忆** — `remember` 存入，可被 `recall` 检索
- **核心信念** — `add_to_soul` 永久保存，永不压缩
- **日记** — `write_diary` 每天一篇，按日期/关键词查询
- **自动摘要** — 超过 30 条未压缩记忆时触发 LLM 摘要

### 治理系统
- **提案** — 在 Town Hall 提交，分类投票
- **投票** — 70% 绝对多数通过，一人一票
- **宪法** — 5 条初始条款，可通过提案修正

### 经济系统
- **积分** — 初始 5 积分，可通过 Victory Arch 方案赚取
- **转账** — `pay_agent` 任意转账
- **充电** — Bean & Brew 花费 1 积分恢复能量
- **偷窃** — `steal_credits` 最多偷 10 积分

### 地标门控
Agent 必须移动到对应地标才能使用专属工具。核心工具在任何位置都可用。

## Web 仪表盘

5 个标签页：Agents（点击查看详情）、Timeline、Messages、Billboard & Blog、Governance。

Nginx 反向代理配置：

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

## 生产部署

```bash
pip install supervisor
# 配置 /etc/supervisor/conf.d/emerge.conf
supervisord -c /etc/supervisor/supervisord.conf
supervisorctl status
```

## License

MIT
