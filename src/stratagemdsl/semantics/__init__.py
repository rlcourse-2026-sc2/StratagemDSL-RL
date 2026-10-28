"""Layer 3: static checks on a parsed Strategy.

* ``validator``   types, scopes, plan structure, bindings
* ``patterns``    strategic facts and typed pattern obligations
* ``execution``   strict SC2 executability (``strict_sc2=True``)
"""
from stratagemdsl.semantics.validator import Validator

__all__ = ["Validator"]
