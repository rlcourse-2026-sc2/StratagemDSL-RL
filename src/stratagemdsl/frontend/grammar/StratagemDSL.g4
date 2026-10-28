grammar StratagemDSL;

/*
 * StratagemDSL v0.6 (Petri-net plans)
 *
 * Canonical source model:
 *   World + Initial State + Strategic Intent + Petri-net PlanGraph + Backend Binding
 *
 * The plan is a place/transition net: phases, joins and `place` declarations
 * are places; `transition t: a, b*2, ?c, !d -> e, f` lists input arcs
 * (normal, weighted, read, inhibitor) and output arcs. `a -> b` is the
 * single-arc special case and keeps its v0.2 meaning.
 *
 * This grammar is intentionally NOT PDDL/HDDL-shaped.
 *
 * Naming contract with StratagemDSL.lark (checked by
 * tests/l1_frontend/test_grammar_names.py):
 *   - every parser rule here is a Lark rule with the same name in snake_case
 *     (strategyDecl = strategy_decl, sumExpr = sum_expr), and vice versa;
 *   - where alternatives build different kinds of value, every alternative is
 *     labeled, and the labels are the Lark aliases in PascalCase
 *     (# ForceDecl = -> force_decl);
 *   - the expression chain (expr ... atom) and the pure-choice rules (planNode,
 *     softId, bindingCtor) are unlabeled on both sides.
 */

document
    : strategyDecl EOF
    ;

strategyDecl
    : STRATEGY ID LBRACE
      worldSection
      initialSection?
      intentSection
      semanticsSection?
      planSection
      bindingSection?
      RBRACE
    ;

// -----------------------------------------------------------------------------
// World model
// -----------------------------------------------------------------------------

worldSection
    : WORLD LBRACE entityDecl* RBRACE
    ;

entityDecl
    : FORCE ID entityBody? SEMI?                # ForceDecl
    | ASSET ID entityBody? SEMI?                # AssetDecl
    | REGION ID entityBody? SEMI?               # RegionDecl
    | ROUTE ID entityBody? SEMI?                # RouteDecl
    ;

entityBody
    : LBRACE propertyStmt* RBRACE
    ;

propertyStmt
    : softId ASSIGN propertyValue SEMI
    ;

// A negative value is one token in Lark (PROP_NUMBER); here the predicate
// requires the digits to follow the minus directly, so `- 3` fails in both.
propertyValue
    : STRING                                    # StrLit
    | INT                                       # NumLit
    | NUMBER                                    # NumLit
    | MINUS INT {$INT.line * 100000 + $INT.pos == $MINUS.line * 100000 + $MINUS.pos + 1}?          # NumLit
    | MINUS NUMBER {$NUMBER.line * 100000 + $NUMBER.pos == $MINUS.line * 100000 + $MINUS.pos + 1}? # NumLit
    | TRUE                                      # TrueLit
    | FALSE                                     # FalseLit
    | softId                                    # NameLit
    | listValue                                 # ListLit
    ;

// Structural keywords that must still be usable as ordinary property/binding
// identifiers (e.g. `initial = false;`, `asset = enemy_home`), since the DSL
// corpus and lowering backend both use these words as plain field names.
// Deliberately excludes TRUE/FALSE/NOT/AND/OR/IMPLIES, which keep their
// operator/literal meaning everywhere.
softId
    : ID
    | STRATEGY | WORLD | INITIAL | INTENT | SEMANTICS | DERIVE | PATTERN
    | PRIMARY | SECONDARY | SUCCESS | FAILURE
    | FORCE | ASSET | REGION | ROUTE
    | PLAN | START | PHASE | JOIN | PURPOSE | ACTORS | FOCUS | ENTRY | DO
    | INVARIANT | EXIT | TERMINAL | TRANSITION | ON | WHEN | PRIORITY
    | ALL | ANY | ATLEAST | SEQUENCE | PARALLEL
    | BINDING | PLACE | CAPACITY | REPEATABLE
    ;

listValue
    : LBRACK (propertyValue (COMMA propertyValue)*)? RBRACK
    ;

// -----------------------------------------------------------------------------
// Initial state + strategic intent
// -----------------------------------------------------------------------------

initialSection
    : INITIAL LBRACE exprStmt* RBRACE
    ;

exprStmt
    : expr SEMI
    ;

intentSection
    : INTENT LBRACE
      patternStmt?
      primaryStmt
      secondaryStmt?
      successStmt
      failureStmt
      RBRACE
    ;

patternStmt
    : PATTERN ID SEMI                                   # PatternSimple
    | PATTERN ID LBRACE patternRoleBinding* RBRACE      # PatternBound
    ;

