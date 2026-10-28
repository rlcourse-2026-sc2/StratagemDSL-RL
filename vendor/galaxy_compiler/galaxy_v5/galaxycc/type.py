from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Tuple
import json
import os
from pathlib import Path

@dataclass
class GType:
    is_const: bool = False

    def __repr__(self):
        return self.__class__.__name__
    
    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        # 比较除 is_const 以外的所有字段
        d1 = {k: v for k, v in self.__dict__.items() if k != 'is_const' and k != 'is_decl'}
        d2 = {k: v for k, v in other.__dict__.items() if k != 'is_const' and k != 'is_decl'}
        return d1 == d2

@dataclass(eq=False)
class IntType(GType):

    def __repr__(self):
        return "int"
    
@dataclass(eq=False)
class FixedType(GType):

    def __repr__(self):
        return "fixed"
    
@dataclass(eq=False)
class BoolType(GType):

    def __repr__(self):
        return "bool"
    
@dataclass(eq=False)
class StringType(GType):

    def __repr__(self):
        return "string"
    
@dataclass(eq=False)
class VoidType(GType):

    def __repr__(self):
        return "void"
    
@dataclass(eq=False)
class NullType(GType):

    def __repr__(self):
        return "null"
    
@dataclass(eq=False)
class StructType(GType):
    name:   str = ''
    fields: Dict[str, GType] = field(default_factory=dict)

    def __repr__(self):
        return f"struct({self.name})"
    
@dataclass(eq=False)
class ArrayType(GType):
    base:   GType = None
    dim:    int = 0

    def __repr__(self):
        return f"array({self.base}, {self.dim})"
    
@dataclass(eq=False)
class FuncType(GType):
    rettyp:     GType = None
    prmtyp:     List[GType] = field(default_factory=list)
    is_decl:    bool = False

    def __repr__(self):
        prmtyp = ", ".join(str(ptyp) for ptyp in self.prmtyp)
        return f"func([{prmtyp}], {self.rettyp})"
    
@dataclass(eq=False)
class BuiltInType(GType):
    name:   str = ''
    ref:    str = ''

    def __repr__(self):
        return f"{self.name}<{self.ref}>"

@dataclass(eq=False)
class ErrorType(GType):
    code:       int = -1
    subcase:    int = -1
    path:       str = ''
    line:       int = -1
    msg:        str = ''
    info:       str = ''

    def __repr__(self):
        subcase = f"-{self.subcase}" if self.subcase > 0 else "" 
        return f"[{self.__class__.__name__}] - Type {self.code}{subcase} Error\n{self.msg}{self.info}"
    
    def set_error(self, code: int = -1, path: str = '', line: int = -1):
        if code != -1:
            self.code = code
        if path != '':
            self.path = path
        if line != -1:
            self.line = line
    
BUILTIN_TYPE = [
    'unit', 'unitgroup', 'unitfilter', 'unitref',
    'point', 'region', 'trigger', 'timer',
    'actor', 'actorscope', "text",
    'wave', 'wavetarget', 'waveinfo',
    'sound', 'soundlink',
    'revealer', 'playergroup',
    'shuffler', 'color', 'abilcmd',
    'order', 'marker', 'bank', 'camerainfo',
    'aifilter', 'effecthistory', 'bitmask',
    'datetime', 'doodad', 'generichandle',
    'transmissionsource', 'byte',
    'funcref', 'structref',
]

PRIMITIVE_TYPE = ['int', 'fixed', 'bool', 'string',]

ALL_TYPE = BUILTIN_TYPE + PRIMITIVE_TYPE + ["void", "null",]

def type_eq(t1: GType, t2: GType) -> bool:
    # special rule: null compatible with non-structref builtin
    if (isinstance(t1, BuiltInType) and t1.name != "structref" and isinstance(t2, NullType)) or \
       (isinstance(t2, BuiltInType) and t2.name != "structref" and isinstance(t1, NullType)):
        return True
    elif (isinstance(t1, StringType) and isinstance(t2, NullType)) or \
        (isinstance(t2, StringType) and isinstance(t1, NullType)):
        return True
    else:
        return t1 == t2
    
def is_complex_type(t: GType) -> bool:
    if isinstance(t, (IntType, FixedType, BoolType, StringType)):
        return False
    return True

def will_bulk_copy(t: GType) -> bool:
    if not is_complex_type(t):
        return False
    elif isinstance(t, (NullType, VoidType, BuiltInType)):
        return False
    elif isinstance(t, ArrayType):
        if t.dim > 1:
            return True
        return will_bulk_copy(t.base)
    elif isinstance(t, StructType):
        if len(t.fields) > 1:
            return True
        return will_bulk_copy(next(iter(t.fields.values())))
    elif isinstance(t, FuncType):
        # if will_bulk_copy(t.rettyp):
        #     return True
        # for ptyp in t.prmtyp:
        #     if will_bulk_copy(ptyp):
        #         return True
        return True
    else:
        print("This cannot happen")
        return True

