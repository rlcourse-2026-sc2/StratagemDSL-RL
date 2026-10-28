from __future__ import annotations
from galaxycc import galaxy_ast as ast
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Dict
from pathlib import Path
import json
from .id_json.trigger_xml import FUNC_DEFS, PRESET_GROUPS
from .id_json.trigger_string import FUNC_STRINGS, BR_STRINGS, PRESET_STRINGS, LABEL_STRINGS

def _load(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_base_ids(folder: str):
    folder = Path(folder)
    return (
        _load(folder / "funcdef_id.json"),
        _load(folder / "preset_val_id.json"),
        _load(folder / "prmdef_id.json"),
        _load(folder / "brdef_id.json"),
    )

# FUNCDEF_ID = {}
# PRESET_VAL_ID = {}
# PRMDEF_ID = {}
# BRDEF_ID = {}

ID_COUNT = 0
LOCAL_DICT: Dict[str, str] = {}
GLOBAL_DICT: Dict[str, str | Tuple[str, List[str]]] = {}

POINT_DICT: Dict[Tuple[float, float], Tuple[str, int]] = {}
POINT_LABEL = ""

def reset_codegen_state():
    """每次 convert_xml 前调用，清除上次运行的残留状态"""
    # global FUNCDEF_ID, PRESET_VAL_ID, PRMDEF_ID, BRDEF_ID, ID_COUNT
    # FUNCDEF_ID, PRESET_VAL_ID, PRMDEF_ID, BRDEF_ID = _load_base_ids(path)
    global ID_COUNT, POINT_LABEL
    ID_COUNT = 0
    LOCAL_DICT.clear()
    GLOBAL_DICT.clear()
    POINT_DICT.clear()
    POINT_LABEL = ""

@dataclass
class XMLNode:
    id: str = 'FFFFFFFF'

    def short(self) -> str:
        return ''

    def long(self) -> str:
        return ''
    
    def text(self) -> str:
        return ''

@dataclass
class TriggerData(XMLNode):
    root: List['Item'] = field(default_factory=list)

    def long(self) -> str:
        info = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<TriggerData>',
            '    <Root>',
        ]
        info.extend([node.short() for node in self.root])
        info.append('    </Root>')
        info.extend([node.long() for node in self.root])
        info.append('</TriggerData>')
        return "\n".join(info)

    def text(self) -> str:
        info = [item.text() for item in self.root]
        return "\n\n".join(info)

@dataclass
class Item(XMLNode):
    name: str = ''

@dataclass
class VarDecl(Item):
    type: str = ''
    val: 'ArgDef' = None

    def short(self, is_local: bool = False) -> str:
        if is_local:
            return f'        <Variable Type="Variable" Id="{self.id}"/>'
        else:
            return f'        <Item Type="Variable" Id="{self.id}"/>'

    def long(self) -> str:
        info = [
            f'    <Element Type="Variable" Id="{self.id}">',
            f'        <Identifier>{self.name}</Identifier>',
            f'        <VariableType>',
            f'            <Type Value="{self.type}"/>',
            f'        </VariableType>',
        ]
        if not self.val is None:
            info.append(f'        <Value Type="Param" Id="{self.val.id}"/>')
        info.append('    </Element>')
        if not self.val is None:
            info.append(self.val.long())
        return "\n".join(info)

    def text(self, is_local: bool = False) -> str:
        indent = "        " if is_local else ""
        val = f" = {self.val.text()} " if not self.val is None else " "
        return f"{indent}{self.name}{val}<{self.type}>"

@dataclass
class FunctionDef(Item):
    rettyp: str = ''
    params: List['ParamDef'] = field(default_factory=list)
    locvar: List[VarDecl] = field(default_factory=list)
    stmts:  List['FunctionCall'] = field(default_factory=list)

    def short(self) -> str:
        return f'        <Item Type="FunctionDef" Id="{self.id}"/>'

    def long(self) -> str:
        info = [
            f'    <Element Type="FunctionDef" Id="{self.id}">',
            f'        <Identifier>{self.name}</Identifier>',
            f'        <FlagCall/>',
            f'        <ReturnType>',
            f'            <Type Value="{self.rettyp}"/>',
            f'        </ReturnType>',
        ]
        info.extend([prmdef.short() for prmdef in self.params])
        info.extend([lv.short(True) for lv in self.locvar])
        info.extend([fc.short() for fc in self.stmts])
        info.append('    </Element>')
        info.extend([prmdef.long() for prmdef in self.params])
        info.extend([lv.long() for lv in self.locvar])
        info.extend([fc.long() for fc in self.stmts])
        return "\n".join(info)

    def text(self) -> str:
        info = [
            f"FuncDef: {self.name}",
            f"    Return Type: {self.rettyp}",
            f"    Parameters:",
        ]
        info.extend([prm.text() for prm in self.params])
        info.append("    Local Variables:")
        info.extend([lv.text(True) for lv in self.locvar])
        info.append("    Actions:")
        info.extend([stmt.text(2) for stmt in self.stmts])
        return "\n".join(info)

