#!/usr/bin/env python3
"""T206 item (c) -- runner invoked as `python3 [-O] t206-c-runner.py <module-path>
<case-id> <field> <bad-value>`.  Imports the named T57 module (never running
`main()`, so no write path is ever reached), corrupts one precondition field
in the already-loaded in-memory capture, and calls `build(case_id)` directly
to see whether the precondition check fires.

Never touches the live store: it never calls `main()` or `guard_store.write_
vector`, and the module it imports lives entirely under a scratch tree staged
at real depth (see t206-c-redgreen.sh).
"""
import importlib.util
import sys

MOD_PATH, CASE_ID, FIELD, BAD_VALUE = sys.argv[1:5]

spec = importlib.util.spec_from_file_location("t57mod_under_test", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # runs module-level code (cap/PIN loads); main() is NOT called

mod.cases[CASE_ID]["inputs"][FIELD] = BAD_VALUE

try:
    mod.build(CASE_ID)
    print("RESULT: BUILD SUCCEEDED -- precondition on %r did NOT fire" % FIELD)
except SystemExit as e:
    print("RESULT: BUILD REFUSED via SystemExit(%r)" % (e.code,))
except AssertionError as e:
    print("RESULT: BUILD REFUSED via AssertionError(%r)" % (str(e),))
