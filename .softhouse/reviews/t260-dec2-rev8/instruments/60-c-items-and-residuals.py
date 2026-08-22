#!/usr/bin/env python3
"""T260 — verify C-1..C-8 + the 35th site against the LANDED revision 8, and classify every
residual `conformance.sh:NNNN` citation as LIVE or HISTORY by reading its own line.

C-1..C-6 are T251's numbering (`.softhouse/reviews/t251-dec2-rev7/CORRECTED-HUNKS.md`).
C-7 and C-8 do NOT appear in any T251 artefact; the labels originate in the driver's dispatch
(`.softhouse/tasks.json`) and T255 mapped them to the two remaining substantive items. That
mapping is recorded here so the table can be audited.

P-75: exact-substring counting via python `str.count` / `in`, never a bare grep or rg, so there
is no `\\b`-as-literal-b fabrication class.
P-66/P-70: every non-existence below states the file it was searched in.
Exit 0 always -- this is a census; the adjudication is the reviewer's.
"""
import re
import sys

REV7 = sys.argv[1]
REV8 = sys.argv[2]
t7 = open(REV7, encoding="utf-8").read()
t8 = open(REV8, encoding="utf-8").read()
l8 = t8.split("\n")
l7 = t7.split("\n")


def n(text, s):
    return text.count(s)


print("T260 — C-item verification against the LANDED revision 8")
print("=" * 100)

print("\n### C-1 — every `.softhouse/conformance.sh:NNNN` citation ELIMINATED (not re-measured)")
res7 = [(i + 1, l) for i, l in enumerate(l7) if re.search(r"conformance\.sh:\d", l)]
res8 = [(i + 1, l) for i, l in enumerate(l8) if re.search(r"conformance\.sh:\d", l)]
print(f"  rev7 lines carrying conformance.sh:NNNN : {len(res7)}")
print(f"  rev8 lines carrying conformance.sh:NNNN : {len(res8)}")
print("  EVERY rev8 residual, printed so it is CLASSIFIED not counted:")
HISTORY_MARKS = ("Revisions 1–6", "Revisions 3–6", "Revisions 3–7", "revision 7 replaced",
                 "revisions 1–6 wrote", "correct at", "stale by revision 7", "were stale",
                 "said *\"", "Revision 4 wrote", "revisions 3–6 carried", "STALE",
                 "⚠ RETRACTION", "were STALE", "Those numbers were stamped")
live = []
for i, l in res8:
    ctx = "\n".join(l8[max(0, i - 4):i + 2])
    hist = any(m in ctx for m in HISTORY_MARKS)
    tag = "HISTORY" if hist else "*** LIVE ***"
    print(f"    L{i:<5} [{tag}] {l.strip()[:130]}")
    if not hist:
        live.append((i, l))
print(f"  -> residuals classified LIVE by this instrument: {len(live)}")

print("\n### C-2 — §4.4's I-3 row: answer column unchanged, citation now an ANCHOR")
print(f"  'NO BY A VECTOR' present rev7={n(t7,'**NO BY A VECTOR')} rev8={n(t8,'**NO BY A VECTOR')}")
print(f"  I-3 row still carries the ANCHOR: "
      f"{n(t8, '[ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`')} occurrence(s)")
print(f"  'is the seventh guard `run_guards` invokes' rev7={n(t7,'is the seventh guard')} "
      f"rev8={n(t8,'is the seventh guard')}")

print("\n### C-3 — §4.4.1's fenced guard enumeration: eight names, DERIVED-FROM-SOURCE")
GUARDS = ["guard_graded_root_is_this_tree", "guard_no_float_in_vectors",
          "guard_no_float_in_harness", "guard_gofmt", "guard_no_float_in_capture_requests",
          "guard_no_narrow_catch_in_capture_rigs", "guard_ledger_invariants",
          "guard_no_fail_open_instruments"]
# locate the fence
fs = [i for i, l in enumerate(l8) if "DERIVED-FROM-SOURCE: run_guards()" in l]
print(f"  DERIVED-FROM-SOURCE sentinel lines in rev8: {len(fs)} at {[i+1 for i in fs]}")
for i in fs:
    op = None
    for j in range(i, -1, -1):
        if l8[j].strip().startswith("```"):
            op = j
            break
    if op is None:
        print("    (not inside a fence)")
        continue
    names = []
    for l in l8[op + 1:]:
        if l.strip().startswith("```"):
            break
        m = re.match(r"^\s*(guard_[a-z0-9_]+)\b", l)
        if m:
            names.append(m.group(1))
    if names:
        print(f"    fence at L{op+1} lists {len(names)}: {names}")
        print(f"    equals the expected eight, in order: {names == GUARDS}")
