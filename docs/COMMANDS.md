# `strat` 命令速查：每个子命令 5 个例子

所有命令都在**仓库根目录**运行，先激活装好 StratagemDSL 的环境（`conda activate strat-rl` 或 `.venv`）。每个子命令都给出 Linux / macOS、Windows PowerShell、Windows cmd 三种写法；三者只在少数地方不同，见下表。同一节里的例子按顺序执行即可；用到前面产物的例子会注明。所有输出都写到 `build/` 下，删掉它不影响仓库。

```text
strat --version           查看版本
strat -h                  列出全部子命令
strat <子命令> -h         查看某个子命令的全部参数
```

| 写法差异 | Linux / macOS（bash、zsh） | Windows PowerShell | Windows cmd |
| --- | --- | --- | --- |
| 设置环境变量 | `export KEY=value` | `$env:KEY = "value"` | `set "KEY=value"` |
| 一条命令写成多行 | 行尾加 ` \` | 行尾加 `` ` ``（反引号） | 行尾加 ` ^` |
| 注释 | `# ...` | `# ...` | `REM ...` |
| 定义变量 | `F=a.strat`，用 `$F` | `$F = "a.strat"`，用 `$F` | `set "F=a.strat"`，用 `%F%` |
| 路径 | `/` | `/` 和 `\` 都可以 | 传给 `strat` 的参数用 `/` 可以；`copy`、`findstr` 等 cmd 自带命令要用 `\` |
| 含空格的路径 | 加双引号 `"..."` | 加双引号 | 加双引号 |

下面的命令里没有用变量，路径都写全了，复制到哪种终端都只需要选对代码块。

## 目录

- [`strat mapinfo`](#strat-mapinfo) — 查看底图地形
- [`strat parse`](#strat-parse) — 解析源码，查看 AST（第 1 层）
- [`strat check`](#strat-check) — 语义检查（第 3 层）
- [`strat graph`](#strat-graph) — 画出计划
- [`strat net`](#strat-net) — Petri 网分析（第 3 层）
- [`strat lower`](#strat-lower) — 生成 Galaxy 地图脚本（第 4 层）
- [`strat compile`](#strat-compile) — 编译成触发器 XML（第 5 层）
- [`strat pack`](#strat-pack) — 打包成 .SC2Map（第 6 层）
- [`strat route`](#strat-route) — 部队在底图上的地面路线
- [`strat generate`](#strat-generate) — 用 LLM 生成变体
- [`strat play`](#strat-play) — 让智能体在地图上对战
- [`strat llm-pysc2`](#strat-llm-pysc2) — 生成 LLM-PySC2 任务包
- [`strat export-api`](#strat-export-api) — 导出 API 目录

## strat mapinfo

**查看底图地形。** 打印地图尺寸、可通行区域、高地/坡道和地形网格；写 `point_xy` 坐标前先看这个。文件名有空格时加双引号。

Linux / macOS（bash、zsh）：

```bash
# 1. 教学图
strat mapinfo assets/base_maps/sdjx_te.SC2Map

# 2. 天梯图（文件名有空格，加引号）
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map"

# 3. 只打印地形网格
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --grid-only

# 4. 把地形描述保存成文件
strat mapinfo assets/base_maps/arid_plateau.SC2Map -o build/mapinfo/arid_plateau.txt

# 5. 检查一个 .strat 的所有坐标是否落在这张图的可通行位置
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --check examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

Windows PowerShell：

```powershell
# 1. 教学图
strat mapinfo assets/base_maps/sdjx_te.SC2Map

# 2. 天梯图（文件名有空格，加引号）
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map"

# 3. 只打印地形网格
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --grid-only

# 4. 把地形描述保存成文件
strat mapinfo assets/base_maps/arid_plateau.SC2Map -o build/mapinfo/arid_plateau.txt

# 5. 检查一个 .strat 的所有坐标是否落在这张图的可通行位置
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --check examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

Windows cmd：

```bat
REM 1. 教学图
strat mapinfo assets/base_maps/sdjx_te.SC2Map

REM 2. 天梯图（文件名有空格，加引号）
strat mapinfo "assets/base_maps/Agna Valley-1.SC2Map"

REM 3. 只打印地形网格
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --grid-only

REM 4. 把地形描述保存成文件
strat mapinfo assets/base_maps/arid_plateau.SC2Map -o build/mapinfo/arid_plateau.txt

REM 5. 检查一个 .strat 的所有坐标是否落在这张图的可通行位置
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --check examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

## strat parse

**解析源码，查看 AST（第 1 层）。** 两套解析器（Lark、ANTLR）默认都会跑一遍并比对结果。

Linux / macOS（bash、zsh）：

```bash
# 1. 打印 AST 摘要：有哪些实体、阶段、转移
strat parse examples/learning/01_event_redeploy.strat

# 2. 把完整 AST 写成 JSON 文件
strat parse examples/learning/03_typed_feint.strat --json build/parse/03_typed_feint.ast.json

# 3. 完整 AST 直接打印到屏幕（- 表示标准输出）
strat parse examples/stratagems/sdjx_18_enter_signal.strat --json -

# 4. 只用 ANTLR 解析器
strat parse examples/learning/04_petri_sync_counter.strat --frontend antlr

# 5. 跳过两套解析器的比对（更快）
strat parse examples/demos/cerulean_lure_zerg_vs_protoss.strat --no-agreement
```

