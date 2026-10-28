# StratagemDSL 核心概念与 API 语言手册

按关键字与 API 阅读和编写策略场景

实现基线：本仓库的 StratagemDSL v0.6。每个 API 的签名、作用范围和证据边界以 [docs/api/API_CONTRACTS.md](../api/API_CONTRACTS.md) 为准（可用 `strat export-api DIR` 从源码重新导出）。

本手册面向需要阅读、修改和生成 .strat 的研究者与团队成员。读完后应能判断一个名字属于哪类语言元素，知道哪些语句改变执行、哪些参与检查、哪些只保存意图，并能沿源码追到 Galaxy 产物。

当前语言通过 world 描述实体，通过 intent 和 pattern 描述目标与模式，通过 PlanGraph 描述阶段和转换，通过 binding 映射到 SC2。调用签名、作用范围和证据边界由 `src/stratagemdsl/registry/contracts.py` 唯一注册并导出；具体绑定及使用位置仍需严格检查。

## 01 阅读路线与概念地图

| 学习任务 | 先查的语言入口 | 随后检查 |
| --- | --- | --- |
| 辨认代码中的名字 | 第 02 节关键字与命名空间 | 第 03 节文件骨架与类型 |
| 定义部队和地图区域 | 第 04 至 06 节 world 属性 binding | 出生点归属 数量 区域几何 |
| 表达目标和局部战术条件 | 第 07 节 intent semantics derive | 第 11 节谓词与指标 |
| 编排条件反应与同步 | 第 08 至 10 节 phase transition join | 第 12 至 13 节事件和动作 |
| 判断计策结构是否成立 | 第 14 节 pattern 与战略关系 | 第 15 节检查能力与边界 |
| 调试生成结果 | 第 16 至 18 节 lowering 示例和运行 | 第 19 节源码与案例反向索引 |

| 概念层 | 目前代码中的表示 | 对后续流程的作用 |
| --- | --- | --- |
| 战略实体与职责 | force asset region route 及属性 | 建立符号和类型；role 当前仅保存在属性中 |
| 战略目标与关系 | intent pattern 显式角色绑定 | 检查表达式和有限模式义务 |
| 状态抽象 | semantics 中的 derive | 定义 Bool/Int/Float 表达式别名；使用时展开 |
| 执行调度 | plan phase transition join | 生成阶段状态、事件触发和条件轮询 |
| 执行词汇 | 谓词 事件 动作 API | 按签名检查；受支持的用法进入后端 |
| 环境表示 | binding sc2 及构造器 | 解析为单位组、圆形区域和坐标 |
| 后端产物 | Galaxy Trigger XML Objects SC2Map | 支持代码和地图工件生成；游戏效果须另行实测 |

阅读约定：后文“支持 lowering”表示代码中存在相应生成规则，仍须满足参数及上下文限制；“仅静态”表示有签名但不能直接用于运行时 guard；“元信息”表示保存用于说明或工具处理。片段示例需要放入对应块中；完整案例见 `examples/learning/`（01–03 为基础写法，04、05 为 Petri 写法）和 `examples/stratagems/`（十二计策各一例）。

## 02 关键字与命名空间

```strat
force scouts { side = ally; role = "decoy"; }
// force 是声明关键字；scouts 是用户命名的实体。
// side 和 role 是属性名；ally 是属性值。
// "decoy" 是字符串，当前不会自动形成诱敌行为。
// move 是内置动作 API；gate 是另一个已声明的实体。
// 下句应写在 phase 或 transition 的 do 块中。
move(scouts, gate);
```

| 名字类别 | 例子 | 由谁解释 |
| --- | --- | --- |
| 语法关键字 | world phase on when | StratagemDSL.lark 或生成的 ANTLR 解析器 |
| 内置 API 名 | count enter attack | api_contracts.py 的签名经 builtins.py 供检查器与 Galaxy 后端使用 |
| 属性名 | side role initial under_construction | 属性字典；只有消费者读取的字段才生效 |
| 绑定构造器及参数 | unit_group point_xy owner spawn | BindingResolver 按名称读取 |
| 模式库名称 | Feint Lure | pattern_library.py 与 PatternChecker |
| 用户定义名称 | scouts gate exposed phase_a | 声明后经符号表解析；名称本身不赋予行为 |
| 后端标识 | sc2 | binding 后面的 NAME；本手册针对 Galaxy 后端 |
| 战略本体术语 | Belief Induce Exploit | Python 概念注册表；不是可直接调用的 .strat API |

当前 bootstrap 文法中共有 43 个字母形式的固定语法词。下表是这些语法词的完整索引；它不是“在所有位置都禁止用作标识符”的全局保留字规范。为便于阅读，应避免用关键字或 API 名重新命名实体。

| 类别 | 关键字 | 作用 |
| --- | --- | --- |
| 文件与实体 | strategy world force asset region route | 定义场景与四类世界对象 |
| 初始事实与意图 | initial intent pattern primary secondary success failure | 声明假设、模式、目标和结果条件 |
| 派生状态 | semantics derive | 给 Bool、Int 或 Float 表达式命名 |
| 计划与阶段 | plan start phase purpose actors focus | 组织计划图和阶段信息 |
| 阶段契约与结束 | entry invariant exit terminal | 前三者目前没有运行时监控；terminal 标记结果 |
| 动作块 | do sequence parallel | 列出动作；sequence 对同一主体后续命令入队，parallel 对每个命令执行 Replace |
| 转换 | transition on when priority | 事件、条件和分支优先级 |
| 汇合 | join all any atleast | 等待若干输入到达 |
| 环境绑定 | binding | 绑定世界实体与环境对象 |
| 逻辑与常量 | and or not implies true false | 逻辑表达式和布尔字面量 |

表达式 API 使用位置参数，例如 attack(main, base)。绑定构造器可以使用命名参数，例如 unit_group(owner=1, unit_type="Marine", count=4, spawn=point_xy(20, 30))。二者的实参文法不同，不能把 attack(actor=main, target=base) 当作当前合法语法。注释支持 // 单行和 /* 多行 */。字符串使用双引号。

## 03 文件骨架与类型

```strat
strategy ScenarioName {
  world { /* 实体声明 */ }
  initial { /* 可选 布尔事实 */ }
  intent {
    /* 可选 pattern 与角色绑定 */
    primary true;
    /* 可选 secondary */
    success true;
    failure false;
  }
  semantics { /* 可选 derive */ }
  plan { /* start 阶段或汇合 转换 */ }
  binding sc2 { /* 分析时可省略 执行时需完整绑定 */ }
}
```

这是结构示意，省略号和注释中的内容需要补齐；true/false 只用于展示语法位置。正式案例应写可观察目标。顶层顺序固定为 world、可选 initial、intent、可选 semantics、plan、可选 binding。phase 内字段、transition 内字段也按文法顺序排列；当前不是任意顺序的键值对象。

