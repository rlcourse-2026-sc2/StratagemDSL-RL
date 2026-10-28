"""ANTLR frontend (canonical syntax) for StratagemDSL.

The generated lexer/parser/visitor live in ``frontend/_generated`` and were
produced from ``grammar/StratagemDSL.g4`` with ANTLR 4.13.2:

    antlr4 -Dlanguage=Python3 -visitor -no-listener -Xexact-output-dir \
        -o src/stratagemdsl/frontend/_generated src/stratagemdsl/frontend/grammar/StratagemDSL.g4

Regenerated for v0.6 (Petri-net plans); the parser now matches the .g4
exactly, so the former ROUTE token adjustment and Lark fallback are gone.

Every ``visit<Name>`` here is a .g4 rule or alternative label, and the Lark
transformer in ``lark_parser`` has the same name in snake_case
(``visitWorldSection`` = ``world_section``, ``visitArcRead`` = ``arc_read``).
A labeled context only has accessors for the tokens of its own alternative,
so each label gets its own method instead of one method testing tokens.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from stratagemdsl.core.model import (
    Strategy, EntityDecl, Intent, DerivedFact, Plan, Phase, Join, Place, Arc, Transition,
    ActionBlock, Binding, BindingArg, BindingCall,
    NameExpr, BoolExpr, NumberExpr, StringExpr, CallExpr, UnaryExpr, BinaryExpr,
)


class SyntaxErrorCollector(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors: list[str] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"{line}:{column}: {msg}")


def _imports():
    try:
        from stratagemdsl.frontend._generated.StratagemDSLLexer import StratagemDSLLexer
        from stratagemdsl.frontend._generated.StratagemDSLParser import StratagemDSLParser
        from stratagemdsl.frontend._generated.StratagemDSLVisitor import StratagemDSLVisitor
        return StratagemDSLLexer, StratagemDSLParser, StratagemDSLVisitor
    except ImportError as e:
        raise RuntimeError(
            "ANTLR generated sources are missing; regenerate them as described "
            "in the docstring of stratagemdsl.frontend.antlr_parser"
        ) from e


def _unquote(text: str) -> str:
    return json.loads(text)


def parse_document(source: str):
    """Raw ANTLR parse tree of ``source``, plus the parser that built it.

    Raises SyntaxError when the checked-in parser rejects the source. Unlike
    parse_source, a parameterized pattern block is not handed off to Lark.
    """
    StratagemDSLLexer, StratagemDSLParser, _Visitor = _imports()

    lexer = StratagemDSLLexer(InputStream(source))
    lex_errors = SyntaxErrorCollector()
    lexer.removeErrorListeners()
    lexer.addErrorListener(lex_errors)

    tokens = CommonTokenStream(lexer)
    parser = StratagemDSLParser(tokens)
    parse_errors = SyntaxErrorCollector()
    parser.removeErrorListeners()
    parser.addErrorListener(parse_errors)

    tree = parser.document()
    errors = lex_errors.errors + parse_errors.errors
    if errors:
        raise SyntaxError("\n".join(errors))
    return tree, parser


def parse_source(source: str) -> Strategy:
    _Lexer, _Parser, Visitor = _imports()
    tree, _parser = parse_document(source)
    from stratagemdsl.frontend.lark_parser import make_transition

    class Builder(Visitor):
        # ---------------- expressions ----------------
        def visitStringLiteral(self, ctx): return StringExpr(_unquote(ctx.STRING().getText()))
        def visitNumberLiteral(self, ctx): return NumberExpr(float(ctx.getText()))
        def visitTrueLiteral(self, ctx): return BoolExpr(True)
        def visitFalseLiteral(self, ctx): return BoolExpr(False)

        def visitCallExpr(self, ctx):
            args = []
            if ctx.argumentList() is not None:
                args = [self.visit(e) for e in ctx.argumentList().expr()]
            return CallExpr(ctx.ID().getText(), args)

        def visitExpr(self, ctx):
            return self.visit(ctx.getChild(0))

        def _left_op(self, ctx):
            if ctx.getChildCount() == 1:
                return self.visit(ctx.getChild(0))
            return BinaryExpr(
                ctx.getChild(1).getText(),
                self.visit(ctx.getChild(0)),
                self.visit(ctx.getChild(2)),
            )

        def visitImplication(self, ctx):
            if ctx.getChildCount() == 1:
                return self.visit(ctx.getChild(0))
            return BinaryExpr("implies", self.visit(ctx.orExpr()), self.visit(ctx.implication()))

        visitOrExpr = _left_op
        visitAndExpr = _left_op
        visitComparison = _left_op
        visitSumExpr = _left_op
        visitProductExpr = _left_op

        def visitUnaryExpr(self, ctx):
            if ctx.getChildCount() == 1:
                return self.visit(ctx.getChild(0))
            return UnaryExpr(ctx.getChild(0).getText(), self.visit(ctx.unaryExpr()))

        def visitAtom(self, ctx):
            if ctx.callExpr() is not None:
                return self.visit(ctx.callExpr())
            if ctx.literal() is not None:
                return self.visit(ctx.literal())
            if ctx.expr() is not None:
                return self.visit(ctx.expr())
            return NameExpr(ctx.ID().getText())

        # ---------------- world ----------------
        def visitStrLit(self, ctx): return _unquote(ctx.STRING().getText())
        def visitNumLit(self, ctx): return float(ctx.getText())
        def visitTrueLit(self, ctx): return True
        def visitFalseLit(self, ctx): return False
        def visitNameLit(self, ctx): return ctx.softId().getText()
        def visitListLit(self, ctx): return self.visit(ctx.listValue())

        def visitListValue(self, ctx):
            return [self.visit(v) for v in ctx.propertyValue()]

        def visitPropertyStmt(self, ctx):
            return ctx.softId().getText(), self.visit(ctx.propertyValue())

        def _entity(self, kind, ctx):
            props = {}
            if ctx.entityBody() is not None:
                props = dict(self.visit(p) for p in ctx.entityBody().propertyStmt())
            return EntityDecl(kind, ctx.ID().getText(), props)

        def visitForceDecl(self, ctx): return self._entity("force", ctx)
        def visitAssetDecl(self, ctx): return self._entity("asset", ctx)
        def visitRegionDecl(self, ctx): return self._entity("region", ctx)
        def visitRouteDecl(self, ctx): return self._entity("route", ctx)

        def visitWorldSection(self, ctx):
            return [self.visit(e) for e in ctx.entityDecl()]

        # ---------------- intent ----------------
        def visitInitialSection(self, ctx):
            return [self.visit(s.expr()) for s in ctx.exprStmt()]

        def visitPatternSimple(self, ctx):
            return ctx.ID().getText(), {}

        def visitPatternBound(self, ctx):
            return ctx.ID().getText(), dict(self.visit(b) for b in ctx.patternRoleBinding())

        def visitPatternRoleBinding(self, ctx):
            return ctx.ID(0).getText(), ctx.ID(1).getText()

        def visitIntentSection(self, ctx):
            pattern, pattern_bindings = None, {}
            if ctx.patternStmt():
                pattern, pattern_bindings = self.visit(ctx.patternStmt())
            primary = self.visit(ctx.primaryStmt().expr())
            secondary = self.visit(ctx.secondaryStmt().expr()) if ctx.secondaryStmt() else None
            success = self.visit(ctx.successStmt().expr())
            failure = self.visit(ctx.failureStmt().expr())
            return Intent(pattern, primary, secondary, success, failure, pattern_bindings)

        def visitDerivedDecl(self, ctx):
            return DerivedFact(ctx.ID().getText(), self.visit(ctx.expr()))

        def visitSemanticsSection(self, ctx):
            return [self.visit(d) for d in ctx.derivedDecl()]

        # ---------------- action blocks ----------------
        def visitActionStmt(self, ctx):
            return self.visit(ctx.callExpr())

        def visitSequentialBlock(self, ctx):
            return ActionBlock("sequence", [self.visit(a) for a in ctx.actionStmt()])

        def visitParallelBlock(self, ctx):
            return ActionBlock("parallel", [self.visit(a) for a in ctx.actionStmt()])

        def _name_list(self, ctx):
            return [x.getText() for x in ctx.ID()]

        def visitPhaseDecl(self, ctx):
            return Phase(
                id=ctx.ID().getText(),
                purpose=self.visit(ctx.purposeStmt()),
                actors=self._name_list(ctx.actorsStmt().nameList()) if ctx.actorsStmt() else [],
                focus=self._name_list(ctx.focusStmt().nameList()) if ctx.focusStmt() else [],
                entry=self.visit(ctx.entryStmt().expr()) if ctx.entryStmt() else None,
                actions=self.visit(ctx.doStmt().actionBlock()) if ctx.doStmt() else None,
                invariant=self.visit(ctx.invariantStmt().expr()) if ctx.invariantStmt() else None,
                exit=self.visit(ctx.exitStmt().expr()) if ctx.exitStmt() else None,
                terminal=self.visit(ctx.terminalStmt().terminalKind()) if ctx.terminalStmt() else None,
                repeatable=ctx.repeatableStmt() is not None,
            )

        def visitPurposeStmt(self, ctx):
            return _unquote(ctx.STRING().getText())

        def visitTerminalSuccess(self, ctx): return "success"
        def visitTerminalFailure(self, ctx): return "failure"

        def visitPlaceTokensStmt(self, ctx): return int(ctx.INT().getText())
        def visitCapacityStmt(self, ctx): return int(ctx.INT().getText())

        def visitPlaceDecl(self, ctx):
            return Place(
                ctx.ID().getText(),
                self.visit(ctx.purposeStmt()) if ctx.purposeStmt() else "",
                self.visit(ctx.placeTokensStmt()) if ctx.placeTokensStmt() else 0,
                self.visit(ctx.capacityStmt()) if ctx.capacityStmt() else None,
            )

        def visitArcNormal(self, ctx): return Arc(ctx.ID().getText())
        def visitArcWeighted(self, ctx): return Arc(ctx.ID().getText(), int(ctx.INT().getText()))
        def visitArcRead(self, ctx): return Arc(ctx.ID().getText(), 1, "read")
        def visitArcReadWeighted(self, ctx): return Arc(ctx.ID().getText(), int(ctx.INT().getText()), "read")
        def visitArcInhibit(self, ctx): return Arc(ctx.ID().getText(), 1, "inhibit")
        def visitArcInhibitWeighted(self, ctx): return Arc(ctx.ID().getText(), int(ctx.INT().getText()), "inhibit")

        def visitArcList(self, ctx):
            return [self.visit(a) for a in ctx.arc()]

        def visitJoinAll(self, ctx): return "all", None
        def visitJoinAny(self, ctx): return "any", None
        def visitJoinAtleast(self, ctx): return "atleast", int(ctx.INT().getText())

        def visitJoinDecl(self, ctx):
            policy, quorum = self.visit(ctx.joinPolicy())
            return Join(ctx.ID().getText(), policy, quorum)

        def visitTransitionDecl(self, ctx):
            return make_transition(
                ctx.ID().getText(),
                self.visit(ctx.arcList(0)),
                self.visit(ctx.arcList(1)),
                self.visit(ctx.onStmt().callExpr()) if ctx.onStmt() else None,
                self.visit(ctx.whenStmt().expr()) if ctx.whenStmt() else None,
                self.visit(ctx.doStmt().actionBlock()) if ctx.doStmt() else None,
                int(ctx.INT().getText()),
            )

        def visitPlanNode(self, ctx):
            return self.visit(ctx.getChild(0))

        def visitPlanSection(self, ctx):
            start = self._name_list(ctx.startStmt().nameList())
            nodes = [self.visit(n) for n in ctx.planNode()]
            transitions = [self.visit(t) for t in ctx.transitionDecl()]
            return Plan(start, nodes, transitions)

        # ---------------- bindings ----------------
        def visitBindingCall(self, ctx):
            args = []
            if ctx.bindingArgList():
                args = [self.visit(a) for a in ctx.bindingArgList().bindingArg()]
            return BindingCall(ctx.bindingCtor().getText(), args)

        def visitBindingString(self, ctx): return _unquote(ctx.STRING().getText())
        def visitBindingNumber(self, ctx): return float(ctx.getText())
        def visitBindingTrue(self, ctx): return True
        def visitBindingFalse(self, ctx): return False
        def visitBindingName(self, ctx): return ctx.softId().getText()
        def visitBindingList(self, ctx): return [self.visit(e) for e in ctx.bindingExpr()]

        def visitNamedBindingArg(self, ctx):
            return BindingArg(ctx.softId().getText(), self.visit(ctx.bindingExpr()))

        def visitPositionalBindingArg(self, ctx):
            return BindingArg(None, self.visit(ctx.bindingExpr()))

        def visitBindingStmt(self, ctx):
            return Binding(ctx.ID().getText(), self.visit(ctx.bindingExpr()))

        def visitBindingSection(self, ctx):
            return (
                ctx.ID().getText(),
                [self.visit(b) for b in ctx.bindingStmt()],
            )

        def visitStrategyDecl(self, ctx):
            name = ctx.ID().getText()
            world = self.visit(ctx.worldSection())
            initial = self.visit(ctx.initialSection()) if ctx.initialSection() else []
            intent = self.visit(ctx.intentSection())
            derived = self.visit(ctx.semanticsSection()) if ctx.semanticsSection() else []
            plan = self.visit(ctx.planSection())
            backend = None
            bindings = []
            if ctx.bindingSection():
                backend, bindings = self.visit(ctx.bindingSection())
            return Strategy(name, world, initial, intent, derived, plan, backend, bindings)

        def visitDocument(self, ctx):
            return self.visit(ctx.strategyDecl())

    return Builder().visit(tree)


def parse_file(path: str | Path) -> Strategy:
    return parse_source(Path(path).read_text(encoding="utf-8"))