@dataclass
class Trigger(Item):
    event:  List['FunctionCall'] = field(default_factory=list)
    locvar: List[VarDecl] = field(default_factory=list)
    cond:   List['FunctionCall'] = field(default_factory=list)
    stmts:  List['FunctionCall'] = field(default_factory=list)

    def short(self) -> str:
        return f'        <Item Type="Trigger" Id="{self.id}"/>'

    def long(self) -> str:
        info = [f'    <Element Type="Trigger" Id="{self.id}">']
        info.append(f'        <Identifier>{self.name}</Identifier>')
        info.extend([lv.short(True) for lv in self.locvar])
        info.extend([f'        <Event Type="FunctionCall" Id="{e.id}"/>' for e in self.event])
        info.extend([f'        <Condition Type="FunctionCall" Id="{cond.id}"/>' for cond in self.cond])
        info.extend([f'        <Action Type="FunctionCall" Id="{fc.id}"/>' for fc in self.stmts])
        info.append(f'    </Element>')
        info.extend([lv.long() for lv in self.locvar])
        info.extend([e.long() for e in self.event])
        info.extend([cond.long() for cond in self.cond])
        info.extend([fc.long() for fc in self.stmts])
        return "\n".join(info)

    def text(self) -> str:
        info = [
            f"Trigger: {self.name}",
            f"    Events:",
        ]
        info.extend([e.text(2) for e in self.event])
        info.append("    Local Variables:")
        info.extend(lv.text(True) for lv in self.locvar)
        info.append("    Conditions:")
        info.extend(cond.text(2) for cond in self.cond)
        info.append("    Actions:")
        info.extend(stmt.text(2) for stmt in self.stmts)
        return "\n".join(info)

@dataclass
class ParamDef(XMLNode):
    name: str = ''
    type: str = ''

    def short(self) -> str:
        return f'        <Parameter Type="ParamDef" Id="{self.id}"/>'

    def long(self) -> str:
        info = [
            f'    <Element Type="ParamDef" Id="{self.id}">',
            f'        <Identifier>{self.name}</Identifier>',
            f'        <ParameterType>',
            f'            <Type Value="{self.type}"/>',
            f'        </ParameterType>',
            f'    </Element>',
        ]
        return "\n".join(info)

    def text(self) -> str:
        return f"        {self.name} <{self.type}>"

@dataclass
class Input(XMLNode):
    pass

@dataclass
class ArgDef(XMLNode):
    prm_id: str = ''
    link: Input = None

    def short(self) -> str:
        return f'        <Parameter Type="Param" Id="{self.id}"/>'

    def long(self) -> str:
        lib =  ' Library="Ntve" ' if not self.prm_id.startswith("FFFD") else ' '
        info = [f'    <Element Type="Param" Id="{self.id}">']
        if self.prm_id != '':
            info.append(f'        <ParameterDef Type="ParamDef"{lib}Id="{self.prm_id}"/>',)
        info.append(self.link.short())
        info.append('    </Element>')
        info.append(self.link.long())
        return "\n".join(info)

    def text(self) -> str:
        return self.link.text()

@dataclass
class FunctionCall(Input):
    callee: str = ''
    br_id:  str = ''
    args:   List[ArgDef | FunctionCall] = field(default_factory=list)

    def short(self) -> str:
        return f'        <FunctionCall Type="FunctionCall" Id="{self.id}"/>'

    def long(self) -> str:
        func_id = _lookup_id(self.callee)
        # func_id = GLOBAL_DICT[self.callee][0] if func_id == "" else func_id
        lib =  ' Library="Ntve" ' if not func_id.startswith("FFFF") else ' '
        info = [
            f'    <Element Type="FunctionCall" Id="{self.id}">',
            f'        <FunctionDef Type="FunctionDef"{lib}Id="{func_id}"/>',
        ]
        if self.br_id != '':
            info.append(f'        <SubFunctionType Type="SubFuncType" Library="Ntve" Id="{self.br_id}"/>')
        info.extend([arg.short() for arg in self.args])
        info.append('    </Element>')
        info.extend([arg.long() for arg in self.args])
        return "\n".join(info)

    def text(self, offset: int = 0) -> str:
        indent = " " * offset * 4
        if not self.callee in FUNC_DEFS:
            label = "[Custom] " if offset != 0 else ""
            prm_list = ", ".join(str(arg.text()) for arg in self.args)
            return f"{indent}{label}Call self-defined function {self.callee}({prm_list})"
        label = f'[{LABEL_STRINGS[FUNC_DEFS[self.callee]["label"]]}] ' if offset != 0 else ""
        template = FUNC_STRINGS[FUNC_DEFS[self.callee]["id"]]
        prm_name = FUNC_DEFS[self.callee]["prm_name"]
        # assert len(self.args) == len(prm_name)
        kwargs = {}
        for prm, arg in zip(prm_name, self.args):
            if isinstance(arg, ArgDef):
                kwargs[prm] = arg.text()
        info = [f"{indent}{label}{template.format(**kwargs)}"] if offset != 0 else [f"({indent}{label}{template.format(**kwargs)})"]
        branches = FUNC_DEFS[self.callee]["br_id"]
        for br_id in branches:
            br_name = BR_STRINGS[br_id]
            info.append(f"{indent}    {br_name}:")
            for arg in self.args:
                if isinstance(arg, FunctionCall) and arg.br_id == br_id:
                    info.append(arg.text(offset + 2))
        return "\n".join(info)

@dataclass
class Preset(Input):

    def short(self) -> str:
        return f'        <Preset Type="PresetValue" Library="Ntve" Id="{self.id}"/>'

    def text(self) -> str:
        return PRESET_STRINGS[self.id]

@dataclass
class Param(Input):
    name: str = ''
    
    def short(self) -> str:
        return f'        <Parameter Type="ParamDef" Id="{self.id}"/>'

    def text(self) -> str:
        return self.name

@dataclass
class Var(Input):
    name: str = ''
    
    def short(self) -> str:
        return f'        <Variable Type="Variable" Id="{self.id}"/>'

    def text(self) -> str:
        return self.name

