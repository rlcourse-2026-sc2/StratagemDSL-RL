"""
Galaxy Script AST Transformer
==============================
将 Lark 生成的 CST（具体语法树）转换为更易于分析的 AST 节点树。

使用 Lark 的 Transformer 机制：每个方法对应 grammar 中一条规则，
接收已转换的子节点，返回 AST 节点对象。

使用方式：
    transformer = GalaxyTransformer()
    ast = transformer.transform(lark_tree)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Literal

from .symbol import SymbolTable, RESERVED_KW
from .type import *
from .analyzer import parse, BIN_OP, Status

CACHE_FOLDER = ""
# CACHE_FOLDER = "E:/galaxy-compiler/testload"
# CACHE_FOLDER = "E:/galaxy-compiler/load"
ROOT_DIR = "E:/galaxy-compiler"
# SYMBOL_TABLE = SymbolTable(cache_folder=CACHE_FOLDER)
SYMBOL_TABLE = SymbolTable()
SAVE_CACHE = False

# ──────────────────────────────────────────────────────────────────────────────
# Pretty-print infrastructure
# ──────────────────────────────────────────────────────────────────────────────

# Box-drawing characters for the tree
_BRANCH = "├── "
_LAST   = "└── "
_PIPE   = "│   "
_BLANK  = "    "

@dataclass
class ASTNode:
    """
    所有 AST 节点的公共基类。

    Attributes:
        line, col: 源码位置（由 Transformer 从 meta 填入）
    """
    line: int = -1
    col:  int = -1

    def _pos(self) -> str:
        if self.line == -1:
            return ""
        return f"  [{self.line}:{self.col}]"

    def _node_label(self) -> str:
        """The header line shown for this node (bold class name + position)."""
        return f"{self.__class__.__name__}{self._pos()}"

    def _fields_repr(self) -> list[tuple[str, Any]]:
        """
        Override in each subclass.
        Return a list of (field_label, value) pairs to display as children.
        Values may be: ASTNode, list[ASTNode|Any], str, int, bool, etc.
        """
        return []

    def _build_lines(self) -> list:
        """Return list of lines for this node with box-drawing characters."""
        header = self._node_label()
        fields = self._fields_repr()
        if not fields:
            return [header]

        lines = [header]

        for i, (label, val) in enumerate(fields):
            is_last     = (i == len(fields) - 1)
            connector   = _LAST if is_last else _BRANCH
            cont_prefix = _BLANK if is_last else _PIPE  # prefix for this field's continuation

            if val is None:
                lines.append(f"{connector}{label}: <none>")

            elif isinstance(val, ASTNode):
                child_lines = val._build_lines()
                lines.append(f"{connector}{label}: {child_lines[0]}")
                for cl in child_lines[1:]:
                    lines.append(cont_prefix + cl)

            elif isinstance(val, list):
                if not val:
                    lines.append(f"{connector}{label}: []")
                else:
                    lines.append(f"{connector}{label}: ({len(val)} items)")
                    for j, item in enumerate(val):
                        last_item = (j == len(val) - 1)
                        sub_conn  = _LAST if last_item else _BRANCH
                        sub_cont  = cont_prefix + (_BLANK if last_item else _PIPE)
                        if isinstance(item, ASTNode):
                            item_lines = item._build_lines()
                            lines.append(cont_prefix + sub_conn + item_lines[0])
                            for il in item_lines[1:]:
                                lines.append(sub_cont + il)
                        else:
                            lines.append(cont_prefix + sub_conn + repr(item))
            else:
                lines.append(f"{connector}{label}: {val!r}")

        return lines

    def pretty(self, _indent: str = "") -> str:
        """Return a pretty-printed string of the AST rooted at this node."""
        return "\n".join(self._build_lines())

    def __repr__(self):
        return self.pretty()

    def judge(self, path=''):
        print("This cannot happen!")
        return create_error(path=path, line=self.line)


def _meta_pos(meta) -> tuple[int, int]:
    if meta is None:
        return -1, -1
    return getattr(meta, 'line', -1), getattr(meta, 'column', -1)

def reset_symbol_table(path: str = ""):
    # This should only be used for demo purpose
    global SYMBOL_TABLE
    if path != "":
        SYMBOL_TABLE = SymbolTable(cache_folder=path)
    else:
        SYMBOL_TABLE = SymbolTable()

# ──────────────────────────────────────────────────────────────────────────────
# 顶层 & 声明节点
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TranslationUnit(ASTNode):
    """整个翻译单元（一个 .galaxy 文件）"""
    decls: List[ASTNode] = field(default_factory=list)

    def _fields_repr(self):
        return [("decls", self.decls)]
    
    def judge(self, path='', load_path=''):
        if load_path != '':
            reset_symbol_table(load_path)
        for decl in self.decls:
            err = decl.judge(path=path)
            if isinstance(err, ErrorType):
                return err
        SYMBOL_TABLE.clear_static(file_path=path)
        if path == '' and SAVE_CACHE:
            SYMBOL_TABLE.save(folder="E:/galaxy-compiler/testload")
        return Status.OK


@dataclass
class IncludeDirective(ASTNode):
    path: str = ''

    def _fields_repr(self):
        return [("path", self.path)]
    
    def judge(self, path=''):
        file_path = f"{ROOT_DIR}/{self.path}.galaxy" if not self.path.endswith(".galaxy") else f"{ROOT_DIR}/{self.path}"
        if not SYMBOL_TABLE.update_include(file_path):
            return Status.OK
        ast = parse(file_path)
        if isinstance(ast, ErrorType):
            ast.set_error(path=path, line=self.line)
            return ast
        return ast.judge(path=file_path)


@dataclass
class TypeSpecNode(ASTNode):
    """类型说明：可能是 `int`, `string`, `MyStruct`, 或带数组维度的 `int[10]`"""
    base_name:  str = ''
    dimensions: List['BaseExpression' | int] = field(default_factory=list)

    def _node_label(self):
        dims = "".join(f"[{d}]" for d in self.dimensions)
        return f"TypeSpec  {self.base_name}{dims}{self._pos()}"

    def _fields_repr(self):
        return []       # fully encoded in the label

    def judge(self, path=''):
        for idx in range(len(self.dimensions)):
            assert isinstance(self.dimensions[idx], BaseExpression)
            dim = self.dimensions[idx].const_judge(path=path)
            if isinstance(dim, ErrorType):
                return dim
            elif not isinstance(dim, int) or dim <= 0:
                return create_error(code=2, path=path, line=self.line, dim=dim)
            else:
                self.dimensions[idx] = dim
        gtype = SYMBOL_TABLE.create_type(self)
        if isinstance(gtype, ErrorType):
            gtype.set_error(path=path, line=self.line)
            return gtype
        err = SYMBOL_TABLE.check_ref(path, gtype)
        if isinstance(err, ErrorType):
            err.set_error(path=path, line=self.line)
            return err
        else:
            return gtype


@dataclass
class VarDecl(ASTNode):
    """变量/常量声明（可含初始值）"""
    type_spec:  TypeSpecNode = None
    name:       str = ''
    init:       Optional['BaseExpression'] = None
    is_static:  bool = False
    is_const:   bool = False

    def _node_label(self):
        flags = " ".join(f for f in (
            "static" if self.is_static else "",
            "const"  if self.is_const  else "",
        ) if f)
        qual = f"  [{flags}]" if flags else ""
        return f"VarDecl{qual}{self._pos()}"

    def _fields_repr(self):
        f = [
            ("type", self.type_spec),
            ("name", self.name),
        ]
        if self.init is not None:
            f.append(("init", self.init))
        return f

    def judge(self, is_local=False, path=''):
        gtype = self.type_spec.judge(path=path)
        val = None
        if isinstance(gtype, ErrorType):
            return gtype
        if not check_void(gtype):
            return create_error(code=5, path=path, line=self.line, var_name=self.name)
        if self.is_const:
            if is_complex_type(gtype):
                if not isinstance(gtype, BuiltInType):
                    return create_error(code=6, subcase=1, path=path, line=self.line, var_name=self.name, var_type=gtype)
                elif is_local:
                    return create_error(code=6, subcase=2, path=path, line=self.line, var_name=self.name, var_type=gtype.name)
                elif gtype.name == "funcref" or gtype.name == "structref":
                    return create_error(code=6, subcase=3, path=path, line=self.line, var_name=self.name, var_type=gtype)
            if self.init == None:
                return create_error(code=7, subcase=1, path=path, line=self.line, var_name=self.name)
            val = self.init.const_judge(path=path)
            if isinstance(val, ErrorType):
                return val
            if isinstance(gtype, StringType) and val is None:
                val = ""
            gtype.is_const = True
        init_type = None
        if not self.init is None:
            init_type = self.init.judge(path=path)
            if isinstance(init_type, ErrorType):
                return init_type
            err = SYMBOL_TABLE.check_assignment(path, gtype, init_type)
            if isinstance(err, ErrorType) :
                err.set_error(path=path, line=self.line)
                return err
        if is_local:
            if self.is_static:
                return create_error(code=9, path=path, line=self.line, var_name=self.name)
            if not SYMBOL_TABLE.update_local(file_path=path, var_name=self.name, var_type=gtype, var_val=val):
                dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
                if not dup_type is None:
                    return create_error(code=11, subcase=1, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="local")
                dup_type = SYMBOL_TABLE.type_scope.get(self.name, None)
                if not dup_type is None:
                    return create_error(code=11, subcase=2, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="local")
                return create_error(code=11, subcase=3, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="local")
        elif self.is_static:
            if not check_structref(gtype):
                return create_error(code=10, path=path, line=self.line, var_name=self.name, var_type=gtype)
            if not SYMBOL_TABLE.update_static(file_path=path, var_name=self.name, var_type=gtype, var_val=val):
                dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
                if not dup_type is None:
                    return create_error(code=11, subcase=1, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="static")
                dup_type = SYMBOL_TABLE.type_scope.get(self.name, None)
                if not dup_type is None:
                    return create_error(code=11, subcase=2, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="static")
                return create_error(code=11, subcase=3, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="static")
        else:
            if not check_structref(gtype):
                return create_error(code=10, path=path, line=self.line, var_name=self.name, var_type=gtype)
            if not SYMBOL_TABLE.update_global(file_path=path, var_name=self.name, var_type=gtype, var_val=val):
                dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
                if not dup_type is None:
                    return create_error(code=11, subcase=1, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="global")
                    if not type_eq(gtype, dup_type) or gtype.is_const != dup_type.is_const:
                        return create_error(code=11, subcase=1, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="global")
                    print(path, self.line, f"Warn: Try to create same global variable '{self.name}'!")
                    return Status.OK
                dup_type = SYMBOL_TABLE.type_scope.get(self.name, None)
                if not dup_type is None:
                    return create_error(code=11, subcase=2, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="global")
                return create_error(code=11, subcase=3, path=path, line=self.line, var_name=self.name, var_type=gtype, dup_type=dup_type, scope_type="global")
        return Status.OK


@dataclass
class ForwardDecl(ASTNode):
    """函数前向声明或 native 声明（无函数体）"""
    type_spec:  TypeSpecNode = None
    name:       str = ''
    params:     List['ParamDecl'] = field(default_factory=list)
    is_native:  bool = False
    is_static:  bool = False
    is_func:    bool = False

    def _node_label(self):
        flags = " ".join(f for f in (
            "static" if self.is_static else "",
            "native" if self.is_native else "",
            "func"   if self.is_func   else "",
        ) if f)
        qual = f"  [{flags}]" if flags else ""
        return f"ForwardDecl  {self.name}{qual}{self._pos()}"

    def _fields_repr(self):
        return [
            ("return_type", self.type_spec),
            ("params",      self.params),
        ]

    def judge(self, path=''):
        gtype = self.type_spec.judge(path=path)
        if isinstance(gtype, ErrorType):
            return gtype
        if self.is_native:
            if self.is_static:
                return create_error(code=12, path=path, line=self.line, func_name=self.name, is_func=self.is_func)
            if self.is_func:
                err = check_return(rettyp=gtype, name=self.name, is_decl=False)
                if isinstance(err, ErrorType):
                    err.set_error(path=path, line=self.line)
                    return err
                prmtyp = []
                for prm in self.params:
                    ptyp = prm.judge(path=path, func_name=self.name)
                    if isinstance(ptyp, ErrorType):
                        return ptyp
                    prmtyp.append(ptyp)
                gtype = FuncType(rettyp=gtype, prmtyp=prmtyp, is_decl=True)
            else:
                assert len(self.params) == 0
            if not SYMBOL_TABLE.update_global(file_path=path, var_name=self.name, var_type=gtype):
                dup, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
                assert not dup is None
                if not type_eq(dup, gtype):
                    return create_error(code=14, subcase=1, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=dup, is_decl=False, is_func=self.is_func)
            SYMBOL_TABLE.clear_local()
            return Status.OK
        else:
            assert self.is_func == True
            err = check_return(rettyp=gtype, name=self.name, is_decl=False)
            if isinstance(err, ErrorType):
                err.set_error(path=path, line=self.line)
                return err
            prmtyp = []
            for prm in self.params:
                ptyp = prm.judge(path=path, func_name=self.name)
                if isinstance(ptyp, ErrorType):
                    return ptyp
                prmtyp.append(ptyp)
            gtype = FuncType(rettyp=gtype, prmtyp=prmtyp, is_decl=False)
            find_same = False
            if self.is_static:
                if not SYMBOL_TABLE.update_static(file_path=path, var_name=self.name, var_type=gtype):
                    find_same = True
            else:
                if not SYMBOL_TABLE.update_global(file_path=path, var_name=self.name, var_type=gtype):
                    find_same = True
            if find_same:
                fn, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
                if fn is None:
                    fn = SYMBOL_TABLE.type_scope.get(self.name, None)
                    if not fn is None:
                        return create_error(code=14, subcase=2, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=False)
                    else:
                        return create_error(code=14, subcase=3, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=False)
                assert not fn is None
                if not isinstance(fn, FuncType):
                    return create_error(code=14, subcase=4, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=False)
                if not type_eq(fn, gtype):
                    return create_error(code=14, subcase=5, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=False)
                assert isinstance(fn, FuncType)
                if fn.is_decl:
                    return create_error(code=14, subcase=6, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=False)
                    print(path, self.line, f"Warn: Function '{self.name}' has already been declared!")
            SYMBOL_TABLE.clear_local()
            return Status.OK


@dataclass
class FuncDef(ASTNode):
    """函数定义（有函数体）"""
    type_spec:  TypeSpecNode = None
    name:       str = ''
    params:     List['ParamDecl'] = field(default_factory=list)
    body:       List[VarDecl | 'BaseStmt'] = field(default_factory=list)
    is_static:  bool = False

    def _node_label(self):
        flag = "  [static]" if self.is_static else ""
        return f"FuncDef  {self.name}{flag}{self._pos()}"

    def _fields_repr(self):
        return [
            ("return_type", self.type_spec),
            ("params",      self.params),
            ("body",        self.body),
        ]

    def judge(self, path=''):
        rettyp = self.type_spec.judge(path=path)
        if isinstance(rettyp, ErrorType):
            return rettyp
        err = check_return(rettyp=rettyp, name=self.name, is_decl=True)
        if isinstance(err, ErrorType):
            err.set_error(path=path, line=self.line)
            return err
        prmtyp = []
        for prm in self.params:
            ptyp = prm.judge(path=path, func_name=self.name)
            if isinstance(ptyp, ErrorType):
                return ptyp
            prmtyp.append(ptyp)
        gtype = FuncType(rettyp=rettyp, prmtyp=prmtyp, is_decl=True)
        find_same = False
        if self.is_static:
            if not SYMBOL_TABLE.update_static(file_path=path, var_name=self.name, var_type=gtype):
                find_same = True
        else:
            if not SYMBOL_TABLE.update_global(file_path=path, var_name=self.name, var_type=gtype):
                find_same = True
        if find_same:
            fn, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
            if fn is None:
                fn = SYMBOL_TABLE.type_scope.get(self.name, None)
                if not fn is None:
                    return create_error(code=14, subcase=2, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=True)
                else:
                    return create_error(code=14, subcase=3, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=True)
            assert not fn is None
            if not isinstance(fn, FuncType):
                return create_error(code=14, subcase=4, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=True)
            if fn.is_decl:
                return create_error(code=14, subcase=6, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=True)
                print(f"Warn: Function '{self.name}' has been declared twice!")
            fn.is_decl = True
            if not type_eq(fn, gtype):
                return create_error(code=14, subcase=5, path=path, line=self.line, func_type=gtype, func_name=self.name, dup_type=fn, is_decl=True)
        status = Status.RET if isinstance(rettyp, VoidType) else Status.NOT_RET
        for stmt in self.body:
            if isinstance(stmt, VarDecl):
                err = stmt.judge(is_local=True, path=path)
                if isinstance(err, ErrorType):
                    return err
            else:
                ret = stmt.judge(path=path, rettyp=rettyp)
                if isinstance(ret, ErrorType):
                    return ret
                status = Status.RET if ret is Status.RET else status
        if status is Status.NOT_RET:
            return create_error(code=15, path=path, line=self.line, func_name=self.name)
        SYMBOL_TABLE.clear_local()
        return Status.OK
        

@dataclass
class ParamDecl(ASTNode):
    type_spec: TypeSpecNode = None
    name:      str = ''

    def _node_label(self):
        return f"Param  {self.name}{self._pos()}"

    def _fields_repr(self):
        return [("type", self.type_spec)]

    def judge(self, path='', func_name=''):
        ptyp = self.type_spec.judge(path=path)
        if isinstance(ptyp, ErrorType):
            return ptyp
        if not check_void(ptyp):
            return create_error(code=16, subcase=1, path=path, line=self.line, func_name=func_name, prm_name=self.name, prm_type=ptyp)
        if isinstance(ptyp, ArrayType) or isinstance(ptyp, StructType) or isinstance(ptyp, FuncType):
            return create_error(code=16, subcase=2, path=path, line=self.line, func_name=func_name, prm_name=self.name, prm_type=ptyp)
        if not SYMBOL_TABLE.update_local(file_path=path, var_name=self.name, var_type=ptyp):
            dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
            if not dup_type is None:
                if isinstance(dup_type, FuncType):
                    return create_error(code=17, subcase=1, path=path, line=self.line, func_name=func_name, prm_name=self.name, prm_type=ptyp, dup_type=dup_type)
                else:
                    return create_error(code=17, subcase=2, path=path, line=self.line, func_name=func_name, prm_name=self.name, prm_type=ptyp, dup_type=dup_type)
            dup_type = SYMBOL_TABLE.type_scope.get(self.name, None)
            if not dup_type is None:
                return create_error(code=17, subcase=3, path=path, line=self.line, func_name=func_name, prm_name=self.name, prm_type=ptyp, dup_type=dup_type)
            return create_error(code=17, subcase=4, path=path, line=self.line, func_name=func_name, prm_name=self.name, prm_type=ptyp)
        return ptyp


@dataclass
class StructDef(ASTNode):
    name:    str = ''
    members: List['StructMember'] = field(default_factory=list)

    def _node_label(self):
        return f"StructDef  {self.name}{self._pos()}"

    def _fields_repr(self):
        return [("members", self.members)]

    def judge(self, path=''):
        assert len(self.members) > 0
        fields = {}
        for member in self.members:
            err = member.judge(path=path, fields=fields, struct_name=self.name)
            if isinstance(err, ErrorType):
                return err
        strutyp = StructType(name=self.name, fields=fields)
        if not SYMBOL_TABLE.update_type(file_path=path, type_name=self.name, type_def=strutyp):
            dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
            if not dup_type is None:
                return create_error(code=18, subcase=1, path=path, line=self.line, struct_name=self.name, dup_type=dup_type)
            dup_type = SYMBOL_TABLE.type_scope.get(self.name, None)
            if not dup_type is None:
                return create_error(code=18, subcase=2, path=path, line=self.line, struct_name=self.name, dup_type=dup_type)
            return create_error(code=18, subcase=3, path=path, line=self.line, struct_name=self.name)
        return Status.OK


@dataclass
class StructMember(ASTNode):
    type_spec: TypeSpecNode = None
    name:      str = ''

    def _node_label(self):
        return f"StructMember  {self.name}{self._pos()}"

    def _fields_repr(self):
        return [("type", self.type_spec)]

    def judge(self, path='', fields: dict = {}, struct_name=''):
        fldtyp = self.type_spec.judge(path=path)
        if isinstance(fldtyp, ErrorType):
            return fldtyp
        if not check_void(fldtyp):
            return create_error(code=19, subcase=1, path=path, line=self.line, struct_name=struct_name, fld_name=self.name, fld_type=fldtyp)
        if not check_structref(fldtyp):
            return create_error(code=19, subcase=2, path=path, line=self.line, struct_name=struct_name, fld_name=self.name, fld_type=fldtyp)
        if self.name in fields:
            return create_error(code=20, subcase=1, path=path, line=self.line, struct_name=struct_name, fld_name=self.name, fld_type=fldtyp, dup_type=fields[self.name])
        dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
        if not dup_type is None and isinstance(dup_type, FuncType):
            return create_error(code=20, subcase=2, path=path, line=self.line, struct_name=struct_name, fld_name=self.name, fld_type=fldtyp, dup_type=dup_type)
        dup_type = SYMBOL_TABLE.type_scope.get(self.name, None)
        if not dup_type is None:
            return create_error(code=20, subcase=3, path=path, line=self.line, struct_name=struct_name, fld_name=self.name, fld_type=fldtyp, dup_type=dup_type)
        if self.name in RESERVED_KW:
            return create_error(code=20, subcase=4, path=path, line=self.line, struct_name=struct_name, fld_name=self.name, fld_type=fldtyp)
        fields[self.name] = fldtyp
        return Status.OK


@dataclass
class TypedefDecl(ASTNode):
    type_spec: TypeSpecNode = None
    alias:     str = ''

    def _node_label(self):
        return f"TypedefDecl  {self.alias}{self._pos()}"

    def _fields_repr(self):
        return [("original_type", self.type_spec)]

    def judge(self, path=''):
        gtype = self.type_spec.judge(path=path)
        if isinstance(gtype, ErrorType):
            return gtype
        if not SYMBOL_TABLE.update_type(file_path=path, type_name=self.alias, type_def=gtype):
            dup_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.alias)
            if not dup_type is None:
                return create_error(code=21, subcase=1, path=path, line=self.line, type_name=self.alias, type_def=gtype, dup_type=dup_type)
            dup_type = SYMBOL_TABLE.type_scope.get(self.alias, None)
            if not dup_type is None:
                return create_error(code=21, subcase=2, path=path, line=self.line, type_name=self.alias, type_def=gtype, dup_type=dup_type)
            return create_error(code=21, subcase=3, path=path, line=self.line, type_name=self.alias, type_def=gtype)
        return Status.OK


# ──────────────────────────────────────────────────────────────────────────────
# 语句节点
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BaseStmt(ASTNode):

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        print(path, self.line, "This cannot happen")
        return create_error(path=path, line=self.line)


@dataclass
class CompoundStmt(BaseStmt):
    items: List[BaseStmt] = field(default_factory=list)

    def _fields_repr(self):
        return [("items", self.items)]

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        status = Status.NOT_RET
        for stmt in self.items:
            ret = stmt.judge(path=path, rettyp=rettyp, is_loop=is_loop)
            if isinstance(ret, ErrorType):
                return ret
            status = Status.RET if ret is Status.RET else status
        return status


@dataclass
class BranchStmt(BaseStmt):
    if_br:   'IfStmt' = None
    elif_br: List['IfStmt'] = field(default_factory=list)
    else_br: Optional[CompoundStmt] = None

    def _fields_repr(self):
        f = [
            ("if",   self.if_br),
            ("elif", self.elif_br),
        ]
        if self.else_br is not None:
            f.append(("else", self.else_br))
        return f

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        assert not self.if_br is None
        status = self.if_br.judge(path=path, rettyp=rettyp, is_loop=is_loop)
        if isinstance(status, ErrorType):
            return status
        for br in self.elif_br:
            ret = br.judge(path=path, rettyp=rettyp, is_loop=is_loop)
            if isinstance(ret, ErrorType):
                return ret
            status = Status.NOT_RET if ret is Status.NOT_RET else status
        if self.else_br is None:
            status = Status.NOT_RET
        else:
            ret = self.else_br.judge(path=path, rettyp=rettyp, is_loop=is_loop)
            if isinstance(ret, ErrorType):
                return ret
            status = Status.NOT_RET if ret is Status.NOT_RET else status
        return status


@dataclass
class IfStmt(BaseStmt):
    cond: 'BaseExpression' = None
    body: CompoundStmt = None

    def _fields_repr(self):
        return [
            ("cond", self.cond),
            ("body", self.body),
        ]

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        cond = self.cond.judge(path=path)
        if isinstance(cond, ErrorType):
            return cond
        err = check_cond(gtype=cond, stmt_type="If")
        if isinstance(err, ErrorType):
            err.set_error(path=path, line=self.line)
            return err
        ret = self.body.judge(path=path, rettyp=rettyp, is_loop=is_loop)
        if isinstance(ret, ErrorType):
            return ret
        return ret


@dataclass
class WhileStmt(BaseStmt):
    cond: 'BaseExpression' = None
    body: CompoundStmt = None

    def _fields_repr(self):
        return [
            ("cond", self.cond),
            ("body", self.body),
        ]

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        cond = self.cond.judge(path=path)
        if isinstance(cond, ErrorType):
            return cond
        err = check_cond(gtype=cond, stmt_type="While")
        if isinstance(err, ErrorType):
            err.set_error(path=path, line=self.line)
            return err
        ret = self.body.judge(path=path, rettyp=rettyp, is_loop=True)
        if isinstance(ret, ErrorType):
            return ret
        return Status.NOT_RET


@dataclass
class DoWhileStmt(BaseStmt):
    body: CompoundStmt = None
    cond: 'BaseExpression' = None

    def _fields_repr(self):
        return [
            ("body", self.body),
            ("cond", self.cond),
        ]

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        cond = self.cond.judge(path=path)
        if isinstance(cond, ErrorType):
            return cond
        err = check_cond(gtype=cond, stmt_type="Do-While")
        if isinstance(err, ErrorType):
            err.set_error(path=path, line=self.line)
            return err
        ret = self.body.judge(path=path, rettyp=rettyp, is_loop=True)
        if isinstance(ret, ErrorType):
            return ret
        return Status.NOT_RET


@dataclass
class ForStmt(BaseStmt):
    init: Optional['AssignmentStmt | FuncCallStmt'] = None
    cond: Optional['BaseExpression'] = None
    post: Optional['AssignmentStmt | FuncCallStmt'] = None
    body: CompoundStmt = None

    def _fields_repr(self):
        return [
            ("init", self.init),
            ("cond", self.cond),
            ("post", self.post),
            ("body", self.body),
        ]

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        if not self.init is None:
            err = self.init.judge(path=path, rettyp=rettyp)
            if isinstance(err, ErrorType):
                return err
        if not self.cond is None:
            cond = self.cond.judge(path=path)
            if isinstance(cond, ErrorType):
                return cond
            err = check_cond(gtype=cond, stmt_type="For")
            if isinstance(err, ErrorType) :
                err.set_error(path=path, line=self.line)
                return err
        if not self.post is None:
            err = self.post.judge(path=path, rettyp=rettyp)
            if isinstance(err, ErrorType):
                return err
        ret = self.body.judge(path=path, rettyp=rettyp, is_loop=True)
        if isinstance(ret, ErrorType):
            return ret
        return Status.NOT_RET


@dataclass
class AssignmentStmt(BaseStmt):
    op:    str = ''
    left:  'BaseExpression' = None
    right: 'BaseExpression' = None

    def _node_label(self):
        return f"AssignStmt  {self.op!r}{self._pos()}"

    def _fields_repr(self):
        return [
            ("left",  self.left),
            ("right", self.right),
        ]

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        lhs_type = self.left.judge(path=path)
        if isinstance(lhs_type, ErrorType):
            return lhs_type
        if isinstance(self.left, Identifier) and lhs_type.is_const:
            return create_error(code=23, path=path, line=self.line, var_name=self.left.name)
        if not isinstance(self.left, (Identifier, ArrayAccess, MemberAccess)):
            return create_error(code=24, path=path, line=self.line)
        rhs_type = self.right.judge(path=path)
        if isinstance(rhs_type, ErrorType):
            return rhs_type
        match self.op:
            case "=":
                err = SYMBOL_TABLE.check_assignment(path, lhs_type, rhs_type)
                if isinstance(err, ErrorType):
                    err.set_error(path=path, line=self.line)
                    return err
                return Status.NOT_RET
            case "+=" | "-=" | "*=" | "/=" | "%=":
                if self.op == "+=" and isinstance(lhs_type, StringType) and isinstance(rhs_type, StringType):
                    return Status.NOT_RET
                if isinstance(lhs_type, IntType) and isinstance(rhs_type, IntType):
                    return Status.NOT_RET
                if isinstance(lhs_type, FixedType) and isinstance(rhs_type, (IntType, FixedType)):
                    return Status.NOT_RET
                return create_error(code=25, subcase=1, path=path, line=self.line, op=self.op, t_lhs=lhs_type, t_rhs=rhs_type)
            case _:
                if isinstance(lhs_type, IntType) and isinstance(rhs_type, IntType):
                    return Status.NOT_RET
                return create_error(code=25, subcase=2, path=path, line=self.line, op=self.op, t_lhs=lhs_type, t_rhs=rhs_type)


@dataclass
class FuncCallStmt(BaseStmt):
    callee: 'BaseExpression' = None
    args:   List['BaseExpression'] = field(default_factory=list)

    def _node_label(self):
        name = self.callee.name if isinstance(self.callee, Identifier) else "…"
        return f"FuncCallStmt  {name}{self._pos()}"

    def _fields_repr(self):
        f = []
        if not isinstance(self.callee, Identifier):
            f.append(("callee", self.callee))
        f.append(("args", self.args))
        return f

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        func_type = self.callee.judge(path=path)
        if isinstance(func_type, ErrorType):
            return func_type
        if isinstance(func_type, BuiltInType) and func_type.name == "funcref":
            func_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=func_type.ref)
        if not isinstance(func_type, FuncType):
            return create_error(code=26, path=path, line=self.line, var_name=self.callee, var_type=func_type)
        if not func_type.is_decl:
            # return create_error(code=27, path=path, line=self.line, func_name=self.callee, func_type=func_type)
            print(path, self.line, f"Warn: Function {self.callee} has not been defined!")
        if len(func_type.prmtyp) != len(self.args):
            return create_error(code=28, path=path, line=self.line, func_name=self.callee, func_type=func_type, prm_len=len(func_type.prmtyp), arg_len=len(self.args))
        for idx in range(len(self.args)):
            arg = self.args[idx]
            argtyp = arg.judge(path=path)
            prmtyp = func_type.prmtyp[idx]
            if isinstance(argtyp, ErrorType):
                return argtyp
            if (isinstance(argtyp, FuncType) or (isinstance(argtyp, BuiltInType) and argtyp.name == "funcref")) and isinstance(prmtyp, BuiltInType) and prmtyp.name == "funcref":
                if isinstance(argtyp, BuiltInType) and argtyp.name == "funcref":
                    argtyp, _ = SYMBOL_TABLE.lookup_var(path, argtyp.ref)
                prmref, _ = SYMBOL_TABLE.lookup_var(path, prmtyp.ref)
                assert isinstance(prmref, FuncType)
                if not type_eq(argtyp, prmref):
                    return create_error(code=29, subcase=1, path=path, line=self.line, func_name=self.callee, func_type=func_type, arg_idx=idx+1, arg_type=argtyp, prm_type=prmtyp, ref_type=prmref)
                continue
            if not (isinstance(argtyp, IntType) and isinstance(prmtyp, FixedType)) and not type_eq(argtyp, prmtyp):
                return create_error(code=29, subcase=2, path=path, line=self.line, func_name=self.callee, func_type=func_type, arg_idx=idx+1, arg_type=argtyp, prm_type=prmtyp)
        return Status.NOT_RET


@dataclass
class ReturnStmt(BaseStmt):
    value: Optional['BaseExpression'] = None

    def _fields_repr(self):
        return [("value", self.value)] if self.value is not None else []

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        if isinstance(rettyp, VoidType):
            if not self.value is None:
                return create_error(code=30, path=path, line=self.line)
            return Status.RET
        if not isinstance(rettyp, VoidType) and self.value is None:
            return create_error(code=31, path=path, line=self.line)
        gtype = self.value.judge(path=path)
        if isinstance(gtype, ErrorType):
            return gtype
        if (isinstance(gtype, FuncType) or (isinstance(gtype, BuiltInType) and gtype.name == "funcref")) and isinstance(rettyp, BuiltInType) and rettyp.name == "funcref":
            if isinstance(gtype, BuiltInType) and gtype.name == "funcref":
                gtype, _ = SYMBOL_TABLE.lookup_var(path, gtype.ref)
            retref, _ = SYMBOL_TABLE.lookup_var(path, rettyp.ref)
            assert isinstance(retref, FuncType)
            if not type_eq(gtype, retref):
                return create_error(code=32, subcase=1, path=path, line=self.line, ret_type=gtype, req_type=rettyp, ref_type=retref)
            return Status.RET
        if not (isinstance(gtype, IntType) and isinstance(rettyp, FixedType)) and not type_eq(gtype, rettyp):
            return create_error(code=32, subcase=2, path=path, line=self.line, ret_type=gtype, req_type=rettyp)
        return Status.RET


@dataclass
class BreakStmt(BaseStmt):
    
    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        if not is_loop:
            return create_error(code=33, path=path, line=self.line)
        return Status.NOT_RET


@dataclass
class ContinueStmt(BaseStmt):

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        if not is_loop:
            return create_error(code=34, path=path, line=self.line)
        return Status.NOT_RET


@dataclass
class BreakpointStmt(BaseStmt):

    def judge(self, path='', rettyp: GType = VoidType(), is_loop: bool = False) -> Literal[Status.NOT_RET, Status.RET] | ErrorType:
        return Status.NOT_RET


# ──────────────────────────────────────────────────────────────────────────────
# 表达式节点
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BaseExpression(ASTNode):

    def judge(self, path='') -> GType:
        print(path, self.line, "This cannot happen")
        return create_error(path=path, line=self.line)
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        print(path, self.line, f"Not constant at [{self.line}:{self.col}]!")
        return create_error(path=path, line=self.line)


@dataclass
class Identifier(BaseExpression):
    name: str = ''

    def _node_label(self):
        return f"Id  {self.name!r}{self._pos()}"

    def _fields_repr(self):
        return []

    def judge(self, path='') -> GType:
        gtype, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
        if gtype is None:
            gtype = SYMBOL_TABLE.type_scope.get(self.name, None)
        if gtype is None:
            return create_error(code=35, subcase=1, path=path, line=self.line, var_name=self.name)
        return gtype
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        gtype, val = SYMBOL_TABLE.lookup_var(file_path=path, var_name=self.name)
        if gtype is None:
            return create_error(code=35, subcase=2, path=path, line=self.line, var_name=self.name)
        if not gtype.is_const:
            return create_error(code=7, subcase=2, path=path, line=self.line, var_name=self.name)
        return val


@dataclass
class IntLiteral(BaseExpression):
    raw: str = ''

    @property
    def value(self) -> int:
        return int(self.raw, 0)

    def _node_label(self):
        return f"IntLit  {self.raw}{self._pos()}"

    def _fields_repr(self):
        return []

    def judge(self, path='') -> GType:
        return IntType()
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return self.value


@dataclass
class FixedLiteral(BaseExpression):
    """Galaxy Script 的定点数字面量（fixed 类型）"""
    raw: str = ''

    @property
    def value(self) -> float:
        return float(self.raw)

    def _node_label(self):
        return f"FixedLit  {self.raw}{self._pos()}"

    def _fields_repr(self):
        return []

    def judge(self, path='') -> GType:
        return FixedType()
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return self.value


@dataclass
class BoolLiteral(BaseExpression):
    value: bool = False

    def _node_label(self):
        v = "true" if self.value else "false"
        return f"BoolLit  {v}{self._pos()}"

    def _fields_repr(self):
        return []

    def judge(self, path='') -> GType:
        return BoolType()
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return self.value


@dataclass
class NullLiteral(BaseExpression):

    def _node_label(self):
        return f"NullLit{self._pos()}"

    def _fields_repr(self):
        return []

    def judge(self, path='') -> GType:
        return NullType()
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return None


@dataclass
class StringLiteral(BaseExpression):
    raw: str = ''   # 含引号的原始字符串

    @property
    def value(self) -> str:
        return self.raw[1:-1]

    def _node_label(self):
        return f"StrLit  {self.raw}{self._pos()}"

    def _fields_repr(self):
        return []

    def judge(self, path='') -> GType:
        return StringType()
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return self.value


@dataclass
class BinaryOp(BaseExpression):
    op:    str = ''
    left:  BaseExpression = None
    right: BaseExpression = None

    def _node_label(self):
        return f"BinOp  {self.op!r}{self._pos()}"

    def _fields_repr(self):
        return [
            ("left",  self.left),
            ("right", self.right),
        ]

    def judge(self, path='') -> GType:
        l_type = self.left.judge(path=path)
        if isinstance(l_type, ErrorType):
            return l_type
        r_type = self.right.judge(path=path)
        if isinstance(r_type, ErrorType):
            return r_type
        match self.op:
            case "+" | "-" | "*" | "/" | "%":
                if self.op == "+":
                    if isinstance(l_type, StringType) and isinstance(r_type, StringType):
                        return StringType()
                    if isinstance(l_type, BuiltInType) and l_type.name == "text" and isinstance(r_type, BuiltInType) and r_type.name == "text":
                        return BuiltInType(name="text")
                if isinstance(l_type, (IntType, FixedType)) and isinstance(r_type, (IntType, FixedType)):
                    if isinstance(l_type, FixedType) or isinstance(r_type, FixedType):
                        return FixedType()
                    return IntType()
                return create_error(code=36, subcase=1, path=path, line=self.line, op=self.op, l_type=l_type, r_type=r_type)
            case "==" | "!=" | ">" | ">=" | "<" | "<=":
                if type_eq(l_type, r_type):
                   return BoolType()
                if isinstance(l_type, (IntType, FixedType)) and isinstance(r_type, (IntType, FixedType)):
                    return BoolType()
                return create_error(code=36, subcase=2, path=path, line=self.line, op=self.op, l_type=l_type, r_type=r_type)
            case "&&" | "||":
                if isinstance(l_type, BoolType) and isinstance(r_type, BoolType):
                    return BoolType()
                return create_error(code=36, subcase=3, path=path, line=self.line, op=self.op, l_type=l_type, r_type=r_type)
            case _:
                if isinstance(l_type, IntType) and isinstance(r_type, IntType):
                    return IntType()
                return create_error(code=36, subcase=4, path=path, line=self.line, op=self.op, l_type=l_type, r_type=r_type)
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        l_const = self.left.const_judge(path=path)
        if isinstance(l_const, ErrorType):
            return l_const
        r_const = self.right.const_judge(path=path)
        if isinstance(r_const, ErrorType):
            return r_const
        match self.op:
            case "+" | "-" | "*" | "/" | "%":
                if self.op == "+" and isinstance(l_const, str) and isinstance(r_const, str):
                    return BIN_OP[self.op](l_const, r_const)
                if type(l_const) in (int, float) and type(r_const) in (int, float):
                    if type(l_const) is float or type(r_const) is float:
                        return float(BIN_OP[self.op](l_const, r_const))
                    return int(BIN_OP[self.op](l_const, r_const))
                return create_error(code=36, subcase=1, path=path, line=self.line, op=self.op, l_type=type(l_const), r_type=type(r_const), is_const=True)
            case "==" | "!=" | ">" | ">=" | "<" | "<=":
                if type(l_const) is type(r_const):
                   return bool(BIN_OP[self.op](l_const, r_const))
                if type(l_const) in (int, float) and type(r_const) in (int, float):
                    return bool(BIN_OP[self.op](l_const, r_const))
                return create_error(code=36, subcase=2, path=path, line=self.line, op=self.op, l_type=type(l_const), r_type=type(r_const), is_const=True)
            case "&&" | "||":
                if type(l_const) is bool and type(r_const) is bool:
                    return bool(BIN_OP[self.op](l_const, r_const))
                return create_error(code=36, subcase=3, path=path, line=self.line, op=self.op, l_type=type(l_const), r_type=type(r_const), is_const=True)
            case _:
                if type(l_const) is int and type(r_const) is int:
                    return int(BIN_OP[self.op](l_const, r_const))
                return create_error(code=36, subcase=4, path=path, line=self.line, op=self.op, l_type=type(l_const), r_type=type(r_const), is_const=True)


@dataclass
class UnaryOp(BaseExpression):
    op:      str = ''
    operand: BaseExpression = None

    def _node_label(self):
        return f"UnaryOp  {self.op!r}{self._pos()}"

    def _fields_repr(self):
        return [("operand", self.operand)]

    def judge(self, path='') -> GType:
        gtype = self.operand.judge(path=path)
        if isinstance(gtype, ErrorType):
            return gtype
        match self.op:
            case "+" | "-":
                if isinstance(gtype, (IntType, FixedType)):
                    return gtype
                return create_error(code=37, subcase=1, path=path, line=self.line, op=self.op, op_type=gtype)
            case "~":
                if isinstance(gtype, IntType):
                    return gtype
                return create_error(code=37, subcase=2, path=path, line=self.line, op=self.op, op_type=gtype)
            case "!":
                if not is_complex_type(gtype):
                    return gtype
                return create_error(code=37, subcase=3, path=path, line=self.line, op=self.op, op_type=gtype)
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        const = self.operand.const_judge(path=path)
        if isinstance(const, ErrorType):
            return const
        match self.op:
            case "+":
                if type(const) in (int, float):
                    return const
                return create_error(code=37, subcase=1, path=path, line=self.line, op=self.op, op_type=type(const), is_const=True)
            case "-":
                if type(const) in (int, float):
                    return - const
                return create_error(code=37, subcase=1, path=path, line=self.line, op=self.op, op_type=type(const), is_const=True)
            case "~":
                if type(const) is int:
                    return ~ const
                return create_error(code=37, subcase=2, path=path, line=self.line, op=self.op, op_type=type(const), is_const=True)
            case "!":
                if type(const) is int:
                    return 0 if const != 0 else 1
                elif type(const) is float:
                    return 0.0 if const != 0.0 else 1.0
                elif type(const) is bool:
                    return not const
                elif type(const) is str:
                    return ""
                return create_error(code=37, subcase=3, path=path, line=self.line, op=self.op, op_type=type(const), is_const=True)


@dataclass
class FuncCall(BaseExpression):
    callee: BaseExpression = None
    args:   List[BaseExpression] = field(default_factory=list)

    def _node_label(self):
        # Try to show the callee name inline when it's a simple identifier
        name = self.callee.name if isinstance(self.callee, Identifier) else "…"
        return f"FuncCall  {name}{self._pos()}"

    def _fields_repr(self):
        f = []
        if not isinstance(self.callee, Identifier):
            f.append(("callee", self.callee))
        f.append(("args", self.args))
        return f

    def judge(self, path='') -> GType:
        func_type = self.callee.judge(path=path)
        if isinstance(func_type, ErrorType):
            return func_type
        if isinstance(func_type, BuiltInType) and func_type.name == "funcref":
            func_type, _ = SYMBOL_TABLE.lookup_var(file_path=path, var_name=func_type.ref)
        if not isinstance(func_type, FuncType):
            return create_error(code=26, path=path, line=self.line, var_name=self.callee, var_type=func_type)
        if not func_type.is_decl:
            # return create_error(code=27, path=path, line=self.line, func_name=self.callee, func_type=func_type)
            print(path, self.line, f"Warn: Function {self.callee} has not been defined!")
        if len(func_type.prmtyp) != len(self.args):
            return create_error(code=28, path=path, line=self.line, func_name=self.callee, func_type=func_type, prm_len=len(func_type.prmtyp), arg_len=len(self.args))
        if isinstance(func_type.rettyp, VoidType):
            return create_error(code=38, path=path, line=self.line, func_name=self.callee)
        for idx in range(len(self.args)):
            arg = self.args[idx]
            argtyp = arg.judge(path=path)
            prmtyp = func_type.prmtyp[idx]
            if isinstance(argtyp, ErrorType):
                return argtyp
            if (isinstance(argtyp, FuncType) or (isinstance(argtyp, BuiltInType) and argtyp.name == "funcref")) and isinstance(prmtyp, BuiltInType) and prmtyp.name == "funcref":
                if isinstance(argtyp, BuiltInType) and argtyp.name == "funcref":
                    argtyp, _ = SYMBOL_TABLE.lookup_var(path, argtyp.ref)
                prmref, _ = SYMBOL_TABLE.lookup_var(path, prmtyp.ref)
                assert isinstance(prmref, FuncType)
                if not type_eq(argtyp, prmref):
                    return create_error(code=29, subcase=1, path=path, line=self.line, func_name=self.callee, func_type=func_type, arg_idx=idx+1, arg_type=argtyp, prm_type=prmtyp, ref_type=prmref)
                continue
            if not (isinstance(argtyp, IntType) and isinstance(prmtyp, FixedType)) and not type_eq(argtyp, prmtyp):
                return create_error(code=29, subcase=2, path=path, line=self.line, func_name=self.callee, func_type=func_type, arg_idx=idx+1, arg_type=argtyp, prm_type=prmtyp)
        return func_type.rettyp
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return create_error(code=7, subcase=3, path=path, line=self.line, var_name=self.callee)


@dataclass
class ArrayAccess(BaseExpression):
    array: BaseExpression = None
    index: BaseExpression = None

    def _fields_repr(self):
        return [
            ("array", self.array),
            ("index", self.index),
        ]

    def judge(self, path='') -> GType:
        arr_type = self.array.judge(path=path)
        if isinstance(arr_type, ErrorType):
            return arr_type
        if not isinstance(arr_type, ArrayType):
            return create_error(code=39, path=path, line=self.line, var_name=self.array, var_type=arr_type)
        idx_type = self.index.judge(path=path)
        if isinstance(idx_type, ErrorType):
            return idx_type
        if not isinstance(idx_type, IntType):
            return create_error(code=40, path=path, line=self.line, arr_name=self.array, idx_type=idx_type)
        return arr_type.base
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return create_error(code=7, subcase=4, path=path, line=self.line, var_name=self.array)


@dataclass
class MemberAccess(BaseExpression):
    obj:    BaseExpression = None
    member: str = ''

    def _node_label(self):
        return f"MemberAccess  .{self.member}{self._pos()}"

    def _fields_repr(self):
        return [("obj", self.obj)]

    def judge(self, path='') -> GType:
        struct_type = self.obj.judge(path=path)
        if isinstance(struct_type, ErrorType):
            return struct_type
        if isinstance(struct_type, BuiltInType) and struct_type.name == "structref":
            struct_type = SYMBOL_TABLE.type_scope.get(struct_type.ref, ErrorType())
        if not isinstance(struct_type, StructType):
            return create_error(code=41, path=path, line=self.line, var_name=self.obj, var_type=struct_type)
        fld_type = struct_type.fields.get(self.member, None)
        if fld_type is None:
            return create_error(code=42, path=path, line=self.line, struct_name=self.obj, struct_type=struct_type.name, fld_name=self.member)
        return fld_type
    
    def const_judge(self, path='') -> ErrorType | int | float | bool | str | None:
        return create_error(code=7, subcase=5, path=path, line=self.line, var_name=self.member, var_type=self.obj)