Windows PowerShell：

```powershell
# 1. 打印 AST 摘要：有哪些实体、阶段、转移
strat parse examples/learning/01_event_redeploy.strat

# 2. 把完整 AST 写成 JSON 文件
strat parse examples/learning/03_typed_feint.strat --json build/parse/03_typed_feint.ast.json

# 3. 完整 AST 直接打印到屏幕（- 表示标准输出）
strat parse examples/stratagems/sdjx_18_enter_signal.strat --json -

# 4. 只用 ANTLR 解析器
strat parse examples/learning/04_petri_sync_counter.strat --frontend antlr

# 5. 跳过两套解析器的比对（更快）
strat parse examples/demos/cerulean_lure_zerg_vs_protoss.strat --no-agreement
```

Windows cmd：

```bat
REM 1. 打印 AST 摘要：有哪些实体、阶段、转移
strat parse examples/learning/01_event_redeploy.strat

REM 2. 把完整 AST 写成 JSON 文件
strat parse examples/learning/03_typed_feint.strat --json build/parse/03_typed_feint.ast.json

REM 3. 完整 AST 直接打印到屏幕（- 表示标准输出）
strat parse examples/stratagems/sdjx_18_enter_signal.strat --json -

REM 4. 只用 ANTLR 解析器
strat parse examples/learning/04_petri_sync_counter.strat --frontend antlr

REM 5. 跳过两套解析器的比对（更快）
strat parse examples/demos/cerulean_lure_zerg_vs_protoss.strat --no-agreement
```

## strat check

**语义检查（第 3 层）。** 默认是严格模式：保证生成的地图在 SC2 里可执行。有错误时退出码为 1。

Linux / macOS（bash、zsh）：

```bash
# 1. 严格检查一个入门例子，期望 [OK] no diagnostics
strat check examples/learning/01_event_redeploy.strat

# 2. 同时输出计策模式的证明报告（Feint 的三条义务）
strat check examples/learning/03_typed_feint.strat --pattern-report

# 3. 检查一条计策范例（关门捉贼，Trap 模式）
strat check examples/stratagems/gmzz_18_enter_signal.strat --pattern-report

# 4. 看一个严格模式下报错的文件：会列出 E005 / E007 / E008，退出码 1
strat check tests/fixtures/seeds/dhls.strat

# 5. 同一个文件用宽松模式：只做基本检查，可以通过（宽松模式打出的地图不保证能跑）
strat check tests/fixtures/seeds/dhls.strat --loose
```

Windows PowerShell：

```powershell
# 1. 严格检查一个入门例子，期望 [OK] no diagnostics
strat check examples/learning/01_event_redeploy.strat

# 2. 同时输出计策模式的证明报告（Feint 的三条义务）
strat check examples/learning/03_typed_feint.strat --pattern-report

# 3. 检查一条计策范例（关门捉贼，Trap 模式）
strat check examples/stratagems/gmzz_18_enter_signal.strat --pattern-report

# 4. 看一个严格模式下报错的文件：会列出 E005 / E007 / E008，退出码 1
strat check tests/fixtures/seeds/dhls.strat

# 5. 同一个文件用宽松模式：只做基本检查，可以通过（宽松模式打出的地图不保证能跑）
strat check tests/fixtures/seeds/dhls.strat --loose
```

Windows cmd：

```bat
REM 1. 严格检查一个入门例子，期望 [OK] no diagnostics
strat check examples/learning/01_event_redeploy.strat

REM 2. 同时输出计策模式的证明报告（Feint 的三条义务）
strat check examples/learning/03_typed_feint.strat --pattern-report

REM 3. 检查一条计策范例（关门捉贼，Trap 模式）
strat check examples/stratagems/gmzz_18_enter_signal.strat --pattern-report

REM 4. 看一个严格模式下报错的文件：会列出 E005 / E007 / E008，退出码 1
strat check tests/fixtures/seeds/dhls.strat

REM 5. 同一个文件用宽松模式：只做基本检查，可以通过（宽松模式打出的地图不保证能跑）
strat check tests/fixtures/seeds/dhls.strat --loose
```

## strat graph

**画出计划。** 输出 PlanGraph 和 Petri 网的 DOT、SVG、Mermaid、JSON、PNML。SVG 需要 Graphviz（`conda install -c conda-forge graphviz`），没有时只有文本格式。

Linux / macOS（bash、zsh）：

```bash
# 1. 最简单的线性计划
strat graph examples/learning/01_event_redeploy.strat -o build/graph/01

# 2. 看 join 汇合长什么样
strat graph examples/learning/02_join_and_counter.strat -o build/graph/02

# 3. Petri 网写法：多输入弧、带权弧
strat graph examples/learning/04_petri_sync_counter.strat -o build/graph/04

# 4. 分叉陷阱（上屋抽梯）
strat graph examples/petri/swct_fork_trap.strat -o build/graph/swct_fork

# 5. 用 ANTLR 前端解析后再画（结果应和 Lark 相同）
strat graph examples/stratagems/wwjz_18_enter_signal.strat --frontend antlr -o build/graph/wwjz
```

