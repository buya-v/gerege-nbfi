#!/usr/bin/env python3
"""T253 — PROPOSED, VERIFIED, AND DELIBERATELY NOT APPLIED.

THE THIRD DEFECT. Fixing D1 (mktemp) made `guard_no_fail_open_instruments` run for the
first time on a non-Mac host. It immediately fails, and correctly refuses:

    THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER (- pinned, + measured):
    +TIER1 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
    -TIER2 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh

THE PIN IS RIGHT AND THE LINTER IS WRONG. TIER2 is the true classification. C1 flags
`/tmp/t234_matrix2.txt` as a dead path, but that instrument CREATES it — line 6 assigns
`C=/tmp/t234_matrix2.txt` and line 7 writes `{ ...; } > "$C"`. The linter already has the
right rule for this ("A path the instrument CREATES or DELETES is its own scratch, not the
corpus it reads", RE_OWNED_HEAD) and the rule MISSES, because the ownership test searches
for the LITERAL path immediately after `>` / `rm` / `mkdir` / `touch` / `tee` / `mktemp`,
while the redirect here goes through the VARIABLE `$C`. The literal never appears in an
owned position, so ownership is never recognised.

WHY IT IS GREEN ON THE MAC AND RED EVERYWHERE ELSE. `os.path.exists()` is evaluated on the
RUNNING HOST. On Buyan's Mac `/tmp/t234_matrix2.txt` is lying around as leftover scratch
from a previous run of that same instrument, so the path "exists" and C1 stays silent. On a
fresh host it does not. The tier a file lands in therefore depends on whether an unrelated
instrument happened to be run recently on the machine doing the linting — the SAME COMMIT
yields TIER1 or TIER2 for the SAME FILE. That is P-69's shape in an instrument rather than
in a document: a classification that was true when it was pinned, and is not a property of
the file at all.

Note the direction: this false positive is fail-CLOSED (it over-reports and blocks the run),
so nothing permissive was ever licensed by it. It is a reproducibility defect, not a safety
hole — but it does make the harness unrunnable on every host but one.

SCOPE. `50-failopen-lint.py` is NOT in T253's write scope, and the RESUME assigns the
fail-open follow-ups to T252, which must serialise on conformance.sh. So this file PROPOSES
and PROVES the fix against a COPY and applies nothing. T252 owns landing it.

MOVING THE PIN WOULD BE WRONG, and is recorded here so nobody tries it as a shortcut:
TIER2 is the correct answer, so pinning TIER1 would make the harness fail on the Mac
instead, and would write a host artefact into the durable record. Loosening the guard to
compare paths while ignoring tiers would destroy the TIER1/TIER2 distinction T248 built.

RUN:  python3 30-proposed-linter-fix.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
LINT = os.path.join(REPO, ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py")
TARGET = ".softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh"

# --- the proposed change ------------------------------------------------------------
# Two lines, inserted into _dead_paths immediately after the existing owned-literal test.
# A path that is assigned to a shell variable which is THEN used in an owned position is
# owned by the instrument, exactly as if the literal had been written there.
OLD = """        if re.search(RE_OWNED_HEAD + re.escape(p), txt):   # the file owns it
            continue
"""
NEW = """        if re.search(RE_OWNED_HEAD + re.escape(p), txt):   # the file owns it
            continue
        if _owned_via_var(p, txt):                        # ...or owns it through a variable
            continue