@dataclass
class Value(Input):
    val:    str = ''
    type:   str = ''
    name:   str = ''

    def short(self) -> str:
        info = [
            f'        <Value>{self.val}</Value>',
            f'        <ValueType Type="{self.type}"/>',
        ]
        if self.type == "":
            info = [f'        <Value>{self.val}</Value>',]
        if self.type == "trigger":
            info = [
                f'        <ValueType Type="{self.type}"/>',
                f'        <ValueElement Type="Trigger" Id="{self.val}"/>'
            ]
        if self.type == "point":
            info = [
                f'        <ValueType Type="{self.type}"/>',
                f'        <ValueId Id="{self.val}"/>'
            ]
        return "\n".join(info)

    def text(self) -> str:
        if self.type == "trigger":
            return self.name
        if self.val == "-;Missile,Dead,Hidden":
            return "(Excluded:Missile,Dead,Hidden)"
        return self.val

def convert_xml(ast_node: ast.TranslationUnit) -> XMLNode:
    reset_codegen_state()
    data = TriggerData()
    convert_global(data, ast_node)
    convert_function(data, ast_node)
    convert_trigger(data, ast_node)
    return data

def convert_global(data: TriggerData, ast_node: ast.TranslationUnit):
    init_fn = None
    for decl in ast_node.decls:
        if isinstance(decl, ast.FuncDef) and decl.name == "InitGlobals":
            init_fn = decl
        if not isinstance(decl, ast.VarDecl):
            continue
        # if decl.type_spec.base_name == "trigger":
        #     continue
        data.root.append(create_global(decl))
    init_global(data, init_fn)

def create_global(decl: ast.VarDecl):
    if decl.type_spec.base_name == "trigger":
        assert decl.name.startswith("gt_"), f"At line {decl.line}: Global trigger declaration must start with 'gt_' prefix."
        return Trigger(id=_generate_id(decl.name, is_gt=True), name=decl.name[3:])
    return VarDecl(id=_generate_id(decl.name), name=decl.name, type=decl.type_spec.base_name)

def init_global(data: TriggerData, init_fn: ast.FuncDef):
    if init_fn is None:
        return
    for stmt in init_fn.body:
        assert isinstance(stmt, ast.AssignmentStmt), f"At line {stmt.line}: InitGlobals Function can only have assignment statements, but a {stmt} is presented."
        for node in data.root:
            if isinstance(node, Trigger):
                continue
            assert isinstance(node, VarDecl)
            assert isinstance(stmt.left, ast.Identifier)
            if node.name == stmt.left.name:
                global POINT_LABEL; POINT_LABEL = node.name
                node.val = convert_expression(stmt.right)
                break

def convert_function(data: TriggerData, ast_node: ast.TranslationUnit):
    for decl in ast_node.decls:
        if not isinstance(decl, ast.ForwardDecl):
            continue
        if not decl.name.startswith("gf_"):
            continue
        assert decl.is_func == True
        params = convert_params(decl.params)
        func = FunctionDef(id=_generate_id(decl.name), name=decl.name[3:], rettyp=decl.type_spec.base_name, params=params)
        data.root.append(func)
        GLOBAL_DICT[decl.name] = (func.id, [prm.id for prm in func.params])
        _clear_local()
        # FUNCDEF_ID[decl.name] = func.id
        # PRMDEF_ID[func.id] = [prm.id for prm in func.params]
    for decl in ast_node.decls:
        if not isinstance(decl, ast.FuncDef):
            continue
        if not decl.name.startswith("gf_"):
            continue
        func = None
        for fn in data.root:
            if isinstance(fn, FunctionDef) and fn.name == decl.name[3:]:
                func = fn
                break
        if func is None:
            params = convert_params(decl.params)
            locvar = convert_locvar(decl.body)
            stmts = convert_stmts(decl.body)
            func = FunctionDef(id=_generate_id(decl.name), name=decl.name[3:], rettyp=decl.type_spec.base_name, params=params, locvar=locvar, stmts=stmts)
            data.root.append(func)
            GLOBAL_DICT[decl.name] = (func.id, [prm.id for prm in func.params])
            # FUNCDEF_ID[decl.name] = func.id
            # PRMDEF_ID[func.id] = [prm.id for prm in func.params]
        else:
            prm_names = [prm.name for prm in decl.params]
            prm_ids = GLOBAL_DICT[decl.name][1]
            for prm_name, prm_id in zip(prm_names, prm_ids):
                LOCAL_DICT[prm_name] = prm_id
            func.locvar = convert_locvar(decl.body)
            func.stmts = convert_stmts(decl.body)
        _clear_local()

def convert_params(prm_list: List[ast.ParamDecl]) -> List[ParamDef]:
    params = []
    for prm in prm_list:
        params.append(ParamDef(id=_generate_id(prm.name, True, True), name=prm.name, type=prm.type_spec.base_name))
    return params

def convert_locvar(decl_list) -> List[VarDecl]:
    locvar = []
    for decl in decl_list:
        if not isinstance(decl, ast.VarDecl):
            break
        lv = VarDecl(id=_generate_id(decl.name, True), name=decl.name, type=decl.type_spec.base_name)
        if not decl.init is None:
            lv.val = convert_expression(decl.init)
        locvar.append(lv)
    # init_local()
    for decl in decl_list:
        if isinstance(decl, ast.VarDecl):
            continue
        if isinstance(decl, ast.AssignmentStmt) and decl.op == "=":
            assert isinstance(decl.left, ast.Identifier)
            for lv in locvar:
                assert isinstance(lv, VarDecl)
                if lv.name == decl.left.name:
                    global POINT_LABEL; POINT_LABEL = lv.name
                    lv.val = convert_expression(decl.right)
                    break
        else:
            break
    return locvar