Windows PowerShell：

```powershell
# 1. 最简单的线性计划
strat graph examples/learning/01_event_redeploy.strat -o build/graph/01

# 2. 看 join 汇合长什么样
strat graph examples/learning/02_join_and_counter.strat -o build/graph/02

# 3. Petri 网写法：多输入弧、带权弧
strat graph examples/learning/04_petri_sync_counter.strat -o build/graph/04

# 4. 分叉陷阱（上屋抽梯）
strat graph examples/petri/swct_fork_trap.strat -o build/graph/swct_fork

# 5. 用 ANTLR 前端解析后再画（结果应和 Lark 相同）
strat graph examples/stratagems/wwjz_18_enter_signal.strat --frontend antlr -o build/graph/wwjz
```

Windows cmd：

```bat
REM 1. 最简单的线性计划
strat graph examples/learning/01_event_redeploy.strat -o build/graph/01

REM 2. 看 join 汇合长什么样
strat graph examples/learning/02_join_and_counter.strat -o build/graph/02

REM 3. Petri 网写法：多输入弧、带权弧
strat graph examples/learning/04_petri_sync_counter.strat -o build/graph/04

REM 4. 分叉陷阱（上屋抽梯）
strat graph examples/petri/swct_fork_trap.strat -o build/graph/swct_fork

REM 5. 用 ANTLR 前端解析后再画（结果应和 Lark 相同）
strat graph examples/stratagems/wwjz_18_enter_signal.strat --frontend antlr -o build/graph/wwjz
```

## strat net

**Petri 网分析（第 3 层）。** 把计划转成 Petri 网，在可达图上检查死锁、有界性和永不触发的转移，结果以 JSON 打印。

Linux / macOS（bash、zsh）：

```bash
# 1. 分析带计数库所的网
strat net examples/learning/04_petri_sync_counter.strat

# 2. 分析带预算库所的佯攻
strat net examples/learning/05_petri_feint_budget.strat

# 3. 同时导出 PNML（可导入其他 Petri 网工具）
strat net examples/petri/cerulean_feint_cycle.strat --pnml build/net/cerulean_feint_cycle.pnml

# 4. 导出展开后的纯 P/T 网
strat net examples/petri/swct_fork_trap.strat --pnml build/net/swct_fork_trap.plain.pnml --plain

# 5. 用第三方库 SNAKES 交叉验证（先装一次 snakes）
python -m pip install snakes
strat net examples/learning/02_join_and_counter.strat --cross-check
```

Windows PowerShell：

```powershell
# 1. 分析带计数库所的网
strat net examples/learning/04_petri_sync_counter.strat

# 2. 分析带预算库所的佯攻
strat net examples/learning/05_petri_feint_budget.strat

# 3. 同时导出 PNML（可导入其他 Petri 网工具）
strat net examples/petri/cerulean_feint_cycle.strat --pnml build/net/cerulean_feint_cycle.pnml

# 4. 导出展开后的纯 P/T 网
strat net examples/petri/swct_fork_trap.strat --pnml build/net/swct_fork_trap.plain.pnml --plain

# 5. 用第三方库 SNAKES 交叉验证（先装一次 snakes）
python -m pip install snakes
strat net examples/learning/02_join_and_counter.strat --cross-check
```

Windows cmd：

```bat
REM 1. 分析带计数库所的网
strat net examples/learning/04_petri_sync_counter.strat

REM 2. 分析带预算库所的佯攻
strat net examples/learning/05_petri_feint_budget.strat

REM 3. 同时导出 PNML（可导入其他 Petri 网工具）
strat net examples/petri/cerulean_feint_cycle.strat --pnml build/net/cerulean_feint_cycle.pnml

REM 4. 导出展开后的纯 P/T 网
strat net examples/petri/swct_fork_trap.strat --pnml build/net/swct_fork_trap.plain.pnml --plain

REM 5. 用第三方库 SNAKES 交叉验证（先装一次 snakes）
python -m pip install snakes
strat net examples/learning/02_join_and_counter.strat --cross-check
```

## strat lower

**生成 Galaxy 地图脚本（第 4 层）。** 产物：`.galaxy`、盟友意图 `agent_intents.json`、计划图。不调用编译器，也不打包。

Linux / macOS（bash、zsh）：

```bash
# 1. 最基本的用法
strat lower examples/learning/01_event_redeploy.strat -o build/lower/01

# 2. 带 join 汇合的计划
strat lower examples/learning/02_join_and_counter.strat -o build/lower/02

# 3. 加终局 GameOver：到达终态时结束对局（给 LLM 对战评测用）
strat lower examples/petri/arid_besiege_wei.strat --gameover -o build/lower/arid_go

# 4. --oracle：己方命令也写进地图脚本，地图自己按计划执行
strat lower examples/demos/cerulean_lure_zerg_vs_protoss.strat --oracle -o build/lower/cerulean_oracle

# 5. Petri 网写法的循环佯攻
strat lower examples/petri/sdjx_feint_cycle.strat -o build/lower/sdjx_cycle
```

