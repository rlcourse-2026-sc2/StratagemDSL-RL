# vendor/galaxy_compiler

第三方（smac-ast 项目的）Galaxy 编译器快照，第 5 层 `stratagemdsl.compiler` 通过 `galaxycc_adapter.py` 调用它：

- `galaxy_v5/ANSI-C95_V5.lark`：Galaxy 文法
- `galaxy_v5/galaxycc/`：解析、语义检查（`judge`）与 Trigger/PlacedObjects XML 生成
- `database/symbol_cache.json`：预先生成的 TriggerLibs 符号表

除删去未被引用的 `HTN.py`、`grammar_error.py` 外保持原样。唯一的修改在 `code_gen.py`：修复 GUI 元数据缺失时数字参数无法拼接成文本的问题（只影响 `FunctionCall.text` 的渲染）。galaxycc 有模块级可变状态，批量编译时每个案例应使用独立进程。

可用 `STRAT_COMPILER_ROOT` 指向外部编译器检出目录。