def convert_stmts(stmt_list, offset: int = 0, skip_ret: bool = False) -> List[FunctionCall]:
    stmts = []
    for stmt in stmt_list:
        if not isinstance(stmt, ast.BaseStmt):
            continue
        if offset > 0 and isinstance(stmt, ast.AssignmentStmt):
            assert stmt.op == "="
            continue
        if offset > 0 and isinstance(stmt, ast.BranchStmt):
            offset -= 1
            if not isinstance(stmt.if_br.cond, ast.Identifier):
                offset = 0
            continue
        if skip_ret and isinstance(stmt, ast.ReturnStmt):
            continue
        stmts.append(convert_statement(stmt))
    return stmts

def convert_trigger(data: TriggerData, ast_node: ast.TranslationUnit):
    trigger_dict = {}
    for decl in ast_node.decls:
        if isinstance(decl, ast.VarDecl) and decl.type_spec.base_name == "trigger" and decl.name.startswith("gt_"):
            trigger_dict[decl.name] = {"func": None, "init": None}
        if isinstance(decl, ast.FuncDef) and decl.name.endswith("_Func") and decl.name.startswith("gt_"):
            trigger_dict[decl.name[:-5]]["func"] = decl
        if isinstance(decl, ast.FuncDef) and decl.name.endswith("_Init") and decl.name.startswith("gt_"):
            trigger_dict[decl.name[:-5]]["init"] = decl
    # trigger_list = []
    for name, gt in trigger_dict.items():
        for item in data.root:
            if isinstance(item, Trigger) and item.name == name[3:]:
                gt_func: ast.FuncDef = gt["func"]
                gt_init: ast.FuncDef = gt["init"]
                item.event = convert_event(gt_init.body)
                item.locvar = convert_locvar(gt_func.body)
                item.cond = convert_cond(gt_func.body)
                item.stmts = convert_stmts(gt_func.body, 2, True)
                break
        # trigger_list.append(create_trigger(name, gt["func"], gt["init"]))
    # data.root.extend(trigger_list)

def create_trigger(gt_name: str, gt_func: ast.FuncDef, gt_init: ast.FuncDef) -> Trigger:
    event = convert_event(gt_init.body)
    locvar = convert_locvar(gt_func.body)
    cond = convert_cond(gt_func.body)
    stmts = convert_stmts(gt_func.body, 2, True)
    return Trigger(id=_generate_id(gt_name, is_gt=True), name=gt_name[3:], event=event, locvar=locvar, cond=cond, stmts=stmts)

def convert_event(stmt_list: List[ast.BaseStmt]) -> List[FunctionCall]:
    events = []
    skip = True
    for stmt in stmt_list:
        if skip:
            skip = False
            continue
        if not (isinstance(stmt, ast.FuncCallStmt) and isinstance(stmt.callee, ast.Identifier) and stmt.callee.name.startswith("TriggerAddEvent")):
            continue
        assert isinstance(stmt, ast.FuncCallStmt) and isinstance(stmt.callee, ast.Identifier), f"At line {stmt.line}: Tigger's Init function can only have function call statements for event registration, but a {stmt} is presented."
        assert stmt.callee.name.startswith("TriggerAddEvent"), f"At line {stmt.line}: Can only call event added function in tigger's Init function, but a {stmt.callee.name} function is called."
        args = []
        prmdef = _get_prmdef_id(stmt.callee.name)
        pstdef = _get_preset_group_id(stmt.callee.name)
        for arg, prm_id, pst_id in zip(stmt.args[1:], prmdef, pstdef):
            args.append(convert_expression(arg, prm_id=prm_id, pst_id=pst_id))
        events.append(FunctionCall(id=_generate_id(), callee=stmt.callee.name, args=args))
    return events

def convert_cond(stmt_list) -> List[FunctionCall]:
    for stmt in stmt_list:
        if not isinstance(stmt, ast.BranchStmt):
            continue
        if not isinstance(stmt.if_br.cond, ast.Identifier):
            return []
        cond_list = []
        for item in stmt.if_br.body.items:
            if not isinstance(item, ast.BranchStmt):
                continue
            assert isinstance(item, ast.BranchStmt), f"At line {item.line}: The testCond block of trigger Func can only have pure if-branch statement, but a {item} is presented."
            cond = item.if_br.cond
            if not (isinstance(cond, ast.UnaryOp) and cond.op == "!"):
                cond = ast.UnaryOp(op='!', operand=ast.UnaryOp(op='!', operand=cond))
            cond_list.append(convert_condition(cond.operand))
        return cond_list

def convert_statement(stmt: ast.BaseStmt, br_id: str = '') -> FunctionCall:
    assert not isinstance(stmt, (ast.CompoundStmt, ast.IfStmt, ast.BreakpointStmt)), f"At line {stmt.line}: Converting {stmt} statement is not supported."
    match type(stmt):
        case ast.BranchStmt:
            return convert_branch_statement(stmt, br_id)
        case ast.WhileStmt:
            return convert_while_statement(stmt, br_id)
        case ast.DoWhileStmt:
            return convert_dowhile_statement(stmt, br_id)
        case ast.ForStmt:
            return convert_for_statement(stmt, br_id)
        case ast.AssignmentStmt:
            return convert_assignment_statement(stmt, br_id)
        case ast.FuncCallStmt:
            return convert_funcall_statement(stmt, br_id)
        case ast.ReturnStmt:
            return convert_return_statement(stmt, br_id)
        case ast.BreakStmt:
            return convert_break_statement(stmt, br_id)
        case ast.ContinueStmt:
            return convert_continue_statement(stmt, br_id)
        case _:
            assert False

