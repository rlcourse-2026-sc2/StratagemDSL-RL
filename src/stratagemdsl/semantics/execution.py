"""Strict SC2 checks: sound local proofs, explicit limits, no gameplay claims.

Enabled with Validator(..., strict_sc2=True) or CLI --strict-sc2. The batch
runner always enables it. DNF search is bounded; exhaustion is a warning,
never a fabricated proof of unsatisfiability. Legacy validation is preserved.
"""
from __future__ import annotations
import json
import math
from dataclasses import asdict
from stratagemdsl.core.model import (
    BinaryExpr, BindingCall, BoolExpr, CallExpr, NameExpr, NumberExpr, Phase, UnaryExpr,
)
from stratagemdsl.registry.contracts import REGISTRY
from stratagemdsl.registry import extensions as api

def named(call, key, default=None):
    return next((a.value for a in call.args if a.name == key), default) if isinstance(call, BindingCall) else default

def walk(e):
    if e is None: return
    yield e
    if isinstance(e, BinaryExpr): yield from walk(e.left); yield from walk(e.right)
    elif isinstance(e, UnaryExpr): yield from walk(e.operand)
    elif isinstance(e, CallExpr):
        for a in e.args: yield from walk(a)

def key(e): return json.dumps(asdict(e), sort_keys=True)

def expand(e, derived, stack=frozenset()):
    if isinstance(e, NameExpr) and e.name in derived and e.name not in stack:
        return expand(derived[e.name], derived, stack | {e.name})
    if isinstance(e, BinaryExpr): return BinaryExpr(e.op, expand(e.left,derived,stack), expand(e.right,derived,stack))
    if isinstance(e, UnaryExpr): return UnaryExpr(e.op, expand(e.operand,derived,stack))
    if isinstance(e, CallExpr): return CallExpr(e.name, [expand(a, derived, stack) for a in e.args])
    return e

def conjuncts(e):
    if isinstance(e,BinaryExpr) and e.op == 'and': return conjuncts(e.left) + conjuncts(e.right)
    return [e]

def has_conjunct(e, wanted):
    if e == wanted: return True
    return isinstance(e,BinaryExpr) and e.op == 'and' and (has_conjunct(e.left,wanted) or has_conjunct(e.right,wanted))

class ProofLimit(Exception): pass

def dnf(e, negate=False):
    if isinstance(e,UnaryExpr) and e.op == 'not': return dnf(e.operand,not negate)
    if isinstance(e,BoolExpr): return [[]] if e.value != negate else []
    if isinstance(e,BinaryExpr) and e.op in {'and','or','implies'}:
        if e.op == 'implies': return dnf(BinaryExpr('or',UnaryExpr('not',e.left),e.right),negate)
        op = ('or' if e.op == 'and' else 'and') if negate else e.op
        a,b = dnf(e.left,negate),dnf(e.right,negate)
        if op == 'or': result = a+b
        else:
            if len(a)*len(b)>64: raise ProofLimit()
            result = [x+y for x in a for y in b]
        if len(result)>64: raise ProofLimit()
        return result
    return [[(e,negate)]]

def count_atom(e,neg):
    if isinstance(e,CallExpr) and e.name in {'alive','destroyed','defeated'}:
        e=BinaryExpr('>' if e.name=='alive' else '==',CallExpr('count',e.args),NumberExpr(0))
    if not isinstance(e,BinaryExpr) or e.op not in {'<','<=','>','>=','==','!='}: return None
    lhs,rhs,op=e.left,e.right,e.op
    if isinstance(lhs,NumberExpr) and isinstance(rhs,CallExpr):
        lhs,rhs=rhs,lhs;op={'<':'>','<=':'>=','>':'<','>=':'<=','==':'==','!=':'!='}[op]
    if not isinstance(lhs,CallExpr) or lhs.name not in {'count','count_in','killed_in'} or not isinstance(rhs,NumberExpr): return None
    if neg: op={'<':'>=','<=':'>','>':'<=','>=':'<','==':'!=','!=':'=='}[op]
    return lhs,op,rhs.value