Windows PowerShell：

```powershell
# 1. 最基本的用法
strat lower examples/learning/01_event_redeploy.strat -o build/lower/01

# 2. 带 join 汇合的计划
strat lower examples/learning/02_join_and_counter.strat -o build/lower/02

# 3. 加终局 GameOver：到达终态时结束对局（给 LLM 对战评测用）
strat lower examples/petri/arid_besiege_wei.strat --gameover -o build/lower/arid_go

# 4. --oracle：己方命令也写进地图脚本，地图自己按计划执行
strat lower examples/demos/cerulean_lure_zerg_vs_protoss.strat --oracle -o build/lower/cerulean_oracle

# 5. Petri 网写法的循环佯攻
strat lower examples/petri/sdjx_feint_cycle.strat -o build/lower/sdjx_cycle
```

Windows cmd：

```bat
REM 1. 最基本的用法
strat lower examples/learning/01_event_redeploy.strat -o build/lower/01

REM 2. 带 join 汇合的计划
strat lower examples/learning/02_join_and_counter.strat -o build/lower/02

REM 3. 加终局 GameOver：到达终态时结束对局（给 LLM 对战评测用）
strat lower examples/petri/arid_besiege_wei.strat --gameover -o build/lower/arid_go

REM 4. --oracle：己方命令也写进地图脚本，地图自己按计划执行
strat lower examples/demos/cerulean_lure_zerg_vs_protoss.strat --oracle -o build/lower/cerulean_oracle

REM 5. Petri 网写法的循环佯攻
strat lower examples/petri/sdjx_feint_cycle.strat -o build/lower/sdjx_cycle
```

## strat compile

**编译成触发器 XML（第 5 层）。** 在 lower 的基础上调用 Galaxy 编译器，生成 `Triggers.xml`、`PlacedObjects.xml`、`TriggerText.txt`。

Linux / macOS（bash、zsh）：

```bash
# 1. 编译一个入门例子
strat compile examples/learning/01_event_redeploy.strat -o build/compile/01

# 2. 编译一条计策范例（调虎离山）
strat compile examples/stratagems/dhls_18_enter_signal.strat -o build/compile/dhls

# 3. 编译天梯图上的人族突袭示例
strat compile examples/demos/cerulean_hellbat_raid.strat -o build/compile/hellbat

# 4. 带终局 GameOver 编译
strat compile examples/petri/cerulean_feint_cycle.strat --gameover -o build/compile/cerulean_cycle_go

# 5. 显式指定编译器目录（默认就是 vendor/galaxy_compiler）
strat compile examples/learning/05_petri_feint_budget.strat --compiler-root vendor/galaxy_compiler -o build/compile/05
```

Windows PowerShell：

```powershell
# 1. 编译一个入门例子
strat compile examples/learning/01_event_redeploy.strat -o build/compile/01

# 2. 编译一条计策范例（调虎离山）
strat compile examples/stratagems/dhls_18_enter_signal.strat -o build/compile/dhls

# 3. 编译天梯图上的人族突袭示例
strat compile examples/demos/cerulean_hellbat_raid.strat -o build/compile/hellbat

# 4. 带终局 GameOver 编译
strat compile examples/petri/cerulean_feint_cycle.strat --gameover -o build/compile/cerulean_cycle_go

# 5. 显式指定编译器目录（默认就是 vendor/galaxy_compiler）
strat compile examples/learning/05_petri_feint_budget.strat --compiler-root vendor/galaxy_compiler -o build/compile/05
```

Windows cmd：

```bat
REM 1. 编译一个入门例子
strat compile examples/learning/01_event_redeploy.strat -o build/compile/01

REM 2. 编译一条计策范例（调虎离山）
strat compile examples/stratagems/dhls_18_enter_signal.strat -o build/compile/dhls

REM 3. 编译天梯图上的人族突袭示例
strat compile examples/demos/cerulean_hellbat_raid.strat -o build/compile/hellbat

REM 4. 带终局 GameOver 编译
strat compile examples/petri/cerulean_feint_cycle.strat --gameover -o build/compile/cerulean_cycle_go

REM 5. 显式指定编译器目录（默认就是 vendor/galaxy_compiler）
strat compile examples/learning/05_petri_feint_budget.strat --compiler-root vendor/galaxy_compiler -o build/compile/05
```

## strat pack

**打包成 .SC2Map（第 6 层）。** 把产物写进底图副本并逐项读回校验。不给 `--base-map` 时按文件名猜底图：`cerulean_*` → cerulean_fall_le，`arid_*` → arid_plateau，`<计策>_*` → `<计策>_te`，其余 jctq_te。

Linux / macOS（bash、zsh）：