# rev7's fence
fs7 = [i for i, l in enumerate(l7) if l.strip() == "```"]
names7 = []
for i, l in enumerate(l7):
    m = re.match(r"^\s*(guard_[a-z0-9_]+)\s*(#|$)", l)
    if m:
        names7.append((i + 1, m.group(1)))
print(f"  rev7 bare guard-name lines (the incomplete fence): {[x[1] for x in names7]}")
print(f"  rev7 mentions guard_no_fail_open_instruments at all: {n(t7,'guard_no_fail_open_instruments')} time(s)")

print("\n### C-4 — the ordinal: one DERIVED token carrying BOTH counting bases")
tok = re.findall(r"\[DERIVED:[^\]]*\]", t8)
print(f"  [DERIVED: ...] tokens in rev8: {len(tok)}")
for x in tok:
    print(f"    {x}")
print(f"  prose 'the seventh guard'  rev7={n(t7,'the seventh guard')} rev8={n(t8,'the seventh guard')}")
print(f"  prose 'the seventh'        rev7={n(t7,'the seventh')} rev8={n(t8,'the seventh')}")
print(f"  prose 'the sixth tallied'  rev8={n(t8,'the sixth tallied')}")
print(f"  prose 'is the sixth'       rev8={n(t8,'is the sixth')}")

print("\n### C-5 — §5's heading")
for i, l in enumerate(l7):
    if l.startswith("## 5. "):
        print(f"  rev7 L{i+1}: {l}")
for i, l in enumerate(l8):
    if l.startswith("## 5. "):
        print(f"  rev8 L{i+1}: {l}")

print("\n### C-6 / C-7 — §8.3's 'the seventh guard' x2 -> the NAME")
for i, l in enumerate(l7):
    if "seventh guard" in l:
        print(f"  rev7 L{i+1}: {l.strip()[:150]}")
for i, l in enumerate(l8):
    if "seventh guard" in l:
        print(f"  rev8 L{i+1}: {l.strip()[:150]}")

print("\n### C-8 — bare `admit.go` / `vector.go:77-81` ambiguity")
print(f"  'admit.go:139-147'    rev7={n(t7,'admit.go:139-147')} rev8={n(t8,'admit.go:139-147')}")
print(f"  'vector.go:77-81'     rev7={n(t7,'vector.go:77-81')} rev8={n(t8,'vector.go:77-81')}")
print(f"  ambiguity NAMED in rev8 ('exists in TWO packages'): {n(t8,'exists in TWO packages')}")
bare = len(re.findall(r"(?<![/\w])admit\.go:\d", t8)) + len(re.findall(r"(?<![/\w])vector\.go:\d", t8))
bare7 = len(re.findall(r"(?<![/\w])admit\.go:\d", t7)) + len(re.findall(r"(?<![/\w])vector\.go:\d", t7))
print(f"  BARE `admit.go:N` / `vector.go:N` citations still present: rev7={bare7} rev8={bare}")

print("\n### the 35th site — §4.4's lead paragraph")
print(f"  'none of them\\ncan be graded today' rev7={n(t7,'and **none of them')} rev8={n(t8,'and **none of them')}")
for i, l in enumerate(l8):
    if "35th SITE" in l or "35th site" in l:
        print(f"  rev8 L{i+1}: {l.strip()[:160]}")

print("\n### the four LIVE stale sites T255 says neither review enumerated")
print(f"  'conformance.sh:718'  rev7={n(t7,'conformance.sh:718')} rev8={n(t8,'conformance.sh:718')}")
print(f"  'conformance.sh:721'  rev7={n(t7,'conformance.sh:721')} rev8={n(t8,'conformance.sh:721')}")
print(f"  'conformance.sh:1254' rev7={n(t7,'conformance.sh:1254')} rev8={n(t8,'conformance.sh:1254')}")
print(f"  'conformance.sh:401'  rev7={n(t7,'conformance.sh:401')} rev8={n(t8,'conformance.sh:401')}")
print(f"  'conformance.sh:411'  rev7={n(t7,'conformance.sh:411')} rev8={n(t8,'conformance.sh:411')}")
print(f"  'conformance.sh:1115' rev7={n(t7,'conformance.sh:1115')} rev8={n(t8,'conformance.sh:1115')}")
print(f"  'records as not existing' rev7={n(t7,'records as not existing')} rev8={n(t8,'records as not existing')}")
print(f"  'both occurrences'    rev7={n(t7,'both occurrences')} rev8={n(t8,'both occurrences')}")