def branch_impossible(branch, capacities):
    seen={};ranges={}
    for expr,neg in branch:
        k=key(expr)
        if k in seen and seen[k] != neg: return True
        seen[k]=neg
        a=count_atom(expr,neg)
        if a is None: continue
        term,op,value=a;k=key(term)
        cap=capacities.get(term.args[0].name) if term.args and isinstance(term.args[0],NameExpr) else None
        # killed_in is cumulative, so don't infer an upper bound from spawn count.
        if term.name=='killed_in': cap=None
        lo,hi,excluded=ranges.setdefault(k,[0,cap if cap is not None else math.inf,set()])
        if op=='>':lo=max(lo,math.floor(value)+1)
        elif op=='>=':lo=max(lo,math.ceil(value))
        elif op=='<':hi=min(hi,math.ceil(value)-1)
        elif op=='<=':hi=min(hi,math.floor(value))
        elif op=='==':lo=max(lo,math.ceil(value));hi=min(hi,math.floor(value))
        elif float(value).is_integer():excluded.add(int(value))
        ranges[k]=[lo,hi,excluded]
        if lo>hi or (math.isfinite(hi) and hi-lo < len(excluded) and all(n in excluded for n in range(int(lo),int(hi)+1))): return True
    return False

# v0.4 roster-changing actions -> argument positions whose rosters change.
REGROUP={'transfer':(0,1),'detach':(0,2),'release':(0,),'build':(1,),'control':(0,1),'force_owner':(0,),'rescue':(0,),'force_replace':(0,)}

def capacities_for(s):
    # A dynamic query has no finite capacity. A spawn action can change a
    # group's roster; conservatively suppress the upper bound for that group.
    spawned=set();regrouped=set()
    for n in [*s.plan.nodes,*s.plan.transitions]:
        block=getattr(n,'actions',None)
        if block:
            for action in block.actions:
                if action.name in REGROUP:
                    regrouped|={a.name for i,a in enumerate(action.args) if i in REGROUP[action.name] and isinstance(a,NameExpr)}
    setup=next((b.value for b in s.bindings if b.name=='__setup__'),None)
    cargo=named(setup,'cargo') or []
    for it in cargo if isinstance(cargo,list) else [cargo]:
        into=named(it,'into')
        if into is None and isinstance(it,BindingCall):
            pos=[a.value for a in it.args if a.name is None];into=pos[3] if len(pos)>3 else None
        if isinstance(into,str):regrouped.add(into)
    for n in [*s.plan.nodes,*s.plan.transitions]:
        block=getattr(n,'actions',None)
        if block:
            for action in block.actions:
                if action.name=='spawn' and action.args and isinstance(action.args[0],NameExpr):spawned.add(action.args[0].name)
    caps={}
    for b in s.bindings:
        c=b.value
        if isinstance(c,BindingCall) and named(c,'adopt') is not None:continue
        if b.name in regrouped:continue
        if isinstance(c,BindingCall) and c.name in {'unit','structure','unit_group'} and b.name not in spawned:
            comp=named(c,'composition')
            caps[b.name]=sum(named(x,'count',1) for x in comp) if comp else named(c,'count',1)
    return caps

def _calls(e):
    return [x for x in walk(e) if isinstance(x,CallExpr)]