```bash
# 1. 自己的文件要显式指定底图
strat pack examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/pack/01

# 2. 按文件名自动选底图（dhls → dhls_te）
strat pack examples/stratagems/dhls_18_enter_signal.strat -o build/pack/dhls

# 3. 天梯图示例（cerulean → cerulean_fall_le）
strat pack examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/pack/cerulean

# 4. 打一张带 GameOver 的对战地图（strat play 的例子会用到）
strat pack examples/petri/arid_besiege_wei.strat --gameover -o build/pack/arid_go

# 5. --oracle + --gameover：地图自己执行计划，作为对照组（strat play --agent plan 用）
strat pack examples/petri/arid_besiege_wei.strat --oracle --gameover -o build/pack/arid_go_oracle
```

Windows PowerShell：

```powershell
# 1. 自己的文件要显式指定底图
strat pack examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/pack/01

# 2. 按文件名自动选底图（dhls → dhls_te）
strat pack examples/stratagems/dhls_18_enter_signal.strat -o build/pack/dhls

# 3. 天梯图示例（cerulean → cerulean_fall_le）
strat pack examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/pack/cerulean

# 4. 打一张带 GameOver 的对战地图（strat play 的例子会用到）
strat pack examples/petri/arid_besiege_wei.strat --gameover -o build/pack/arid_go

# 5. --oracle + --gameover：地图自己执行计划，作为对照组（strat play --agent plan 用）
strat pack examples/petri/arid_besiege_wei.strat --oracle --gameover -o build/pack/arid_go_oracle
```

Windows cmd：

```bat
REM 1. 自己的文件要显式指定底图
strat pack examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/pack/01

REM 2. 按文件名自动选底图（dhls → dhls_te）
strat pack examples/stratagems/dhls_18_enter_signal.strat -o build/pack/dhls

REM 3. 天梯图示例（cerulean → cerulean_fall_le）
strat pack examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/pack/cerulean

REM 4. 打一张带 GameOver 的对战地图（strat play 的例子会用到）
strat pack examples/petri/arid_besiege_wei.strat --gameover -o build/pack/arid_go

REM 5. --oracle + --gameover：地图自己执行计划，作为对照组（strat play --agent plan 用）
strat pack examples/petri/arid_besiege_wei.strat --oracle --gameover -o build/pack/arid_go_oracle
```

## strat route

**部队在底图上的地面路线。** 把计划里每次移动画成地面路径（JSON、SVG；装了 matplotlib 还有 PNG），能看出哪条路要绕坡道、哪条走不通。

Linux / macOS（bash、zsh）：

```bash
# 1. 天梯图上的调虎离山
strat route examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/route/cerulean

# 2. 围魏救赵（Arid Plateau）
strat route examples/petri/arid_besiege_wei.strat -o build/route/arid

# 3. 自己的文件指定底图
strat route examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/route/01

# 4. 不生成 PNG
strat route examples/petri/sdjx_feint_cycle.strat --no-png -o build/route/sdjx_cycle

# 5. --strict：有走不通的路线时退出码为 1（适合检查作业）
strat route examples/demos/cerulean_hellbat_raid.strat --strict -o build/route/hellbat
```

Windows PowerShell：

```powershell
# 1. 天梯图上的调虎离山
strat route examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/route/cerulean

# 2. 围魏救赵（Arid Plateau）
strat route examples/petri/arid_besiege_wei.strat -o build/route/arid

# 3. 自己的文件指定底图
strat route examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/route/01

# 4. 不生成 PNG
strat route examples/petri/sdjx_feint_cycle.strat --no-png -o build/route/sdjx_cycle

# 5. --strict：有走不通的路线时退出码为 1（适合检查作业）
strat route examples/demos/cerulean_hellbat_raid.strat --strict -o build/route/hellbat
```

Windows cmd：

```bat
REM 1. 天梯图上的调虎离山
strat route examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/route/cerulean

REM 2. 围魏救赵（Arid Plateau）
strat route examples/petri/arid_besiege_wei.strat -o build/route/arid

REM 3. 自己的文件指定底图
strat route examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/route/01

REM 4. 不生成 PNG
strat route examples/petri/sdjx_feint_cycle.strat --no-png -o build/route/sdjx_cycle

REM 5. --strict：有走不通的路线时退出码为 1（适合检查作业）
strat route examples/demos/cerulean_hellbat_raid.strat --strict -o build/route/hellbat
```

## strat generate

**用 LLM 生成变体。** 把底图地形和种子策略写进提示词，模型输出后逐层检查，失败就把错误发回去修，通过后打包。例 1 不需要 API key；例 2–5 需要你自己的模型账号（配置见 docs/LLM_GENERATION.md）。用真实模型前先装 SDK：`python -m pip install -e ".[llm]"`。

Linux / macOS（bash、zsh）：

