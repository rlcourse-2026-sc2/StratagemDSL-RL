from lark import Transformer, Token, Tree, v_args
from . import galaxy_ast as ast

# ──────────────────────────────────────────────────────────────────────────────
# Transformer
# ──────────────────────────────────────────────────────────────────────────────

class GalaxyTransformer(Transformer):
    """
    将 Lark CST 转换为 Galaxy Script AST。
    规则名与 grammar 中的产生式名保持一致。

    使用 @v_args(meta=True) 来获取源码位置。
    """

    # ── 辅助 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _set_pos(node: ast.ASTNode, meta) -> ast.ASTNode:
        if meta:
            node.line = getattr(meta, 'line', -1)
            node.col  = getattr(meta, 'column', -1)
        return node

    # ── TOP ───────────────────────────────────────────────────────────────

    @v_args(inline=True)
    def start(self, item):
        return item
    
    @v_args(meta=True)
    def translation_unit(self, meta, items):
        node = ast.TranslationUnit(decls=[i for i in items if i is not None])
        return self._set_pos(node, meta)
    
    def external_declaration(self, items):
        return items[0] if items else None
    
    @v_args(meta=True, inline=True)
    def forward_definition(self, meta, func_decl):
        is_static = func_decl[0]
        type_spec = func_decl[1]
        func_name = func_decl[2]
        params = func_decl[3]
        node = ast.ForwardDecl(type_spec=type_spec, name=func_name, params=params, is_static=is_static, is_func=True)
        return self._set_pos(node, meta)
    
    @v_args(meta=True, inline=True)
    def type_declaration(self, meta, tok, type_spec, type_name):
        node = ast.TypedefDecl(type_spec=type_spec, alias=type_name.value)
        return self._set_pos(node, meta)

    @v_args(meta=True)
    def native_declaration(self, meta, items):
        native = items[0]
        type_spec = items[1]
        name = items[2]
        if len(items) > 3:
            params = items[3]
            node = ast.ForwardDecl(type_spec=type_spec, name=name, params=params, is_native=True, is_func=True)
        else:
            node = ast.ForwardDecl(type_spec=type_spec, name=name, params=[], is_native=True, is_func=False)
        return self._set_pos(node, meta)
    
    @v_args(meta=True, inline=True)
    def include_directive(self, meta, inc, path_node):
        path = path_node.value   # '"TriggerLibs/natives"' 含引号
        node = ast.IncludeDirective(path=path)
        return self._set_pos(node, meta)

    # ── DECLARATION ───────────────────────────────────────────────────────

    @v_args(meta=True, inline=True)
    def declaration(self, meta, decl_spec, init_decl):
        is_static = decl_spec[0]
        is_const = decl_spec[1]
        type_spec = decl_spec[2]
        name = init_decl[0]
        init_val = init_decl[1]
        node = ast.VarDecl(type_spec=type_spec, name=name, init=init_val, is_static=is_static, is_const=is_const)
        return self._set_pos(node, meta)

    def init_declarator(self, items):
        name = items[0]
        if len(items) > 1:
            op = items[1]
            init_val = items[2]
            return (name, init_val)
        return (name, None)

    @v_args(inline=True)
    def declarator(self, id):
        return id.name
    
    @v_args(inline=True)
    def initializer(self, expr):
        return expr

    def declaration_specifiers(self, items):
        if len(items) == 1:
            return (False, False, items[0])
        elif len(items) == 2:
            if items[0].type == "STATIC":
                return (True, False, items[1])
            elif items[0].type == "CONST":
                return (False, True, items[1])
            else:
                print("This cannot happen!")
                exit(1)
        else:
            return (True, True, items[2])

    # ── TYPE ──────────────────────────────────────────────────────────────
    
    @v_args(inline=True)
    def storage_class_specifier(self, tok):
        return tok  # 直接返回 STATIC token

    @v_args(inline=True)
    def type_qualifier(self, tok):
        return tok  # 直接返回 CONST token
    
    def type_specifier(self, items):
        type_spec = items[0]
        if len(items) > 1:
            dims = items[1]
            type_spec.dimensions = dims
        return type_spec

    def array_dimensions(self, exprs):
        dims = [e for e in exprs]
        return dims
    
    @v_args(meta=True, inline=True)
    def base_type_specifier(self, meta, tok):
        base_name = tok.value
        node = ast.TypeSpecNode(base_name=base_name, dimensions=[])
        return self._set_pos(node, meta)

    # ── STRUCT ────────────────────────────────────────────────────────────

    @v_args(meta=True, inline=True)
    def structure_definition(self, meta, tok, name, body):
        node = ast.StructDef(name=name, members=body)
        return self._set_pos(node, meta)
    
    @v_args(inline=True)
    def struct_name(self, id):
        return id.value
    
    def struct_body(self, fields):
        body = [fld for fld in fields]
        return body
    
    @v_args(meta=True, inline=True)
    def field_declaration(self, meta, type_spec, name):
        node = ast.StructMember(type_spec=type_spec, name=name)
        return self._set_pos(node, meta)

    # ── FUNCTION ──────────────────────────────────────────────────────────
    
    @v_args(meta=True, inline=True)
    def function_definition(self, meta, func_title, func_body):
        is_static = func_title[0]
        type_spec = func_title[1]
        func_name = func_title[2]
        params = func_title[3]
        node = ast.FuncDef(type_spec=type_spec, name=func_name, params=params, body=func_body, is_static=is_static)
        return self._set_pos(node, meta)

    def function_declaration(self, items):
        params = items[-1]
        func_name = items[-2]
        type_spec = items[-3]
        is_static = False
        if len(items) > 3:
            is_static = True
        return (is_static, type_spec, func_name, params)
    
    @v_args(inline=True)
    def function_name(self, id):
        return id.name
    
    def parameter_list(self, params):
        prm_list = [prm for prm in params]
        return prm_list
    
    @v_args(meta=True, inline=True)
    def parameter_declaration(self, meta, type_spec, id):
        name = id.name
        node = ast.ParamDecl(type_spec=type_spec, name=name)
        return self._set_pos(node, meta)
    
    def function_body(self, items):
        body = [stmt for stmt in items if stmt != None]
        return body

    # ── STATEMENT ─────────────────────────────────────────────────────────
    
    def statement(self, stmt):
        return stmt[0] if len(stmt) > 0 else None

    @v_args(meta=True)
    def compound_statement(self, meta, stmts):
        items = [stmt for stmt in stmts if stmt != None]
        node = ast.CompoundStmt(items=items)
        return self._set_pos(node, meta)

    @v_args(meta=True)
    def selection_statement(self, meta, items):
        if_br = items[0]
        elif_br = []
        node = ast.BranchStmt(if_br=if_br)
        for idx in range(2, len(items), 2):
            if isinstance(items[idx], ast.CompoundStmt):
                node.else_br = items[idx]
            else:
                elif_br.append(items[idx])
        node.elif_br = elif_br
        return self._set_pos(node, meta)

    @v_args(meta=True, inline=True)
    def if_statement(self, meta, tok, cond, stmts):
        node = ast.IfStmt(cond=cond, body=stmts)
        return self._set_pos(node, meta)

    @v_args(meta=True, inline=True)
    def while_statement(self, meta, tok, cond, stmts):
        node = ast.WhileStmt(cond=cond, body=stmts)
        return self._set_pos(node, meta)
    
    @v_args(meta=True, inline=True)
    def do_statement(self, meta, tok1, stmts, tok2, cond):
        node = ast.DoWhileStmt(body=stmts, cond=cond)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def for_statement(self, meta, items):
        init = None
        cond = None
        post = None
        idx = 1
        if isinstance(items[idx], Token):
            idx += 1
        else:
            init = items[idx]
            idx += 2
        if isinstance(items[idx], Token):
            idx += 1
        else:
            cond = items[idx]
            idx += 2
        if idx < len(items) - 1:
            post = items[idx]
        body = items[-1]
        node = ast.ForStmt(init=init, cond=cond, post=post, body=body)
        return self._set_pos(node, meta)

    @v_args(meta=True)
    def jump_statement(self, meta, items):
        kw = items[0].value
        if kw == 'continue':
            node = ast.ContinueStmt()
        elif kw == 'break':
            node = ast.BreakStmt()
        elif kw == 'breakpoint':
            node = ast.BreakpointStmt()
        else:  # return
            val = items[1] if len(items) > 1 else None
            node = ast.ReturnStmt(value=val)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def funcall_statement(self, meta, items):
        callee = items[0]
        args = []
        if len(items) > 1:
            args = items[1]
        node = ast.FuncCallStmt(callee=callee, args=args)
        return self._set_pos(node, meta)
    
    @v_args(meta=True, inline=True)
    def assignment_statement(self, meta, lhs, op, rhs):
        node = ast.AssignmentStmt(op=op, left=lhs, right=rhs)
        return self._set_pos(node, meta)

    @v_args(inline=True)
    def assignment_operator(self, tok):
        return tok.value

    # ── EXPRESSION ────────────────────────────────────────────────────────

    @v_args(inline=True)
    def expression(self, expr):
        return expr

    @v_args(meta=True)
    def logical_or_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def logical_and_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    

    @v_args(meta=True)
    def bitwise_or_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def bitwise_xor_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def bitwise_and_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def equality_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def relational_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def shift_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def additive_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def multiplicative_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items), 2):
            op = items[idx].value
            right = items[idx + 1]
            node = ast.BinaryOp(op=op, left=node, right=right)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)
    
    @v_args(meta=True)
    def unary_expression(self, meta, items):
        node = items[-1]
        for idx in reversed(range(0, len(items) - 1)):
            node = ast.UnaryOp(op=items[idx], operand=node)
            self._set_pos(node, meta)
        return self._set_pos(node, meta)

    @v_args(meta=True)
    def postfix_expression(self, meta, items):
        node = items[0]
        for idx in range(1, len(items)):
            op = items[idx][0]
            postfix = items[idx][1]
            if op == "index_access":
                node = ast.ArrayAccess(array=node, index=postfix)
                self._set_pos(node, meta)
            elif op == "function_call":
                node = ast.FuncCall(callee=node, args=postfix)
                self._set_pos(node, meta)
            elif op == "field_access":
                node = ast.MemberAccess(obj=node, member=postfix)
                self._set_pos(node, meta)
            else:
                print("This cannot happen!")
                exit(1)
        return self._set_pos(node, meta)

    @v_args(inline=True)
    def primary_expression(self, expr):
        return expr
    
    @v_args(inline=True)
    def index_access(self, idx):
        return ("index_access", idx)
    
    def function_call(self, items):
        args = []
        if len(items) > 0:
            args = items[0]
        return ("function_call", args)
    
    @v_args(inline=True)
    def field_access(self, field):
        return ("field_access", field.name)

    def argument_list(self, exprs):
        args = [arg for arg in exprs]
        return args

    @v_args(inline=True)
    def unary_operator(self, tok):
        return tok.value

    # ── TOKEN ─────────────────────────────────────────────────────────────

    def IDENTIFIER(self, tok):
        node = ast.Identifier(name=tok.value)
        return self._set_pos(node, tok)

    def CONSTANT(self, tok):
        raw = tok.value
        if '.' in raw or ('e' in raw.lower() and not raw.startswith('0x')):
            node = ast.FixedLiteral(raw=raw)
        else:
            node = ast.IntLiteral(raw=raw)
        return self._set_pos(node, tok)

    def STRING_LITERAL(self, tok):
        raw = tok.value
        node = ast.StringLiteral(raw=raw)
        return self._set_pos(node, tok)

    def TRUE(self,tok):
        node = ast.BoolLiteral(value=True)
        return self._set_pos(node, tok)

    def FALSE(self, tok):
        node = ast.BoolLiteral(value=False)
        return self._set_pos(node, tok)

    def NULL(self, tok):
        node = ast.NullLiteral()
        return self._set_pos(node, tok)