| 类型 | 声明或来源 | 兼容关系 |
| --- | --- | --- |
| Force | force F | 属于 Entity；可作为动作主体和部队计数对象 |
| Asset | asset A | 属于 Entity；基地、建筑或目标单位 |
| Region | region R | 属于 Location；目前 SC2 执行使用 circle |
| Route | route T | 属于 Location；存在类型，尚无路径跟随 lowering |
| Bool | 谓词 逻辑运算 derive | when 与目标表达式要求 Bool |
| Int Float | 数值字面量和指标 | Int 可匹配 Float 或 Number；Float 可匹配 Number |
| String | 双引号字符串 | 能力或模式名称等参数 |

Entity、Location、Force 等大写名字是检查器内部的类型名称。你写的是 force squad，不是 Force squad。Region 不属于 Entity，因此 attack(squad, region_name) 类型不匹配；移动到区域用 move，攻击目标实体用 attack。Any 是检查器的宽类型，事件和动作签名返回 Any 不表示它们可以任意嵌入 when。

数值与逻辑运算支持 + - * /、== != < <= > >=、not and or implies。按当前文法，not 属于较高优先级的一元运算；复杂条件建议写成 not (count(F) < 2)，避免误解。derive 可以定义 Bool、Int 或 Float，例如 `derive power = count(F);`，引用时按类型检查并展开。

## 04 world 与实体声明

```strat
world {
  force scouts { side = ally; role = "decoy"; }
  force defenders { side = enemy; }
  asset base { side = enemy; role = "protected_target"; }
  region gate { role = "observation_zone"; }
  route bypass;
}
```

force 是按部队处理的实体集合，asset 是可保护或攻击的对象，region 是有战略意义的区域，route 是路线抽象。名字负责建立后续引用关系；单靠声明不会创建 SC2 单位或区域。具体数量、兵种、玩家和坐标在 binding 中给出。上面的 route 用于说明类型；若要实际 move(..., bypass)，当前后端会因为缺少目标点 lowering 而失败。

| 声明 | 在 AST 中 | Galaxy 表示 |
| --- | --- | --- |
| force scouts | EntityDecl("force", "scouts", properties) | 静态绑定通常成为 unitgroup；动态绑定生成实时查询 |
| asset base | EntityDecl("asset", "base", properties) | 当前也用 unitgroup 包装，通常含一个单位 |
| region gate | EntityDecl("region", "gate", properties) | circle 绑定生成 region 与 RegionCircle |
| route bypass | EntityDecl("route", "bypass", properties) | 保留在战略模型中；不生成可跟随路线 |

静态检查会发现实体重复声明、未声明引用和 API 参数类型不符。它不会因为名字叫 defenders 就自动推断敌方，也不会因为名字叫 base 就自动设置建筑类型。

## 05 属性与辅助语义

| 字段或位置 | 当前读取方式 | 实际效果 |
| --- | --- | --- |
| side = ally / enemy / neutral | 检查器检查取值并对未知值警告；后端读取 | 决定动作是否由环境脚本发出，并参与部分表达式处理 |
| role = "decoy" | 存于 properties；可往返序列化 | 实体 role 目前不驱动角色检查或 Galaxy 生成 |
| initial = false | world 中单位实体的属性 | 静态部队在 gf_Spawn 中先保持为空；默认 true |
| under_construction = true | 单位实体属性或 composition 子项 | 单位创建标志设置为 c_unitCreateConstruct |
| purpose "..." | 检查非空字符串 | 阶段说明；无直接执行代码 |
| actors [F] | 检查名字存在且属于 Force | 描述参与者；不会自动填入动作，也未强制核对每条动作主体是否列出 |
| focus [A, R] | 检查名字存在且是 Entity 或 Location | 描述关注对象；不会自动产生目标选择 |
| entry invariant exit | 基础检查要求 Bool | 后端不执行契约；strict_sc2 以 E002 拒绝，需写明确转换 |
| initial { alive(F); } | 基础检查要求各项 Bool | 初始事实说明；不会生成单位或启动时断言 |

side 与 binding.owner 是两个不同字段。side 描述 DSL 阵营，owner 指定 SC2 玩家编号；当前没有完整的一致性检查。常用约定为 ally 对应 owner=1，enemy 对应 owner=2。写出矛盾配置可能仍通过部分检查，所以修改场景时应同时核对。

关于 role 的准确定位：它可以发展成辅助的可检查注解，当前仍为元信息。模式中的 decoy = scouts 属于另一套显式角色绑定，会参与模式检查。实体 role 与模式角色目前没有自动连接。一个实体在不同阶段也可能承担不同职责，因此未来的角色检查需要职责兼容或阶段作用域，不能只按字符串不相等就报错。

实测：本手册三个完整示例删除所有实体 role 后，严格检查诊断和生成的 Galaxy 文本均保持一致。这不代表模式角色绑定可删；删除必需的 pattern 绑定会触发 C091 等诊断。

## 06 binding 与环境对象 API

binding sc2 通过实体名连接世界对象和环境对象。基础检查验证目标存在、绑定是否重复、构造器与实体类别是否匹配；后端再读取实参。构造器文法较宽，不能把“语法能接受的参数名”视为“后端都会使用的参数名”。

```strat
binding sc2 {
  squad = unit_group(owner=1, unit_type="Marine", count=4,
                     spawn=point_xy(20, 30));
  base = unit(owner=2, unit_type="Nexus", at=point_xy(60, 45));
  gate = circle(center=point_xy(50, 40), radius=8);
  __setup__ = setup(terminal_policy="first_wins");
}
```

| 构造器 | 主要参数 | 后端支持与限制 |
| --- | --- | --- |
| unit_group | owner unit_type count spawn；或 composition | 创建静态部队；count 默认 1，需为正整数 |
| unit 或 structure | owner unit_type count at | 用于 asset；同样进入单位创建逻辑，不额外证明兵种一定是建筑 |
| composition 中的 unit | unit_type count；可选 at/spawn under_construction | 继承外层 owner；子项坐标覆盖外层出生点 |
| dynamic_group | owner；可选 unit_type hallucinated | 不生成单位；每次查询当前地图上的匹配存活单位 |
| dynamic_unit | owner；可选 unit_type hallucinated | 用于 asset；当前也是组查询，未保证唯一单位 |
| group_slice | owner unit_type count source | 当前按静态创建处理；没有基于 role 的原部队切片筛选 |
| circle | center radius | RegionCircle；radius 必须为正数 |
| point_xy | x y，或 x=... y=... | Point(x,y)；后续代码生成合成 ObjectPoint |
| point_id | 一个 id，或 id=... | PointFromId(id)；底图必须存在该点 |
| region_id 或 polygon | 基础绑定检查允许名称 | 当前 Galaxy 区域绑定只实现 circle |
| route | route(...) | 保留在模型；当前没有路径点序列的执行生成 |

### 坐标点与预置点

```strat
point_xy(20, 30)
point_xy(x=50.5, y=42.25)
point_id(336436468)
```

```galaxy
Point(20, 30)
Point(50.5, 42.25)
PointFromId(336436468)
```

本手册新增示例全部使用 point_xy，坐标取自 sdjx_te.SC2Map 的真实 Objects。坐标写法消除了预置点 ID 的依赖，但仍需符合对应地图的范围、地形和可达性。把旧 point_id 案例迁移为坐标时，需要先查对应底图的点坐标。

