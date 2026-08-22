#!/usr/bin/env python3
"""T252 instrument 50 -- DRIVE THE MOVED PIN RED THROUGH `bash .softhouse/conformance.sh`.

P-22: a guard you have not seen fail THROUGH THE ROUTE THAT RUNS IT is not wired. P-45: a
guard that only fails when invoked by hand enforces NOTHING. Instrument 40 drove C6 red by
calling the linter directly, which proves the RULE and says nothing about the GATE. This
drives the whole harness.

WHAT IS DRIVEN, and why it is not the same drive T243 did:
  T243 planted the shape T238 wrote its rules FROM -- a `|| echo` arm -- so it proved the
  wiring and said nothing about coverage, which is exactly how the frontier stayed blind to
  r11-hygiene.sh through a green red-drive. The plant here is a C6-ONLY shape: a non-fatal
  entry into a dead directory whose only subsequent output is a COUNT and an empty JSON list.
  It carries no `|| echo`, no reassuring sentence, and no dead path outside the entry, so
  NOTHING in the linter as it stood before T252 would have seen it. If the harness refuses,
  it refuses because C6 reached the gate.

DISCRIMINATION (P-72), which is the whole difficulty of a red drive through a harness that
has many ways to refuse: an EXIT 2 alone proves nothing -- conformance.sh has several. The
row below is accepted as RED only if the output carries the FRONTIER refusal AND names the
planted path. A run that died for any other reason is reported as INCONCLUSIVE, never as a
pass and never as a red.

ENGINE (P-33/P-53): the assertions are python substring tests over the harness's own captured
output. No shell search engine participates, so P-75's shadowed ugrep cannot silently drop a
line and turn a missing refusal into a green.
"""
import os
import shutil
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
assert ROOT and os.path.isdir(ROOT), "T252-50 ABORT: not in a git work tree"
os.chdir(ROOT)
SCRATCH = ".softhouse/capture/t252-tier3/evidence/conf-red-scratch"
PLANT = os.path.join(SCRATCH, "planted-c6-failopen.sh")
DEAD = "/nonexistent/t252/conformance-red-drive"

BODY = """#!/usr/bin/env bash
# PLANTED BY T252 instrument 50. A C6-ONLY fail-open: no `|| echo` arm, no reassuring
# sentence, no dead path except the entry itself. Nothing before T252 could see it.
set -u
D=%s
cd "$D"
git grep -n -F 'needle' -- . | sed 's/^/  /'
python3 -c 'import json,sys; sys.stdout.write(json.dumps({"findings": [], "n": 0}))'
printf '\\nchecked: 0 findings\\n'
""" % DEAD


