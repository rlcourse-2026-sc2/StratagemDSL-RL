# StratagemDSL：用战略描述语言生成《星际争霸 II》地图

用 `.strat` 文件描述一场战术（双方部队、目标、分阶段的计划、在地图上的坐标），工具链会检查它、把计划编译成地图触发器，并打包成可以直接在 StarCraft II 里打开的 `.SC2Map`。

```text
你的 .strat ──strat check──▶ 语义检查 ──strat compile──▶ Galaxy 脚本 + 触发器 XML ──strat pack──▶ .SC2Map
                                                                                   （写入底图副本并读回校验）
```

整个流程不需要安装 StarCraft II；只有想进游戏实际跑地图时才需要。

## 仓库里有什么

```text
examples/learning/     入门课 01–05，从这里开始（04、05 是 Petri 网写法）
examples/stratagems/   十二计策各一个完整范例，都通过严格检查，可直接当作业起点
examples/demos/        在天梯图 Cerulean Fall 上的完整对战示例
examples/petri/        进阶：用 Petri 网写循环佯攻、分叉/同步
assets/base_maps/      39 张底图（*_te 为教学图，其余为天梯图）
docs/                  命令速查、语言手册、API 目录、LLM 生成、进游戏运行
src/stratagemdsl/      工具链源码（不需要改）
tests/                 回归测试（不需要改；tests/fixtures/ 里是测试专用输入）
```

下文每段命令都给出三种写法：**Linux / macOS**（bash、zsh）、**Windows PowerShell**、**Windows cmd**。分不清自己在哪种终端时看提示符：PowerShell 是 `PS C:\...>`，cmd 是 `C:\...>`。所有命令都在仓库根目录运行。

## 1. 安装

需要 Python 3.10+（推荐 3.12）。两种方式任选其一。

**用 conda**（三种终端写法相同；PowerShell 第一次用 conda 前要先运行一次 `conda init powershell` 并重开终端）：

```bash
conda create -n strat-rl python=3.12 -y
conda activate strat-rl
python -m pip install -r requirements.txt
python -m pip install -e .
```

**用 venv**，只有激活那一行不同：

Linux / macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

Windows PowerShell（提示“禁止运行脚本”时先运行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`）：

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

Windows cmd：

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip install -e .
```

装好后运行 `strat --version`，应输出 `strat (StratagemDSL) 0.6.0`。

可选组件：
- `conda install -c conda-forge graphviz`：生成计划图的 SVG；没有它只输出 `.dot` 和 `.mmd` 文本。
- `python -m pip install -e ".[llm]"`：用真实模型跑 `strat generate`。
- `python -m pip install -e ".[dev]"`：跑测试。

打包地图用的 StormLib 随仓库提供 Linux x86-64 和 Windows x64 两个版本，按系统自动选择；macOS 等其他系统见 [assets/native/README.md](assets/native/README.md)。

## 2. 五分钟跑通

Linux / macOS：

```bash
strat check examples/learning/01_event_redeploy.strat --pattern-report
strat pack  examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/first
```

Windows PowerShell：

```powershell
strat check examples/learning/01_event_redeploy.strat --pattern-report
strat pack  examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/first
```

Windows cmd：

```bat
strat check examples/learning/01_event_redeploy.strat --pattern-report
strat pack  examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/first
```

第一条应输出 `[OK] no diagnostics`；第二条最后出现 `pack passed` 就成功了，地图在 `build/first/01_event_redeploy.SC2Map`。同一目录里还有：

| 文件 | 看什么 |
| --- | --- |
| `*.PlanGraph.svg`、`*.PetriNet.svg` | 计划的阶段和转移画成的图，先看这个确认计划结构对不对（需要 Graphviz） |
| `*.routes.svg` | 各部队在底图上的地面路线 |
| `*.galaxy` | 生成的地图脚本：部队创建、事件注册、条件判断、敌方命令 |
| `*.agent_intents.json` | 己方（盟友）的期望动作，留给智能体执行，地图脚本不代办 |
| `pattern_report.txt` | 声明了计策模式（`pattern Feint {...}` 等）时，各项义务是否找到证据 |
| `result.json` | 每一层是否通过；失败时记录失败的层和错误 |

## 3. 选定某个计策做5张自己的地图

**① 选底图，看地形。** `strat mapinfo` 打印地图尺寸、可通行区域、高地/坡道和地形网格，坐标都从这里取。文件名有空格时加双引号。

**② 选一个起点复制过来。** 想从零理解就复制入门课；想直接做某条计策就复制 `examples/stratagems/` 里对应的一个。