### 静态编组与动态查询

```strat
mixed = unit_group(owner=2,
  composition=[unit(unit_type="Marine", count=3),
               unit(unit_type="Marauder", count=2)],
  spawn=point_xy(40, 40));
illusions = dynamic_group(owner=1, unit_type="Zealot",
                           hallucinated=true);
```

静态组保存创建时加入的成员，适合身份过滤和死亡事件。动态组按玩家、兵种等重新查询，可能包含同玩家的其他部队；当前 dynamic_group 不按 role 划分成员。死亡事件中的 EventUnit 已死亡，动态的存活查询通常找不到它，所以 strict_sc2 拒绝将动态组直接作为 unit_died 的主体。hallucinated=true 增加幻象筛选条件；false 不等于显式排除所有幻象。

### setup 场景设置

```strat
__setup__ = setup(
  terminal_policy="first_wins",
  resources=[minerals(player=1, value=500),
             supplies_made(player=1, value=30)],
  options=[tech_requirements(player=1, enabled=false)]
);
```

| 设置项 | 参数 | 生成方式 |
| --- | --- | --- |
| terminal_policy | "first_wins" 或 "legacy" | 前者生成计划结果锁存；严格模式必须显式声明 |
| minerals | player value | PlayerModifyPropertyInt |
| supplies_made | player value | PlayerModifyPropertyFixed |
| upgrade | player name level=1 | libNtve_gf_SetUpgradeLevelForPlayer |
| creep | region enabled=true | CreepModify，以已绑定圆形区域为范围 |
| remove_behavior | asset name | UnitBehaviorRemove，对组内第一个单位处理 |
| tech_requirements | player enabled=false | TechTreeRequirementsEnable |

resources、options 在上例中是用于装载设置列表的参数名，当前实现遍历 setup 的子构造器；它们不是额外的 DSL 关键字。设置参数缺少完整的统一 Schema 校验，未识别的设置项可能被忽略。当前 MapInit 还会关闭雾与遮罩并默认关闭玩家 1 和 2 的科技要求，复用到需要部分可观测性的任务时必须复核这一行为。

## 07 intent 与 semantics

```strat
intent {
  primary destroyed(base);
  secondary alive(main);
  success destroyed(base);
  failure not alive(main);
}
semantics {
  derive ready = alive(main) and count(main) >= 4;
  derive exposed = count_in(defenders, real_zone) < 2;
}
```

primary 和 secondary 表达研究者希望实现的战略目标，success 和 failure 表达结果条件。基础检查要求它们为 Bool，但没有全局自动监视器去持续检查这些条件。要改变执行，需在 transition.when 中引用相应条件，进入 terminal 阶段。

derive 是场景内 Bool/Int/Float 表达式的命名抽象。引用 ready 时，后端展开其表达式，不生成持久变量或自动记忆。可以前向引用其他 derive，但禁止递归环和与已有符号重名。`derive escaped_units = count_in(main, gate);` 可在目标和 guard 中继续写 `escaped_units >= 2`。它特别适合把抽象的“暴露”“准备就绪”落实成可观察的数量、位置和存活条件。

| 意图 | 可写的定义 | 含义边界 |
| --- | --- | --- |
| 集结完成 | derive assembled = count_in(main, rally) >= 4; | 当前区域内达到数量门槛，不保证阵型和朝向 |
| 防守减少 | derive exposed = count_in(defenders, real_zone) < 2; | 这一已绑定组在区域内的人数减少，不代表所有敌人或总战力 |
| 代价已付出 | derive paid = killed_in(bait, danger) >= 3; | 累计区域死亡达到阈值，不证明牺牲导致收益 |

把一个条件命名为 exposed 不会让检查器自动把它视为已经证明的 DefenseWeakened 事实。当前派生条件用于表达式检查和 guard 展开；模式事实抽取另有固定规则。战略命名与证据之间需要保持清楚对应。

## 08 plan 与 phase

```strat
plan {
  start [feint, monitor];
  phase feint {
    purpose "Observe the decoy approaching";
    actors [decoy];
    focus [fake_target];
    do { move(decoy, trigger_zone); }
  }
  // 其余阶段和转换写在这里
}
```

plan 是显式计划图，start 指定开局激活的阶段。多个 start 表示多个同时活跃的观察或执行分支。phase 的 do 在阶段首次进入时处理；阶段不会因为动作自然完成就自动结束，需要 transition 指定推进条件。默认阶段一轮内只进入一次（后到的 token 被丢弃）；计划图中的环必须经过 `repeatable` 阶段或资源库所（见 10b）。

phase 字段顺序为 purpose、actors、focus、entry、do、invariant、exit、terminal；只有 purpose 在语法中必需。entry、invariant、exit 目前不能依赖它们生成执行约束。严格模式要求改为显式转换或独立监控分支。

| 写法 | 当前效果 | 容易混淆之处 |
| --- | --- | --- |
| do { attack(F,A); } | 进入阶段时处理一个动作 | 不会等待敌人被消灭 |
| do sequence { move(F,R); attack(F,A); } | 同一主体首条 `c_orderQueueReplace`，后续 `c_orderQueueAddToEnd` | 同一动作块内建立命令队列；没有 await、到达确认或跨块自动排队 |
| do parallel { move(F1,R1); move(F2,R2); } | 每条命令各用 `c_orderQueueReplace`；部队可随后同时行动 | 对同一主体重复发令仍会覆盖；没有自动完成屏障 |
| terminal success | 进入终点并在 first_wins 下锁存成功 | 不会自动调用 SC2 胜利 API，也不会自动发 PyMARL reward |

当前后端以构造环境机制为目标：只有动作第一个参数对应 side=enemy 时，才按环境动作发出 Galaxy 命令。ally 的 move、attack 等保留为 MARL 应执行的计划意图，编译流程另行导出 `*.agent_intents.json`（阶段、盟友期望动作序列、焦点、出口观察和终局目标）。这个筛选也作用于 spawn 等动作，不能把 ally 的 spawn 当作通用的脚本增援接口。意图文件不是 agent 可执行策略或自动生成的 reward 函数。

## 09 transition 事件 条件与优先级

```strat
transition redeploy: feint -> observe {
  on enter(decoy, trigger_zone);
  when alive(main);
  do { retarget(defenders, fake_target); }
  priority 10;
}
```

转换字段顺序为 on、when、do、priority。on、when 至少有一个；priority 必填，非负整数。触发时检查源阶段活跃及事件身份过滤，再检查 guard；成立后退出源阶段，处理转换动作，激活目标并处理目标阶段动作。源阶段退出后，竞争的其他出口通常无法再走。

| 转换形式 | Galaxy 调度 | 应怎样理解 |
| --- | --- | --- |
| on enter(F,R) 可再加 when | TriggerAddEventUnitRegion 加身份与阶段条件 | 在区域边界事件发生时检查；不会自动补发阶段激活前的旧事件 |
| 无 on 且 when 为实时条件 | TriggerAddEventTimePeriodic，周期 1.0 游戏秒 | 每次 tick 重新检查，不是每帧连续监测 |
| 无 on 且最高优先级为 when true | 同步展开到前序或初始化代码 | 直接推进；若有更高优先级的实时条件竞争，则作为轮询分支中的兜底 |