patternRoleBinding
    : ID ASSIGN ID SEMI
    ;

primaryStmt
    : PRIMARY expr SEMI
    ;

secondaryStmt
    : SECONDARY expr SEMI
    ;

successStmt
    : SUCCESS expr SEMI
    ;

failureStmt
    : FAILURE expr SEMI
    ;


semanticsSection
    : SEMANTICS LBRACE derivedDecl* RBRACE
    ;

derivedDecl
    : DERIVE ID ASSIGN expr SEMI
    ;

// -----------------------------------------------------------------------------
// Canonical PlanGraph
// -----------------------------------------------------------------------------

planSection
    : PLAN LBRACE
      startStmt
      planNode+
      transitionDecl*
      RBRACE
    ;

startStmt
    : START nameList SEMI
    ;

planNode
    : phaseDecl
    | joinDecl
    | placeDecl
    ;

phaseDecl
    : PHASE ID LBRACE
      purposeStmt
      repeatableStmt?
      actorsStmt?
      focusStmt?
      entryStmt?
      doStmt?
      invariantStmt?
      exitStmt?
      terminalStmt?
      RBRACE
    ;

purposeStmt
    : PURPOSE STRING SEMI
    ;

repeatableStmt
    : REPEATABLE SEMI
    ;

actorsStmt
    : ACTORS nameList SEMI
    ;

focusStmt
    : FOCUS nameList SEMI
    ;

entryStmt
    : ENTRY expr SEMI
    ;

doStmt
    : DO actionBlock
    ;

invariantStmt
    : INVARIANT expr SEMI
    ;

exitStmt
    : EXIT expr SEMI
    ;

terminalStmt
    : TERMINAL terminalKind SEMI
    ;

terminalKind
    : SUCCESS                                   # TerminalSuccess
    | FAILURE                                   # TerminalFailure
    ;

joinDecl
    : JOIN ID joinPolicy SEMI
    ;

joinPolicy
    : ALL                                       # JoinAll
    | ANY                                       # JoinAny
    | ATLEAST LPAREN INT RPAREN                 # JoinAtleast
    ;

// v0.6 token place: no actions, only a marking and an optional bound.
placeDecl
    : PLACE ID LBRACE
      purposeStmt?
      placeTokensStmt?
      capacityStmt?
      RBRACE
    ;

placeTokensStmt
    : INITIAL INT SEMI
    ;

capacityStmt
    : CAPACITY INT SEMI
    ;

transitionDecl
    : TRANSITION ID COLON arcList ARROW arcList LBRACE
      onStmt?
      whenStmt?
      doStmt?
      PRIORITY INT SEMI
      RBRACE
    ;

arcList
    : arc (COMMA arc)*
    ;

arc
    : ID                                        # ArcNormal
    | ID MUL INT                                # ArcWeighted
    | QMARK ID                                  # ArcRead
    | QMARK ID MUL INT                          # ArcReadWeighted
    | BANG ID                                   # ArcInhibit
    | BANG ID MUL INT                           # ArcInhibitWeighted
    ;

onStmt
    : ON callExpr SEMI
    ;

whenStmt
    : WHEN expr SEMI
    ;

actionBlock
    : LBRACE actionStmt* RBRACE                 # SequentialBlock
    | SEQUENCE LBRACE actionStmt* RBRACE        # SequentialBlock
    | PARALLEL LBRACE actionStmt* RBRACE        # ParallelBlock
    ;

actionStmt
    : callExpr SEMI
    ;

nameList
    : LBRACK (ID (COMMA ID)*)? RBRACK
    ;

// -----------------------------------------------------------------------------
// Backend binding
// -----------------------------------------------------------------------------

bindingSection
    : BINDING ID LBRACE bindingStmt* RBRACE
    ;

bindingStmt
    : ID ASSIGN bindingExpr SEMI
    ;

bindingExpr
    : bindingCtor LPAREN bindingArgList? RPAREN # BindingCall
    | STRING                                    # BindingString
    | INT                                       # BindingNumber
    | NUMBER                                    # BindingNumber
    | MINUS INT {$INT.line * 100000 + $INT.pos == $MINUS.line * 100000 + $MINUS.pos + 1}?          # BindingNumber
    | MINUS NUMBER {$NUMBER.line * 100000 + $NUMBER.pos == $MINUS.line * 100000 + $MINUS.pos + 1}? # BindingNumber
    | TRUE                                      # BindingTrue
    | FALSE                                     # BindingFalse
    | softId                                    # BindingName
    | LBRACK (bindingExpr (COMMA bindingExpr)*)? RBRACK # BindingList
    ;

