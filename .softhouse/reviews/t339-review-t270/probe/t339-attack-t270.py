#!/usr/bin/env python3
"""T339 -- ATTACKS on T270's two new instruments.  P-22: a guard I have not seen
refuse an input it SHOULD refuse is not a guard.

Every arm builds a throwaway copy of the rig (and, where the arm needs one, a
throwaway git repo) and never touches the committed tree.

  python3 t339-attack-t270.py <path-to-a-tree-containing-.softhouse>

exit 0  every arm behaved as ASSERTED below (which includes arms that assert a
        KNOWN, DISCLOSED fail-open still being open -- read the arm text)
exit 1  an assertion failed
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
RIG_SRC = os.path.join(SRC, ".softhouse", "capture", "tierA-a2")
A211_SRC = os.path.join(SRC, ".softhouse", "reviews", "A2-11")
PY = sys.executable

n_ok = n_bad = 0


def ok(label, cond, detail=""):
    global n_ok, n_bad
    print(("  ok   " if cond else "  FAIL ") + label)
    if detail:
        for line in str(detail).splitlines()[:6]:
            print("         " + line[:160])
    if cond:
        n_ok += 1
    else:
        n_bad += 1


def sandbox_rig(dst):
    """A copy of the rig big enough for guard-parse-float-ast.py to run."""
    shutil.copytree(RIG_SRC, dst, symlinks=True)
    return dst


def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout + p.stderr


print("=" * 78)
print("ARM A -- resolve-supersession.py accepts a `..`-ESCAPING replacement path.")
print("         T270 fixed exactly this shape in guard-parse-float-ast.py's")
print("         check_reproduction ('refused with `..` ... spelled by a different")
print("         name'), then shipped a NEW resolver with no such check.  P-80.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    reg = os.path.join(td, "SUPERSEDED.txt")
    outside = os.path.join(td, "OUTSIDE-THE-RIG.py")
    open(outside, "w").write("print('I am not in the rig and I am not a guard')\n")
    rigdir = os.path.join(td, "rig")
    os.makedirs(rigdir)
    reg = os.path.join(rigdir, "SUPERSEDED.txt")
    open(reg, "w").write("prove-mkreq7-guard-red.py -> ../OUTSIDE-THE-RIG.py\n")
    rc, out = run([PY, os.path.join(A211_SRC, "resolve-supersession.py"),
                   reg, "prove-mkreq7-guard-red.py"])
    ok("a `../` replacement OUTSIDE the register's directory is ACCEPTED (rc=0)",
       rc == 0, "rc=%d  stdout=%r" % (rc, out.strip()))
    ok("...and the resolver hands that path straight back to the caller to exec",
       out.strip() == "../OUTSIDE-THE-RIG.py", out.strip())

print()
print("=" * 78)
print("ARM B -- resolve-supersession.py accepts an ABSOLUTE replacement path.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    rigdir = os.path.join(td, "rig")
    os.makedirs(rigdir)
    outside = os.path.join(td, "abs-outside.py")
    open(outside, "w").write("print('absolute, outside')\n")
    reg = os.path.join(rigdir, "SUPERSEDED.txt")
    open(reg, "w").write("prove-mkreq7-guard-red.py -> %s\n" % outside)
    rc, out = run([PY, os.path.join(A211_SRC, "resolve-supersession.py"),
                   reg, "prove-mkreq7-guard-red.py"])
    ok("an ABSOLUTE out-of-tree replacement is ACCEPTED (rc=0)", rc == 0,
       "rc=%d  stdout=%r" % (rc, out.strip()))
    print("         NOTE the shell caller writes \"$RIG/$REPL\", so an ABSOLUTE path")
    print("         happens to produce a broken concatenation and dies loudly; the")
    print("         `..` form in ARM A does NOT -- it resolves and runs.")

print()
print("=" * 78)
print("ARM C -- run-all.sh section 8 executes WHATEVER the register names, with no")
print("         check that the replacement is a guard, and IGNORES its exit code.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    a211 = os.path.join(td, "A2-11")
    shutil.copytree(A211_SRC, a211, symlinks=True)
    rig = os.path.join(td, "capture", "tierA-a2")
    os.makedirs(os.path.dirname(rig))
    shutil.copytree(RIG_SRC, rig, symlinks=True)
    # section 8 resolves "$DIR/../../capture/tierA-a2"
    fake = os.path.join(rig, "NOT-A-GUARD.py")
    open(fake, "w").write("import sys\nprint('I did not check anything')\nsys.exit(1)\n")
    regp = os.path.join(rig, "SUPERSEDED.txt")
    s = open(regp).read()
    s = s.replace("prove-mkreq7-guard-red.py -> guard-parse-float-ast.py",
                  "prove-mkreq7-guard-red.py -> NOT-A-GUARD.py")
    open(regp, "w").write(s)
    rc, out = run([PY, os.path.join(a211, "resolve-supersession.py"), regp,
                   "prove-mkreq7-guard-red.py"])
    ok("the resolver accepts a replacement that is NOT a guard at all", rc == 0,
       "rc=%d stdout=%r" % (rc, out.strip()))
    # now drive section 8's shell logic in isolation, exactly as run-all.sh writes it
    sh = os.path.join(td, "sec8.sh")
    open(sh, "w").write(
        '#!/bin/bash\nDIR="%s"\nRIG="$DIR/../capture/tierA-a2"\n'
        'if REPL="$(python3 "$DIR/resolve-supersession.py" "$RIG/SUPERSEDED.txt" '
        'prove-mkreq7-guard-red.py)"; then\n'
        '  echo "SUPERSEDED.txt resolves: prove-mkreq7-guard-red.py -> $REPL"\n'
        '  python3 "$RIG/$REPL"; echo "exit=$?"\n'
        'else\n  echo "exit=2  (REFUSED)"\nfi\n' % a211)
    rc2, out2 = run(["bash", sh])
    ok("section 8's own logic RUNS it and the section still ends rc=0 overall",
       rc2 == 0 and "I did not check anything" in out2, out2)
    ok("...and the failing exit code is only PRINTED, never propagated",
       "exit=1" in out2 and rc2 == 0, out2)

print()
print("=" * 78)
print("ARM D -- (a) THE DURABLE PIN.  T263 measured: edit an exempted file -> guard")
print("         dies -> `manifest.py write` -> guard REVIVES.  With field 7 the")
print("         revival must FAIL.  This is T270's headline exemption fix.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    rig = sandbox_rig(os.path.join(td, "tierA-a2"))
    victim = os.path.join(rig, "verify-provenance-a2-15.py")
    rc0, out0 = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("baseline: the sandbox rig is GREEN", rc0 == 0 and "PASS --" in out0,
       out0.splitlines()[-1] if out0 else "")
    with open(victim, "a") as fh:
        fh.write("\n# T339 attack: an edit to a file the register calls FROZEN\n")
    rc1, out1 = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("after the edit the guard REFUSES", rc1 != 0, "rc=%d" % rc1)
    rc2, out2 = run([PY, os.path.join(rig, "manifest.py"), "write"], cwd=rig)
    rc3, out3 = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("`manifest.py write` (rc=%d) does NOT revive it -- the register pin holds"
       % rc2, rc3 != 0, "rc=%d\n%s" % (rc3, "\n".join(
           l for l in out3.splitlines() if "HAS BEEN EDITED" in l)))
    ok("...and the refusal names the REGISTER, not the manifest, as the pin",
       "THIS REGISTER pins" in out3,
       "\n".join(l for l in out3.splitlines() if "THIS REGISTER" in l))

print()
print("=" * 78)
print("ARM E -- (a) IS OPT-OUT-ABLE.  Field 7 is optional (6 fields still accepted).")
print("         Delete field 7 and T263's revival attack works again, END TO END.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    rig = sandbox_rig(os.path.join(td, "tierA-a2"))
    regp = os.path.join(rig, "PARSE-FLOAT-EXEMPT.txt")
    lines = open(regp).read().splitlines(True)
    out_lines = []
    for l in lines:
        if l.startswith("verify-provenance-a2-15.py |"):
            l = "|".join(l.rstrip("\n").split("|")[:6]).rstrip() + "\n"
        out_lines.append(l)
    open(regp, "w").write("".join(out_lines))
    run([PY, os.path.join(rig, "manifest.py"), "write"], cwd=rig)
    rc0, out0 = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("a 6-field record is still ALLOWED, graded MANIFEST-ONLY -- WEAK",
       rc0 == 0 and "MANIFEST-ONLY" in out0,
       "\n".join(l for l in out0.splitlines() if "MANIFEST-ONLY" in l))
    with open(os.path.join(rig, "verify-provenance-a2-15.py"), "a") as fh:
        fh.write("\n# T339 attack\n")
    rc1, _ = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("edit the file -> guard refuses", rc1 != 0, "rc=%d" % rc1)
    run([PY, os.path.join(rig, "manifest.py"), "write"], cwd=rig)
    rc2, out2 = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("`manifest.py write` REVIVES the exemption -- T263 F-4(a) is closed only for "
       "records that opted IN to field 7", rc2 == 0,
       "rc=%d  %s" % (rc2, out2.splitlines()[-1] if out2 else ""))

print()
print("=" * 78)
print("ARM F -- (c) `produced:` STILL SWAPPABLE.  T270 says so in the source; this")
print("         MEASURES it rather than taking the comment's word for it.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    rig = sandbox_rig(os.path.join(td, "tierA-a2"))
    regp = os.path.join(rig, "PARSE-FLOAT-EXEMPT.txt")
    s = open(regp).read().replace("produced:PROVENANCE-A2-15.txt",
                                  "produced:CAPTURE-PLAN.md")
    open(regp, "w").write(s)
    run([PY, os.path.join(rig, "manifest.py"), "write"], cwd=rig)
    rc, out = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    ok("swapping the evidence for an unrelated but MANIFEST-pinned file still ALLOWS",
       rc == 0 and "produced CAPTURE-PLAN.md" in out,
       "\n".join(l for l in out.splitlines() if "CAPTURE-PLAN" in l))

print()
print("=" * 78)
print("ARM G -- (d) `reproduces:` absolute / `..` / symlink.  This one T270 CLOSED;")
print("         a review that only re-runs the author's own arms proves nothing, so")
print("         the symlink spelling is driven here too.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    rig = sandbox_rig(os.path.join(td, "tierA-a2"))
    regp = os.path.join(rig, "PARSE-FLOAT-EXEMPT.txt")
    base = open(regp).read()
    outside = os.path.join(td, "outside-target.py")
    open(outside, "w").write("import json\nx = json.load(open('a'))\n")
    victim = os.path.join(rig, "t339-victim.py")
    open(victim, "w").write("import json\n\n\nd = json.load(open('m.json'))\n")
    for spelling, target in (
            ("ABSOLUTE", outside),
            ("DOT-DOT", "../../../outside-target.py"),
            ("SYMLINK", "t339-link.py")):
        if spelling == "SYMLINK":
            try:
                os.symlink(outside, os.path.join(rig, "t339-link.py"))
            except OSError as e:
                print("  SKIP symlink arm: %s" % e)
                continue
        open(regp, "w").write(
            base + "t339-victim.py | 4 | REPRODUCTION-T207 | pinned | "
            "reproduces:%s:2 | T339 attack\n" % target)
        run([PY, os.path.join(rig, "manifest.py"), "write"], cwd=rig)
        rc, out = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
        ok("%s `reproduces:` target is REFUSED" % spelling, rc != 0,
           "rc=%d  %s" % (rc, next((l for l in out.splitlines()
                                    if "reproduces" in l or "escapes" in l
                                    or "ABSOLUTE" in l), "")))

print()
print("=" * 78)
print("ARM H -- (b) MINTING.  A brand-new unguarded money-shaped loader, TRACKED in")
print("         git, cited against evidence it never produced.  T270 says this is")
print("         still open; measure it, do not relay it.")
print("=" * 78)
with tempfile.TemporaryDirectory() as td:
    repo = os.path.join(td, "repo")
    rig = sandbox_rig(os.path.join(repo, ".softhouse", "capture", "tierA-a2"))
    run(["git", "init", "-q", repo])
    run(["git", "-C", repo, "config", "user.email", "t339@local"])
    run(["git", "-C", repo, "config", "user.name", "t339"])
    minted = os.path.join(rig, "t339-minted-loader.py")
    open(minted, "w").write(
        "import json\n\n\ndef load(p):\n    return json.load(open(p))\n")
    run(["git", "-C", repo, "add", "-A"])
    run(["git", "-C", repo, "commit", "-qm", "mint"])
    import hashlib
    dig = hashlib.sha256(open(minted, "rb").read()).hexdigest()
    regp = os.path.join(rig, "PARSE-FLOAT-EXEMPT.txt")
    with open(regp, "a") as fh:
        fh.write("t339-minted-loader.py | 5 | FROZEN-T114 | produced:RED-GREEN-A2-7-guards.txt "
                 "| it did not produce that file at all | %s\n" % dig)
    # the register's field order is file|line|category|pinned|detail|reason|sha
    lines = open(regp).read().splitlines(True)
    # field 4 is the PINNED SOURCE LINE, verbatim -- an extra control T270 inherited
    # from T164 and which this arm must satisfy for the minting attack to be a real
    # test of the FROZEN precondition rather than of the drift check.
    pinned_src = open(minted).read().splitlines()[4].strip()
    lines[-1] = ("t339-minted-loader.py | 5 | FROZEN-T114 | %s | "
                 "produced:RED-GREEN-A2-7-guards.txt | it did not produce that file "
                 "at all | %s\n" % (pinned_src, dig))
    open(regp, "w").write("".join(lines))
    run([PY, os.path.join(rig, "manifest.py"), "write"], cwd=rig)
    run(["git", "-C", repo, "add", "-A"])
    run(["git", "-C", repo, "commit", "-qm", "mint2"])
    rc, out = run([PY, os.path.join(rig, "guard-parse-float-ast.py")])
    minted_ok = rc == 0 and "t339-minted-loader.py" in out
    ok("a NEWLY MINTED unguarded json.load, citing evidence it never produced, is "
       "ALLOWED (fail-open still OPEN, as T270 states)", minted_ok,
       "rc=%d  %s" % (rc, next((l for l in out.splitlines()
                                if "t339-minted" in l), out.splitlines()[-1] if out else "")))
    ok("...and its provenance IS graded ASSERTED ONLY, so the grade at least prints",
       "t339-minted-loader.py" in out and
       any("t339-minted" in l and "ASSERTED ONLY" in l for l in out.splitlines()),
       "\n".join(l for l in out.splitlines() if "t339-minted" in l))

print()
print("=" * 78)
print("%d ok, %d FAILED" % (n_ok, n_bad))
sys.exit(1 if n_bad else 0)
