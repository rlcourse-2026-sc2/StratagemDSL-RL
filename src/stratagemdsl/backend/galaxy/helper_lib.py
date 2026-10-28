"""Galaxy helper-function generators for Strat v0.4 lowering (see extensions.py).

Every helper iterates the *alive* members of a unit group with the same loop
shape v0.3 already ships (index loop, no Wait), so trigger bodies stay atomic.
"""

LOOP_LOCALS = ["    int lv_i;", "    int lv_n;", "    unit lv_u;"]
LOOP_HEAD = [
    "    lv_n = UnitGroupCount(lp_g, c_unitCountAll);",
    "    lv_i = 1;",
    "    while (lv_i <= lv_n) {",
    "        lv_u = UnitGroupUnit(lp_g, lv_i);",
]
LOOP_TAIL = ["        lv_i = (lv_i + 1);", "    }"]


def _params(extra):
    return ", ".join(["unitgroup lp_g"] + [f"{t} {n}" for t, n in extra])


def agg(name, extra, kind, expr, rtype="fixed", init=None, guard="(UnitIsAlive(lv_u) == true)", locals_=()):
    """kind: any | all | count | sum | min | max over alive members.
    `expr` is a Galaxy expression in terms of lv_u and the extra params."""
    ret = {"any": "bool", "all": "bool", "count": "int"}.get(kind, rtype)
    lines = [f"{ret} {name} ({_params(extra)}) {{", *LOOP_LOCALS, *[f"    {l};" for l in locals_]]
    if kind == "any":
        body = [f"        if ({guard} && ({expr})) {{", "            return true;", "        }"]
        tail = ["    return false;", "}"]
        lines += LOOP_HEAD + body + LOOP_TAIL + tail
    elif kind == "all":
        lines += ["    bool lv_seen;", "    lv_seen = false;"] + LOOP_HEAD + [
            f"        if ({guard}) {{",
            "            lv_seen = true;",
            f"            if (!({expr})) {{",
            "                return false;",
            "            }",
            "        }",
        ] + LOOP_TAIL + ["    return lv_seen;", "}"]
    elif kind == "count":
        lines += ["    int lv_c;", "    lv_c = 0;"] + LOOP_HEAD + [
            f"        if ({guard} && ({expr})) {{", "            lv_c = (lv_c + 1);", "        }"
        ] + LOOP_TAIL + ["    return lv_c;", "}"]
    elif kind == "sum":
        zero = "0" if ret == "int" else "0.0"
        lines += [f"    {ret} lv_s;", f"    lv_s = {zero};"] + LOOP_HEAD + [
            f"        if ({guard}) {{", f"            lv_s = (lv_s + ({expr}));", "        }"
        ] + LOOP_TAIL + ["    return lv_s;", "}"]
    elif kind in ("min", "max"):
        start = init if init is not None else ("100000.0" if kind == "min" else "0.0")
        op = "<" if kind == "min" else ">"
        lines += [f"    {ret} lv_b;", f"    {ret} lv_v;", f"    lv_b = {start};"] + LOOP_HEAD + [
            f"        if ({guard}) {{",
            f"            lv_v = ({expr});",
            f"            if (lv_v {op} lv_b) {{",
            "                lv_b = lv_v;",
            "            }",
            "        }",
        ] + LOOP_TAIL + ["    return lv_b;", "}"]
    else:
        raise ValueError(kind)
    return name, lines


def foreach(name, extra, stmts, guard="(UnitIsAlive(lv_u) == true)"):
    """Apply statement(s) to every alive member (actions / rewrites)."""
    body = [f"        if ({guard}) {{"] + [f"            {s}" for s in stmts] + ["        }"]
    return name, [f"void {name} ({_params(extra)}) {{", *LOOP_LOCALS] + LOOP_HEAD + body + LOOP_TAIL + ["}"]


def raw(name, lines):
    return name, lines


def pairwise_any(name, extra, expr):
    """True if any alive u in lp_g and alive t in lp_h satisfy expr(lv_u, lv_t)."""
    lines = [f"bool {name} (unitgroup lp_g, unitgroup lp_h{''.join(', ' + t + ' ' + n for t, n in extra)}) {{",
             *LOOP_LOCALS, "    int lv_j;", "    int lv_m;", "    unit lv_t;",
             "    lv_m = UnitGroupCount(lp_h, c_unitCountAll);"] + LOOP_HEAD + [
        "        if (UnitIsAlive(lv_u) == true) {",
        "            lv_j = 1;",
        "            while (lv_j <= lv_m) {",
        "                lv_t = UnitGroupUnit(lp_h, lv_j);",
        f"                if ((UnitIsAlive(lv_t) == true) && ({expr})) {{",
        "                    return true;",
        "                }",
        "                lv_j = (lv_j + 1);",
        "            }",
        "        }",
    ] + LOOP_TAIL + ["    return false;", "}"]
    return name, lines