def convert_compound_statement(stmts: ast.CompoundStmt, br_id: str = '') -> List[FunctionCall]:
    stmt_list = []
    for stmt in stmts.items:
        stmt_list.append(convert_statement(stmt, br_id))
    return stmt_list

def convert_branch_statement(stmt: ast.BranchStmt, br_id: str = '') -> FunctionCall:
    # ForEachSetBitInBitMask ×
    # ForEachUnSetBitInBitMask ×

    # IfThenElse: if ... else ...
    # IfThen: if ... else if ... else if ...
    # Switch: if ... else if ... else if ... else ...
    # Cycle -> IfThenElse
    if_br_id, then_br_id, else_br_id = _get_brdef_id("IfThenElse")
    else_stmts = stmt.else_br if not stmt.else_br is None else ast.CompoundStmt()
    else_br = convert_compound_statement(else_stmts, br_id=else_br_id)
    node = FunctionCall(id=_generate_id(), callee="IfThenElse", br_id=else_br_id, args=else_br)
    for elif_stmts in reversed(stmt.elif_br):
        then_br = convert_compound_statement(elif_stmts.body, br_id=then_br_id)
        node.args.extend(then_br)
        if_br = convert_condition(elif_stmts.cond, br_id=if_br_id)
        node.args.append(if_br)
        node = FunctionCall(id=_generate_id(), callee="IfThenElse", br_id=else_br_id, args=[node])
    then_br = convert_compound_statement(stmt.if_br.body, br_id=then_br_id)
    node.args.extend(then_br)
    if_br = convert_condition(stmt.if_br.cond, br_id=if_br_id)
    node.args.append(if_br)
    node.br_id = br_id
    return node

def convert_while_statement(stmt: ast.WhileStmt, br_id: str = '') -> FunctionCall:
    cond_br_id, body_br_id = _get_brdef_id("While")
    cond_br = convert_condition(stmt.cond, br_id=cond_br_id)
    node = FunctionCall(id=_generate_id(), callee="While", br_id=br_id, args=[cond_br])
    body_br = convert_compound_statement(stmt.body, br_id=body_br_id)
    node.args.extend(body_br)
    return node

def convert_dowhile_statement(stmt: ast.DoWhileStmt, br_id: str = '') -> FunctionCall:
    cond_br_id, body_br_id = _get_brdef_id("While2")
    cond_br = convert_condition(stmt.cond, br_id=cond_br_id)
    node = FunctionCall(id=_generate_id(), callee="While2", br_id=br_id, args=[cond_br])
    body_br = convert_compound_statement(stmt.body, br_id=body_br_id)
    node.args.extend(body_br)
    return node

def convert_for_statement(stmt: ast.ForStmt, br_id: str = '') -> FunctionCall:
    stmt_ = ast.WhileStmt(cond=stmt.cond, body=stmt.body)
    if not stmt.post is None:
        stmt_.body.items.append(stmt.post)
    cond_br_id, body_br_id = _get_brdef_id("While")
    cond_br = convert_condition(stmt_.cond, br_id=cond_br_id)
    node = FunctionCall(id=_generate_id(), callee="While", br_id=br_id, args=[cond_br])
    body_br = convert_compound_statement(stmt_.body, br_id=body_br_id)
    node.args.extend(body_br)
    if not stmt.init is None:
        if_br_id, then_br_id, else_br_id = _get_brdef_id("IfThenElse")
        init = convert_statement(stmt.init, br_id=then_br_id)
        node.br_id = then_br_id
        node = FunctionCall(id=_generate_id(), callee="IfThenElse", br_id=br_id, args=[init]+[node])
    return node

def convert_assignment_statement(stmt: ast.AssignmentStmt, br_id: str = '') -> FunctionCall:
    assert isinstance(stmt.left, ast.Identifier)
    assert stmt.op in {"=", "+=", "-=", "*=", "/="}
    match stmt.op:
        case "=":
            left_prm_id, right_prm_id = _get_prmdef_id("SetVariable")
            left = convert_identifier(stmt.left, prm_id=left_prm_id)
            right = convert_expression(stmt.right, prm_id=right_prm_id)
            return FunctionCall(id=_generate_id(), callee="SetVariable", br_id=br_id, args=[left, right])
        case "+=" | "-=" | "*=" | "/=":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("IncrementReal")
            _, op_pst_id, _ = _get_preset_group_id("IncrementReal")
            left = convert_identifier(stmt.left, prm_id=left_prm_id)
            right = convert_expression(stmt.right, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, stmt.op[0])))
            return FunctionCall(id=_generate_id(), callee="IncrementReal", br_id=br_id, args=[left, op, right])
        case _:
            assert False

def convert_funcall_statement(stmt: ast.FuncCallStmt, br_id: str = '') -> FunctionCall:
    assert isinstance(stmt.callee, ast.Identifier)
    func_name = stmt.callee.name[11:] if stmt.callee.name.startswith("libNtve_gf_") else stmt.callee.name
    _check_special_rules(func_name, stmt)
    prmdef = _get_prmdef_id(func_name)
    pstdef = _get_preset_group_id(func_name)
    assert len(stmt.args) == len(prmdef)
    args = []
    for arg, prm_id, pst_id in zip(stmt.args, prmdef, pstdef):
        args.append(convert_expression(arg, prm_id=prm_id, pst_id=pst_id))
    return FunctionCall(id=_generate_id(), callee=func_name, br_id=br_id, args=args)

