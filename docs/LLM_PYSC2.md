# 用 LLM-PySC2 跑生成的地图：`strat llm-pysc2`

`strat play` 用 StratagemDSL 自己的宏动作（move / attack / hold / retreat，raw 接口）指挥己方。
[LLM-PySC2](https://github.com/NKAI-Decision-Team/LLM-PySC2) 是另一套评测环境：LLM 通过 PySC2 的
feature-layer 接口逐个小队下命令（屏幕坐标、单位 tag、`Move_Minimap`、技能），并且多个 LLM 智能体分工协作。
这一页说明怎样把 StratagemDSL 生成的地图交给 LLM-PySC2（配套的 LLM-PySC2 分支 `feature/stratagemdsl-bridge`，
其中的 `llm_pysc2.stratagem` 包读这里导出的任务包）。

```text
 .strat ──strat llm-pysc2──▶ <stem>.SC2Map (--gameover)  +  <stem>.llm_pysc2.json (任务包)
                                        │                              │
                                        ▼                              ▼
            python -m llm_pysc2.bin.stratagem_run --bundle <stem>.llm_pysc2.json [--engine fake] [--model ...]
                     SC2Env ── MainAgent ── 每支己方部队一个 LLM 智能体（神族/人族/虫族）
```

## 1. 生成地图和任务包

```bash
strat llm-pysc2 examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/cerulean
#   map     build/cerulean/cerulean_lure_zerg_vs_protoss.SC2Map
#   bundle  build/cerulean/cerulean_lure_zerg_vs_protoss.llm_pysc2.json
#   races   ally zerg vs enemy protoss; agents for zergling_bait, roach_strike
```

和 `strat pack --gameover` 一样逐层编译、打包、读回（终局时 `GameOver`，一局一个计分回合）；
`--oracle` 让地图也执行己方命令（"按计划执行"对照组），`--loose` 放宽严格检查（只通过宽松检查的旧写法需要），
`--map M --base-map B` 只为已有地图写任务包。`--screen/--minimap/--camera-width` 要和 LLM-PySC2 运行时一致（默认 128/64/24）。

## 2. 任务包（`stratagemdsl.llm-pysc2-task.v1`）

| 字段 | 内容 |
| --- | --- |
| `map` | 打包好的 .SC2Map 绝对路径、底图、宽高、可玩区域；`gameover`、`oracle` |
| `interface` | feature 屏幕/小地图尺寸、镜头宽度、`raw_resolution`（= 地图长边，raw 1 像素 = 1 格） |
| `races` / `players` | 己方/敌方种族（LLM-PySC2 据此选动作空间）、玩家编号 |
| `forces` | 每个 force/asset：阵营、owner、编成、出生点（世界坐标 + 小地图像素）、是否由智能体指挥 |
| `regions` | 命名区域：圆心与半径，世界坐标 + 小地图像素 |
| `objective` | intent 的胜负条件（DSL 文本） |
| `plan` | 阶段、转移、`brief`（计划的文字版）、`force_plans`（每支己方部队在各阶段的命令、目标的小地图坐标、何时开始） |
| `terrain` | 高地与坡道，世界坐标版和小地图像素版 |
| `source` | .strat 源文件（LLM-PySC2 一侧用它做部队匹配和计划跟踪） |

小地图坐标按 PySC2 `crop_to_playable_area=False` 的约定：整张地图按 `minimap / max(宽, 高)` 缩放，原点左上，y 向下。
`play.llm_pysc2.Projection` 做换算；LLM-PySC2 一侧在每局开头用小地图 `player_relative` 层核对一次（`minimap_check_px`）。

## 3. LLM-PySC2 一侧做了什么

- **三族动作**：接入扩展后的 `llm_action.py`（人族、虫族动作表），修正了两个写错的函数编号
  （`Ability_InjectLarva` 写成 527，应为 204；`Morph_Baneling` 写成 80，应为 458）——编号错了的动作永远不会出现在合法动作里；
  `lib/unit_actions.py` 按单位类型给出三族的动作空间（例如蟑螂 = 基础动作 + 钻地/出地 + 变异破坏者）；
  prompt / 观测 / 通信的工厂补上 terran、zerg。
- **按部队分组**：原版按单位类型把新单位分给第一个能用它的智能体；这里由 `StratagemRuntime`
  （复用本仓库的 `play.observe.ForceTracker`：owner、类型、最近出生点、容量）决定单位属于哪支 force，
  所以同为跳虫的诱饵和主力会分给两个指挥官。每支部队一个 `CombatGroup-<force>` 智能体（`--layout single` 则一个智能体管全部），
  每种单位类型一个小队、一个编队（含钻地/攻城等变形后的类型）。
- **提示词**（`'stratagem'` prompt 与观测翻译器）：目标、命名区域和地形（小地图像素）、所有部队的当前态势（区域进出事件）；
  `--condition intents` 再加计划和**计划进度估计**——`play.plantracker.PlanTracker` 用己方能观测到的事件重放 Petri 网
  （迷雾下敌方未见即"未知"；己方事件触发的转移在守卫未知时按"成立"处理，轮询转移要求守卫确定成立）。
- **其它修正**：未知模型名回退到 OpenAI 兼容客户端（DeepSeek、Qwen、vLLM 等都能直接用）；动作翻译把每个
  `Team X:` 块按名字对齐到小队（原来按出现顺序，LLM 换个顺序就会把命令发给错的小队）；`get_func` 不再就地清空共享的动作表。
- **开局编组加速**：LLM-PySC2 给每个新单位编队需要 2–3 个界面动作，step_mul=8 时 20 个单位要用掉约 10 秒游戏时间。
  `stratagem_run` 在编组完成前每步只推进 1 个 game loop（`--no-fast-setup` 关闭）。

## 4. 运行

```bash
# 真机（装好 SC2，SC2PATH 指向安装目录；地图用绝对路径，不用拷进 Maps/）
python -m llm_pysc2.bin.stratagem_run --bundle build/cerulean/cerulean_lure_zerg_vs_protoss.llm_pysc2.json \
    --condition intents --model gpt-4o-mini --api-base https://api.openai.com/v1 --api-key $KEY --episodes 10

# 没有 SC2：协议级替身引擎；没有 LLM：离线的计划跟随者（不是语言模型，只用于跑通和对照）
python -m llm_pysc2.bin.stratagem_run --bundle ... --engine fake --model offline
```

输出目录里 `summary.json` 与 `strat play` 同格式（胜率与 Wilson 95% 区间、结果计数、平均时长、LLM 调用与 token），
`episodes.jsonl` 每局一行：结果、各智能体的查询次数与 token、区域事件、坐标标定、计划跟踪器看到的转移；
`--engine fake` 时还有地图脚本（Petri 网）实际触发的转移和敌方命令、智能体下达的命令记录。
LLM-PySC2 自己的逐智能体日志（提示词、每轮观测 `o.txt`、原始回答 `a_raw.txt`、执行的 pysc2 函数 `a_his.txt`）在 `llm_log/` 下，路径记在每局记录里。

## 5. 没有 SC2 时：`--engine fake` 与 `play.plansim`

`play.plansim.PlanSim` 是计划驱动的替身世界：敌方由计划的 Petri 网（`net.TokenGame`，与地图脚本同一套步进语义）在
进出区域、单位死亡、受攻击、技能、计时器和轮询事件上推进，并执行阶段 `do` 块与转移动作里的敌方命令；
地面单位沿底图的高地/坡道走 A* 路径，空军直飞；战斗是平摊 DPS（先扣护盾、再按每击扣护甲，无溅射、无克制加成）；
己方视野之外的敌人不可见，见过的敌方建筑保留快照。

`llm_pysc2.stratagem.fake_sc2` 在它外面包了一层 s2client 协议：`SC2Env`、pysc2 `Features`（feature 层、feature_units、
raw_units、合法动作、`transform_action`）以及 LLM-PySC2 的 MainAgent/LLMAgent 全部是真实代码，只有游戏进程被替换。
所以它能验证接口和流程，**不能**代替真机评测：数值、寻路、碰撞、技能效果都只是近似。

本仓库的 `strat play --dry-run --sim plan` 也可以用它（`--agent plan` 时计划同时指挥己方）。

## 6. 已知局限与观察

- `examples/petri/arid_besiege_wei.strat` 是一场竞速：在替身引擎里不下任何己方命令时 Nexus 约 11 秒被拆，
  oracle（地图自己在 0 秒下令）约 8.6 秒触发 `rear_threat` 并获胜；LLM-PySC2 的界面延迟（镜头、选择、编队，每轮决策数秒游戏时间）
  让己方第一条命令晚于这个窗口，所以替身引擎里总是失败。真机上的时间需要实测；做对比实验时可以拉开围城部队的出生点或加强 Nexus。
- 计划进度是估计：敌方单位在迷雾里死亡、`targeting` 这类看不到的事实不会触发转移。
- 敌方玩家 2 是 PySC2 的内置 AI（默认 `very_easy`），在真机上它可能和地图脚本抢敌方单位的控制权；先跑一局并看回放确认（同 `docs/PLAY.md`）。