def _interaction_rules(s,bag,nodes,bindings,derived,fog_on):
    setup=bindings.get('__setup__')
    allow_rewrite=named(setup,'allow_rewrite') is True
    timers={(t.event.args[0].name,float(t.event.args[1].value)) for t in s.plan.transitions
            if t.event and t.event.name=='timer' and len(t.event.args)==2 and isinstance(t.event.args[0],NameExpr) and isinstance(t.event.args[1],NumberExpr)}
    window={'window_held','hold_window','resume_window','restart_window'}
    sides={b.name:b for b in s.world}
    def window_check(c,where):
        if c.name in window and len(c.args)==2 and isinstance(c.args[0],NameExpr) and isinstance(c.args[1],NumberExpr):
            if (c.args[0].name,float(c.args[1].value)) not in timers:
                bag.error('E120_WINDOW_TIMER',f'{where}: {c.name}({c.args[0].name}, {c.args[1].value:g}) needs a transition on timer({c.args[0].name}, {c.args[1].value:g})')
    # Validate references wherever a predicate can occur, not only in guards.
    expressions=[('initial', e) for e in s.initial]
    expressions += [(f'intent.{field}', getattr(s.intent,field)) for field in ('primary','secondary','success','failure')]
    expressions += [(t.id,t.guard) for t in s.plan.transitions]
    expressions += [(f'{n.id}.{attr}',getattr(n,attr)) for n in s.plan.nodes if isinstance(n,Phase) for attr in ('entry','invariant','exit')]
    for label,expr in expressions:
        for call in _calls(expand(expr,derived)):window_check(call,label)
    for n in [*s.plan.nodes,*s.plan.transitions]:
        block=getattr(n,'actions',None)
        if not block:continue
        is_phase=isinstance(n,Phase)
        target=nodes.get(getattr(n,'target',None))
        to_success=(is_phase and n.terminal=='success') or (isinstance(target,Phase) and target.terminal=='success')
        for a in block.actions:
            window_check(a,n.id)
            for arg in a.args:
                for c in _calls(expand(arg,derived)):window_check(c,n.id)
            scripted_control=(a.name=='control' and a.args and isinstance(a.args[0],NameExpr) and sides.get(a.args[0].name) is not None and sides[a.args[0].name].properties.get('side')=='enemy')
            if a.name in api.REWRITE_ACTIONS or scripted_control:
                if not allow_rewrite:
                    bag.warn('W110_REWRITE',f'{n.id}: {a.name}(...) rewrites game state outside causal attribution; add setup(allow_rewrite=true) to acknowledge')
                if to_success:
                    bag.error('E122_REWRITE_SUCCESS',f'{n.id}: {a.name}(...) on a direct path into terminal success would manufacture the result')
            if a.name in ('reveal','reveal_while') and not fog_on:
                bag.warn('W103_VISIBILITY_WITHOUT_FOG',f'{n.id}: {a.name}(...) has no effect while fog of war is disabled; add setup(fog=true)')
            if a.name=='reveal_while' and not is_phase:
                bag.error('E123_REVEAL_SCOPE',f'{n.id}: reveal_while(...) belongs in a phase do-block (it is withdrawn when the phase ends)')
            if a.name=='no_fly':
                bag.warn('W112_NO_FLY',f'{n.id}: no_fly(...) only biases air pathing; units can still be ordered into the zone')
            if a.name=='build' and a.args and isinstance(a.args[0],NameExpr) and sides.get(a.args[0].name) is not None and sides[a.args[0].name].properties.get('side')=='enemy':
                bag.warn('W113_SCRIPTED_BUILD',f'{n.id}: enemy build(...) spawns a construction-stage structure; no worker or build ability is involved')
    if setup is not None and not allow_rewrite:
        used=[a.name for a in setup.args if a.name in api.SETUP_REWRITE_KEYS and
              any(not (isinstance(it,BindingCall) and it.name in api.V03_SETUP_ITEMS) for it in (a.value if isinstance(a.value,list) else [a.value]))]
        for k in used:
            bag.warn('W110_REWRITE',f'setup {k}=... rewrites initial game state; add setup(allow_rewrite=true) to acknowledge')