def convert_return_statement(stmt: ast.ReturnStmt, br_id: str = '') -> FunctionCall:
    if stmt.value is None:
        return FunctionCall(id=_generate_id(), callee="SkipRemaining", br_id=br_id)
    else:
        [prm_id] = _get_prmdef_id("Return")
        ret_val = convert_expression(stmt.value, prm_id=prm_id)
        return FunctionCall(id=_generate_id(), callee="Return", br_id=br_id, args=[ret_val])

def convert_break_statement(stmt: ast.BreakStmt, br_id: str = '') -> FunctionCall:
    return FunctionCall(id=_generate_id(), callee="StopLooping", br_id=br_id)

def convert_continue_statement(stmt: ast.ContinueStmt, br_id: str = '') -> FunctionCall:
    return FunctionCall(id=_generate_id(), callee="Continue", br_id=br_id)

def convert_condition(cond: ast.BaseExpression, br_id: str = '') -> FunctionCall:
    if cond is None:
        cond = ast.BoolLiteral(value=True)
    if not isinstance(cond, (ast.BinaryOp, ast.UnaryOp)):
        cond = ast.BinaryOp(op="==", left=cond, right=ast.BoolLiteral(value=True))
    assert isinstance(cond, (ast.BinaryOp, ast.UnaryOp))
    assert cond.op in {"!", "&&", "||", "==", "!=", "<", "<=", ">", ">="}
    match cond.op:
        case "!":
            [not_br_id] = _get_brdef_id("Not")
            not_br = convert_condition(cond.operand, br_id=not_br_id)
            return FunctionCall(id=_generate_id(), callee="Not", br_id=br_id, args=[not_br])
        case "&&":
            [and_br_id] = _get_brdef_id("And")
            left_br = convert_condition(cond.left, br_id=and_br_id)
            right_br = convert_condition(cond.right, br_id=and_br_id)
            return FunctionCall(id=_generate_id(), callee="And", br_id=br_id, args=[left_br, right_br])
        case "||":
            [or_br_id] = _get_brdef_id("Or")
            left_br = convert_condition(cond.left, br_id=or_br_id)
            right_br = convert_condition(cond.right, br_id=or_br_id)
            return FunctionCall(id=_generate_id(), callee="Or", br_id=br_id, args=[left_br, right_br])
        case "==" | "!=" | "<" | "<=" | ">" | ">=":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("Comparison")
            _, op_pst_id, _ = _get_preset_group_id("Comparison")
            left = convert_expression(cond.left, prm_id=left_prm_id)
            right = convert_expression(cond.right, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, cond.op)))
            return FunctionCall(id=_generate_id(), callee="Comparison", br_id=br_id, args=[left, op, right])
        case _:
            assert False

def convert_expression(exp: ast.BaseExpression, prm_id: str = '', pst_id: str = '') -> ArgDef:
    assert not isinstance(exp, (ast.ArrayAccess, ast.MemberAccess)), f"At line {exp.line}: Converting {exp} expression is not supported."
    match type(exp):
        case ast.Identifier:
            return convert_identifier(exp, prm_id, pst_id)
        case ast.IntLiteral:
            return convert_int_literal(exp, prm_id, pst_id)
        case ast.FixedLiteral:
            return convert_fixed_literal(exp, prm_id)
        case ast.BoolLiteral:
            return convert_bool_literal(exp, prm_id, pst_id)
        case ast.NullLiteral:
            return convert_null_literal(exp, prm_id, pst_id)
        case ast.StringLiteral:
            return convert_string_literal(exp, prm_id, pst_id)
        case ast.BinaryOp:
            return convert_binary_operation(exp, prm_id)
        case ast.UnaryOp:
            return convert_unary_operation(exp, prm_id)
        case ast.FuncCall:
            return convert_funcall_expression(exp, prm_id)
        case _:
            assert False

def convert_identifier(exp: ast.Identifier, prm_id: str = '', pst_id: str = '') -> ArgDef:
    var_name = exp.name
    id = _lookup_id(var_name)
    if id == "" and pst_id != "" and var_name in PRESET_GROUPS[pst_id]:
        id = PRESET_GROUPS[pst_id][var_name]
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Preset(id=id))
    elif _is_gt(var_name):
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Value(val=id, type="trigger", name=var_name))
    elif _is_param(var_name):
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Param(id=id, name=var_name))
    elif var_name in LOCAL_DICT or var_name in GLOBAL_DICT:
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Var(id=id, name=var_name))
    else:
        assert False, f"At line {exp.line}: Error when converting {var_name} variable."

def convert_int_literal(exp: ast.IntLiteral, prm_id: str = '', pst_id: str = '') -> ArgDef:
    if pst_id != "" and exp.raw in PRESET_GROUPS[pst_id]:
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Preset(id=PRESET_GROUPS[pst_id][exp.raw]))
    return ArgDef(id=_generate_id(), prm_id=prm_id, link=Value(val=exp.raw, type='int'))

def convert_fixed_literal(exp: ast.FixedLiteral, prm_id: str = '') -> ArgDef:
    return ArgDef(id=_generate_id(), prm_id=prm_id, link=Value(val=exp.raw, type='fixed'))