bindingArgList
    : bindingArg (COMMA bindingArg)*
    ;

bindingArg
    : softId ASSIGN bindingExpr                 # NamedBindingArg
    | bindingExpr                               # PositionalBindingArg
    ;

bindingCtor
    : ID
    | ROUTE
    ;

// -----------------------------------------------------------------------------
// Expressions
// -----------------------------------------------------------------------------
//
// Layered like the Lark grammar. Comparison operands are sums, so
// `a < b == c` is not a comparison of a comparison.

expr
    : implication
    ;

implication
    : orExpr
    | orExpr IMPLIES implication
    ;

orExpr
    : andExpr
    | orExpr OR andExpr
    ;

andExpr
    : comparison
    | andExpr AND comparison
    ;

comparison
    : sumExpr
    | sumExpr op=(LT | LE | GT | GE | EQ | NEQ) sumExpr
    ;

sumExpr
    : productExpr
    | sumExpr op=(PLUS | MINUS) productExpr
    ;

productExpr
    : unaryExpr
    | productExpr op=(MUL | DIV) unaryExpr
    ;

unaryExpr
    : NOT unaryExpr
    | MINUS unaryExpr
    | atom
    ;

atom
    : LPAREN expr RPAREN
    | callExpr
    | literal
    | ID
    ;

callExpr
    : ID LPAREN argumentList? RPAREN
    ;

argumentList
    : expr (COMMA expr)*
    ;

literal
    : STRING                                    # StringLiteral
    | INT                                       # NumberLiteral
    | NUMBER                                    # NumberLiteral
    | TRUE                                      # TrueLiteral
    | FALSE                                     # FalseLiteral
    ;

// -----------------------------------------------------------------------------
// Lexer
// -----------------------------------------------------------------------------

STRATEGY : 'strategy' ;
WORLD : 'world' ;
INITIAL : 'initial' ;
INTENT : 'intent' ;
SEMANTICS : 'semantics' ;
DERIVE : 'derive' ;
PATTERN : 'pattern' ;
PRIMARY : 'primary' ;
SECONDARY : 'secondary' ;
SUCCESS : 'success' ;
FAILURE : 'failure' ;

FORCE : 'force' ;
ASSET : 'asset' ;
REGION : 'region' ;
ROUTE : 'route' ;

PLAN : 'plan' ;
START : 'start' ;
PHASE : 'phase' ;
JOIN : 'join' ;
PURPOSE : 'purpose' ;
ACTORS : 'actors' ;
FOCUS : 'focus' ;
ENTRY : 'entry' ;
DO : 'do' ;
INVARIANT : 'invariant' ;
EXIT : 'exit' ;
TERMINAL : 'terminal' ;
TRANSITION : 'transition' ;
ON : 'on' ;
WHEN : 'when' ;
PRIORITY : 'priority' ;

ALL : 'all' ;
ANY : 'any' ;
ATLEAST : 'atleast' ;
SEQUENCE : 'sequence' ;
PARALLEL : 'parallel' ;

BINDING : 'binding' ;
PLACE : 'place' ;
CAPACITY : 'capacity' ;
REPEATABLE : 'repeatable' ;

TRUE : 'true' ;
FALSE : 'false' ;
NOT : 'not' ;
AND : 'and' ;
OR : 'or' ;
IMPLIES : 'implies' ;

ARROW : '->' ;
QMARK : '?' ;
COLON : ':' ;
SEMI : ';' ;
COMMA : ',' ;
ASSIGN : '=' ;

EQ : '==' ;
NEQ : '!=' ;
BANG : '!' ;
LE : '<=' ;
GE : '>=' ;
LT : '<' ;
GT : '>' ;
PLUS : '+' ;
MINUS : '-' ;
MUL : '*' ;
DIV : '/' ;

LBRACE : '{' ;
RBRACE : '}' ;
LBRACK : '[' ;
RBRACK : ']' ;
LPAREN : '(' ;
RPAREN : ')' ;

INT
    : [0-9]+
    ;

NUMBER
    : [0-9]+ ('.' [0-9]+)?
    ;

STRING
    : '"' ( STRING_ESC | ~["\\\r\n] )* '"'
    ;

fragment STRING_ESC
    : '\\' ( ["\\/bfnrt] | 'u' HEX HEX HEX HEX )
    ;

fragment HEX
    : [0-9a-fA-F]
    ;

ID
    : [A-Za-z_] [A-Za-z0-9_]*
    ;

COMMENT
    : '//' ~[\r\n]* -> skip
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;

WS
    : [ \t\r\n]+ -> skip
    ;