def check_execution_semantics(s, bag, backend_probe=None):
    """Strict SC2 executability checks. ``backend_probe(strategy) -> str | None``
    is supplied by the pipeline so this layer never imports the backend."""
    nodes={n.id:n for n in s.plan.nodes};bindings={b.name:b.value for b in s.bindings}
    world={e.name:e for e in s.world}
    derived={d.name:d.expr for d in s.derived};caps=capacities_for(s)
    if named(bindings.get('__setup__'),'terminal_policy')!='first_wins':
        bag.error('E001_TERMINAL_POLICY','strict SC2 plans require setup(terminal_policy="first_wins") to stop competing branches after a terminal result')
    for n in s.plan.nodes:
        if isinstance(n,Phase):
            for attr in ['entry','invariant','exit']:
                if getattr(n,attr) is not None:
                    bag.error('E002_PHASE_CONTRACT',f'{n.id}.{attr} is an annotation in this backend; encode an explicit transition/monitor instead')
            if n.terminal and n.id in s.plan.start:bag.error('E003_TERMINAL_START',f'{n.id}: strict plans need an observable transition before a terminal result')
    for t in s.plan.transitions:
        e=expand(t.guard,derived)
        if e is not None:
            try:
                branches=dnf(e)
                if not branches or all(branch_impossible(b,caps) for b in branches):
                    bag.error('E004_IMPOSSIBLE_GUARD',f'{t.id}: guard is contradictory or outside the statically bound roster capacity')
            except ProofLimit:bag.warn('W101_PROOF_LIMIT',f'{t.id}: Boolean expansion exceeds 64 branches; satisfiability was not proven')
            for expr in walk(e):
                if isinstance(expr,CallExpr) and expr.name=='elapsed' and expr.args and isinstance(expr.args[0],NameExpr) and expr.args[0].name not in [a.place for a in t.inputs if a.kind!='inhibit']:
                    bag.error('E011_ELAPSED_SCOPE',f'{t.id}: elapsed({expr.args[0].name}) is only defined while that node is active; use elapsed({t.source}) in transitions leaving {t.source}')
                if isinstance(expr,CallExpr) and expr.name in {'distance','nearest_distance','bearing','flank_angle'}:
                    for arg in expr.args:
                        if world.get(getattr(arg,'name',None)) and world[arg.name].kind=='region':continue
                        # Explicit conjunction is intentionally conservative; no claim to a theorem prover.
                        if isinstance(arg,NameExpr) and not has_conjunct(e,CallExpr('alive',[arg])):
                            bag.error('E005_EMPTY_DISTANCE',f'{t.id}: {expr.name}({arg.name}, ...) requires an explicit alive({arg.name}) conjunct')
        if t.event and t.event.name=='unit_died' and t.event.args:
            subject=t.event.args[0]
            b=bindings.get(subject.name) if isinstance(subject,NameExpr) else None
            if isinstance(b,BindingCall) and b.name.startswith('dynamic_'):
                bag.error('E006_DYNAMIC_DEATH',f'{t.id}: dynamic live-group queries exclude the dead EventUnit; use a stable roster or observed-live then count polling')
        if any(isinstance(nodes.get(a.place),Phase) and nodes[a.place].terminal=='success' for a in t.outputs):
            goal=expand(s.intent.success,derived);failure=UnaryExpr('not',expand(s.intent.failure,derived))
            if not has_conjunct(e,goal):bag.error('E007_UNCONFIRMED_SUCCESS',f'{t.id}: terminal success must explicitly require intent.success')
            if not has_conjunct(e,failure):bag.error('E008_SUCCESS_FAILURE_RACE',f'{t.id}: success must exclude intent.failure in the same observation')
    fog_on=named(bindings.get('__setup__'),'fog') is True
    if not fog_on:
        for t in s.plan.transitions:
            if any(isinstance(x,CallExpr) and x.name=='visible_to' for x in walk(expand(t.guard,derived))):
                bag.warn('W103_VISIBILITY_WITHOUT_FOG',f'{t.id}: visible_to(...) is always true while fog of war is disabled; add setup(fog=true)')
    _interaction_rules(s,bag,nodes,bindings,derived,fog_on)
    groups={}
    for t in s.plan.transitions:
        # v0.6: transitions race for every place they consume from.
        for place in dict.fromkeys(t.consumed or [t.source]):
            groups.setdefault((place,key(t.event) if t.event else 'poll'),[]).append(t)
    for group in groups.values():
        previous=None
        for t in sorted(group,key=lambda x:x.priority):
            if previous:bag.error('E009_SHADOWED_BRANCH',f'{t.id} is shadowed by unconditional same-dispatch branch {previous}')
            if t.guard is None or t.guard==BoolExpr(True):previous=t.id
    for n in [*s.plan.nodes,*s.plan.transitions]:
        block=getattr(n,'actions',None)
        if not block:continue
        actors={}
        for action in block.actions:
            if action.name in {'move','retreat','attack','hold','retarget','cast','set_mode','block'} and action.args and isinstance(action.args[0],NameExpr):
                actor=action.args[0].name
                if actor in actors and block.mode=='parallel' and world.get(actor) and world[actor].properties.get('side')=='enemy':
                    bag.warn('W102_REPLACED_ORDER',f'{n.id}: parallel orders to {actor} each replace the preceding order')
                actors[actor]=action
    # Contract-level checks run before code emission, so failures name the
    # offending API and offer a concrete observation or target-shape remedy.
    for b in s.bindings:
        decl=world.get(b.name)
        if decl is None or decl.kind not in {'force','asset'}:continue
        side=decl.properties.get('side')
        owner=named(b.value,'owner')
        if isinstance(owner,str): owner={'ally':1,'enemy':2}.get(owner.lower(),owner)
        if side in {'ally','enemy'} and isinstance(owner,(int,float)) and not isinstance(owner,bool):
            expected={'ally':1,'enemy':2}[side]
            if owner!=expected:bag.error('E014_OWNER_SIDE_MISMATCH',f'{b.name}: side={side} declares player {expected} but binding owner={owner}; align side (controller policy) with the actual owner')
    for t in s.plan.transitions:
        for expr in walk(expand(t.guard,derived)):
            if not isinstance(expr,CallExpr):continue
            spec=REGISTRY.get(('function',expr.name))
            if spec and spec.backend in {'unsupported','strategic_only'}:
                bag.error('E010_BACKEND_CAPABILITY',f'{t.id}: {expr.name} cannot lower into a Galaxy guard; {spec.prerequisites}')
        if t.event:
            spec=REGISTRY.get(('event',t.event.name))
            if spec and spec.backend=='unsupported':bag.error('E010_BACKEND_CAPABILITY',f'{t.id}: {t.event.name} has no event lowering; {spec.prerequisites}')
    for n in [*s.plan.nodes,*s.plan.transitions]:
        block=getattr(n,'actions',None)
        if not block:continue
        for action in block.actions:
            spec=REGISTRY.get(('action',action.name))
            actor=action.args[0].name if action.args and isinstance(action.args[0],NameExpr) else None
            # Ally actions are explicitly strategic intent; the environment
            # backend neither issues them nor promises their effects.
            if actor is None or world.get(actor) is None or world[actor].properties.get('side')!='enemy':continue
            if spec and spec.backend=='unsupported':
                bag.error('E010_BACKEND_CAPABILITY',f'{n.id}: enemy action {action.name} cannot lower; {spec.prerequisites}')
            if action.name in {'move','retreat'} and len(action.args)>1 and isinstance(action.args[1],NameExpr):
                target=world.get(action.args[1].name)
                if target and target.kind=='route':bag.error('E010_BACKEND_CAPABILITY',f'{n.id}: {action.name}(force, Route) has no concrete point lowering; bind a Region target instead')
    # The backend's own support checks act as a capability gate; this does
    # not compile Galaxy or replace the separate compiler stage.
    if backend_probe is not None and not bag.has_errors:
        problem=backend_probe(s)
        if problem:bag.error('E010_BACKEND_CAPABILITY',problem)
