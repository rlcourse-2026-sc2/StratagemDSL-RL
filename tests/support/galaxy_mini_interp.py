"""
A deliberately tiny interpreter for the specific, narrow subset of Galaxy
syntax GalaxyLowerer actually emits (variable assignment, if-blocks, boolean/
arithmetic comparisons, and native-function calls treated as recorded
no-ops). This exists specifically because a prior external review correctly
pointed out that asserting on substrings of the generated TEXT ("does the
string 'gv_phase_active_done = true' appear somewhere") does not prove
anything about actual RUNTIME behavior -- two correct-looking lines in the
wrong nesting/ordering can still produce wrong behavior. This interpreter
actually EXECUTES the generated trigger bodies against a globals dict and a
call-count dict, so tests can assert on real post-execution state.

Not a general Galaxy/C interpreter -- it only supports the exact grammar
shapes GalaxyLowerer's own code generation produces (see the private `_'
helpers below). Anything outside that raises, on purpose, rather than being
silently approximated -- an unsupported shape should fail loudly, not give
a false sense of coverage.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class GalaxyMiniState:
    globals: dict = field(default_factory=dict)
    calls: dict = field(default_factory=lambda: {})  # function name -> count
    trigger_enabled: dict = field(default_factory=dict)  # trigger var name -> bool
    # Configurable native-call return values, keyed by (function_name,
    # evaluated_args_tuple). A call not found here falls back to
    # `native_default` (True). This is what lets a test distinguish e.g.
    # UnitGroupCount(gv_a, ...) == 0 from UnitGroupCount(gv_b, ...) > 0
    # instead of every native call being an indistinguishable "always
    # true" no-op -- needed to exercise "only the low-priority guard is
    # true" style scenarios, not just "both guards happen to be checking
    # the same underlying fact and are therefore always true together".
    native_returns: dict = field(default_factory=dict)
    native_default: object = True

    def record_call(self, name: str):
        self.calls[name] = self.calls.get(name, 0) + 1

    def native_call(self, name: str, args: tuple):
        self.record_call(name)
        return self.native_returns.get((name, args), self.native_default)


_TOKEN_RE = re.compile(r"""
    \s*(?:
        (?P<num>\d+(?:\.\d+)?)
      | (?P<true>true\b)
      | (?P<false>false\b)
      | (?P<andand>&&)
      | (?P<oror>\|\|)
      | (?P<eq>==)
      | (?P<ne>!=)
      | (?P<ge>>=)
      | (?P<le><=)
      | (?P<not>!)
      | (?P<gt>>)
      | (?P<lt><)
      | (?P<plus>\+)
      | (?P<minus>-)
      | (?P<lparen>\()
      | (?P<rparen>\))
      | (?P<comma>,)
      | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
    )
""", re.X)


def _tokenize(expr: str) -> list[tuple[str, str]]:
    pos = 0
    out = []
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m or m.end() == pos:
            if expr[pos:].strip() == "":
                break
            raise ValueError(f"cannot tokenize: {expr[pos:pos+30]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


class _ExprEval:
    """Recursive-descent evaluator, precedence low->high:
    || , && , == != , >= <= > < , + , unary ! , atom/call/paren."""

    def __init__(self, tokens, state: GalaxyMiniState):
        self.toks = tokens
        self.i = 0
        self.state = state

    def _peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def _eat(self, kind=None):
        k, v = self._peek()
        if kind is not None and k != kind:
            raise ValueError(f"expected {kind}, got {k} ({v!r}) at {self.i}")
        self.i += 1
        return v

    def parse(self):
        v = self.or_expr()
        if self.i != len(self.toks):
            raise ValueError(f"trailing tokens: {self.toks[self.i:]}")
        return v

    def or_expr(self):
        v = self.and_expr()
        while self._peek()[0] == "oror":
            self._eat("oror")
            # Always parse the right-hand side even if `v` already
            # determines the result -- using Python's short-circuiting
            # `or`/`and` here would skip calling self.and_expr()/cmp_expr()
            # when the left side already decides the outcome, leaving the
            # parser's position stuck mid-expression and making the
            # top-level "did we consume every token" check fail even
            # though the boolean LOGIC would have been correct.
            rhs = self.and_expr()
            v = v or rhs
        return v

    def and_expr(self):
        v = self.cmp_expr()
        while self._peek()[0] == "andand":
            self._eat("andand")
            rhs = self.cmp_expr()  # always parsed -- see or_expr's comment
            v = v and rhs
        return v

    def cmp_expr(self):
        v = self.add_expr()
        k, _ = self._peek()
        while k in ("eq", "ne", "ge", "le", "gt", "lt"):
            self._eat(k)
            rhs = self.add_expr()
            v = {"eq": v == rhs, "ne": v != rhs, "ge": v >= rhs,
                 "le": v <= rhs, "gt": v > rhs, "lt": v < rhs}[k]
            k, _ = self._peek()
        return v

    def add_expr(self):
        v = self.unary()
        while self._peek()[0] in ("plus", "minus"):
            op = self._eat()
            rhs = self.unary()
            v = v + rhs if op == "+" else v - rhs
        return v

    def unary(self):
        if self._peek()[0] == "not":
            self._eat("not")
            return not self.unary()
        if self._peek()[0] == "minus":
            self._eat("minus")
            return -self.unary()
        return self.atom()

    def atom(self):
        k, v = self._peek()
        if k == "num":
            self._eat()
            return float(v) if "." in v else int(v)
        if k == "true":
            self._eat()
            return True
        if k == "false":
            self._eat()
            return False
        if k == "lparen":
            self._eat("lparen")
            v = self.or_expr()
            self._eat("rparen")
            return v
        if k == "ident":
            name = self._eat("ident")
            if self._peek()[0] == "lparen":
                self._eat("lparen")
                args = []
                if self._peek()[0] != "rparen":
                    args.append(self.or_expr())
                    while self._peek()[0] == "comma":
                        self._eat("comma")
                        args.append(self.or_expr())
                self._eat("rparen")
                return self.state.native_call(name, tuple(args))
            if name not in self.state.globals:
                if name.startswith("c_"):
                    # Galaxy built-in constant (e.g. c_unitCountAlive) used
                    # only as an opaque argument to a native call this
                    # interpreter already treats as a no-op -- its actual
                    # value never affects any assignment or condition this
                    # interpreter evaluates, so a placeholder is safe.
                    return 0
                raise ValueError(f"unknown identifier '{name}' referenced before assignment")
            return self.state.globals[name]
        raise ValueError(f"unexpected token {k} ({v!r})")


def eval_expr(expr: str, state: GalaxyMiniState):
    return _ExprEval(_tokenize(expr), state).parse()


_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+);$")
_IF_OPEN_RE = re.compile(r"^if\s*\((.+)\)\s*\{$")
_ELSE_IF_RE = re.compile(r"^\}\s*else if\s*\((.+)\)\s*\{$")
_CALL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(.*\)\s*;$")
_TRIGGER_ENABLE_RE = re.compile(r"^TriggerEnable\(([A-Za-z_][A-Za-z0-9_]*),\s*(true|false)\)\s*;$")
_RETURN_RE = re.compile(r"^return\s+.*;$")


def _find_branch_end(lines: list[str], start_idx: int) -> int:
    """`lines[start_idx]` is the first line INSIDE a branch body (right
    after its opening `{`). Returns the index of the line that closes this
    branch: either a bare `}` (the if/else-if chain ends here) or a
    `} else if (...) {` continuation (more branches follow) -- found by
    tracking brace depth, where any OTHER line ending in `{` increases
    depth and a bare `}` decreases it; a continuation or closer seen at
    depth 0 is this branch's own end."""
    depth = 0
    j = start_idx
    while True:
        l2 = lines[j].strip()
        if depth == 0 and (_ELSE_IF_RE.match(l2) or l2 == "}"):
            return j
        if l2.endswith("{"):
            depth += 1
        elif l2 == "}":
            depth -= 1
        j += 1