`after(600)` 是相对**任务开始**的绝对秒数谓词，等价于 `mission_time() >= 600`，不是 `on after(600)` 事件。写 `transition timeout: watch -> loss { when after(600); priority 0; }` 可在阶段晚于 600 秒激活时也观测到超时；无事件的转换按 1.0 游戏秒检查。要保证 episode 边界，独立的起始观察阶段可一直保持活跃，且终点条件需要和已有失败条件一起写入 `intent.failure`。

priority 数值越小优先级越高。同一源节点的所有出口要求不同 priority；后端会把同源同一事件的分支合并排序，也会把同源无事件的分支合并排序。不同事件触发器之间不形成全局优先级，不能靠两个不同事件的 priority 保证跨触发器先后顺序。

```strat
transition win_edge: active -> win {
  when destroyed(base) and not (not alive(main));
  priority 10;
}
transition loss_edge: active -> loss {
  when not alive(main);
  priority 0;
}
```

此片段对应 intent.success = destroyed(base)、intent.failure = not alive(main)。严格模式的成功边要求显式包含 success 和 not failure。检查器主要做结构匹配，没有通用逻辑等价证明，因此保留 not (not alive(main)) 比手动简化更容易满足当前检查。失败监控也可以用一个独立 start 分支，以覆盖整个计划期间的失败。

## 10 join 与多分支同步

```strat
join ready all;
join first_signal any;
join enough_signals atleast(2);
```

all 等待全部输入边的到达，any 等待至少一个，atleast(k) 等待 k 个。join 自身没有动作块；它必须有输入，且当前要求恰好一个输出转换。后端用整数累计到达并用 fired 标志防止重复释放。

| 结构 | 结果 | 检查或设计要点 |
| --- | --- | --- |
| 两个独立 start 阶段各连 ready all | 可以各完成一次，累计两个到达 | 本手册示例 02 使用此结构 |
| 一个 phase 的两个互斥出口都连 ready all | 同一源先退出，通常不能贡献两个到达 | 可能触发 P023 汇合死锁检查 |
| 信号 A 曾满足，稍后信号 B 满足 | all 可能已收齐历史到达 | 不保证两个状态此刻仍同时成立；在输出边重新检查 |
| any 或 atleast 先满足阈值 | 只释放一次 | 其他已活跃观察分支不会仅因 join 释放就自动全部取消 |

例如“诱饵曾经进入区域”和“守军曾经损失两名”可由 join 记录；实际攻击前还要检查诱饵是否仍在区域、主力是否还活着。join 检查的是同步结构和已到达记录，当前状态是否保持需要新的 when 条件。

## 10b Petri 网写法（v0.6）

计划图在 v0.6 中被编译成一张 Petri 网：阶段和 join 是库所，转换带输入/输出弧。上面各节的写法都是单弧的特例，含义不变；需要并发、计数、预算或循环时可以直接写弧。

```strat
place budget { purpose "extra feints"; initial 2; capacity 2; }
phase feint { purpose "..."; repeatable; do { move(decoy, gate); } }
transition threat: feint -> regroup, pulled { on enter(decoy, gate); priority 10; }   // 一次触发，两个分支
transition again: regroup, budget -> feint { on enter(decoy, home); priority 10; }   // 每次重复消耗一个预算
transition go: wait_strike, ?pulled, !budget -> strike { when alive(allies); priority 10; }
```

| 写法 | 含义 |
| --- | --- |
| `place p { purpose "..."; initial n; capacity c; }` | 纯 token 库所，没有动作，三个字段都可省略但顺序固定 |
| `repeatable;`（紧跟 purpose） | 阶段一轮内可以重复进入；默认一轮只进入一次，后到的 token 被丢弃 |
| `a, b -> c, d` | 同时消耗 a、b 各一个 token，同时产生到 c、d |
| `p*k` | 带权弧 |
| `?p` | 读弧：要求有 token，不消耗 |
| `!p` | 抑制弧：要求 p 为空（`!p*k`：少于 k 个） |
| `tokens(p)`、`active(p)` | 在 `when` 中读取标识；只读标识的无事件转换按即时转换处理 |

消耗同一库所的转换必须有不同的 priority（P009）。环必须经过 repeatable 阶段或资源库所（P031），无容量的库所必须能被证明有界（N001），即时转换不能成环（N030）。检查器在网的可达图上给出 P023、N010（永不触发）、N011（永不标记）、N040（卡住）、N050（无成功路径）等结论；示例见 `examples/learning/04_petri_sync_counter.strat`、`05_petri_feint_budget.strat` 与 `examples/petri/`。

## 11 谓词与指标 API

共 27 个名称，由 `api_contracts.py` 生成 `builtins.FUNCTIONS`。下表以签名为准，F 为 Force，A 为 Asset，E 为 Entity，R 为 Region，L 为 Location，S 为 String。实体实参应写已声明名称。支持列针对表达式需要实际进入 Galaxy 的上下文，例如 transition.when；只写在未执行的 intent 说明里可能不会暴露后端缺口。

| API | 参数与返回 | 当前语义和支持 |
| --- | --- | --- |
| alive | E → Bool | 组内存活数量 > 0 |
| destroyed | E → Bool | 组内存活数量 == 0 |
| defeated | F → Bool | 与 destroyed 一样按数量为 0 判断 |
| relieved | A → Bool | 仅静态；没有运行时解围谓词 |
| at | E, L → Bool | 仅静态；不自动等价于 in_region |
| in_region | E, R → Bool | 支持；至少一个组员在区域内 |
| targeting | F, E → Bool | 仅静态；无当前攻击目标查询 |
| retargeted | F, E → Bool | 仅静态；无自动重定向状态记录 |
| retreating | F → Bool | 仅静态；没有撤退状态查询 |
| threatened | A → Bool | 仅静态；没有威胁观测规则 |
| defense_weakened | A → Bool | 仅静态；须另写可观察 derive |
| support_separated | F, E → Bool | 仅静态；没有支援分离查询 |
| center_passable | R → Bool | 支持；只检查圆形区域中心点通行性，推荐代替旧名 |
| path_passable | R → Bool | 支持；只检查圆形区域中心点通行性 |
| path_connected | R, R → Bool | 支持；`PointPathingIsConnected` 检查两个区域中心的地面连通性 |
| creep_available | R → Bool | 支持；只检查区域中心点菌毯 |
| construction_complete | A → Bool | 支持稳定单单位 asset：当前存活且未在施工；不等于曾发生完工事件 |
| mode_is | E, S → Bool | 仅静态；set_mode 动作可发出不代表有反向查询 |
| count | F → Int | 支持；绑定组中的存活单位数 |
| count_in | F, R → Int | 支持；绑定组在区域内的存活单位数 |
| killed_in | F, R → Int | 支持；累计该组在区域内的死亡数 |
| distance | E, E → Float | 支持；两单位组中心的距离 |
| mission_time | 无 → Float | 支持；`GameGetMissionTime()`，相对任务开始 |
| after | Number → Bool | 支持；任务时间到达非负阈值；不是事件，通常每 1.0 游戏秒复查 |
| strength | F → Float | 仅静态；没有战斗力计算模型 |
| player_unit_count | F → Int | 支持；按绑定 owner 查询全图符合默认筛选的存活单位，不限于绑定部队 |
| apparent_count | F → Int | 兼容旧名，发 W110；等价于 player_unit_count，不代表观察者视野 |

