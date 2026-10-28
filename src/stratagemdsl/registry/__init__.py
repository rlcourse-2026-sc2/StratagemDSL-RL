"""Layer 2: the language surface -- signatures, literal vocabularies, contracts.

Importing any module of this package first runs this file, which loads
``extensions`` so the interaction APIs are always published into the shared
FUNCTIONS / EVENTS / ACTIONS / REGISTRY tables before anyone reads them.
"""
from stratagemdsl.registry import extensions  # noqa: F401