def run_block(lines: list[str], state: GalaxyMiniState) -> None:
    """Executes a flat list of already-dedented statement lines (assignment,
    call, or an `if (...) { ... } else if (...) { ... }` chain -- with no
    trailing bare `else`, which nothing this interpreter targets currently
    generates) against `state`. Raises on anything outside the supported
    shapes -- see module docstring."""
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == "" or line == "}":
            i += 1
            continue
        m = _IF_OPEN_RE.match(line)
        if m:
            branch_start = i + 1
            cond_text = m.group(1)
            handled = False
            while True:
                branch_end = _find_branch_end(lines, branch_start)
                if not handled and bool(eval_expr(cond_text, state)):
                    run_block(lines[branch_start:branch_end], state)
                    handled = True
                closer = lines[branch_end].strip()
                m2 = _ELSE_IF_RE.match(closer)
                if m2:
                    cond_text = m2.group(1)
                    branch_start = branch_end + 1
                    continue
                i = branch_end + 1
                break
            continue
        m = _TRIGGER_ENABLE_RE.match(line)
        if m:
            state.trigger_enabled[m.group(1)] = (m.group(2) == "true")
            i += 1
            continue
        if _RETURN_RE.match(line):
            i += 1
            continue
        m = _ASSIGN_RE.match(line)
        if m:
            name, expr = m.group(1), m.group(2)
            state.globals[name] = eval_expr(expr, state)
            i += 1
            continue
        m = _CALL_RE.match(line)
        if m:
            state.record_call(m.group(1))
            i += 1
            continue
        raise ValueError(f"unsupported statement shape: {line!r}")


def extract_func_body_lines(galaxy_src: str, func_name: str) -> list[str]:
    """Pulls the statement lines between `if (!runActions) { return true; }`
    and the closing brace of a `bool <func>(...) {...}` definition -- i.e.
    just the `runActions` action body, skipping the testConds guard block
    (tests drive testConds pass/fail explicitly via which trigger they
    choose to run, matching how the real engine only runs actions after
    conditions already passed)."""
    m = re.search(re.escape(func_name) + r"\s*\(bool testConds, bool runActions\)\s*\{(.*?)\n\}", galaxy_src, re.S)
    if not m:
        raise AssertionError(f"{func_name} not found")
    body = m.group(1)
    marker = "if (!runActions) {\n        return true;\n    }\n"
    idx = body.find(marker)
    if idx == -1:
        raise AssertionError(f"{func_name}: could not find the runActions guard to split on")
    action_text = body[idx + len(marker):]
    return [l for l in action_text.split("\n")]


def extract_test_conds(galaxy_src: str, func_name: str) -> str | None:
    """Returns a single combined boolean expression string for every
    `if (!(<cond>)) { return false; }` inside the testConds block, ANDed
    together (mirrors what the real trigger would require to actually run
    its actions), or None if there is no testConds block at all."""
    m = re.search(re.escape(func_name) + r"\s*\(bool testConds, bool runActions\)\s*\{(.*?)\n\}", galaxy_src, re.S)
    if not m:
        raise AssertionError(f"{func_name} not found")
    body = m.group(1)
    if "if (testConds) {" not in body:
        return None
    conds = re.findall(r"if \(!\((.+)\)\) \{\s*return false;\s*\}", body)
    if not conds:
        return "true"
    return " && ".join(f"({c})" for c in conds)