def conformance():
    r = subprocess.run(["bash", ".softhouse/conformance.sh"],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


print("T252 -- CONFORMANCE-ROUTE RED DRIVE FOR THE MOVED FRONTIER PIN")
print("commit : %s" % subprocess.run(["git", "rev-parse", "HEAD"],
                                     capture_output=True, text=True).stdout.strip())
print("plant  : %s" % PLANT)
print("dead   : %s   exists now? %s" % (DEAD, os.path.exists(DEAD)))
assert not os.path.exists(DEAD), "T252-50 ABORT: the 'dead' path EXISTS; the plant is not fail-open."
print()

verdicts = []
try:
    os.makedirs(SCRATCH, exist_ok=True)
    open(PLANT, "w", encoding="utf-8").write(BODY)
    subprocess.run(["git", "add", "-N", PLANT], check=True)
    seen = subprocess.run(["git", "ls-files", PLANT],
                          capture_output=True, text=True).stdout.split()
    print("### PLANT VISIBLE TO `git ls-files` (the linter's corpus selector): %d/1" % len(seen))
    assert len(seen) == 1, "T252-50 ABORT: the plant is not tracked; the linter would never see it."
    print()

    print("### RED -- `bash .softhouse/conformance.sh` with the plant in the tree")
    rc, out = conformance()
    print("  exit = %d" % rc)
    checks = [
        ("exit is 2 (no verdict available)", rc == 2),
        ("names the FRONTIER refusal",
         "THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER" in out),
        ("names the PLANTED path", PLANT in out),
        ("shows it as an ADDED row (`+`)",
         any(l.startswith("+") and PLANT in l for l in out.splitlines())),
        ("classifies the plant TIER1B (C6, not C1/C2)",
         any(l.startswith("+") and "TIER1B" in l and PLANT in l for l in out.splitlines())),
        ("does NOT print a PASS verdict", "VERDICT: PASS" not in out),
    ]
    for label, got in checks:
        print("  %-46s %s" % (label, "YES" if got else "*** NO ***"))
        verdicts.append(got)
    print()
    print("  the refusal, verbatim:")
    for l in out.splitlines():
        if ("FAIL-OPEN FRONTIER" in l or (l.startswith(("+", "-")) and "softhouse" in l)
                or "EXIT 2 — no verdict" in l):
            print("    | %s" % l)
    print()

    red_ok = all(v for _l, v in zip([c[0] for c in checks], verdicts))
    if rc == 2 and not checks[1][1]:
        print("  *** INCONCLUSIVE: the harness exited 2 for a reason that is NOT the frontier gate.")
        print("  *** An exit code alone is not a red drive. Reporting this as inconclusive.")
finally:
    subprocess.run(["git", "rm", "-q", "--cached", "--force", PLANT], capture_output=True)
    shutil.rmtree(SCRATCH, ignore_errors=True)

print("### GREEN -- the plant removed, the SAME command run again")
left = subprocess.run(["git", "ls-files", SCRATCH], capture_output=True, text=True).stdout.split()
print("  cleanup: scratch exists %s, still in ls-files %d" % (os.path.isdir(SCRATCH), len(left)))
rc2, out2 = conformance()
print("  exit = %d" % rc2)
g = [
    ("exit is 0", rc2 == 0),
    ("VERDICT: PASS present", "VERDICT: PASS" in out2),
    ("frontier == pinned, ELEVEN rows",
     "frontier == pinned (all 11 rows, by path)." in out2),
    ("census line reads `pinned at 11`", "pinned at 11." in out2),
    # WHERE THIS ROW IS CHECKED, AND WHY NOT IN THE HARNESS OUTPUT.
    #
    # The first draft asserted that `FAILOPEN-FRONTIER TIER1B ...rederive-provenance.sh`
    # appears in conformance.sh's own stdout. It does not, and cannot: the guard diverts the
    # linter's output to a temp FILE and `sed`s the frontier rows into scratch, so those rows
    # are never on the harness's stdout at all. The check therefore read "*** NO ***" about a
    # green harness -- this instrument's SECOND false negative about its own subject, and
    # both were caught only because another column disagreed with it.
    #
    # Membership is established where it actually lives, in two observable halves:
    #   (i)  the PIN LITERAL in conformance.sh contains the row -- read from the file here;
    #   (ii) the harness asserts frontier == pinned, both directions, on this run.
    # (i) AND (ii) together entail that the measured frontier contains the row. Either alone
    # does not, which is the point of stating both.
    ("(i) the PIN LITERAL in conformance.sh carries the TIER1B row",
     "TIER1B .softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh"
     in open(".softhouse/conformance.sh", encoding="utf-8").read()),
    ("(ii) the harness asserts frontier == pinned this run",
     "frontier == pinned" in out2),
]
for label, got in g:
    print("  %-46s %s" % (label, "YES" if got else "*** NO ***"))
print()
for l in out2.splitlines():
    if "frontier" in l or "pinned at" in l:
        print("    | %s" % l.strip())
print()

allok = all(verdicts) and all(v for _l, v in g)
print("RED/GREEN THROUGH THE ROUTE THAT RUNS IT: %s"
      % ("BOTH ARMS AS EXPECTED" if allok else "*** SOMETHING DID NOT BEHAVE ***"))
sys.exit(0 if allok else 1)
