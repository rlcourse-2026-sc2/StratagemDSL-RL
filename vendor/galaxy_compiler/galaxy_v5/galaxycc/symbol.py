from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Set, Dict, Tuple, Optional
from .type import *

CACHE_FILENAME = "symbol_cache.json"

RESERVED_KW = set([
    "breakpoint", "continue", "return", "break",
    "while", "else", "for", "do", "if", "const",
    "null", "false", "true", "typedef", "static",
    "struct", "include", "native", ] + ALL_TYPE)

@dataclass
class SymbolTable:
    # var_name -> (var_type, var_val)
    global_scope: Dict[str, Tuple[GType, Any]] = field(default_factory=dict)
    # file_path -> {var_name -> (var_type, var_val)}
    static_scope: Dict[str, Dict[str, Tuple[GType, Any]]] = field(default_factory=dict)
    # var_name -> (var_type, var_val)
    local_scope: Dict[str, Tuple[GType, Any]] = field(default_factory=dict)
    # alias -> type_name
    type_scope: Dict[str, GType] = field(default_factory=dict)
    # path
    include_scope: Set[str] = field(default_factory=set)
    # load
    cache_folder: str = ""

    def __repr__(self):
        return "SymbolTable"
    
    def __post_init__(self):
        if self.cache_folder != "":
            self.load(self.cache_folder)

    def update_global(self, file_path: str, var_name: str, var_type: GType, var_val: Any = None) -> bool:
        scope = self.static_scope.get(file_path, {})
        if var_name in self.global_scope or var_name in scope or var_name in self.type_scope or var_name in RESERVED_KW:
            return False
        self.global_scope[var_name] = (var_type, var_val)
        return True

    def update_static(self, file_path: str, var_name: str, var_type: GType, var_val: Any = None) -> bool:
        if file_path not in self.static_scope:
            self.static_scope[file_path] = {}
        scope = self.static_scope[file_path]
        if var_name in scope or var_name in self.global_scope or var_name in self.type_scope or var_name in RESERVED_KW:
            return False
        scope[var_name] = (var_type, var_val)
        return True
    
    def clear_static(self, file_path: str):
        if file_path in self.static_scope:
            del self.static_scope[file_path]
    
    def update_local(self, file_path: str, var_name: str, var_type: GType, var_val: Any = None) -> bool:
        if var_name in self.local_scope or var_name in self.type_scope or var_name in RESERVED_KW:
            return False
        static_scope = self.static_scope.get(file_path, {})
        if var_name in static_scope and isinstance(static_scope[var_name][0], FuncType):
            return False
        if var_name in self.global_scope and isinstance(self.global_scope[var_name][0], FuncType):
            return False
        self.local_scope[var_name] = (var_type, var_val)
        return True
    
    def clear_local(self):
        self.local_scope.clear()
    
    def update_type(self, file_path: str, type_name: str, type_def: GType) -> bool:
        var_type, _ = self.lookup_var(file_path=file_path, var_name=type_name)
        if not var_type is None or type_name in self.type_scope or type_name in RESERVED_KW:
            return False
        self.type_scope[type_name] = type_def
        return True
    
    def update_include(self, path: str) -> bool:
        if path in self.include_scope:
            return False
        self.include_scope.add(path)
        return True

    def lookup_var(self, file_path: str, var_name: str) -> Tuple[Optional[GType], Any]:
        # 1 local
        if var_name in self.local_scope:
            return self.local_scope[var_name]
        # 2 static
        if file_path in self.static_scope:
            scope = self.static_scope[file_path]
            if var_name in scope:
                return scope[var_name]
        # 3 global
        if var_name in self.global_scope:
            return self.global_scope[var_name]
        return (None, None)
    
    def create_type(self, node):
        from .galaxy_ast import TypeSpecNode
        assert isinstance(node, TypeSpecNode)
        type_name = node.base_name
        gtype = self.create_type_from_string(type_name)
        if isinstance(gtype, ErrorType):
            return gtype
        for dim in node.dimensions:
            gtype = ArrayType(base=gtype, dim=dim)
        return gtype
    
    def create_type_from_string(self, type_name: str, is_const: bool = False):
        if type_name == 'int':
            return IntType(is_const=is_const)
        elif type_name == 'fixed':
            return FixedType(is_const=is_const)
        elif type_name == 'bool':
            return BoolType(is_const=is_const)
        elif type_name == 'string':
            return StringType(is_const=is_const)
        elif type_name == 'void':
            return VoidType()
        elif type_name.startswith('funcref<') and type_name.endswith(">"):
            return BuiltInType(name='funcref', ref=type_name[8:-1])
        elif type_name.startswith('structref<') and type_name.endswith(">"):
            return BuiltInType(name='structref', ref=type_name[10:-1])
        elif type_name in BUILTIN_TYPE:
            return BuiltInType(name=type_name)
        elif type_name in self.type_scope.keys():
            return self.type_scope[type_name]
        else:
            return create_error(code=3, type_name=type_name)
        
    def check_ref(self, file_path: str, gtype: GType):
        if not isinstance(gtype, BuiltInType):
            return True
        if gtype.name == "funcref":
            ref_type, _ = self.lookup_var(file_path, gtype.ref)
            if ref_type == None:
                return create_error(code=4, subcase=1, ref=gtype.ref)
            if not isinstance(ref_type, FuncType):
                return create_error(code=4, subcase=2, ref=gtype.ref, ref_type=ref_type)
            if isinstance(ref_type.rettyp, BuiltInType) and ref_type.rettyp.name == "funcref":
                return create_error(code=4, subcase=3, ref=gtype.ref)
            for ref_prm in ref_type.prmtyp:
                if isinstance(ref_prm, BuiltInType) and ref_prm.name == "funcref":
                    return create_error(code=4, subcase=4, ref=gtype.ref)
            rettyp = ref_type.rettyp
            while isinstance(rettyp, ArrayType):
                rettyp = rettyp.base
            if isinstance(rettyp, BuiltInType) and rettyp.name == "funcref":
                return create_error(code=4, subcase=3, ref=gtype.ref)
        if gtype.name == "structref":
            ref_type = self.type_scope.get(gtype.ref, None)
            if ref_type == None:
                return create_error(code=4, subcase=5, ref=gtype.ref)
            if not isinstance(ref_type, StructType):
                return create_error(code=4, subcase=6, ref=gtype.ref, ref_type=ref_type)
        return True
    
    def check_assignment(self, file_path: str, t_lhs: GType, t_rhs: GType):
        if isinstance(t_lhs, (VoidType, NullType)):
            return create_error(code=8, subcase=1, t_lhs=t_lhs, t_rhs=t_rhs)
        if isinstance(t_lhs, BuiltInType) and t_lhs.name == 'structref':
            if isinstance(t_rhs, StructType) and t_lhs.ref == t_rhs.name:
                return True
            if isinstance(t_rhs, NullType):
                return create_error(code=8, subcase=2, t_lhs=t_lhs, t_rhs=t_rhs)
        if isinstance(t_lhs, BuiltInType) and t_lhs.name == 'funcref':
            if isinstance(t_rhs, FuncType):
                ref_lhs, _ = self.lookup_var(file_path, t_lhs.ref)
                if type_eq(ref_lhs, t_rhs) and t_rhs.is_decl:
                    return True
            if isinstance(t_rhs, BuiltInType) and t_rhs.name == 'funcref':
                ref_lhs, _ = self.lookup_var(file_path, t_lhs.ref)
                ref_rhs, _ = self.lookup_var(file_path, t_rhs.ref)
                if type_eq(ref_lhs, ref_rhs):
                    return True
            return create_error(code=8, subcase=3, t_lhs=t_lhs, t_rhs=t_rhs)
        if isinstance(t_lhs, FixedType) and isinstance(t_rhs, IntType):
            return True
        if isinstance(t_lhs, StringType) and isinstance(t_rhs, NullType):
            return True
        if type_eq(t_lhs, t_rhs):
            if will_bulk_copy(t_rhs):
                return create_error(code=8, subcase=4, t_lhs=t_lhs, t_rhs=t_rhs)
            return True
        return create_error(code=8, subcase=5, t_lhs=t_lhs, t_rhs=t_rhs)
    

    # ── SymbolTable methods (add these inside the class) ──────────────────────

    def save(self, folder: str) -> None:
        """
        Serialize global_scope, type_scope, and include_scope into
        <folder>/symbol_cache.json.
        """
        os.makedirs(folder, exist_ok=True)

        data = {
            "global_scope": {
                name: [_serialize_type(gtype), _serialize_val(val)]
                for name, (gtype, val) in self.global_scope.items()
            },
            "type_scope": {
                name: _serialize_type(gtype)
                for name, gtype in self.type_scope.items()
            },
            "include_scope": list(self.include_scope),
        }

        out_path = Path(folder) / CACHE_FILENAME
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[SymbolTable] Saved cache to {out_path}")


    def load(self, folder: str) -> bool:
        """
        Load global_scope, type_scope, and include_scope from
        <folder>/symbol_cache.json.
        Merges into the current table (existing entries are NOT overwritten).
        Returns True on success, False if the cache file doesn't exist.
        """
        in_path = Path(folder) / CACHE_FILENAME
        if not in_path.exists():
            print(f"[SymbolTable] No cache found at {in_path}")
            return False

        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # type_scope first — global_scope entries may reference these types
        for name, type_dict in data.get("type_scope", {}).items():
            if name not in self.type_scope:
                self.type_scope[name] = _deserialize_type(type_dict)

        for name, (type_dict, val) in data.get("global_scope", {}).items():
            if name not in self.global_scope:
                self.global_scope[name] = (_deserialize_type(type_dict), _deserialize_val(val))

        for path in data.get("include_scope", []):
            self.include_scope.add(path)

        print(f"[SymbolTable] Loaded cache from {in_path}")
        return True