def check_return(rettyp: GType, name: str, is_decl: bool):
    if will_bulk_copy(rettyp):
        return create_error(code=13, subcase=1, rettyp=rettyp, func_name=name, is_decl=is_decl)
    if not isinstance(rettyp, VoidType) and not check_void(rettyp):
        return create_error(code=13, subcase=2, rettyp=rettyp, func_name=name, is_decl=is_decl)
    if not check_structref(rettyp):
        return create_error(code=13, subcase=3, rettyp=rettyp, func_name=name, is_decl=is_decl)
    return True

def check_void(gtype: GType) -> bool:
    if isinstance(gtype, VoidType):
        return False
    if isinstance(gtype, ArrayType):
        return check_void(gtype.base)
    if isinstance(gtype, StructType):
        for fld in gtype.fields.values():
            if not check_void(fld):
                return False
    if isinstance(gtype, FuncType):
        for prm in gtype.prmtyp:
            if not check_void(prm):
                return False
    return True

def check_cond(gtype: GType, stmt_type: str=''):
    if isinstance(gtype, (FuncType, VoidType)):
        return create_error(code=22, subcase=1, cond_type=gtype, stmt_type=stmt_type)
    if isinstance(gtype, (ArrayType, StructType)) and will_bulk_copy(gtype):
        return create_error(code=22, subcase=2, cond_type=gtype, stmt_type=stmt_type)
    if isinstance(gtype, BuiltInType) and (gtype.name == "funcref" or gtype.name == "structref"):
        return create_error(code=22, subcase=3, cond_type=gtype, stmt_type=stmt_type)
    return True

def check_structref(gtype: GType) -> bool:
    if isinstance(gtype, BuiltInType) and gtype.name == "structref":
        return False
    if isinstance(gtype, ArrayType):
        return check_structref(gtype.base)
    return True

# def promote_numeric(t1: GType, t2: GType) -> IntType | FixedType | None:

def pick_nonnull(t1: GType, t2: GType) -> GType:
    if not isinstance(t1, NullType):
        return t1
    return t2


@dataclass(eq=False, repr=False)
class ScopeError(ErrorType):
    # illegal name
    pass

@dataclass(eq=False, repr=False)
class GTypeError(ErrorType):
    # illegal type
    pass

@dataclass(eq=False, repr=False)
class CompatibilityError(ErrorType):
    # type mismatch
    pass

@dataclass(eq=False, repr=False)
class ControlFlowError(ErrorType):
    # error about statement
    pass

@dataclass(eq=False, repr=False)
class StructError(ErrorType):
    # error about field access
    pass

@dataclass(eq=False, repr=False)
class ArrayError(ErrorType):
    # error about array access
    pass

@dataclass(eq=False, repr=False)
class FuncCallError(ErrorType):
    # error about function call
    pass

@dataclass(eq=False, repr=False)
class OtherError(ErrorType):
    pass

