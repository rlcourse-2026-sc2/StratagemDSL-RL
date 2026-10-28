# 在《星际争霸 II》里跑生成的地图：`strat play`

`strat play` 让一个智能体通过 PySC2 指挥地图里的己方部队，对局结束时读出胜负，并把每一步写成日志。敌方仍由地图里的 Galaxy 脚本（计划的 token game）指挥，和 MARL 训练时一样。

## 1. 两种地图：要不要 GameOver

| 用途 | 打包方式 | 到达终局时 |
| --- | --- | --- |
| MARL 训练 | `strat pack FILE`（默认） | 只记下结局，游戏继续，下一回合重新刷兵 |
| LLM / 脚本智能体评测 | `strat pack FILE --gameover` | 调用 `GameOver`：success 终局己方胜、对方负，failure 终局反之；一局就是一个计分回合 |

`--gameover` 可以和 `--oracle` 叠加：oracle 让地图自己执行己方命令，用于"按计划执行"这一组对照。

```bash
strat pack examples/petri/arid_besiege_wei.strat --gameover -o build/arid_go             # 普通版 + GameOver
strat pack examples/petri/arid_besiege_wei.strat --gameover --oracle -o build/arid_go_or # oracle 版 + GameOver
```

不写 `--base-map` 时按文件名选底图：`arid_*` 用 arid_plateau，`cerulean_*` 用 cerulean_fall_le，`sdjx_*` 用 sdjx_te，其余用 jctq_te。命令会打印实际用的底图。

## 2. 安装

- 《星际争霸 II》：Linux 无头版（SMAC 用的 4.10）或 Windows / macOS 客户端，`SC2PATH` 指向安装目录。
- `pip install -e ".[play]"`，会装 PySC2 和 LLM SDK。
- PySC2 4.0 有两个常见问题：
  - protobuf 太新时报 "Descriptors cannot be created directly"。设 `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`，或装 `protobuf<=3.20.3`。
  - Python 3.11 及以上 import 时报 `random.shuffle` 参数错误。用 Python 3.8–3.10（和 SMAC 一样）。
- LLM 的配置和 `strat generate` 一样：`--provider/--model/--api-key`，或 `~/.stratagemdsl/llm.json`。

## 3. 四种条件

```bash
M=build/arid_go/arid_besiege_wei.SC2Map
F=examples/petri/arid_besiege_wei.strat
strat play $F --map $M --agent llm     --provider anthropic --model <id> --episodes 20 -o runs/arid/llm
strat play $F --map $M --agent intents --provider anthropic --model <id> --episodes 20 -o runs/arid/intents
strat play $F --map build/arid_go_or/arid_besiege_wei.SC2Map --agent plan --episodes 20 -o runs/arid/plan
strat play $F --map $M --agent direct  --episodes 20 -o runs/arid/direct
```

| 条件 | 谁指挥己方 | LLM 知道什么 |
| --- | --- | --- |
| `llm` | LLM，每隔 `--decision-seconds`（默认 4 秒游戏时间）决策一次 | 目标（intent 的胜负条件）、地形、命名区域、初始位置、当前局面 |
| `intents` | 同上 | 另加计划：各阶段的目的、命令和推进条件 |
| `plan` | 没有智能体；用 `--oracle` 地图，计划自己执行 | — |
| `direct` | 固定命令，默认所有己方部队攻击最大的敌方部队；可用 `--orders force:action:target ...` 指定 | — |

LLM 只能用 DSL 的动作词汇：`move(force, region)`、`attack(force, target)`、`hold(force)`、`retreat(force, region)`。回答必须是 JSON：`{"orders": [...], "note": "..."}`。回答无效时会把错误反馈给它重试一次，无效次数计入统计。

## 4. 输出

`-o` 目录下：

- `summary.json`：胜率及 Wilson 95% 区间、各结果计数、平均对局时长、平均 LLM 调用次数和 token 数、无效回答数、运行参数。
- `episodes.jsonl`：每局一行，包括结果、时长、调用统计、区域进出事件（谁在什么时候进了哪个区域，可用来判断计策是否真的发生），以及坐标标定。
- `episode_<k>.jsonl`：每次决策一行，包括局面摘要、给 LLM 的提示、它的原话、解析出的命令和错误。

## 5. 先跑通再批量跑

1. `--dry-run`：不启动游戏，用一个只会移动的玩具模拟器跑完整流程，检查提示词、LLM 连接和日志。不加 `--provider` 时用 `--answers` 文件里的固定回答。
   加 `--sim plan` 改用计划驱动的替身（`play.plansim`）：计划的 Petri 网指挥敌方，有简化的战斗和地面寻路，终局会结束对局。
   用 LLM-PySC2 的多智能体接口跑同一张图见 [LLM_PYSC2.md](LLM_PYSC2.md)。
2. 真机跑 1 局，加上 `--replays runs/replays`，用客户端看回放确认：
   - 部队认对了。`summary.json` 的 `calibration_warnings` 为空，说明每支部队第一次出现的位置离它的出生点不远；坐标系翻转时会在这里报出来。
   - 敌方按脚本行动。PySC2 的对手是内置 AI（默认 `--bot very_easy`），它可能也会指挥敌方单位，和地图脚本冲突。
   - 到终局时对局结束，结果是 victory 或 defeat，而不是 timeout。
3. 确认后再加 `--episodes`。

## 6. 局限

- 地图上的 Galaxy 用到的原生函数在 4.10 版引擎里能否全部运行，需要在你的环境里实测；较新的底图也一样。
- 观测只包括己方能看到的单位（战争迷雾），敌方部队的位置是可见部分的中心或最后看到的位置。
- `attack` 指向敌方部队时，用的是下命令那一刻的位置；敌方移动后需要重新下令（`direct` 每次决策都会重新下令）。