# ── serialization helpers ──────────────────────────────────────────────────

def _serialize_type(gtype: GType) -> dict:
    """Recursively serialize a GType into a JSON-compatible dict."""
    base = {"is_const": gtype.is_const}

    if isinstance(gtype, IntType):
        return {**base, "_t": "int"}
    elif isinstance(gtype, FixedType):
        return {**base, "_t": "fixed"}
    elif isinstance(gtype, BoolType):
        return {**base, "_t": "bool"}
    elif isinstance(gtype, StringType):
        return {**base, "_t": "string"}
    elif isinstance(gtype, VoidType):
        return {**base, "_t": "void"}
    elif isinstance(gtype, NullType):
        return {**base, "_t": "null"}
    elif isinstance(gtype, ErrorType):
        return {**base, "_t": "error", "msg": gtype.msg}
    elif isinstance(gtype, BuiltInType):
        return {**base, "_t": "builtin", "name": gtype.name, "ref": gtype.ref}
    elif isinstance(gtype, ArrayType):
        return {**base, "_t": "array", "base": _serialize_type(gtype.base), "dim": gtype.dim}
    elif isinstance(gtype, StructType):
        return {
            **base, "_t": "struct",
            "name": gtype.name,
            "fields": {k: _serialize_type(v) for k, v in gtype.fields.items()},
        }
    elif isinstance(gtype, FuncType):
        return {
            **base, "_t": "func",
            "rettyp": _serialize_type(gtype.rettyp),
            "prmtyp": [_serialize_type(p) for p in gtype.prmtyp],
            "is_decl": gtype.is_decl,
        }
    else:
        raise TypeError(f"Unknown GType subclass: {type(gtype)}")