**③ 修改。** 一个 `.strat` 由四块组成：`world`（部队、建筑、区域）、`intent`（目标、成功/失败条件、计策模式）、`plan`（阶段与转移：`on` 事件、`when` 条件、`do` 动作）、`binding sc2`（每个实体对应的单位类型、数量、坐标）。换底图时把坐标都改成 `point_xy(x, y)`：`examples/stratagems/` 里的 `point_id(...)` 是教学图上的预置点，只在各自的 `<计策>_te` 底图上有效。语法和全部 API 见 [语言手册](docs/language/LANGUAGE_MANUAL.md) 和 [API 目录](docs/api/API_CONTRACTS.md)。

**④ 检查并打包。** 按顺序，前一步通过再做下一步：坐标检查 → 语义检查 → 画计划图 → 打包。自己的文件要用 `--base-map` 指明底图；不指定时按文件名猜（`cerulean_*`、`arid_*`、`<计策>_*`），猜不到就用 `jctq_te`。

Linux / macOS：

```bash
# ① 看地形
ls assets/base_maps
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map"
# ② 复制起点
mkdir -p work
cp examples/stratagems/dhls_18_enter_signal.strat work/my_lure.strat
# ③ 用编辑器修改 work/my_lure.strat
# ④ 检查并打包
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map" --check work/my_lure.strat
strat check work/my_lure.strat --pattern-report
strat graph work/my_lure.strat -o build/my_lure
strat pack  work/my_lure.strat --base-map "assets/base_maps/Agna Valley-1.SC2Map" -o build/my_lure
```

Windows PowerShell：

```powershell
# ① 看地形
ls assets/base_maps
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map"
# ② 复制起点
New-Item -ItemType Directory -Force work
Copy-Item examples/stratagems/dhls_18_enter_signal.strat work/my_lure.strat
# ③ 用编辑器修改 work/my_lure.strat，例如 notepad work/my_lure.strat
# ④ 检查并打包
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map" --check work/my_lure.strat
strat check work/my_lure.strat --pattern-report
strat graph work/my_lure.strat -o build/my_lure
strat pack  work/my_lure.strat --base-map "assets/base_maps/Agna Valley-1.SC2Map" -o build/my_lure
```

Windows cmd：

```bat
REM ① 看地形
dir assets\base_maps
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map"
REM ② 复制起点
mkdir work
copy examples\stratagems\dhls_18_enter_signal.strat work\my_lure.strat
REM ③ 用编辑器修改 work\my_lure.strat，例如 notepad work\my_lure.strat
REM ④ 检查并打包
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map" --check work/my_lure.strat
strat check work/my_lure.strat --pattern-report
strat graph work/my_lure.strat -o build/my_lure
strat pack  work/my_lure.strat --base-map "assets/base_maps/Agna Valley-1.SC2Map" -o build/my_lure
```

复制过来的文件还没改坐标时，④ 的第一条会报 `point_id is not portable`，最后的 `pack` 会报 `Missing point IDs`，这是预期的：这些预置点只存在于 `dhls_te` 上。把坐标都改成 Agna Valley 上的 `point_xy` 后，四条命令都应通过。

**⑤（必做）让 LLM 帮你生成变体。** `strat generate` 把底图地形和种子策略写进提示词，模型输出后自动逐层检查、把错误发回去修，通过后直接打包。先用 `--replay` 离线演练一遍（用现成文件代替模型回答，不需要 API key）：

Linux / macOS：

```bash
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat \
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp \
  --replay examples/stratagems/dhls_18_enter_signal.strat \
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

Windows PowerShell：

```powershell
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat `
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp `
  --replay examples/stratagems/dhls_18_enter_signal.strat `
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

Windows cmd：

```bat
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat ^
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp ^
  --replay examples/stratagems/dhls_18_enter_signal.strat ^
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