def convert_bool_literal(exp: ast.BoolLiteral, prm_id: str = '', pst_id: str = '') -> ArgDef:
    raw = 'true' if exp.value else 'false'
    if pst_id != "" and raw in PRESET_GROUPS[pst_id]:
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Preset(id=PRESET_GROUPS[pst_id][raw]))
    return ArgDef(id=_generate_id(), prm_id=prm_id, link=Value(val=raw, type='bool'))

def convert_null_literal(exp: ast.NullLiteral, prm_id: str = '', pst_id: str = '') -> ArgDef:
    if pst_id != "" and 'null' in PRESET_GROUPS[pst_id]:
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Preset(id=PRESET_GROUPS[pst_id]['null']))
    return ArgDef(id=_generate_id(), prm_id=prm_id, link=Value(val='null'))

def convert_string_literal(exp: ast.StringLiteral, prm_id: str = '', pst_id: str = '') -> ArgDef:
    if pst_id != "" and exp.value in PRESET_GROUPS[pst_id]:
        return ArgDef(id=_generate_id(), prm_id=prm_id, link=Preset(id=PRESET_GROUPS[pst_id][exp.value]))
    return ArgDef(id=_generate_id(), prm_id=prm_id, link=Value(val=exp.value, type='string'))

def convert_binary_operation(exp: ast.BinaryOp, prm_id: str = '') -> ArgDef:
    node = ArgDef(id=_generate_id(), prm_id=prm_id)
    match exp.op:
        case "+" | "-" | "*" | "/":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("ArithmeticReal")
            _, op_pst_id, _ = _get_preset_group_id("ArithmeticReal")
            left = convert_expression(exp.left, prm_id=left_prm_id)
            right = convert_expression(exp.right, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, exp.op)))
            node.link = FunctionCall(id=_generate_id(), callee="ArithmeticReal", args=[left, op, right])
        case "<<" | ">>" | "&" | "|" | "^":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("ArithmeticInt2")
            _, op_pst_id, _ = _get_preset_group_id("ArithmeticInt2")
            left = convert_expression(exp.left, prm_id=left_prm_id)
            right = convert_expression(exp.right, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, exp.op)))
            node.link = FunctionCall(id=_generate_id(), callee="ArithmeticInt2", args=[left, op, right])
        case "==" | "!=" | "<" | "<=" | ">" | ">=":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("Comparison")
            _, op_pst_id, _ = _get_preset_group_id("Comparison")
            left = convert_expression(exp.left, prm_id=left_prm_id)
            right = convert_expression(exp.right, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, exp.op)))
            node.link = FunctionCall(id=_generate_id(), callee="Comparison", args=[left, op, right])
        case "&&" | "||":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("AndOr")
            _, op_pst_id, _ = _get_preset_group_id("AndOr")
            left = convert_expression(exp.left, prm_id=left_prm_id)
            right = convert_expression(exp.right, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, exp.op)))
            node.link = FunctionCall(id=_generate_id(), callee="AndOr", args=[left, op, right])
        case "%":
            left_prm_id, right_prm_id = _get_prmdef_id("ModI")
            left = convert_expression(exp.left, prm_id=left_prm_id)
            right = convert_expression(exp.right, prm_id=right_prm_id)
            node.link = FunctionCall(id=_generate_id(), callee="ModI", args=[left, right])
        case _:
            assert False
    return node

def convert_unary_operation(exp: ast.UnaryOp, prm_id: str = '') -> ArgDef:
    node = ArgDef(id=_generate_id(), prm_id=prm_id)
    match exp.op:
        case "+":
            node = convert_expression(exp.operand, prm_id=prm_id)
        case "-":
            left_prm_id, op_prm_id, right_prm_id = _get_prmdef_id("ArithmeticReal")
            _, op_pst_id, _ = _get_preset_group_id("ArithmeticReal")
            left = ArgDef(id=_generate_id(), prm_id=left_prm_id, link=Value(val="0", type="int"))
            right = convert_expression(exp.operand, prm_id=right_prm_id)
            op = ArgDef(id=_generate_id(), prm_id=op_prm_id, link=Preset(id=_get_preset_val_id(op_pst_id, "-")))
            node.link = FunctionCall(id=_generate_id(), callee="ArithmeticReal", args=[left, op, right])
        case "!":
            [prm_id] = _get_prmdef_id("AndOrMult2")
            arg = convert_expression(exp.operand, prm_id=prm_id)
            node.link = FunctionCall(id=_generate_id(), callee="AndOrMult2", args=[arg])
        case _:
            assert False
    return node

def convert_funcall_expression(exp: ast.FuncCall, prm_id: str = '') -> ArgDef:
    assert isinstance(exp.callee, ast.Identifier)
    node = ArgDef(id=_generate_id(), prm_id=prm_id)
    # func_name = exp.callee.name
    func_name = exp.callee.name[11:] if exp.callee.name.startswith("libNtve_gf_") else exp.callee.name
    obj = _check_special_rules(func_name, exp)
    if not obj is None:
        node.link = obj
        return node
    prmdef = _get_prmdef_id(func_name)
    pstdef = _get_preset_group_id(func_name, len(prmdef))
    assert len(exp.args) == len(prmdef)
    args = []
    for arg, prm_id, pst_id in zip(exp.args, prmdef, pstdef):
        args.append(convert_expression(arg, prm_id=prm_id, pst_id=pst_id))
    node.link = FunctionCall(id=_generate_id(), callee=func_name, args=args)
    return node

