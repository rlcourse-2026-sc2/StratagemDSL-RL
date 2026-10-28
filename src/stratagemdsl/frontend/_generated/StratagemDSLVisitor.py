# Generated from src/stratagemdsl/frontend/grammar/StratagemDSL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .StratagemDSLParser import StratagemDSLParser
else:
    from StratagemDSLParser import StratagemDSLParser

# This class defines a complete generic visitor for a parse tree produced by StratagemDSLParser.

class StratagemDSLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by StratagemDSLParser#document.
    def visitDocument(self, ctx:StratagemDSLParser.DocumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#strategyDecl.
    def visitStrategyDecl(self, ctx:StratagemDSLParser.StrategyDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#worldSection.
    def visitWorldSection(self, ctx:StratagemDSLParser.WorldSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ForceDecl.
    def visitForceDecl(self, ctx:StratagemDSLParser.ForceDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#AssetDecl.
    def visitAssetDecl(self, ctx:StratagemDSLParser.AssetDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#RegionDecl.
    def visitRegionDecl(self, ctx:StratagemDSLParser.RegionDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#RouteDecl.
    def visitRouteDecl(self, ctx:StratagemDSLParser.RouteDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#entityBody.
    def visitEntityBody(self, ctx:StratagemDSLParser.EntityBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#propertyStmt.
    def visitPropertyStmt(self, ctx:StratagemDSLParser.PropertyStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#StrLit.
    def visitStrLit(self, ctx:StratagemDSLParser.StrLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#NumLit.
    def visitNumLit(self, ctx:StratagemDSLParser.NumLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#TrueLit.
    def visitTrueLit(self, ctx:StratagemDSLParser.TrueLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#FalseLit.
    def visitFalseLit(self, ctx:StratagemDSLParser.FalseLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#NameLit.
    def visitNameLit(self, ctx:StratagemDSLParser.NameLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ListLit.
    def visitListLit(self, ctx:StratagemDSLParser.ListLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#softId.
    def visitSoftId(self, ctx:StratagemDSLParser.SoftIdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#listValue.
    def visitListValue(self, ctx:StratagemDSLParser.ListValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#initialSection.
    def visitInitialSection(self, ctx:StratagemDSLParser.InitialSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#exprStmt.
    def visitExprStmt(self, ctx:StratagemDSLParser.ExprStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#intentSection.
    def visitIntentSection(self, ctx:StratagemDSLParser.IntentSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#PatternSimple.
    def visitPatternSimple(self, ctx:StratagemDSLParser.PatternSimpleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#PatternBound.
    def visitPatternBound(self, ctx:StratagemDSLParser.PatternBoundContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#patternRoleBinding.
    def visitPatternRoleBinding(self, ctx:StratagemDSLParser.PatternRoleBindingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#primaryStmt.
    def visitPrimaryStmt(self, ctx:StratagemDSLParser.PrimaryStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#secondaryStmt.
    def visitSecondaryStmt(self, ctx:StratagemDSLParser.SecondaryStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#successStmt.
    def visitSuccessStmt(self, ctx:StratagemDSLParser.SuccessStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#failureStmt.
    def visitFailureStmt(self, ctx:StratagemDSLParser.FailureStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#semanticsSection.
    def visitSemanticsSection(self, ctx:StratagemDSLParser.SemanticsSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#derivedDecl.
    def visitDerivedDecl(self, ctx:StratagemDSLParser.DerivedDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#planSection.
    def visitPlanSection(self, ctx:StratagemDSLParser.PlanSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#startStmt.
    def visitStartStmt(self, ctx:StratagemDSLParser.StartStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#planNode.
    def visitPlanNode(self, ctx:StratagemDSLParser.PlanNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#phaseDecl.
    def visitPhaseDecl(self, ctx:StratagemDSLParser.PhaseDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#purposeStmt.
    def visitPurposeStmt(self, ctx:StratagemDSLParser.PurposeStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#repeatableStmt.
    def visitRepeatableStmt(self, ctx:StratagemDSLParser.RepeatableStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#actorsStmt.
    def visitActorsStmt(self, ctx:StratagemDSLParser.ActorsStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#focusStmt.
    def visitFocusStmt(self, ctx:StratagemDSLParser.FocusStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#entryStmt.
    def visitEntryStmt(self, ctx:StratagemDSLParser.EntryStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#doStmt.
    def visitDoStmt(self, ctx:StratagemDSLParser.DoStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#invariantStmt.
    def visitInvariantStmt(self, ctx:StratagemDSLParser.InvariantStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#exitStmt.
    def visitExitStmt(self, ctx:StratagemDSLParser.ExitStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#terminalStmt.
    def visitTerminalStmt(self, ctx:StratagemDSLParser.TerminalStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#TerminalSuccess.
    def visitTerminalSuccess(self, ctx:StratagemDSLParser.TerminalSuccessContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#TerminalFailure.
    def visitTerminalFailure(self, ctx:StratagemDSLParser.TerminalFailureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#joinDecl.
    def visitJoinDecl(self, ctx:StratagemDSLParser.JoinDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#JoinAll.
    def visitJoinAll(self, ctx:StratagemDSLParser.JoinAllContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#JoinAny.
    def visitJoinAny(self, ctx:StratagemDSLParser.JoinAnyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#JoinAtleast.
    def visitJoinAtleast(self, ctx:StratagemDSLParser.JoinAtleastContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#placeDecl.
    def visitPlaceDecl(self, ctx:StratagemDSLParser.PlaceDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#placeTokensStmt.
    def visitPlaceTokensStmt(self, ctx:StratagemDSLParser.PlaceTokensStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#capacityStmt.
    def visitCapacityStmt(self, ctx:StratagemDSLParser.CapacityStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#transitionDecl.
    def visitTransitionDecl(self, ctx:StratagemDSLParser.TransitionDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#arcList.
    def visitArcList(self, ctx:StratagemDSLParser.ArcListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ArcNormal.
    def visitArcNormal(self, ctx:StratagemDSLParser.ArcNormalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ArcWeighted.
    def visitArcWeighted(self, ctx:StratagemDSLParser.ArcWeightedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ArcRead.
    def visitArcRead(self, ctx:StratagemDSLParser.ArcReadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ArcReadWeighted.
    def visitArcReadWeighted(self, ctx:StratagemDSLParser.ArcReadWeightedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ArcInhibit.
    def visitArcInhibit(self, ctx:StratagemDSLParser.ArcInhibitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ArcInhibitWeighted.
    def visitArcInhibitWeighted(self, ctx:StratagemDSLParser.ArcInhibitWeightedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#onStmt.
    def visitOnStmt(self, ctx:StratagemDSLParser.OnStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#whenStmt.
    def visitWhenStmt(self, ctx:StratagemDSLParser.WhenStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#SequentialBlock.
    def visitSequentialBlock(self, ctx:StratagemDSLParser.SequentialBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#ParallelBlock.
    def visitParallelBlock(self, ctx:StratagemDSLParser.ParallelBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#actionStmt.
    def visitActionStmt(self, ctx:StratagemDSLParser.ActionStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#nameList.
    def visitNameList(self, ctx:StratagemDSLParser.NameListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#bindingSection.
    def visitBindingSection(self, ctx:StratagemDSLParser.BindingSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#bindingStmt.
    def visitBindingStmt(self, ctx:StratagemDSLParser.BindingStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingCall.
    def visitBindingCall(self, ctx:StratagemDSLParser.BindingCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingString.
    def visitBindingString(self, ctx:StratagemDSLParser.BindingStringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingNumber.
    def visitBindingNumber(self, ctx:StratagemDSLParser.BindingNumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingTrue.
    def visitBindingTrue(self, ctx:StratagemDSLParser.BindingTrueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingFalse.
    def visitBindingFalse(self, ctx:StratagemDSLParser.BindingFalseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingName.
    def visitBindingName(self, ctx:StratagemDSLParser.BindingNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#BindingList.
    def visitBindingList(self, ctx:StratagemDSLParser.BindingListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#bindingArgList.
    def visitBindingArgList(self, ctx:StratagemDSLParser.BindingArgListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#NamedBindingArg.
    def visitNamedBindingArg(self, ctx:StratagemDSLParser.NamedBindingArgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#PositionalBindingArg.
    def visitPositionalBindingArg(self, ctx:StratagemDSLParser.PositionalBindingArgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#bindingCtor.
    def visitBindingCtor(self, ctx:StratagemDSLParser.BindingCtorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#expr.
    def visitExpr(self, ctx:StratagemDSLParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#implication.
    def visitImplication(self, ctx:StratagemDSLParser.ImplicationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#orExpr.
    def visitOrExpr(self, ctx:StratagemDSLParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#andExpr.
    def visitAndExpr(self, ctx:StratagemDSLParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#comparison.
    def visitComparison(self, ctx:StratagemDSLParser.ComparisonContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#sumExpr.
    def visitSumExpr(self, ctx:StratagemDSLParser.SumExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#productExpr.
    def visitProductExpr(self, ctx:StratagemDSLParser.ProductExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#unaryExpr.
    def visitUnaryExpr(self, ctx:StratagemDSLParser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#atom.
    def visitAtom(self, ctx:StratagemDSLParser.AtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#callExpr.
    def visitCallExpr(self, ctx:StratagemDSLParser.CallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#argumentList.
    def visitArgumentList(self, ctx:StratagemDSLParser.ArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#StringLiteral.
    def visitStringLiteral(self, ctx:StratagemDSLParser.StringLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#NumberLiteral.
    def visitNumberLiteral(self, ctx:StratagemDSLParser.NumberLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#TrueLiteral.
    def visitTrueLiteral(self, ctx:StratagemDSLParser.TrueLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by StratagemDSLParser#FalseLiteral.
    def visitFalseLiteral(self, ctx:StratagemDSLParser.FalseLiteralContext):
        return self.visitChildren(ctx)



del StratagemDSLParser