```strat
when alive(main) and count(main) >= 4;
when count_in(defenders, real_zone) < 2;
when alive(main) and alive(defenders)
     and distance(main, defenders) <= 10;
```

distance 的空组风险需要显式 alive 防护，严格模式要求这些条件直接作为合取项出现。当前检查只识别有限表达式形状；它不会自动证明所有逻辑改写等价。in_region 是“至少一个成员”，不能直接用来表达“全军进入”；后者可比较 count_in(F,R) 与 count(F)，并加 alive(F)。

killed_in 会引入死亡监控触发器、计数器及已计数单位集合；在 gf_Spawn 时重置。配合同一死亡事件判断阈值时，后端会处理本次死亡尚未计入或已被监控计入的顺序差异，避免漏算或双计数。它依赖稳定成员身份；动态存活组需要额外设计。

apparent_count(F) 目前没有完整的可见性、观察者或信念模型，不能将其解释为智能体主观看到的精确数量。path_passable(R) 也不证明一条路线端到端可达。`construction_complete(A)` 要求 A 的绑定确实是单个稳定单位；不能把动态查询结果第一项误当成同一建筑。这些名称的语义必须以当前生成规则为准。

## 12 事件 API

共 8 个名称，用在 transition 的 on 中。事件 API 与状态谓词属于不同命名空间：enter 是一次进入事件，in_region 是当前区域内状态。事件注册通常先监听广义 SC2 事件，再使用 UnitGroupHasUnit(group, EventUnit()) 过滤到指定实体。

| 事件 | 参数 | 后端映射 |
| --- | --- | --- |
| enter | Force, Region | 成员进入区域；TriggerAddEventUnitRegion，entering=true |
| leave | Force, Region | 成员离开区域；同一注册 API，entering=false |
| unit_died | Entity[, Force] | 成员死亡；可选第二实参筛选凶手 `libNtve_gf_KillingUnit()`；环境死亡无可归属凶手时不触发二参分支 |
| unit_attacked | Entity[, Force] | 成员受攻击；可选第二实参用 `EventUnitTarget()` 筛选攻击者，不保证受伤 |
| unit_became_idle | Force | `TriggerAddEventUnitBecomesIdle`；组内**一个**单位变空闲，不能证明全组到达 |
| ability_completed | Entity, String | 能力完成；TriggerAddEventUnitAbility，完成阶段 |
| ability_cast | Entity, String | 能力施放；TriggerAddEventUnitAbility，施放阶段 |
| construction_completed | Asset | 建设完成；TriggerAddEventUnitConstructProgress |

```strat
on enter(decoy, trigger_zone);
on unit_died(defenders);
on unit_died(bait, main_force);
on unit_attacked(base, enemy_scouts);
on unit_became_idle(enemy_scouts);
on ability_completed(caster, "ForceField");
```

ability_cast 与 ability_completed 的第二个参数必须是对应游戏数据里的能力标识符。解析成功不会证明兵种具有该能力或满足科技、能量和目标条件。`construction_completed` 是当次完成事件；`construction_complete` 是当前存活单单位的状态查询。多个同型单位组可通过组成员过滤区分；dynamic_group 的范围则取决于动态查询。`on unit_died(bait, main_force)` 表示 bait 组员死亡且本次凶手属于 main_force；`killed_in(bait, danger)` 仍按死亡地点累计，不提供 `by=` 参数。事件和动作的普通调用都只支持位置实参，不能写 `by=...`。

## 13 动作 API

共 13 个名称，用在 phase.do 或 transition.do 中。下面的后端支持均以“动作主体属于 enemy 环境方”为前提；ally 的动作当前不转成命令。F 为 Force，E 为 Entity，A 为 Asset，L 为 Location，R 为 Region，S 为 String。Location 包含 Region 与 Route，但后端目前不能取 route 的目标点。

| 动作 | 参数 | 当前生成行为 |
| --- | --- | --- |
| move | F, L | move 命令至圆形区域中心；Route 不可执行 |
| attack | F, E | attack 命令，目标为实体单位组 |
| hold | F | 映射到 stop 命令；不是完整的驻守策略 |
| retreat | F, L | 映射到 move；无自动路径规划或脱战保证 |
| retarget | F, E | 同 side 目标使用 move 至出生点；不同 side 使用 attack |
| transport | F, F, L | 仅静态；环境侧缺专门 lowering |
| cast | F, S，或 F, S, E/R | 支持无目标、实体组目标和区域中心目标的能力命令 |
| set_mode | E, S | unsieged→Unsiege，sieged→SiegeMode，phasing→PhasingMode；其余原样用作能力名 |
| control | F, F | 仅静态；环境侧缺专门 lowering |
| build | F, A, R | 仅静态；环境侧缺专门 lowering |
| cancel | A | 仅静态；环境侧缺专门 lowering |
| spawn | F, L | 按绑定的兵种数量在指定中心创建并加入原组；仍受 enemy 筛选 |
| block | F, R | 当前固定映射 ForceField 能力目标点命令 |

```strat
retarget(defenders, fake_target);
attack(defenders, main);
set_mode(enemy_tanks, "unsieged");
```

retarget 到同阵营实体时，目标点来自该实体的静态出生绑定，并不持续跟随移动目标。hold 发 stop，block 发 ForceField，retreat 发 move；这些是具体后端约定，不代表完整高层战术控制器。cast 与 set_mode 还需要兵种能力和 SC2 数据验证。

control、transport、build、cancel 出现在盟友计划中时可能通过严格检查，因为该分支不会发出环境命令。这只能说明它们在此处作为 agent 行为描述被保留，不能据此把它们列为已经完成环境侧 lowering 的 API。

## 14 pattern 与战略概念

```strat
pattern Feint {
  decoy = scouts;
  fake_target = main_base;
  defenders = guards;
  main_force = strike_team;
  real_target = expansion;
}
```

pattern 在 intent 内选择模式。绑定左侧是模式库规定的角色参数，右侧是 world 声明的实体名。检查器用这些绑定实例化模式义务，再从 PlanGraph 事件和动作中抽取事实并寻找关联路径。这里的角色绑定确实参与检查，实体 role 字符串仍不参与。

| 参数化模式 | 必需角色 | 检查的关系链 |
| --- | --- | --- |
| Feint | decoy Force；fake_target Asset；defenders Force；main_force Force；real_target Asset | Threat → Relocate → DefenseWeakened → Attack；3 条义务 |
| Lure | bait Force；enemy Force；stronghold Asset；lure_zone Region；relocation_target Region；strike_force Force | Stimulus → Relocate → DefenseWeakened → Attack；3 条义务 |
| IndirectRelief | relief_force Force；pressure_force Force；protected_target Asset；diversion_target Asset | Threat → Relocate → PressureReduced → Attack；3 条义务 |
| Trap | enemy Force；lure 任意；way_out 任意；trap_force Force；objective Entity | Commit → Isolated → Exploit；2 条义务 |
| CovertBypass | covert_force Force；blocker Force；rear_region Region；target Asset | Conceal → Bypass → Attack；2 条义务 |