```bash
# 1. 离线演练：用现成文件代替模型回答，验证整条流水线（不需要 API key）
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat \
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp \
  --replay examples/stratagems/dhls_18_enter_signal.strat \
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat

# 2. DeepSeek，用环境变量配置模型和密钥（推荐，密钥不写进命令历史）
export STRAT_LLM_PROVIDER=deepseek
export STRAT_LLM_MODEL=deepseek-flash
export DEEPSEEK_API_KEY=sk-XXXXXXXX
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat \
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp \
  --param ally_race=zerg --param enemy_race=protoss

# 3. Claude，用命令行参数配置；--brief 写设计要求，-n 2 生成两个变体
strat generate --seed examples/stratagems/sdjx_18_enter_signal.strat \
  --base-map "assets/base_maps/Agna Valley-1.SC2Map" --theme feint \
  --provider anthropic --model claude-sonnet-5-5 --api-key sk-ant-XXXXXXXX \
  --brief "声东击西：小队佯攻北侧坡道，主力从南侧绕后" -n 2

# 4. 本地 OpenAI 兼容服务（如 Ollama）；模型不支持工具调用时加 --no-tool-calling
strat generate --seed examples/stratagems/wwjz_18_enter_signal.strat \
  --base-map assets/base_maps/arid_plateau.SC2Map --theme relief \
  --provider ollama --model qwen3:32b --base-url http://localhost:11434/v1 \
  --no-tool-calling --max-repairs 5

# 5. 不给底图：只生成到 XML、不检查坐标、不打包；--no-thinking 关闭思考，更快
export STRAT_LLM_PROVIDER=deepseek
export STRAT_LLM_MODEL=deepseek-flash
export DEEPSEEK_API_KEY=sk-XXXXXXXX
strat generate --seed examples/stratagems/gmzz_18_enter_signal.strat --theme trap --no-thinking \
  --param "enemy_force=4 Stalker + 4 Zealot" -o build/llm/gmzz_draft
```

Windows PowerShell：

```powershell
# 1. 离线演练：用现成文件代替模型回答，验证整条流水线（不需要 API key）
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat `
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp `
  --replay examples/stratagems/dhls_18_enter_signal.strat `
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat

# 2. DeepSeek，用环境变量配置模型和密钥（推荐，密钥不写进命令历史）
$env:STRAT_LLM_PROVIDER = "deepseek"
$env:STRAT_LLM_MODEL = "deepseek-flash"
$env:DEEPSEEK_API_KEY = "sk-XXXXXXXX"
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat `
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp `
  --param ally_race=zerg --param enemy_race=protoss

# 3. Claude，用命令行参数配置；--brief 写设计要求，-n 2 生成两个变体
strat generate --seed examples/stratagems/sdjx_18_enter_signal.strat `
  --base-map "assets/base_maps/Agna Valley-1.SC2Map" --theme feint `
  --provider anthropic --model claude-sonnet-5-5 --api-key sk-ant-XXXXXXXX `
  --brief "声东击西：小队佯攻北侧坡道，主力从南侧绕后" -n 2

# 4. 本地 OpenAI 兼容服务（如 Ollama）；模型不支持工具调用时加 --no-tool-calling
strat generate --seed examples/stratagems/wwjz_18_enter_signal.strat `
  --base-map assets/base_maps/arid_plateau.SC2Map --theme relief `
  --provider ollama --model qwen3:32b --base-url http://localhost:11434/v1 `
  --no-tool-calling --max-repairs 5

# 5. 不给底图：只生成到 XML、不检查坐标、不打包；--no-thinking 关闭思考，更快
$env:STRAT_LLM_PROVIDER = "deepseek"
$env:STRAT_LLM_MODEL = "deepseek-flash"
$env:DEEPSEEK_API_KEY = "sk-XXXXXXXX"
strat generate --seed examples/stratagems/gmzz_18_enter_signal.strat --theme trap --no-thinking `
  --param "enemy_force=4 Stalker + 4 Zealot" -o build/llm/gmzz_draft
```

Windows cmd：

```bat
REM 1. 离线演练：用现成文件代替模型回答，验证整条流水线（不需要 API key）
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat ^
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp ^
  --replay examples/stratagems/dhls_18_enter_signal.strat ^
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat

REM 2. DeepSeek，用环境变量配置模型和密钥（推荐，密钥不写进命令历史）
set "STRAT_LLM_PROVIDER=deepseek"
set "STRAT_LLM_MODEL=deepseek-flash"
set "DEEPSEEK_API_KEY=sk-XXXXXXXX"
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat ^
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp ^
  --param ally_race=zerg --param enemy_race=protoss

REM 3. Claude，用命令行参数配置；--brief 写设计要求，-n 2 生成两个变体
strat generate --seed examples/stratagems/sdjx_18_enter_signal.strat ^
  --base-map "assets/base_maps/Agna Valley-1.SC2Map" --theme feint ^
  --provider anthropic --model claude-sonnet-5-5 --api-key sk-ant-XXXXXXXX ^
  --brief "声东击西：小队佯攻北侧坡道，主力从南侧绕后" -n 2

REM 4. 本地 OpenAI 兼容服务（如 Ollama）；模型不支持工具调用时加 --no-tool-calling
strat generate --seed examples/stratagems/wwjz_18_enter_signal.strat ^
  --base-map assets/base_maps/arid_plateau.SC2Map --theme relief ^
  --provider ollama --model qwen3:32b --base-url http://localhost:11434/v1 ^
  --no-tool-calling --max-repairs 5

REM 5. 不给底图：只生成到 XML、不检查坐标、不打包；--no-thinking 关闭思考，更快
set "STRAT_LLM_PROVIDER=deepseek"
set "STRAT_LLM_MODEL=deepseek-flash"
set "DEEPSEEK_API_KEY=sk-XXXXXXXX"
strat generate --seed examples/stratagems/gmzz_18_enter_signal.strat --theme trap --no-thinking ^
  --param "enemy_force=4 Stalker + 4 Zealot" -o build/llm/gmzz_draft
```