"""
HELPER = '''

def _owned_via_var(p, txt):
    """True when VAR=<p> and VAR is later used in a position that CREATES or DELETES.

    [T253] The literal-only ownership test above misses the overwhelmingly common shell
    idiom of naming a scratch file once and redirecting into it by variable:

        C=<a scratch path under /tmp>
        { printf ...; } > "$C"

    The live instance is 02-escape-matrix-fix.sh lines 6-7 (cited in this module's header).

    Nothing here widens WHICH paths are inspected; it only stops calling an instrument's
    OWN scratch output a dead corpus path. The variable must be assigned THIS EXACT path,
    so it cannot launder an unrelated location.
    """
    for m in re.finditer(r'(?:^|[;&|(\\s])([A-Za-z_][A-Za-z0-9_]*)=["\\']?' + re.escape(p)
                         + r'["\\']?(?:\\s|$|;)', txt, re.M):
        var = m.group(1)
        use = r'(?:>>?|\\brm\\b|\\bmkdir\\b|\\btouch\\b|\\btee\\b)\\s*(?:-\\S+\\s+)*["\\']?\\$\\{?' \\
              + re.escape(var) + r'\\}?'
        if re.search(use, txt):
            return True
    return False
'''


def run(path, scope):
    """Run a linter copy, with its JSON sidecar DIVERTED to scratch.

    The linter's default JSON destination is a TRACKED file
    (.softhouse/capture/t238-failopen/evidence/lint.json). Running it by hand rewrites that
    file and dirties a tree outside T253's write scope -- which is exactly why
    guard_no_fail_open_instruments sets FAILOPEN_LINT_JSON before invoking it. This driver
    does the same. [Found the hard way: the first run of this file DID dirty lint.json.]
    """
    env = dict(os.environ, FAILOPEN_LINT_JSON=os.path.join(tempfile.gettempdir(),
                                                           "t253-lint-sidecar.json"))
    r = subprocess.run([sys.executable, path, scope], capture_output=True, text=True,
                       cwd=REPO, env=env)
    return r.stdout + r.stderr


def tier_of(out, target):
    """Read the machine-readable FRONTIER rows the linter prints at the end.

    [P-72 note] The first version of this function parsed the human "### TIER n" section
    HEADINGS and reported NOT-ON-FRONTIER for everything, and the whole-tree comparison
    parsed rows as lines starting "TIER1 ". Both were wrong: the authoritative rows are
    prefixed `FAILOPEN-FRONTIER `. Checks 3-5 failed against a CORRECT patch until this was
    fixed -- the probe, not the subject, exactly as in this task's other two drives.
    """
    for line in out.split("\n"):
        if line.startswith("FAILOPEN-FRONTIER ") and line.rstrip().endswith(target):
            return line.split()[1]
    return "NOT-ON-FRONTIER"


def main():
    src = open(LINT, encoding="utf-8").read()
    assert src.count(OLD) == 1, "anchor not unique — the linter moved; re-derive this patch"

    tmp = tempfile.mkdtemp(prefix="t253-lint.")
    try:
        shipped = os.path.join(tmp, "shipped.py")
        patched = os.path.join(tmp, "patched.py")
        shutil.copyfile(LINT, shipped)
        body = src.replace(OLD, NEW, 1)
        # place the helper just before the `viol = []` driver section
        anchor = "\nviol = []"
        assert body.count(anchor) == 1
        body = body.replace(anchor, HELPER + anchor, 1)
        open(patched, "w", encoding="utf-8").write(body)

        print("=" * 78)
        print("PROPOSED FIX for 50-failopen-lint.py  — PROVED HERE, APPLIED NOWHERE")
        print("=" * 78)
        print("scratch file present on this host? %s" %
              os.path.exists("/tmp/t234_matrix2.txt"))
        print()

        ok = True
        # --- 1. the shipped linter, scoped to the one file: TIER1 (the false positive)
        a = run(shipped, TARGET)
        ta = tier_of(a, TARGET)
        print("SHIPPED linter on the target : %s" % ta)
        if ta == "TIER1":
            print("OK    1 reproduces the false positive that blocks the harness")
        else:
            ok = False
            print("FAIL  1 expected TIER1 from the shipped linter, got %s" % ta)

        # --- 2. the patched linter on the same file: TIER2 (matches the pin)
        b = run(patched, TARGET)
        tb = tier_of(b, TARGET)
        print("PATCHED linter on the target : %s" % tb)
        if tb == "TIER2":
            print("OK    2 patched linter agrees with the PIN — C1 no longer fires")
        else:
            ok = False
            print("FAIL  2 expected TIER2 from the patched linter, got %s" % tb)

        # --- 3. ADDITIVITY over the WHOLE tree. The change must LOSE no detection other
        #        than the one false positive; T248 established that as the standard for
        #        touching this linter at all.
        full_a = run(shipped, ".softhouse")
        full_b = run(patched, ".softhouse")

        def rows(out):
            # FRONTIER rows only (TIER1/TIER2) -- that is exactly what the pin compares.
            return set(l.strip()[len("FAILOPEN-FRONTIER "):] for l in out.split("\n")
                       if l.startswith("FAILOPEN-FRONTIER "))

        ra, rb = rows(full_a), rows(full_b)
        lost, gained = ra - rb, rb - ra
        print()
        print("WHOLE-TREE frontier rows: shipped %d, patched %d" % (len(ra), len(rb)))
        print("  LOST   (%d): %s" % (len(lost), sorted(lost) or "none"))
        print("  GAINED (%d): %s" % (len(gained), sorted(gained) or "none"))
        expect_lost = {"TIER1 " + TARGET}
        expect_gain = {"TIER2 " + TARGET}
        if lost == expect_lost and gained == expect_gain:
            print("OK    3 STRICTLY the intended reclassification: one row moves TIER1 -> TIER2,")
            print("        nothing else is lost and nothing else is gained.")
        else:
            ok = False
            print("FAIL  3 the change is NOT confined to the intended row.")

        # --- 4. NEGATIVE CONTROL. A genuinely dead path that the instrument does NOT own
        #        must STILL be flagged, or the patch is an amnesty rather than a fix.
        probe_dir = os.path.join(REPO, ".softhouse/capture/t253-portability/src")
        probe = os.path.join(probe_dir, "_t253_negctl.sh")
        rel = ".softhouse/capture/t253-portability/src/_t253_negctl.sh"

        def track():
            # the linter reads `git ls-files`, so an untracked probe is INVISIBLE to it.
            subprocess.run(["git", "add", "-f", rel], cwd=REPO, capture_output=True)

        open(probe, "w", encoding="utf-8").write(
            "#!/bin/bash\n"
            "# negative control for T253's proposed linter patch; deleted by the driver.\n"
            "D=/nonexistent-t253-corpus/tree\n"
            "cd \"$D\" && git grep -n 'x' -- . || echo \"(no hits)\"\n")  # lint-failopen: ok -- specimen text WRITTEN INTO a throwaway probe file, not this driver's own failure arm; it must be fail-open or check 4 could not discriminate.
        try:
            track()
            c = run(patched, rel)
            tc = tier_of(c, "_t253_negctl.sh")
            print()
            print("NEGATIVE CONTROL — a dead path the file READS but does not create: %s" % tc)
            if tc == "TIER1":
                print("OK    4 still flagged TIER1. The patch exempts OWNERSHIP, not dead paths.")
            else:
                ok = False
                print("FAIL  4 the patch swallowed a real dead path (got %s) — that is an amnesty." % tc)

            # --- 5. and the SAME path, this time CREATED through a variable, must be exempt.
            open(probe, "w", encoding="utf-8").write(
                "#!/bin/bash\n"
                "# negative control, second half: same shape, but the file OWNS the path.\n"
                "D=/nonexistent-t253-corpus/tree\n"
                "mkdir -p \"$D\"\n"
                "cd \"$D\" && git grep -n 'x' -- . || echo \"(no hits)\"\n")  # lint-failopen: ok -- same specimen, owned-path half of the negative control.
            track()
            d = run(patched, rel)
            td = tier_of(d, "_t253_negctl.sh")
            print("SAME path, now CREATED via \"$D\"                                : %s" % td)
            if td == "TIER2":
                print("OK    5 exempted from C1 once owned — and STILL on the frontier for its")
                print("        `|| echo` arm, so ownership never hides the C2 defect.")
            else:
                ok = False
                print("FAIL  5 expected TIER2, got %s" % td)
        finally:
            subprocess.run(["git", "rm", "-f", "--cached", "--quiet", rel],
                           cwd=REPO, capture_output=True)
            if os.path.exists(probe):
                os.remove(probe)

        print()
        print("=" * 78)
        print("RESULT: %s" % ("ALL CHECKS PASS — patch is ready for T252 to land"
                              if ok else "CHECKS FAILED"))
        print("APPLIED: NOTHING. 50-failopen-lint.py is untouched on disk:")
        print("  sha256 unchanged =", subprocess.run(
            ["sha256sum", LINT], capture_output=True, text=True).stdout.split()[0])
        print("=" * 78)
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