def _deserialize_type(d: dict) -> GType:
    """Reconstruct a GType from its serialized dict."""
    t = d["_t"]
    is_const = d.get("is_const", False)

    if t == "int":
        return IntType(is_const=is_const)
    elif t == "fixed":
        return FixedType(is_const=is_const)
    elif t == "bool":
        return BoolType(is_const=is_const)
    elif t == "string":
        return StringType(is_const=is_const)
    elif t == "void":
        return VoidType()
    elif t == "null":
        return NullType()
    elif t == "error":
        return ErrorType(msg=d["msg"])
    elif t == "builtin":
        return BuiltInType(is_const=is_const, name=d["name"], ref=d.get("ref", ""))
    elif t == "array":
        return ArrayType(is_const=is_const, base=_deserialize_type(d["base"]), dim=d["dim"])
    elif t == "struct":
        return StructType(
            is_const=is_const,
            name=d["name"],
            fields={k: _deserialize_type(v) for k, v in d["fields"].items()},
        )
    elif t == "func":
        return FuncType(
            is_const=is_const,
            rettyp=_deserialize_type(d["rettyp"]),
            prmtyp=[_deserialize_type(p) for p in d["prmtyp"]],
            is_decl=d.get("is_decl", False),
        )
    else:
        raise ValueError(f"Unknown type tag: {t}")

def _serialize_val(val: Any) -> Any:
    """Serialize a variable's value (only primitives are expected here)."""
    # Values in global/static scope are typically primitive literals or None.
    # If you later store more complex runtime values, extend this.
    return val

def _deserialize_val(val: Any) -> Any:
    return val