## strat play

**让智能体在地图上对战。** 需要先用 `strat pack --gameover` 打出对战地图（见 pack 例 4、5）。例 1–4 用 `--dry-run` 替身模拟器，不需要游戏；例 5 要装 StarCraft II 和 PySC2（PySC2 需要 Python 3.8–3.10，要另建环境，见 docs/PLAY.md）。结果在 `-o` 目录的 `summary.json`。

Linux / macOS（bash、zsh）：

```bash
# 1. 替身模拟器 + 固定回答，跑通整个流程
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --dry-run --episodes 2 --max-minutes 5 -o build/play/dry

# 2. --sim plan：计划驱动的替身，敌方按计划行动，有简化战斗
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/plansim

# 3. --agent plan：没有智能体，用 oracle 地图让计划自己执行（对照组）
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go_oracle/arid_besiege_wei.SC2Map --agent plan --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/plan

# 4. --agent direct：固定命令、不用计策的基线；--orders 部队:动作[:目标]
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --agent direct --orders raid_force:attack:enemy_home ambush_force:hold --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/direct

# 5. 真机：LLM 知道计划（intents），跑 20 局并保存回放（需要 SC2 + PySC2 + 模型账号）
export SC2PATH=/path/to/StarCraftII
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map \
  --agent intents --provider deepseek --model deepseek-flash --api-key sk-XXXXXXXX \
  --episodes 20 --replays build/play/replays -o build/play/intents
```

Windows PowerShell：

```powershell
# 1. 替身模拟器 + 固定回答，跑通整个流程
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --dry-run --episodes 2 --max-minutes 5 -o build/play/dry

# 2. --sim plan：计划驱动的替身，敌方按计划行动，有简化战斗
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/plansim

# 3. --agent plan：没有智能体，用 oracle 地图让计划自己执行（对照组）
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go_oracle/arid_besiege_wei.SC2Map --agent plan --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/plan

# 4. --agent direct：固定命令、不用计策的基线；--orders 部队:动作[:目标]
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --agent direct --orders raid_force:attack:enemy_home ambush_force:hold --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/direct

# 5. 真机：LLM 知道计划（intents），跑 20 局并保存回放（需要 SC2 + PySC2 + 模型账号）
$env:SC2PATH = "C:\Program Files (x86)\StarCraft II"
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map `
  --agent intents --provider deepseek --model deepseek-flash --api-key sk-XXXXXXXX `
  --episodes 20 --replays build/play/replays -o build/play/intents
```

Windows cmd：

```bat
REM 1. 替身模拟器 + 固定回答，跑通整个流程
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --dry-run --episodes 2 --max-minutes 5 -o build/play/dry

REM 2. --sim plan：计划驱动的替身，敌方按计划行动，有简化战斗
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/plansim

REM 3. --agent plan：没有智能体，用 oracle 地图让计划自己执行（对照组）
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go_oracle/arid_besiege_wei.SC2Map --agent plan --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/plan

REM 4. --agent direct：固定命令、不用计策的基线；--orders 部队:动作[:目标]
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --agent direct --orders raid_force:attack:enemy_home ambush_force:hold --dry-run --sim plan --episodes 2 --max-minutes 5 -o build/play/direct

REM 5. 真机：LLM 知道计划（intents），跑 20 局并保存回放（需要 SC2 + PySC2 + 模型账号）
set "SC2PATH=C:\Program Files (x86)\StarCraft II"
strat play examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map ^
  --agent intents --provider deepseek --model deepseek-flash --api-key sk-XXXXXXXX ^
  --episodes 20 --replays build/play/replays -o build/play/intents
```

## strat llm-pysc2

**生成 LLM-PySC2 任务包。** 打一张 `--gameover` 地图，再写一个任务包 JSON，交给 LLM-PySC2（配套分支 `feature/stratagemdsl-bridge`）运行：每支己方部队一个 LLM 智能体。运行方法见 docs/LLM_PYSC2.md。

Linux / macOS（bash、zsh）：

```bash
# 1. 天梯图示例（虫族 vs 神族）
strat llm-pysc2 examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/llm_pysc2/cerulean

# 2. 围魏救赵（神族）
strat llm-pysc2 examples/petri/arid_besiege_wei.strat -o build/llm_pysc2/arid

# 3. --oracle：地图也执行己方命令，作为“按计划执行”对照组
strat llm-pysc2 examples/petri/arid_besiege_wei.strat --oracle -o build/llm_pysc2/arid_oracle

# 4. 用已经打好的 --gameover 地图，只写任务包（先跑 pack 例 4）
strat llm-pysc2 examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --base-map assets/base_maps/arid_plateau.SC2Map -o build/llm_pysc2/arid_existing

# 5. 观测尺寸要和 LLM-PySC2 运行时一致（默认 128 / 64 / 24）
strat llm-pysc2 examples/demos/cerulean_hellbat_raid.strat --screen 128 --minimap 64 --camera-width 32 -o build/llm_pysc2/hellbat
```