Trap 的事实来自这几条解释规则：敌方被命令攻击或移动到 lure，或计划观察到敌方进入 lure，得到 Commit(enemy)；对 way_out 施放 block，或把 way_out 处的 Supply Depot 设为 "raised"，得到 Isolated(enemy)；trap_force 攻击 objective，或计划对 objective 的阵亡事件作出反应，得到 Exploit(objective)。关门捉贼绑定 way_out = 其中一个补给站（多扇门时只检查绑定的那一扇），上屋抽梯绑定 way_out = 坡道区域。exit 是关键字，所以角色名用 way_out。

角色检查包括必需项 C091、未知实体 C092、类型 C093、未知角色 C094 和指定角色不能同实体 C095。例如 Feint 要求 fake_target 与 real_target 不同，但当前没有要求 decoy 与 main_force 必定是不同实体。不能把直觉里的所有战术分工都当作已经实现的约束。

只有 pattern Feint; 而没有绑定时，会出现 C090 并跳过参数化模式义务。语料用到但还没有因果定义的名称（见 library.py 的 UNCHECKED_PATTERNS）只做旧的启发式检查（如果有），模式报告显示 NOT CHECKED。其他名称给出警告 C096_PATTERN_UNKNOWN 并提示最接近的已知名称；模式名区分大小写。模式报告的状态有三种：PASS（每条义务都有见证）、FAIL（绑定或义务失败）、NOT CHECKED（未检查任何义务，附原因）。五个参数化模式共 13 条义务，覆盖 12 个计策中的 6 个（Trap 同时用于关门捉贼和上屋抽梯），不等于 12 个计策都具有完整的形式化因果检查。

当前“因果检查”的范围是静态结构证据：事件响应、模式解释规则和 PlanGraph 先后关系形成事实图，然后搜索连接路径。DefenseWeakened 等部分事实来自模式解释，未计算地图遮挡、真实战斗力和对手心理；路径搜索也没有区分所有 relation 种类的强弱。通过检查不证明游戏中策略一定成功，也不证明所有运行轨迹都满足该因果链。

### 本体词汇和可执行语言的边界

strategic_ontology.py 登记了 24 个概念和 12 个战略算子。概念为 Actor、Force、Asset、Region、Route、Capability、Belief、Attention、Suspicion、Trust、Strength、Defense、Supply、Mobility、Cohesion、Morale、Dependency、Alliance、Support、Vulnerability、OpportunityWindow、Risk、Cost、Payoff。算子为 Deceive、Conceal、Induce、Redirect、Weaken、Isolate、Leverage、Substitute、Sacrifice、Delay、Exploit、Withdraw。

这些词汇用于统一战略解释与模式描述，并非 24 种实体声明或 12 个可调用动作。不能直接写 do { Induce(...); }。模式的 composed_from 目前是描述字段，没有把宏自动展开成 PlanGraph 的模板编译器；阶段、事件和动作仍需显式写出。

## 15 语义检查与错误定位

| 检查层 | 主要职责 | 常见诊断 |
| --- | --- | --- |
| 语法解析 | 关键字结构 字段顺序 括号与实参形式 | Parse error |
| 符号和类型 | 声明重名 未知引用 调用位置与参数类型 | S001 T001 T030 T040 T050 T060 T061 |
| 派生条件 | 同名、递归依赖或不支持的结果类型 | D001 D002；Bool/Int/Float 可用 |
| 计划结构 | 起点 转换目标 优先级 无环 可达性 汇合 | P003 P009 P010 P015 P020 P021 P023 |
| 绑定 | 实体是否完整绑定 构造器类别 | B003 B005 B006 |
| 模式角色与结构 | 角色绑定及有限关系义务 | C090 至 C096；C101 等 |
| 严格 SC2 执行检查 | 后端契约 能力 结果竞争 局部矛盾 | E001 至 E010 |
| Galaxy 编译 | 生成代码的类型 API 与 XML 转换 | Galaxy judge 或 codegen 错误 |

| 严格错误 | 含义 | 修正方向 |
| --- | --- | --- |
| E001 | 缺少 first_wins | 在 __setup__ 中声明终点策略 |
| E002 | phase 使用 entry invariant exit | 改为 transition.when 或独立监控 |
| E003 | 起始节点已是 terminal | 通过可观察的转换确认结果 |
| E004 | guard 可证明矛盾或超出固定编组数量 | 核对比较阈值与生成数量 |
| E005 | distance 缺少显式 alive 合取 | 给两个组加存活条件 |
| E006 | dynamic 组直接使用 unit_died | 使用稳定编组或另设计动态死亡观测 |
| E007 | 成功边未显式包含 intent.success | 把目标条件放进同一 guard |
| E008 | 成功边未显式排除 intent.failure | 同时加入 not failure |
| E009 | 同一调度组中后分支被无条件分支遮蔽 | 检查 priority 与兜底顺序 |
| E010 | 实际后端无法生成相应用法 | 核对 API 支持表与绑定限制 |
| E014 | side 与 owner=1/2 阵营约定冲突 | 同步修正实体阵营或玩家编号 |

严格检查还会给出 W101 布尔展开超过 64 分支、W102 `do parallel` 中敌方同一主体多个 Replace 命令互相覆盖、W110 旧 API 别名等警告。`after(-1)` 这类负字面量会报 T080。数量上界检查刻意排除动态查询、显式 spawn 改变编组的情况，并不给累计 killed_in 简单套用初始数量上界。它是有限局部检查，不是完整可满足性求解器。

不要把“无错误”理解为“每个抽象概念已经执行”。注解仍可能不产生代码，盟友动作仍可能留给 agent，部分语义仍依赖模式解释。当前源码中的结果和行为边界应一起阅读。

## 16 从 Strat 到 Galaxy 的 lowering 对照

以下给出七类常见 lowering，每类三个对照。涉及 gv_ 名称的是简化片段，编译器还会加入初始化、身份过滤、阶段条件和冲突消解后的命名；完整生成程序位于 examples 与 build 目录。F/G 表示具体编组，R 表示圆形区域，P 表示阶段。

### 坐标和区域

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| point_xy(20, 30) | Point(20, 30) |
| point_id(336436468) | PointFromId(336436468) |
| circle(center=point_xy(50,40), radius=8) | RegionCircle(Point(50, 40), 8) |

### 部队和成员

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| unit_group(... unit_type="Marine", count=4, spawn=point_xy(20,30)) | libNtve_gf_CreateUnitsWithDefaultFacing(4, "Marine", 0, 1, Point(20, 30)); |
| 将上述创建结果绑定到 F | UnitGroupAddUnitGroup(gv_F, UnitLastCreatedGroup()); |
| dynamic_group(owner=2, unit_type="Zealot") | UnitGroup(UnitTypeFromString("Zealot"), 2, RegionEntireMap(), FILTER, 0) |

