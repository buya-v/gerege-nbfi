"""T145 differential harness -- injected via PYTHONPATH, NOT committed into any script.

Patches json.load / json.loads so that every call that did NOT already pass parse_float=
behaves as if it had passed parse_float=Decimal. This is the whole population's repair,
applied without editing a single byte of any script -- which is how T114's ruling
("never edit a script that produced committed evidence") is honoured across 196 files at
once instead of file by file.

The patch is EXACTLY the repair under consideration and nothing else: it does not touch
parse_int, does not normalise, does not round.
"""
import json as _json
from decimal import Decimal as _D

_orig_load = _json.load
_orig_loads = _json.loads


def _load(fp, **kw):
    kw.setdefault("parse_float", _D)
    return _orig_load(fp, **kw)


def _loads(s, **kw):
    kw.setdefault("parse_float", _D)
    return _orig_loads(s, **kw)


_json.load = _load
_json.loads = _loads