Windows PowerShell：

```powershell
# 1. 天梯图示例（虫族 vs 神族）
strat llm-pysc2 examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/llm_pysc2/cerulean

# 2. 围魏救赵（神族）
strat llm-pysc2 examples/petri/arid_besiege_wei.strat -o build/llm_pysc2/arid

# 3. --oracle：地图也执行己方命令，作为“按计划执行”对照组
strat llm-pysc2 examples/petri/arid_besiege_wei.strat --oracle -o build/llm_pysc2/arid_oracle

# 4. 用已经打好的 --gameover 地图，只写任务包（先跑 pack 例 4）
strat llm-pysc2 examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --base-map assets/base_maps/arid_plateau.SC2Map -o build/llm_pysc2/arid_existing

# 5. 观测尺寸要和 LLM-PySC2 运行时一致（默认 128 / 64 / 24）
strat llm-pysc2 examples/demos/cerulean_hellbat_raid.strat --screen 128 --minimap 64 --camera-width 32 -o build/llm_pysc2/hellbat
```

Windows cmd：

```bat
REM 1. 天梯图示例（虫族 vs 神族）
strat llm-pysc2 examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/llm_pysc2/cerulean

REM 2. 围魏救赵（神族）
strat llm-pysc2 examples/petri/arid_besiege_wei.strat -o build/llm_pysc2/arid

REM 3. --oracle：地图也执行己方命令，作为“按计划执行”对照组
strat llm-pysc2 examples/petri/arid_besiege_wei.strat --oracle -o build/llm_pysc2/arid_oracle

REM 4. 用已经打好的 --gameover 地图，只写任务包（先跑 pack 例 4）
strat llm-pysc2 examples/petri/arid_besiege_wei.strat --map build/pack/arid_go/arid_besiege_wei.SC2Map --base-map assets/base_maps/arid_plateau.SC2Map -o build/llm_pysc2/arid_existing

REM 5. 观测尺寸要和 LLM-PySC2 运行时一致（默认 128 / 64 / 24）
strat llm-pysc2 examples/demos/cerulean_hellbat_raid.strat --screen 128 --minimap 64 --camera-width 32 -o build/llm_pysc2/hellbat
```

## strat export-api

**导出 API 目录。** 把全部谓词、事件、动作的签名导出为 `API_CONTRACTS.md` / `.json`，以及 LLM 生成时用的 `STRATEGY_TOOL.json`。写 `.strat` 时查 API 用。

Linux / macOS（bash、zsh）：

```bash
# 1. 导出到 build/api
strat export-api build/api

# 2. 查看 LLM 生成时模型必须填写的 JSON 结构（STRATEGY_TOOL.json）
strat export-api build/api
cat build/api/STRATEGY_TOOL.json

# 3. 在导出的目录里查某个 API，比如 count_in
strat export-api build/api
grep -n count_in build/api/API_CONTRACTS.md

# 4. 只看某一个 API 的签名、词汇和作用域（直接查第 2 层，不写文件）
python -m stratagemdsl.registry count_in

# 5. 列出全部 API：类别、名字、是否已实现（lowered / unsupported）、签名
python -m stratagemdsl.registry
```

Windows PowerShell：

```powershell
# 1. 导出到 build/api
strat export-api build/api

# 2. 查看 LLM 生成时模型必须填写的 JSON 结构（STRATEGY_TOOL.json）
strat export-api build/api
Get-Content build/api/STRATEGY_TOOL.json

# 3. 在导出的目录里查某个 API，比如 count_in
strat export-api build/api
Select-String -Path build/api/API_CONTRACTS.md -Pattern count_in

# 4. 只看某一个 API 的签名、词汇和作用域（直接查第 2 层，不写文件）
python -m stratagemdsl.registry count_in

# 5. 列出全部 API：类别、名字、是否已实现（lowered / unsupported）、签名
python -m stratagemdsl.registry
```

Windows cmd：

```bat
REM 1. 导出到 build/api
strat export-api build/api

REM 2. 查看 LLM 生成时模型必须填写的 JSON 结构（STRATEGY_TOOL.json）
strat export-api build/api
type build\api\STRATEGY_TOOL.json

REM 3. 在导出的目录里查某个 API，比如 count_in
strat export-api build/api
findstr /n count_in build\api\API_CONTRACTS.md

REM 4. 只看某一个 API 的签名、词汇和作用域（直接查第 2 层，不写文件）
python -m stratagemdsl.registry count_in

REM 5. 列出全部 API：类别、名字、是否已实现（lowered / unsupported）、签名
python -m stratagemdsl.registry
```