### 布尔与数量条件

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| alive(F) | UnitGroupCount(gv_F, c_unitCountAlive) > 0 |
| count_in(F,R) >= 2 | UnitGroupCount(UnitGroupFilterRegion(gv_F, gv_R, 0), c_unitCountAlive) >= 2 |
| derive ready = alive(F);  在 when 中使用 ready | 在使用处展开 alive(F)，不创建名为 ready 的持久状态 |
| derive n = count_in(F,R); when n >= 2; | 校验 Int 后展开为实际 `UnitGroupFilterRegion` 数量比较 |
| when after(600); | `GameGetMissionTime() >= 600`；无 on 转换由周期触发器复查 |

### 事件注册

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| on enter(F,R); | TriggerAddEventUnitRegion(gt_T, null, gv_R, true); |
| on leave(F,R); | TriggerAddEventUnitRegion(gt_T, null, gv_R, false); |
| on unit_died(F); | TriggerAddEventUnitDied(gt_T, null); |
| on unit_attacked(A,F); | TriggerAddEventUnitAttacked2，筛 `EventUnit()` 与 `EventUnitTarget()` |
| on unit_died(A,F); | TriggerAddEventUnitDied，筛 `EventUnit()` 与 `libNtve_gf_KillingUnit()` |
| on unit_became_idle(F); | TriggerAddEventUnitBecomesIdle，筛变空闲的 `EventUnit()` |

### 环境动作

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| attack(enemy, ally) | UnitGroupIssueOrder(gv_enemy, OrderTargetingUnitGroup(AbilityCommand("attack", 0), gv_ally), c_orderQueueReplace); |
| move(enemy, R) | UnitGroupIssueOrder(gv_enemy, OrderTargetingPoint(AbilityCommand("move", 0), Point(x,y)), c_orderQueueReplace); |
| set_mode(enemy_tanks, "unsieged") | UnitGroupIssueOrder(gv_enemy_tanks, Order(AbilityCommand("Unsiege", 0)), c_orderQueueReplace); |
| do sequence { move(enemy,R); attack(enemy,A); } | 同一主体首条 Replace，第二条 `c_orderQueueAddToEnd`；不同主体分别从 Replace 开始 |
| do parallel { move(enemy,R); attack(enemy,A); } | 两条都是 Replace；严格模式警告 W102 |

### 阶段转换调度

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| P -> Q，on enter(F,R) | 每种事件一个触发器（如 gt_react）：先记下此刻已使能且守卫成立的转换，按优先级依次触发（取走 P 的令牌、首次标记 Q 并执行 Q 的环境动作），再运行 gf_net_settle |
| P -> Q，when alive(F) | 轮询转换：所有带实时守卫、无事件的转换共用一个触发器 TriggerAddEventTimePeriodic(gt_net_tick, 1.0, c_timeGame)，守卫成立时触发 |
| P -> Q，when true 且无更高优先级实时竞争 | 立即转换：在 gf_net_settle 里按优先级立刻触发；不为这条边单独注册事件 |

### 汇合和结果状态

| Strat 或输入含义 | Galaxy 或生成机制 |
| --- | --- |
| join J all，两条独立输入 | 每条输入一个库所 gv_net_m_J_in_<来源>；两个库所都有令牌时，同步转换 gf_net_fire_J_sync 一起取走并标记 J |
| killed_in(F,R) >= 3 | 死亡监控更新 gv_killed_in_*；阈值比较读取累计计数 |
| terminal success 且 first_wins | gv_plan_outcome = 1；关闭其他阶段，后续转换受结果状态保护 |

上表 FILTER 表示后端的默认单位筛选表达式，x/y 表示 R.center 的具体坐标。它们是解释用占位符，不是可复制执行的 Galaxy 名字。示例包中的 .galaxy 均为真实编译输出。

## 17 完整示例的学习入口

| 文件 | 重点 | 本次验证 |
| --- | --- | --- |
| examples/learning/01_event_redeploy.strat | 盟友进入区域 → 敌方回防 → 观察目标销毁 | 原教学包双前端、严格语义、Galaxy/XML、地图读回均通过 |
| examples/learning/02_join_and_counter.strat | 两个独立信号 → all 汇合 → 重新检查 → 结果确认 | 同上；包含 killed_in 监控和历史信号复查 |
| examples/learning/03_typed_feint.strat | 五个模式角色 → 三条 Feint 义务 → 敌方机制与盟友意图 | 同上；3 条参数化模式义务均有路径见证 |
| examples/stratagems/dhls_18_enter_signal.strat | 调虎离山：入区信号触发关键阶段、模式角色、成功与失败终态 | 严格检查、Galaxy/XML、地图读回通过；其余 11 个计策同一写法 |

前三例使用 point_xy，按 sdjx_te.SC2Map 底图编写；`examples/stratagems/` 用 point_id（底图预置点），文件名前缀即对应底图（dhls → dhls_te.SC2Map）。测试覆盖到 .SC2Map 内容回读；没有启动 SC2 引擎，也没有检验 agent 是否学会计策。示例的盟友动作不由脚本代替执行。

### 示例一 阅读一个完整策略

```strat
strategy EventRedeploy {
  world {
    force allies { side = ally; role = "main_attack"; }
    force guards { side = enemy; role = "mobile_defense"; }
    asset base { side = enemy; role = "critical"; }
    region gate { role = "observation_zone"; }
  }
  intent {
    primary destroyed(base);
    success destroyed(base);
    failure not alive(allies);
  }
  plan {
    start [approach, fail_watch];
    phase approach {
      purpose "Approach the observation zone";
      actors [allies]; focus [base];
      do { move(allies, gate); }
    }
    phase exploit {
      purpose "Attack while observing the result";
      actors [allies]; focus [base];
      do { attack(allies, base); }
    }
    phase win { purpose "Confirm the objective"; terminal success; }
    phase fail_watch { purpose "Observe allied defeat"; }
    phase loss { purpose "Record failure"; terminal failure; }
    transition react: approach -> exploit {
      on enter(allies, gate);
      when alive(allies);
      do { retarget(guards, base); }
      priority 10;
    }
    transition finish: exploit -> win {
      when destroyed(base) and not (not alive(allies));
      priority 10;
    }
    transition lose: fail_watch -> loss {
      when not alive(allies); priority 0;
    }
  }
  binding sc2 {
    allies = unit_group(owner=1, unit_type="Marine", count=4,
                        spawn=point_xy(25.96, 38.5798));
    guards = unit_group(owner=2, unit_type="Zealot", count=3,
                        spawn=point_xy(36.7597, 49.73));
    base = unit(owner=2, unit_type="Nexus", at=point_xy(54.99, 47.18));
    gate = circle(center=point_xy(54.99, 47.18), radius=8);
    __setup__ = setup(terminal_policy="first_wins");
  }
}
```

建议从 react 转换开始读：on 决定观察事件，when 检查主力还活着，retarget 使 guards 朝同阵营 base 的出生点移动。exploit 中 ally 的 attack 只记录期望行为；finish 通过每秒轮询确认目标已被摧毁且失败条件不成立。独立 fail_watch 覆盖失败结果。