第一次“回答”是种子原文，因为用了 `point_id` 被地形检查拒绝；第二次通过并打包，产物在 `build/llm/`。连真实模型时去掉两个 `--replay`，配置方法见 [docs/LLM_GENERATION.md](docs/LLM_GENERATION.md)，例子见 [命令速查](docs/COMMANDS.md#strat-generate)。

## 4. 命令速查

每个子命令的 5 个例子（三种终端写法）见 **[docs/COMMANDS.md](docs/COMMANDS.md)**。`strat <子命令> -h` 列出全部参数。

| 命令 | 做什么 | 作业里什么时候用 |
| --- | --- | --- |
| `strat mapinfo MAP` | 底图地形；`--check F` 检查坐标 | 写坐标前、改完坐标后 |
| `strat parse F` | 解析，看 AST | 语法报错时 |
| `strat check F` | 语义检查；`--pattern-report` 看计策证明 | 每次改完 |
| `strat graph F -o DIR` | 画计划图 | 确认计划结构 |
| `strat net F` | Petri 网分析：死锁、有界、永不触发 | 用 Petri 网写法时 |
| `strat lower` / `compile F -o DIR` | 只生成到 Galaxy / 触发器 XML | 想看生成的脚本时 |
| `strat pack F --base-map MAP -o DIR` | 打包成 `.SC2Map` | 交作业前 |
| `strat route F -o DIR` | 部队地面路线；`--strict` 有走不通的就报错 | 检查路线是否可达 |
| `strat generate --seed S --base-map MAP` | LLM 生成变体 | 可选 |
| `strat play` / `llm-pysc2` | 让智能体在地图上对战 / 生成 LLM-PySC2 任务包 | 进阶 |
| `strat export-api DIR` | 导出全部 API 签名 | 查 API |

## 5. 示例清单

| 文件 | 学什么 |
| --- | --- |
| `learning/01_event_redeploy` | 最小完整策略：进入区域 → 敌方回防 → 确认目标被摧毁；独立的失败监视 |
| `learning/02_join_and_counter` | 两个独立信号用 `join ... all` 汇合；`killed_in` 累计击杀 |
| `learning/03_typed_feint` | 声明 `pattern Feint` 并把五个角色绑定到实体，看 `pattern_report.txt` |
| `learning/04_petri_sync_counter`、`05_petri_feint_budget` | 02、03 的 Petri 网写法：多输入弧、带权弧、计数库所 |
| `stratagems/` | 十二计策各一例，结构相同（入区信号打开关键阶段，成功终态要求目标达成且排除失败）：`adcc` 暗渡陈仓、`dhls` 调虎离山、`fkwz` 反客为主、`gmzz` 关门捉贼、`jctq` 金蝉脱壳、`jdsr` 借刀杀人、`sdjx` 声东击西、`swct` 上屋抽梯、`tlhz` 偷梁换柱、`wwjz` 围魏救赵、`wzsy` 无中生有、`yqgz` 欲擒故纵 |
| `demos/cerulean_lure_zerg_vs_protoss` | 天梯图上的调虎离山（虫族 vs 神族），全部 `point_xy`，换底图时最好的参照 |
| `demos/cerulean_hellbat_raid` | 天梯图上的人族突袭 |
| `petri/` | 循环佯攻、分叉陷阱、围魏救赵的 Petri 网版本 |

## 6. 常见报错

| 报错 | 意思和改法 |
| --- | --- |
| `无法将“F=...”项识别为 cmdlet` | 在 PowerShell 里用了 bash 写法；换成上面 PowerShell 代码块里的命令 |
| `strat: command not found` / `不是内部或外部命令` | 环境没激活，或 `pip install -e .` 没装成功 |
| `E007_UNCONFIRMED_SUCCESS` | 进入 `terminal success` 的转移，`when` 里必须写出 `intent` 的成功条件 |
| `E008_SUCCESS_FAILURE_RACE` | 成功转移还要写 `not (失败条件)`：failure 是 `not alive(allies)` 时写 `when destroyed(base) and not (not alive(allies))` |
| `E005_EMPTY_DISTANCE` | 用 `distance(x, ...)` 时要同时写 `alive(x)`，否则 x 全灭后距离没有意义 |
| `point_id is not portable to ...` | 换了底图却还在用预置点，改成 `point_xy(x, y)` |
| `... do not fit the base map` | 坐标落在悬崖、虚空或障碍物上；`strat mapinfo --check` 会给出最近的可用位置 |
| `cannot load StormLib` | 打包需要的原生库没找到，见 [assets/native/README.md](assets/native/README.md) |

检查器默认是严格模式（保证地图在 SC2 里可执行）；`--loose` 只做基本检查，用它打出来的地图不保证能跑。

## 7. 补充说明

- **进游戏跑地图**：`strat pack --gameover` 生成一局一结算的地图，`strat play` 通过 PySC2 让 LLM 或脚本智能体来打，见 [docs/PLAY.md](docs/PLAY.md)；不装游戏可以先用 `--dry-run` 替身模拟器。配合 LLM-PySC2 的多智能体运行见 [docs/LLM_PYSC2.md](docs/LLM_PYSC2.md)。
- **逐层调试**：每层都能单独运行，例如 `python -m stratagemdsl.frontend 文件 --compare`（两个解析器是否一致）、`python -m stratagemdsl.backend 文件 -o x.galaxy`。
- **跑测试**：装好 `.[dev]` 后运行 `python -m pytest -q`（约 1–2 分钟）。

工具链通过只说明产物能被编译器和地图格式接受；部队是否真按计划行动、计策是否奏效，要进游戏观察。