def generate_xml(data: TriggerData) -> tuple[str, str, str]:
    return data.long(), generate_obj(), data.text()

def generate_obj() -> str:
    info = [
        f'<?xml version="1.0" encoding="utf-8"?>',
        f'<PlacedObjects Version="27">',
    ]
    for (x, y), (name, id) in POINT_DICT.items():
        info.append(f'    <ObjectPoint Id="{id}" Position="{x},{y},0" Scale="1,1,1" Type="Normal" Name="{name}" Color="0,0,0,0"/>')
    info.append(f'</PlacedObjects>')
    return "\n".join(info)

def _check_special_rules(func_name: str, exp: ast.FuncCall):
    global POINT_LABEL
    match func_name:
        case "UnitFilter":
            return Value(val="-;Missile,Dead,Hidden", type="unitfilter")
        case "UnitRefFromVariable":
            assert len(exp.args) == 1 and isinstance(exp.args[0], ast.StringLiteral)
            var_name = exp.args[0].value
            return Var(id=_lookup_id(var_name), name=var_name)
        case "UnitRefFromUnit":
            assert len(exp.args) == 1 and isinstance(exp.args[0], ast.FuncCall)
            return convert_funcall_expression(exp.args[0]).link
        case "PointFromId":
            assert len(exp.args) == 1 and isinstance(exp.args[0], ast.IntLiteral)
            return Value(val=exp.args[0].raw, type="point")
        case "Point":
            assert len(exp.args) == 2 and isinstance(exp.args[0], (ast.IntLiteral, ast.FixedLiteral)) and isinstance(exp.args[1], (ast.IntLiteral, ast.FixedLiteral))
            point = (float(exp.args[0].raw), float(exp.args[1].raw))
            return _create_point(point)
        case "CreateUnitsWithDefaultFacing" | "UnitCreateFacingPoint":
            if isinstance(exp.args[0], ast.IntLiteral) and isinstance(exp.args[1], ast.StringLiteral):
                POINT_LABEL = f"{exp.args[0].raw}{exp.args[1].value}"
            return None
        case "OrderTargetingPoint":
            if isinstance(exp.args[0], ast.FuncCall) and isinstance(exp.args[0].args[0], ast.StringLiteral):
                POINT_LABEL = f"{exp.args[0].args[0].value}"
            return None
        case _:
            return None

def _generate_id(var_name: str = '', is_local: bool = False, is_param: bool = False, is_gt: bool = False) -> str:
    global ID_COUNT
    ID_COUNT += 1
    id = "FFFF" + str(ID_COUNT).zfill(4)
    if is_param:
        id = "FFFD" + str(ID_COUNT).zfill(4)
    if is_gt:
        id = "FFFE" + str(ID_COUNT).zfill(4)
    if var_name != '':
        if is_local:
            LOCAL_DICT[var_name] = id
        else:
            GLOBAL_DICT[var_name] = id
    return id

def _lookup_id(var_name: str) -> str:
    if var_name in LOCAL_DICT:
        return LOCAL_DICT[var_name]
    elif var_name in GLOBAL_DICT:
        id = GLOBAL_DICT[var_name]
        return id[0] if isinstance(id, tuple) else id
    elif var_name in FUNC_DEFS:
        return FUNC_DEFS[var_name]["id"]
    else:
        return ""
        # return PRESET_VAL_ID[var_name]

def _is_param(var_name: str) -> bool:
    return LOCAL_DICT.get(var_name, "FFFF").startswith("FFFD")

def _is_gt(var_name: str) -> bool:
    return GLOBAL_DICT.get(var_name, "FFFF").startswith("FFFE")

# def _get_funcdef_id (func_name: str) -> str:
#     return FUNCDEF_ID[func_name]

# def _get_preset_val_id(var_name: str) -> str:
#     return PRESET_VAL_ID[var_name]

def _get_preset_val_id(group_id: str, pst_name: str) -> str:
    assert group_id in PRESET_GROUPS and pst_name in PRESET_GROUPS[group_id], f"Unknown preset: {pst_name}."
    return PRESET_GROUPS[group_id][pst_name]

def _get_preset_group_id(func_name: str, offset: int = 0) -> List[str]:
    if func_name in FUNC_DEFS:
        return FUNC_DEFS[func_name]["preset_id"]
    elif func_name in GLOBAL_DICT:
        return [""] * offset
    else:
        assert False

def _get_brdef_id(func_name: str) -> List[str]:
    assert func_name in FUNC_DEFS
    return FUNC_DEFS[func_name]["br_id"]
    # return BRDEF_ID[FUNCDEF_ID[func_name]]

def _get_prmdef_id(func_name: str) -> List[str]:
    if func_name in FUNC_DEFS:
        return FUNC_DEFS[func_name]["prm_id"]
    elif func_name in GLOBAL_DICT:
        # assert isinstance(GLOBAL_DICT[func_name], tuple)
        return GLOBAL_DICT[func_name][1]
    else:
        print(func_name)
        assert False
    # return PRMDEF_ID[FUNCDEF_ID[func_name]]

def _clear_local():
    LOCAL_DICT.clear()

def _create_point(point: Tuple[float, float]):
    if point in POINT_DICT:
        return Value(val=POINT_DICT[point][1], type="point")
    global ID_COUNT, POINT_LABEL
    ID_COUNT += 1
    id = 1000000000 + ID_COUNT
    name = f"Point-{ID_COUNT}: {POINT_LABEL}"
    POINT_DICT[point] = (name, id)
    POINT_LABEL = ""
    return Value(val=POINT_DICT[point][1], type="point")