### 示例二 检查历史信号与当前状态

```strat
join ready all;
transition attrition: losses_watch -> ready {
  on unit_died(guards); when losses_observed; priority 10;
}
transition release: ready -> exploit {
  when in_region(allies, gate) and losses_observed and alive(allies);
  priority 10;
}
```

examples/learning/02_join_and_counter.strat 还有来自 approach_watch 的独立输入。打开生成文件，搜索 gv_killed_in、gv_net_m_ready_in_、gf_net_fire_ready_sync 和 gt_net_tick，依次观察计数监控、各条输入的到达库所、汇合的同步转换和实时条件的轮询。

### 示例三 看模式角色怎样参与检查

打开 examples/learning/03_typed_feint.strat，将 pattern Feint 的五个角色对应到七个 world 实体；再沿 induce、exploit、finish 三个转换读取。守军出生点距离 real_zone 中心约 12.58，区域半径设为 15，名义出生点在防区内；induce 要求防区内至少两名守军，exposed 则要求全部三名守军仍存活且防区内少于两名。这样避免“守军原本不在防区”或“守军死亡”被误当成调离，但仍需在 SC2 中观察实际移动，地图打包不证明动作奏效。原教学包 pattern_report.txt 中的三条见证来自指定角色参与的事件、动作及前后关系，属于静态路径证据；world 中的 role 字符串即使删除，仍不改变这些见证或 Galaxy 输出。

## 18 编译命令 产物与调试

在本交付包根目录运行下面的命令。`mkdir -p` 是 Bash 写法；PowerShell 可先手动创建 build 目录。

```bash
mkdir -p build
strat check examples/learning/01_event_redeploy.strat --pattern-report
strat graph examples/learning/01_event_redeploy.strat -o build/example
```

`strat compile` 默认执行严格检查（`--loose` 关闭）。`--compiler-root` 默认为 `vendor/galaxy_compiler`，即包含 galaxy_v5 和 database 的目录；不应只指向 galaxy_v5 子目录。

```bash
strat compile examples/learning/01_event_redeploy.strat -o build/example
```

strat compile 生成 Galaxy、Triggers.xml、PlacedObjects.xml、TriggerText.txt 和 `agent_intents.json`；它自身不负责最终 .SC2Map 打包。

```bash
strat pack examples/learning/01_event_redeploy.strat --base-map assets/base_maps/sdjx_te.SC2Map -o build/example
```

`strat pack` 把产物写入底图副本并逐项读回校验。不给 `--base-map` 时按文件名猜底图（`cerulean_*` → cerulean_fall_le，`arid_*` → arid_plateau，`<计策>_*` → `<计策>_te`，其余 jctq_te），自己写的文件建议总是显式指定。仓库自带 Linux x86-64 与 Windows x64 的 StormLib，其他平台见 `assets/native/README.md`。

| 产物 | 用于回答的问题 |
| --- | --- |
| AST.json | 源代码被解析成什么结构，属性和绑定是否存在 |
| PlanGraph DOT 或 JSON | 哪些阶段同时开始，转换和汇合如何连接 |
| pattern_report.txt | 已绑定模式的哪些义务找到见证 |
| example.galaxy | 实际有哪些部队创建、事件注册、guard 和环境命令 |
| Triggers.xml | Galaxy 如何映射到可编辑的 Trigger 表示 |
| PlacedObjects.xml | point_xy 等需要合成哪些地图对象 |
| TriggerText.txt | 生成触发器相关的文本资源 |
| agent_intents.json | 盟友阶段期望动作、顺序及分支观测；供训练侧自行消费，非可执行 agent |
| example.SC2Map | 打包后的地图；仍需 SC2 运行验证 |
| VERIFICATION.json 与 result.json | 本次各阶段是否通过、警告、计数和地图摘要 |

| 断点位置 | 建议观察 |
| --- | --- |
| frontend.parse_file 或 bootstrap_frontend.parse_file | strategy.world、intent.pattern_bindings、plan.transitions |
| Validator.validate | symbol_types、diagnostic bag、pattern_report |
| BindingResolver.bind_entity | 静态 spawn_components 与动态查询的区别 |
| GalaxyLowerer.emit_action | actor.side 与盟友动作被保留为说明的原因 |
| GalaxyLowerer.emit_transition_guard | derive 展开与 killed_in 本次事件修正 |
| GalaxyLowerer.emit | transition_kinds、notes 与完整 lines |
| compile_galaxy_source | Galaxy AST、judge_result、生成 XML |

## 19 源码与案例反向索引

下表把常见学习问题对应到示例和源码位置。路径均相对 `src/stratagemdsl/`。

| 想学习的概念 | 优先读的文件或词条 | 对应源码 |
| --- | --- | --- |
| 角色注解和模式角色 | 示例 03；role 与 pattern 词条 | core/model.py；semantics/patterns/checker.py |
| 坐标与部队绑定 | 示例 01；point_xy unit_group | backend/galaxy/bindings.py（BindingResolver） |
| 抽象条件落到可观察状态 | 示例 03 exposed；derive count_in | semantics/validator.py；backend/galaxy/expressions.py |
| 条件反应 | 示例 01 react；on enter retarget | backend/galaxy/events.py；backend/galaxy/actions.py |
| 历史信号汇合 | 示例 02 ready；join all | net/（计划 → Petri 网）；backend/galaxy/lowerer.py |
| 牺牲和累计损失 | 示例 02；killed_in | backend/galaxy/lowerer.py |
| 执行契约与成功判定 | 示例 01 finish；terminal | semantics/execution.py |
| 声明过但未实现的 API | 第 11 和 13 节；API 契约导出 | registry/contracts.py 对照 backend/galaxy/ |

`src/stratagemdsl` 是本手册所对应的完整语言源码，`vendor/galaxy_compiler/` 是随仓库提供的 Galaxy 编译器。当前文档没有把尚未实现的 role 检查、模式自动展开、路线跟随或心理状态模型写成已完成能力。

| 源码 | 职责 |
| --- | --- |
| frontend/grammar/StratagemDSL.lark、.g4 | 文法（Lark 与 ANTLR 两套，结果必须一致） |
| frontend/lark_parser.py、antlr_parser.py | 文法树到 AST |
| core/model.py | 实体、意图、派生事实和 PlanGraph 数据结构 |
| registry/contracts.py、builtins.py | 单一契约源：谓词、指标、事件、动作的签名 |
| net/ | 计划 → Petri 网、可达图分析 |
| semantics/validator.py | 符号、类型、图结构、绑定与模式检查入口 |
| semantics/execution.py | 严格 SC2 可执行性检查 |
| semantics/patterns/ | 模式库（library.py）、事实抽取（facts.py）、见证搜索（checker.py）、本体（ontology.py） |
| backend/galaxy/ | 绑定解析和 Galaxy lowering |
| compiler/galaxycc_adapter.py | 调用 Galaxy 编译器 |
| packaging/ | 用 StormLib 写入底图副本并读回 |
| cli.py 与 pipeline.py | `strat` 命令入口、逐层运行与产物输出 |
