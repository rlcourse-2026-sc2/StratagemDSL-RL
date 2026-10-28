# 用 LLM 在指定底图上生成变体

`strat generate` 把一次完整的变体生成串起来：读取底图地形 → 连同种子策略和你的参数写进提示词 → 调用模型（工具调用，按 schema 约束输出）→ 逐层检查，失败时把具体错误连同模型自己上一次的输出一起发回去修 → 通过后生成 Galaxy、触发器 XML，并打包成基于该底图的 `.SC2Map`。

```text
底图 .SC2Map ──strat mapinfo──▶ 地形描述（尺寸、可玩区域、高地/坡道、障碍、地形网格）
种子 .strat + 主题/brief/--param ─┐
                                  ▼
                       提示词 ──▶ LLM（tool call，JSON 受 schema 约束）
                                  │
          ┌───────────── 修复循环（最多 --max-repairs 次）─────────────┐
          ▼                                                            │
  schema 校验 → 回写 DSL → ANTLR 重解析 → 严格语义检查 → 地形检查 → Galaxy → galaxycc
          │ 任一步失败：错误 + 上一次 JSON 发回模型 ───────────────────┘
          ▼ 全部通过
  打包到底图副本并读回 → build/llm/<种子名>/<变体名>/
```

## 1. 本地环境

```bash
cd StratagemDSL
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e ".[llm]"                      # 额外安装 openai、anthropic 两个 SDK
```

读取底图和打包需要 StormLib，仓库自带两个版本，按系统自动选择：Linux / WSL 用 `assets/native/libstorm.so`，Windows（64 位 Python）用 `assets/native/StormLib.dll`。其他情况用 `STORMLIB_PATH` 指向自己编译的库；库加载不了时也可以改用 `MPQEditor.exe`（设置 `MPQEDITOR_PATH`，自动切换）。详见 `assets/native/README.md`。

## 2. 配置模型

三种方式任选，优先级从高到低：命令行参数 > 环境变量 > 配置文件。

**环境变量**（推荐，密钥不落盘）：

```bash
export STRAT_LLM_PROVIDER=deepseek        # anthropic | openai | deepseek | qwen | moonshot | zhipu | ollama | 其他
export STRAT_LLM_MODEL=deepseek-flash     # 你账号可用的模型名（deepseek-flash / deepseek-v4-pro）
export DEEPSEEK_API_KEY=sk-...            # 或通用的 STRAT_LLM_API_KEY
# 自建或其他 OpenAI 兼容服务：export STRAT_LLM_BASE_URL=http://host:port/v1
```

PowerShell 用 `$env:STRAT_LLM_PROVIDER="deepseek"` 这种写法，cmd 用 `set STRAT_LLM_PROVIDER=deepseek`。

常用的三家：

| 服务 | `STRAT_LLM_PROVIDER` | `STRAT_LLM_MODEL` 示例 | 密钥变量 |
| --- | --- | --- | --- |
| Claude（Anthropic） | `anthropic` | `claude-sonnet-5-5`、`claude-opus-5-5`、`claude-haiku-5-5` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | 你账号可用的模型名，如 `gpt-5.5`、`gpt-6.1-sol` | `OPENAI_API_KEY` |
| DeepSeek | `deepseek` | `deepseek-flash`（快）、`deepseek-v4-pro`（强、慢） | `DEEPSEEK_API_KEY` |

- Claude 新模型（Opus 5.5 起）总是先思考再回答，思考也计入输出上限，所以 `anthropic` 默认 `--max-tokens 32000`，其他服务默认 8096。
- Claude 新模型不接受强制工具调用和非默认 `temperature`；OpenAI 新模型要用 `max_completion_tokens`。客户端会自动适配（被拒的参数去掉后重试），不用手动处理；`--temperature` 保持默认 1.0 最稳。
- DeepSeek V4（`deepseek-flash`、`deepseek-v4-pro`）默认开启思考：一次调用常要几分钟，思考也计入输出上限，所以 `deepseek` 默认 `--max-tokens 32000`。等待期间每 20 秒打印一行进度（已用时间、思考/回答各收到多少字符）。想快一些就加 `--no-thinking`（等价于 `--extra-body '{"thinking": {"type": "disabled"}}'`）。
- 通过中转/代理服务访问时，用 `STRAT_LLM_BASE_URL`（或配置文件的 `baseurl`）指向它：`anthropic` 需要 Anthropic 格式的接口，其余需要 OpenAI 兼容接口。只是网络需要代理时，设置 `HTTPS_PROXY` 即可，两个 SDK 都会使用它。

