#!/usr/bin/env python3
"""T181 -- independent reproduction of the PRE-FIX (RED) behaviour.

SAFETY, STATED FIRST.  The pre-fix scripts resolve their target as FOUR
dirnames up from THEIR OWN absolute path (`W = dirname^4(__file__)`), not from
the cwd.  So a copy placed at

    <scratchroot>/.softhouse/reviews/t47-probe/<script>.py

can only ever reach <scratchroot>/docs/adr/... .  Nothing in this file ever
runs a rewriter from the repository, and the repository's own copies of the two
protected artefacts are sha256'd before and after and the run fails if either
moves.  The pre-fix bytes come from the immutable fork point, never from `main`.

WHAT IS BEING RE-DERIVED.  T178's headline: `t47_edit_4.py` as shipped by T47
was a LIVE gate bypass -- it applied cleanly to the CURRENT ratified DEC-1,
exit 0, taking it from 49dc8923... to cabc2aeb..., with no argv and no gate of
any kind.  And the O_TRUNC claim: `io.open(p, "w")` empties the target before
writing, so an interruption leaves 0 bytes.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"
FORK = "dfa1bfa96084a2175f0d89d0a401a8c105d9a35f"

SCRIPTS = ["t47_edit_2.py", "t47_edit_3.py", "t47_edit_4.py", "t47_edit_4c.py",
           "t47_edit_5.py", "t47_edit_6.py", "t47_edit_7.py", "t47_edit_8.py"]


def sha256_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def git_bytes(*a):
    return subprocess.run(["git", "-C", REPO] + list(a),
                          capture_output=True).stdout


def main():
    adr_abs = os.path.join(REPO, ADR_REL)
    go_abs = os.path.join(REPO, GO_REL)
    adr0, go0 = sha256_file(adr_abs), sha256_file(go_abs)
    print("REPO INTEGRITY BEFORE  DEC-1       %s" % adr0)
    print("REPO INTEGRITY BEFORE  contract.go %s" % go0)
    print()
    print("pre-fix bytes from immutable fork point %s" % FORK)
    print()

    live, inert, trunc = [], [], []
    print("%-15s %-30s %-6s %-9s %s"
          % ("script", "case", "exit", "moved?", "sha256 before -> after"))
    print("-" * 100)

    for s in SCRIPTS:
        pre = git_bytes("show", "%s:.softhouse/reviews/t47-probe/%s" % (FORK, s))
        if not pre:
            print("MISSING pre-fix %s" % s)
            continue
        is_go = b"contract/contract.go" in pre and b"docs/adr" not in pre
        root = tempfile.mkdtemp(prefix="t181red-")
        sd = os.path.join(root, ".softhouse", "reviews", "t47-probe")
        os.makedirs(sd)
        os.makedirs(os.path.join(root, "docs", "adr"))
        os.makedirs(os.path.join(root, "nexus", "internal", "apps",
                                 "loanschedule", "contract"))
        sp = os.path.join(sd, s)
        io.open(sp, "wb").write(pre)

        # seed the scratch tree with the CURRENT ratified/frozen artefact
        tgt_rel = GO_REL if is_go else ADR_REL
        src_abs = go_abs if is_go else adr_abs
        tgt = os.path.join(root, tgt_rel)
        shutil.copyfile(src_abs, tgt)
        b = sha256_file(tgt)

        p = subprocess.run([sys.executable, sp], capture_output=True,
                           text=True, errors="replace", cwd=root)
        a = sha256_file(tgt)
        moved = (a != b)
        tag = ""
        if p.returncode == 0 and moved:
            live.append(s)
            tag = "   <<< LIVE GATE BYPASS"
        else:
            inert.append(s)
        print("%-15s %-30s %-6s %-9s %s -> %s%s"
              % (s, "RED-B current artefact", p.returncode,
                 "YES" if moved else "no", b[:8], a[:8], tag))

        # --- O_TRUNC probe: interrupt right after open(...,"w") returns ----
        shutil.copyfile(src_abs, tgt)
        size_before = os.path.getsize(tgt)
        harness = os.path.join(sd, "_trunc_%s" % s)
        io.open(harness, "w").write(
            "import io, runpy, sys\n"
            "_real = io.open\n"
            "def _patched(*a, **k):\n"
            "    m = k.get('mode', a[1] if len(a) > 1 else 'r')\n"
            "    fh = _real(*a, **k)\n"
            "    if 'w' in m:\n"
            "        raise KeyboardInterrupt('interrupted after O_TRUNC')\n"
            "    return fh\n"
            "io.open = _patched\n"
            "runpy.run_path(%r, run_name='__main__')\n" % sp)
        p2 = subprocess.run([sys.executable, harness], capture_output=True,
                            text=True, errors="replace", cwd=root)
        size_after = os.path.getsize(tgt)
        truncated = (size_after == 0 and size_before > 0)
        if truncated:
            trunc.append(s)
        print("%-15s %-30s %-6s %-9s %d bytes -> %d bytes%s"
              % (s, "RED-C interrupt at O_TRUNC", p2.returncode,
                 "YES" if size_after != size_before else "no",
                 size_before, size_after,
                 "   <<< TRUNCATED TO ZERO" if truncated else ""))

        shutil.rmtree(root, ignore_errors=True)

    print("-" * 100)
    adr1, go1 = sha256_file(adr_abs), sha256_file(go_abs)
    print()
    print("REPO INTEGRITY AFTER   DEC-1       %s  %s"
          % (adr1, "UNCHANGED" if adr1 == adr0 else "*** MOVED ***"))
    print("REPO INTEGRITY AFTER   contract.go %s  %s"
          % (go1, "UNCHANGED" if go1 == go0 else "*** MOVED ***"))
    print()
    print("scripts driven                    : %d" % len(SCRIPTS))
    print("LIVE against CURRENT artefact     : %d  %s" % (len(live), live))
    print("inert against CURRENT artefact    : %d  %s" % (len(inert), inert))
    print("truncated to 0 bytes on interrupt : %d  %s" % (len(trunc), trunc))
    if adr1 != adr0 or go1 != go0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