def create_error(code: int = -1, path: str = '', line: int = -1, **kwargs) -> ErrorType:
    msg = ''
    info = ''
    match code:
        case 1:
            file_path = kwargs.get("file_path", "UNKNOWN_PATH")
            msg = f"Try to include file that does not exist.\n"
            info = f"No file found in path: {file_path}\n"
            return ScopeError(code=code, path=path, line=line, msg=msg, info=info)
        case 2:
            dim = kwargs.get("dim", "UNKNOWN_DIM")
            msg = f"Try to create an array with invalid dimension of {dim}.\n"
            info = "The dimension of an array should be a constant int value and at least 1.\n"
            return GTypeError(code=code, path=path, line=line, msg=msg, info=info)
        case 3:
            type_name = kwargs.get("type_name", "UNKNOWN_TYPE")
            msg = f"Try to create unknown type: '{type_name}'.\n"
            info = ""
            return GTypeError(code=code, path=path, line=line, msg=msg, info=info)
        case 4:
            subcase = kwargs.get("subcase", 0)
            ref = kwargs.get("ref", "UNKNOWN_REF")
            ref_type = kwargs.get("ref", "UNKNOWN_REF_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to create 'funcref<{ref}>' type that point to unknown function '{ref}'.\n"
                    info = "A funcref must refer to a function that has already been declared.\n"
                case 2:
                    msg = f"Try to create 'funcref<{ref}>' type that point to a '{ref_type}' variable.\n"
                    info = "A funcref must refer to a function that has already been declared.\n"
                case 3:
                    msg = f"Try to create invalid 'funcref<{ref}>' where '{ref}' is a function that returns a funcref.\n"
                    info = "Nested funcrefs are not allowed; a funcref must point to a function that does not return a funcref.\n"
                case 4:
                    msg = f"Try to create invalid 'funcref<{ref}>' where '{ref}' is a function that takes funcref parameters.\n"
                    info = "Nested funcrefs are not allowed; a funcref must point to a function that does not pass funcrefs.\n"
                case 5:
                    msg = f"Try to create 'structref<{ref}>' type that point to unknown structure '{ref}'.\n"
                    info = "A structref must refer to a structure that has already been defined.\n"
                case 6:
                    msg = f"Try to create 'structref<{ref}>' type that point to '{ref_type}' type.\n"
                    info = "A structref must refer to a structure that has already been defined.\n"
                case _:
                    msg = "Invalid use of structref/funcref for unknown reason.\n"
                    info = ""
            return GTypeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 5:
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            msg = f"Try to create void variable '{var_name}'.\n"
            info = "Cannot create void variable or array/struct with void members.\n"
            return GTypeError(code=code, path=path, line=line, msg=msg, info=info)
        case 6:
            subcase = kwargs.get("subcase", 0)
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            var_type = kwargs.get("var_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to create a constant {var_type} variable '{var_name}'.\n"
                    info = "Cannot create constant array/structure/function.\n"
                case 2:
                    msg = f"Try to create a constant {var_type} variable '{var_name}' in local.\n"
                    info = "Cannot create non-ref built-in type in local; you can only create them in global.\n"
                case 3:
                    msg = f"Try to create a constant {var_type} variable '{var_name}' (in global).\n"
                    info = "You can never create a constant funcref/structref variable.\n"
                case _:
                    msg = "Try to create an invalid constant variable for unknown reason.\n"
                    info = ""
            return GTypeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 7:
            subcase = kwargs.get("subcase", 0)
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            var_type = kwargs.get("var_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Does not initialize the constant variable '{var_name}' in declaration.\n"
                    info = "Must initialize constant variables.\n"
                case 2:
                    msg = f"Try to use non-constant variable '{var_name}' in the initialization of a constant variable.\n"
                    info = f"To initialize a constant variable, all the variables on the rhs should be constant. But variable '{var_name}' is not constant.\n"
                case 3:
                    msg = f"Try to call function '{var_name}' in the initialization of a constant variable.\n"
                    info = "Function call, field access, and array access are not allowed in the initialization of a constant variable.\n"
                case 4:
                    msg = f"Try to access an array '{var_name}' in the initialization of a constant variable.\n"
                    info = "Function call, field access, and array access are not allowed in the initialization of a constant variable.\n"
                case 5:
                    msg = f"Try to access a field '{var_name}' of a structure '{var_type}' in the initialization of a constant variable.\n"
                    info = "Function call, field access, and array access are not allowed in the initialization of a constant variable.\n"
                case _:
                    msg = "Invalid initialization for a constant variable for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 8:
            subcase = kwargs.get("subcase", 0)
            t_lhs = kwargs.get("t_lhs", "UNKNOWN_TYPE")
            t_rhs = kwargs.get("t_rhs", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Cannot assign '{t_rhs}' to '{t_lhs}'.\n"
                    info = "Cannot assign value to a void/null type variable.\n"
                case 2:
                    msg = f"Cannot assign '{t_rhs}' to '{t_lhs}'.\n"
                    info = f"Cannot assign null to a structref variable; you can only assign '{t_lhs}' with '{t_lhs}' or a '{t_lhs.ref}' structure.\n"
                case 3:
                    msg = f"Cannot assign '{t_rhs}' to '{t_lhs}'.\n"
                    info = f"You can only assign '{t_lhs}' with null, a function, or a funcref that points to a function with the same signature as '{t_lhs.ref}'.\n"
                case 4:
                    msg = f"Cannot assign '{t_rhs}' to '{t_lhs}' with bulk copy.\n"
                    info = "For array/struct assignments, they must contain exactly one element or member recursively.\n"
                case 5:
                    msg = f"Cannot assign '{t_rhs}' to '{t_lhs}'.\n"
                    info = "The type on both sides should be compatible.\n"
                case _:
                    msg = "Incompatible type for an assignment for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 9:
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            msg = f"Try to create static variable '{var_name}' in local.\n"
            info = "Cannot use static in local.\n"
            return GTypeError(code=code, path=path, line=line, msg=msg, info=info)
        case 10:
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            var_type = kwargs.get("var_type", "UNKNOWN_STRUCT")
            msg = f"Cannot create global/static {var_type} variable '{var_name}'.\n"
            info = "'structref' can only be used in local.\n"
            return GTypeError(code=code, path=path, line=line, msg=msg, info=info)
        case 11:
            subcase = kwargs.get("subcase", 0)
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            var_type = kwargs.get("var_type", "UNKNOWN_TYPE")
            dup_type = kwargs.get("dup_type", "UNKNOWN_TYPE")
            scope_type = kwargs.get("scope_type", "UNKNOWN_SCOPE")
            match subcase:
                case 1:
                    scope_range = "local" if scope_type == "local" else "static or global"
                    msg = f"Cannot redefine a {var_type} type variable '{var_name}' in {scope_type}.\n"
                    info = f"A {scope_range} variable '{var_name}' with '{dup_type}' type has already been declared.\n"
                case 2:
                    msg = f"Cannot redefine '{var_name}' with {var_type} type in {scope_type}.\n"
                    info = f"'{var_name}' is already defined as a structure or an alias to '{dup_type}' type.\n"
                case 3:
                    msg = f"Cannot define a {var_type} type {scope_type} variable '{var_name}'.\n"
                    info = f"'{var_name}' is a reserved keyword; please change a different name.\n"
                case _:
                    msg = f"Try to redefine an existing variable for unknown reason.\n"
                    info = ""
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 12:
            func_name = kwargs.get("func_name", "UNKNOWN_FUNC")
            is_func = kwargs.get("is_func", True)
            ext_type = "function" if is_func else "variable"
            msg = f"Try to extern a static native {ext_type} '{func_name}'.\n"
            info = "Cannot use static with native.\n"
            return GTypeError(code=code, path=path, line=line, msg=msg, info=info)
        case 13:
            subcase = kwargs.get("subcase", 0)
            rettyp = kwargs.get("rettyp", "UNKNOWN_TYPE")
            func_name = kwargs.get("func_name", "UNKNOWN_FUNC")
            is_decl = kwargs.get("is_decl", True)
            decl_type = "define" if is_decl else "forward declare"
            match subcase:
                case 1:
                    msg = f"Try to {decl_type} a function '{func_name}' that returns '{rettyp}' with bulk copy.\n"
                    info = "Functions can only return array/struct with exactly one element or member recursively.\n"
                case 2:
                    msg = f"Try to {decl_type} a function '{func_name}' that returns '{rettyp}' with void element or member.\n"
                    info = ""
                case 3:
                    msg = f"Try to {decl_type} a function '{func_name}' that returns '{rettyp}'.\n"
                    info = "Functions cannot return structref.\n"
                case _:
                    msg = "Invalid return type for a function signature for unknown reason.\n"
                    info = ""
            return GTypeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 14:
            subcase = kwargs.get("subcase", 0)
            func_type = kwargs.get("func_type", "UNKNOWN_TYPE")
            func_name = kwargs.get("func_name", "UNKNOWN_FUNC")
            dup_type = kwargs.get("dup_type", "UNKNOWN_TYPE")
            is_decl = kwargs.get("is_decl", True)
            is_func = kwargs.get("is_func", False)
            decl_type = "define" if is_decl else "forward declare"
            match subcase:
                case 1:
                    decl_type = "function" if is_func else "variable"
                    msg = f"Try to extern a native {func_type} {decl_type} '{func_name}' that already exists.\n"
                    info = f"A {dup_type} symbol with same name is already declared or defined.\n"
                case 2:
                    msg = f"Try to {decl_type} '{func_name}' as a function. \n"
                    info = f"'{func_name}' is already defined as a structure or an alias to '{dup_type}'.\n"
                case 3:
                    msg = f"Try to {decl_type} a function '{func_name}' with reserved keyword. \n"
                    info = f"'{func_name}' is a reserved keyword; please change a function name.\n"
                case 4:
                    msg = f"Try to {decl_type} a function with invalid function name '{func_name}'.\n"
                    info = f"A {dup_type} variable with same name already exists.\n"
                case 5:
                    msg = f"Try to {decl_type} a function '{func_name}' with signature {func_type} that does not match previous declaration.\n"
                    info = f"A function with same name and signature {dup_type} has already been declared.\n"
                case 6:
                    msg = f"Try to {decl_type} a function '{func_name}' that has already been defined.\n"
                    info = "You cannot redefine a function twice.\n"
                case _:
                    msg = "Try to redefine a existing function for unknown reason.\n"
                    info = ""
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 15:
            func_name = kwargs.get("func_name", "UNKNOWN_FUNC")
            msg = f"Function '{func_name}' does not have return statement.\n"
            return ControlFlowError(code=code, path=path, line=line, msg=msg)
        case 16:
            subcase = kwargs.get("subcase", 0)
            func_name = kwargs.get("func_name", "UNKNOWN_FUNC")
            prm_name = kwargs.get("prm_name", "UNKNOWN_PARAM")
            prm_type = kwargs.get("prm_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to define invalid parameter '{prm_name}' with illegal type {prm_type} for function {func_name}.\n"
                    info = "Functions cannot have void (or array/struct containing void) parameters.\n"
                case 2:
                    msg = f"Try to define invalid parameter '{prm_name}' with {prm_type} type for function {func_name}.\n"
                    info = "Functions can only accept basic type, cannot pass array/struct/function as parameters; please try to use structref/funcref instead.\n"
                case _:
                    msg = "Try to define a parameter with invalid type for unknown reason.\n"
                    info = ""
            return GTypeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 17:
            subcase = kwargs.get("subcase", 0)
            func_name = kwargs.get("func_name", "UNKNOWN_FUNC")
            prm_name = kwargs.get("prm_name", "UNKNOWN_PARAM")
            prm_type = kwargs.get("prm_type", "UNKNOWN_TYPE")
            dup_type = kwargs.get("dup_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to define an invalid {prm_type} parameter '{prm_name}' for function {func_name}.\n"
                    info = f"A function with signature of {dup_type} and same name already exists; cannot use other function as parameter name.\n"
                case 2:
                    msg = f"Try to redefine a {prm_type} parameter '{prm_name}' for function {func_name}.\n"
                    info = f"A {dup_type} parameter with same name already exists; cannot use same parameter name.\n"
                case 3:
                    msg = f"Try to define a {prm_type} parameter with illegal name '{prm_name}' for function {func_name}.\n"
                    info = f"'{prm_name}' is a structure name or alias of {dup_type} type.\n"
                case 4:
                    msg = f"Try to define a {prm_type} parameter with reserved name '{prm_name}' for function {func_name}.\n"
                    info = f"'{prm_name}' is a reserved keyword; please change a parameter name.\n"
                case _:
                    msg = "Try to define a parameter with invalid name for unknown reason.\n"
                    info = ""
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 18:
            subcase = kwargs.get("subcase", 0)
            struct_name = kwargs.get("struct_name", "UNKNOWN_STRUCT")
            dup_type = kwargs.get("dup_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to redefine a structure '{struct_name}'.\n"
                    info = f"A '{dup_type}' type symbol with same name already exists.\n"
                case 2:
                    msg = f"Try to redefine a structure '{struct_name}'.\n"
                    info = f"'{struct_name}' is already defined as {dup_type}.\n"
                case 3:
                    msg = f"Try to define a structure with invalid name '{struct_name}'.\n"
                    info = f"'{struct_name}' is a reserved keyword; please change a name.\n"
                case _:
                    msg = "Try to define an invalid structure for unknown reason.\n"
                    info = ""
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 19:
            subcase = kwargs.get("subcase", 0)
            struct_name = kwargs.get("struct_name", "UNKNOWN_STRUCT")
            fld_name = kwargs.get("fld_name", "UNKNOWN_FIELD")
            fld_type = kwargs.get("fld_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to define invalid '{fld_type}' type field '{fld_name}' for structure {struct_name}.\n"
                    info = "Structure cannot have void field.\n"
                case 2:
                    msg = f"Try to define invalid '{fld_type}' type field '{fld_name}' for structure {struct_name}.\n"
                    info = "Structure cannot have structref field.\n"
                case _:
                    msg = "Try to define a field with invalid type for a structure for unknown reason.\n"
                    info = ""
            return GTypeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 20:
            subcase = kwargs.get("subcase", 0)
            struct_name = kwargs.get("struct_name", "UNKNOWN_STRUCT")
            fld_name = kwargs.get("fld_name", "UNKNOWN_FIELD")
            fld_type = kwargs.get("fld_type", "UNKNOWN_TYPE")
            dup_type = kwargs.get("dup_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Cannot redefine '{fld_name}' field with '{fld_type}' type for structure {struct_name}.\n"
                    info = f"A '{dup_type}' type field with same name already exists; a structure cannot have fields with same name.\n"
                case 2:
                    msg = f"Try to define an invalid {fld_type} field '{fld_name}' for structure {struct_name}.\n"
                    info = f"A function with signature of {dup_type} and same name already exists; cannot use other function as field name.\n"
                case 3:
                    msg = f"Try to define a {fld_type} field with illegal name '{fld_name}' for structure {struct_name}.\n"
                    info = f"'{fld_name}' is a structure name or alias of {dup_type} type.\n"
                case 4:
                    msg = f"Try to define a {fld_type} field with reserved name '{fld_name}' for structure {struct_name}.\n"
                    info = f"'{fld_name}' is a reserved keyword; please change a field name.\n"
                case _:
                    msg = "Try to define a field with invalid name for a structure for unknown reason.\n"
                    info = ""
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 21:
            subcase = kwargs.get("subcase", 0)
            type_name = kwargs.get("type_name", "UNKNOWN_ALIAS")
            type_def = kwargs.get("type_def", "UNKNOWN_TYPE")
            dup_type = kwargs.get("dup_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Try to typedef a variable or a function '{type_name}' as {type_def}.\n"
                    info = f"Typedef requires an unused identifier, but a '{dup_type}' type symbol with same name already exists.\n"
                case 2:
                    msg = f"Try to typedef a structure or a type-alias '{type_name}' as {type_def}.\n"
                    info = f"Typedef requires an unused identifier, but a '{dup_type}' type symbol with same name already exists.\n"
                case 3:
                    msg = f"Try to typedef a reserved keyword '{type_name}' as {type_def}.\n"
                    info = f"Typedef requires an unused identifier, but a '{type_name}' is a reserved keyword; please change a name.\n"
                case _:
                    msg = f"Try to typedef with invalid alias for unknown reason.\n"
                    info = ""
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 22:
            subcase = kwargs.get("subcase", 0)
            cond_type = kwargs.get("cond_type", "UNKNOWN_TYPE")
            stmt_type = kwargs.get("stmt_type", "UNKNOWN_STMT")
            match subcase:
                case 1:
                    msg = f"Try to pass incompatible '{cond_type}' type expression to {stmt_type} statement.\n"
                    info = f"The condition entry for {stmt_type} statement can only accept basic type and non-ref built-in type expression; cannot pass void/function to condition entry.\n"
                case 2:
                    msg = f"Try to pass incompatible '{cond_type}' type expression to {stmt_type} statement.\n"
                    info = f"The condition entry for {stmt_type} statement can only accept basic type and non-ref built-in type expression; cannot pass array/struct with bulk copy to condition entry.\n"
                case 3:
                    msg = f"Try to pass incompatible '{cond_type}' type expression to {stmt_type} statement.\n"
                    info = f"The condition entry for {stmt_type} statement can only accept basic type and non-ref built-in type expression; cannot pass funcref/structref to condition entry.\n"
                case _:
                    msg = f"Try to pass incompatible type to the condition entry for a statement for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 23:
            var_name = kwargs.get("var_name", "UNKNOWN_VARIABLE")
            msg = f"Try to modify a constant variable '{var_name}'.\n"
            info = "Cannot modify constant variables.\n"
            return CompatibilityError(code=code, path=path, line=line, msg=msg, info=info)
        case 24:
            msg = "Invalid lvalue in assignment; the left hand side of an assignment statement can only be a variable, an array access, or a field access.\n"
            info = ""
            return CompatibilityError(code=code, path=path, line=line, msg=msg, info=info)
        case 25:
            subcase = kwargs.get("subcase", 0)
            op = kwargs.get("op", "UNKNOWN_OPERATOR")
            t_lhs = kwargs.get("t_lhs", "UNKNOWN_TYPE")
            t_rhs = kwargs.get("t_rhs", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    msg = f"Cannot use '{op}' assignment operator on '{t_lhs}' (lhs) and '{t_rhs}' (rhs).\n"
                    if op == "+=":
                        info = "When '+=' is used, the lhs can only be int/fixed/string type.\nIf the lhs is string, the rhs can only be string;\nIf the lhs is int, the rhs can only be int;\nIf the lhs is fixed, the rhs can be either int or fixed.\n"
                    else:
                        info = f"When '{op}' is used, the lhs can only be int or fixed type.\nIf the lhs is int, the rhs can only be int;\nIf the lhs is fixed, the rhs can be either int or fixed.\n"
                case 2:
                    msg = f"Cannot use bitwise assignment operator '{op}' on '{t_lhs}' (lhs) and '{t_rhs}' (rhs).\n"
                    info = f"Bitwise assignment operator '{op}' can only be used on integer type. Please make sure lhs and rhs are both int type.\n"
                case _:
                    msg = f"Invalid use of advanced assignment operator for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 26:
            var_name = kwargs.get("var_name", "UNKNOWN_CALLEE")
            var_type = kwargs.get("var_type", "UNKNOWN_TYPE")
            msg = f"Try to call a non-function variable '{var_name}'.\n"
            info = f"'{var_name}' is a {var_type} type variable but not a function; please make sure to call the right function.\n"
            return FuncCallError(code=code, path=path, line=line, msg=msg, info=info)
        case 27:
            func_name = kwargs.get("func_name", "UNKNOWN_CALLEE")
            func_type = kwargs.get("func_type", "UNKNOWN_TYPE")
            msg = f"Function '{func_name}' with signature {func_type} has been forward declared but not officially defined.\n"
            info = "Please define the function before calling it.\n"
            return FuncCallError(code=code, path=path, line=line, msg=msg, info=info)
        case 28:
            func_name = kwargs.get("func_name", "UNKNOWN_CALLEE")
            func_type = kwargs.get("func_type", "UNKNOWN_TYPE")
            prm_len = kwargs.get("prm_len", -1)
            arg_len = kwargs.get("arg_len", -1)
            msg = f"Try to call function '{func_name}' with signature {func_type} with wrong number of parameters.\n"
            info = f"Function '{func_name}' requires {prm_len} parameters, but {arg_len} arguments are passed.\n"
            return FuncCallError(code=code, path=path, line=line, msg=msg, info=info)
        case 29:
            subcase = kwargs.get("subcase", 0)
            func_name = kwargs.get("func_name", "UNKNOWN_CALLEE")
            func_type = kwargs.get("func_type", "UNKNOWN_TYPE")
            arg_idx = kwargs.get("arg_idx", -1)
            arg_type = kwargs.get("arg_type", "UNKNOWN_TYPE")
            prm_type = kwargs.get("prm_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    ref_type = kwargs.get("ref_type", "UNKNOWN_TYPE")
                    msg = f"Try to call function '{func_name}' with incompatible funcref argument; the signature of function '{func_name}' is {func_type}.\n"
                    info = f"The type of the {arg_idx}-th argument of the function call is a function or a funcref pointing to a function with signature '{arg_type}', but a '{prm_type}' type parameter is required, where the signature of '{prm_type.ref}' is {ref_type}. The signature of two functions should match.\n"
                case 2:
                    msg = f"Try to call function '{func_name}' with incompatible argument type; the signature of function '{func_name}' is {func_type}.\n"
                    info = f"The type of the {arg_idx}-th argument of the function call is '{arg_type}', but a '{prm_type}' type parameter is required. The type of the argument and parameter should match.\n"
                case _:
                    msg = f"Try to call function with incompatible argument type for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 30:
            msg = "Try to return a value in void function.\n"
            info = "Cannot return any value in void function.\n"
            return ControlFlowError(code=code, path=path, line=line, msg=msg, info=info)
        case 31:
            msg = "Expected a value in return statement.\n"
            info = "Non-void function should have a value returned.\n"
            return ControlFlowError(code=code, path=path, line=line, msg=msg, info=info)
        case 32:
            subcase = kwargs.get("subcase", 0)
            ret_type = kwargs.get("ret_type", "UNKNOWN_TYPE")
            req_type = kwargs.get("req_type", "UNKNOWN_TYPE")
            match subcase:
                case 1:
                    ref_type = kwargs.get("ref_type", "UNKNOWN_TYPE")
                    msg = "Try to return a function or a funcref pointing to a function mismatch with the return type of the function that returns a function.\n"
                    info = f"The function should return '{req_type}', where '{req_type.ref}' is a function with signature {ref_type}, but the actual function (or function pointed by the funcref) returned has a signature of {ret_type}. The signature of two functions should match.\n"
                case 2:
                    msg = "Try to return an incompatible type with the function's return type.\n"
                    info = f"The function should return '{req_type}', but '{ret_type}' is actually returned.\n"
                case _:
                    msg = "Try to return incompatible type for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 33:
            msg = "Try to break out of a loop.\n"
            info = "Unexpected break statement.\n"
            return ControlFlowError(code=code, path=path, line=line, msg=msg, info=info)
        case 34:
            msg = "Try to continue out of a loop.\n"
            info = "Unexpected continue statement.\n"
            return ControlFlowError(code=code, path=path, line=line, msg=msg, info=info)
        case 35:
            subcase = kwargs.get("subcase", 0)
            var_name = kwargs.get("var_name", "UNKNOWN_ID")
            match subcase:
                case 1:
                    msg = f"Unknown identifier '{var_name}'.\n"
                    info = "Please declare the variable before using it; please make sure using the correct symbol.\n"
                case 2:
                    msg = f"Unknown constant variable '{var_name}'.\n"
                    info = f"'{var_name}' should be a constant variable; please declare and initialize it before using it.\n"
            return ScopeError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 36:
            subcase = kwargs.get("subcase", 0)
            op = kwargs.get("op", "UNKNOWN_OPERATOR")
            l_type = kwargs.get("l_type", "UNKNOWN_TYPE")
            r_type = kwargs.get("r_type", "UNKNOWN_TYPE")
            is_const = kwargs.get("is_const", False)
            const = " for constant judgement" if is_const else ""
            match subcase:
                case 1:
                    msg = f"Cannot use '{op}' operator on '{l_type}' and '{r_type}'{const}.\n"
                    if op == "+":
                        info = "When '+' is used, the two operands must be:\na. 'string' + 'string';\nb. 'text' + 'text';\nc. 'int'/'fixed' + 'int'/'fixed'.\n"
                    else:
                        info = f"When '{op}' is used, the operands must be 'int' or 'fixed' (int is automatically promoted to fixed when used with fixed).\n"
                case 2:
                    msg = f"Cannot use comparison operator '{op}' on '{l_type}' and '{r_type}'{const}.\n"
                    info = "The operands of comparison operator must have the same type.\n"
                case 3:
                    msg = f"Cannot use logical operator '{op}' on '{l_type}' and '{r_type}'{const}.\n"
                    info = "The operands of comparison operator must be 'bool'.\n"
                case 4:
                    msg = f"Cannot use bitwise operator '{op}' on '{l_type}' and '{r_type}'{const}.\n"
                    info = f"The operands of bitwise operator must be 'int'.\n"
                case _:
                    msg = f"Invalid use of binary operator for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 37:
            subcase = kwargs.get("subcase", 0)
            op = kwargs.get("op", "UNKNOWN_OPERATOR")
            op_type = kwargs.get("op_type", "UNKNOWN_TYPE")
            is_const = kwargs.get("is_const", False)
            const = " for constant judgement" if is_const else ""
            match subcase:
                case 1:
                    msg = f"Cannot use unary operator '{op}' on '{op_type}'{const}.\n"
                    info = f"The operand of '{op}' can only be 'int' or 'fixed' type.\n"
                case 2:
                    msg = f"Cannot use bitwise not operator '{op}' on '{op_type}'{const}.\n"
                    info = f"The operand of '{op}' can only be 'int' type.\n"
                case 3:
                    msg = f"Cannot use bitwise not operator '{op}' on '{op_type}'{const}.\n"
                    info = f"The operand of '{op}' can only be basic type.\n"
                case _:
                    msg = f"Invalid use of unary operator for unknown reason.\n"
                    info = ""
            return CompatibilityError(code=code, subcase=subcase, path=path, line=line, msg=msg, info=info)
        case 38:
            func_name = kwargs.get("func_name", "UNKNOWN_CALLEE")
            msg = f"Try to call a void function '{func_name}' in expression.\n"
            info = "Cannot call void functions in expression; the function call in expression must have a non-void returned value.\n"
            return FuncCallError(code=code, path=path, line=line, msg=msg, info=info)
        case 39:
            var_name = kwargs.get("var_name", "UNKNOWN_OBJECT")
            var_type = kwargs.get("var_type", "UNKNOWN_TYPE")
            msg = f"Try to access an element of a non-array variable '{var_name}'.\n"
            info = f"'{var_name}' is a '{var_type}' type variable, but not an array.\n"
            return ArrayError(code=code, path=path, line=line, msg=msg, info=info)
        case 40:
            arr_name = kwargs.get("arr_name", "UNKNOWN_OBJECT")
            idx_type = kwargs.get("idx_type", "UNKNOWN_OBJECT")
            msg = f"Try to access array '{arr_name}' with '{idx_type}' type index.\n"
            info = "Array access can only accept 'int' type index.\n"
            return ArrayError(code=code, path=path, line=line, msg=msg, info=info)
        case 41:
            var_name = kwargs.get("var_name", "UNKNOWN_OBJECT")
            var_type = kwargs.get("var_type", "UNKNOWN_TYPE")
            msg = f"Try to access a field of a non-struct variable '{var_name}'.\n"
            info = f"'{var_name}' is a '{var_type}' type variable, but not a structure.\n"
            return StructError(code=code, path=path, line=line, msg=msg, info=info)
        case 42:
            struct_name = kwargs.get("struct_name", "UNKNOWN_STRUCT")
            struct_type = kwargs.get("struct_type", "UNKNOWN_TYPE")
            fld_name = kwargs.get("fld_name", "UNKNOWN_FIELD")
            msg = f"Try to access an unknown field '{fld_name}' of structure '{struct_name}'.\n"
            info = f"'{struct_name}' is a '{struct_type}' structure that does not have a '{fld_name}' field.\n"
            return StructError(code=code, path=path, line=line, msg=msg, info=info)
        case _:
            msg = "Unknown error.\n"
            info = "This cannot happen.\n"
            return OtherError(code=code, path=path, line=line, msg=msg, info=info)

    