**配置文件** `~/.stratagemdsl/llm.json`（也兼容 smac-ast 网页端的 `~/.smac_ast/config.json`）：

```json
{
  "default_provider": "deepseek",
  "providers": {
    "deepseek":  {"apikey": "sk-...", "model": "deepseek-v4-pro", "extra_body": {"thinking": {"type": "disabled"}}},
    "anthropic": {"apikey": "sk-ant-...", "model": "claude-sonnet-5-5"},
    "openai":    {"apikey": "sk-...", "model": "gpt-5.5"},
    "local":     {"apikey": "x", "baseurl": "http://localhost:8000/v1", "model": "<本地模型名>"}
  }
}
```

`anthropic` 走 Anthropic SDK；其余名字都按 OpenAI 兼容接口调用。deepseek、qwen、moonshot、zhipu、ollama 已内置默认地址，其他服务需要给 `baseurl` / `--base-url`。模型名必须显式给出。

## 3. 先看模型会拿到什么地形

```bash
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map
strat mapinfo assets/base_maps/cerulean_fall_le.SC2Map --check examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

输出就是提示词里 `[TARGET MAP TERRAIN]` 那一段：可玩区域、按高度划分的平台（每个附带最开阔的点）、连接平台的坡道，以及地形网格（`1/2/3` 为高度层，`/` 坡道，`#` 不可通行，`x` 可能挡路的装饰物）。`--check` 用同一套规则检查一个 `.strat` 的所有坐标。

新底图放到 `assets/base_maps/` 下即可，用 `--base-map` 指向它。坡道编号（R1、R2…）和平台编号（P1、P2…）是每张图各自编的，换图后 `--brief` 里的坐标和编号都要按新图的 `strat mapinfo` 重写；对不上时 `strat generate` 开头会给出 `[WARN]`。

## 4. 生成

```bash
strat generate \
  --seed examples/stratagems/dhls_18_enter_signal.strat \
  --base-map assets/base_maps/cerulean_fall_le.SC2Map \
  --theme zvp_lure \
  --param ally_race=zerg --param enemy_race=protoss \
  --param "enemy_force=4 Stalker + 4 Zealot guarding the Nexus" \
  --brief "调虎离山：小股 Zergling 诱敌下坡，Roach 主力从另一条坡道偷袭 Nexus" \
  -n 3 --max-repairs 3
```

| 参数 | 作用 |
| --- | --- |
| `--seed` | 种子策略。变体保留它的 `intent.pattern`（如 `Lure`），结构和写法以它为范例。建议用通过严格检查的种子：`examples/stratagems/<计策>_18_enter_signal.strat`（十二计策各一个）或 `examples/demos/…` |
| `--base-map` | 目标底图：地形写进提示词、每个 `point_xy` 都按它检查、最后打包到它的副本 |
| `--theme` | 变体标签，会出现在变体名和输出文件名里 |
| `--brief` | 自由文本设计要求 |
| `--param KEY=VALUE` | 结构化设计参数，可重复；以“必须满足”的列表写进提示词（种族、兵力、阈值、时间限制等） |
| `-n` | 生成几个变体（主题自动加 `_1`、`_2`…） |
| `--max-repairs` | 每个变体最多修复几轮（默认 3） |
| `--temperature`、`--max-tokens` | 采样温度（默认 1.0；Claude 新模型和 OpenAI 推理模型只接受默认值，会自动忽略）、单次输出上限（默认 `anthropic` 32000，其他 8096；一个完整策略约 4–6k token） |
| `--loose` | 只做基本语义检查，不做严格 SC2 可执行性检查（不建议用于要打包的变体） |
| `--no-tool-calling` | 模型不支持工具调用时，改为要求输出纯 JSON |
| `--no-thinking` | 关闭模型的思考：deepseek / zhipu 发 `thinking: disabled`，qwen 发 `enable_thinking: false`，openai 改为 `reasoning_effort: low`；Claude 新模型总是思考，不支持 |
| `--extra-body JSON` | 原样合并进 OpenAI 兼容请求体的字段（也可用 `STRAT_LLM_EXTRA_BODY` 或配置文件的 `extra_body`） |
| `--provider/--model/--api-key/--base-url/--config` | 覆盖第 2 节的配置 |
| `-o` | 输出目录，默认 `build/llm/<种子名>/` |

不传 `--base-map` 时不加地形、不检查坐标、也不打包，只到 XML 为止。

## 5. 产物

```text
build/llm/<种子名>/
  prompt_<theme>.txt            实际发给模型的完整提示词
  generation_records.json       每个变体：用了第几次尝试、每次被哪一层拒绝、错误原文、
                                被拒的 JSON（failed_attempts）、地图打包结果
  <变体名>/
    <变体名>.strat              模型产出、回写后的 DSL 源码（可以手改后用 strat pack 重建）
    <变体名>.galaxy / .Triggers.xml / .PlacedObjects.xml / .TriggerText.txt
    <变体名>.agent_intents.json 盟友意图
    <变体名>.SC2Map             打包好的地图（给了 --base-map 时）
    <变体名>.dot / .mmd / .ast.json / .ast.txt
```

挑中的变体可以手改后用 `strat check` / `strat pack --base-map …` 重新检查和打包。

## 6. 不联网先演练

`--replay` 用现成文件代替模型回答，按顺序作为第 1、2… 次尝试的输出，整条链路（包括修复循环和打包）照常执行：

```bash
strat generate --seed examples/stratagems/dhls_18_enter_signal.strat \
  --base-map assets/base_maps/cerulean_fall_le.SC2Map --theme zvp \
  --replay examples/stratagems/dhls_18_enter_signal.strat \
  --replay examples/demos/cerulean_lure_zerg_vs_protoss.strat
```

第一次回答沿用了种子的 `point_id`，会在地形检查被拒；第二次回答全部是 `point_xy`，通过并打包。`tests/llm/test_generate_offline.py` 就是这个场景。

## 7. 在 Python 里调用

```python
from stratagemdsl.llm.config import resolve_provider
from stratagemdsl.llm.pipeline import run_llm_variant
from stratagemdsl import paths

provider = resolve_provider()   # 读环境变量 / 配置文件
record = run_llm_variant(
    provider, "examples/stratagems/dhls_18_enter_signal.strat", "zvp",
    compiler_root=paths.compiler_root(), out_dir="build/llm/demo",
    brief="Designer parameters:\n  - ally_race: zerg\n  - enemy_race: protoss",
    base_map=paths.base_maps_dir() / "cerulean_fall_le.SC2Map", strict=True, max_repairs=3)
print(record["ok"], record.get("name"), record.get("map", {}).get("status"))
```

## 8. 常见问题

| 现象 | 处理 |
| --- | --- |
| `[CONFIG] no API key …` / `no model …` | 按第 2 节补上密钥或模型名 |
| `LLM call failed …` | 检查网络、`base_url`、模型名；OpenAI 兼容服务不支持工具调用时加 `--no-tool-calling` |
| 长时间没有输出 | 思考模型一次调用要几分钟，看每 20 秒一行的进度：`thinking` 表示还在思考，`writing` 表示开始写答案；嫌慢加 `--no-thinking` 或换更快的模型 |
| `output hit max tokens=…` | 思考加答案超过了上限，调大 `--max-tokens`（如 64000），或加 `--no-thinking` |
| 反复在 `terrain` 被拒 | 每条拒绝都附带 `nearest valid spot`，模型会按它修；仍不收敛时调大 `--max-repairs`，或把那个坐标直接写进 `--param` |
| 开头出现 `[WARN] --brief/--param mention (x, y) …` | `--brief` / `--param` 里的坐标不在这张底图上（多半是从别的图抄来的）。坐标、坡道编号都要从这张图的 `strat mapinfo` 输出里取 |
| 反复在 `validate` 被拒 | 换一个通过严格检查的种子；或把具体要求写进 `--param` |
| `Schema validation failed` | 输出被截断时调大 `--max-tokens` |
| 打包失败 / `cannot load StormLib` | 确认 StormLib 能加载（`STORMLIB_PATH`），或设置 `MPQEDITOR_PATH` 改用 MPQEditor.exe；底图不是只读或损坏的文件 |

**边界：** 地形检查依据底图的高度层、坡道和装饰物位置近似判断，编辑器生成的精确寻路数据不在地图文件里；通过检查不等于单位一定能走到。生成、编译和打包通过只说明工具链接受这些产物，战术效果仍需进游戏验证。
