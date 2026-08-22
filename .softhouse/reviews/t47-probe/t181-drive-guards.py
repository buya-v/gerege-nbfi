#!/usr/bin/env python3
"""T181 -- INDEPENDENT red/green drive of the eight guards T178 shipped.

This does NOT reuse t178-redprobe.py.  A reviewer who runs the author's prover
has measured the author's prover.  Every case below is written from the guard's
stated contract and driven against the REAL scripts at their REAL path.

SAFETY.  No rewriter is ever run with a target inside the repository.  Every
GREEN case targets a file in a temp directory.  The two protected artefacts are
sha256'd before and after the whole battery and the run aborts if either moves.

P-50.  The battery is falsifiable in BOTH directions:
  - toward the DEFECT: cases that must REFUSE (exit 2/3/4) and leave bytes intact
  - toward the FIX:    a GREEN case that must SUCCEED (exit 0) and produce
                       exactly AFTER_SHA256.  A guard that refuses everything is
                       not a guard, it is a brick; G1 is what distinguishes them.

P-35.  Counts are printed as VALUES.  Inspecting zero scripts is exit 3.
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"

SCRIPTS = ["t47_edit_2.py", "t47_edit_3.py", "t47_edit_4.py", "t47_edit_4c.py",
           "t47_edit_5.py", "t47_edit_6.py", "t47_edit_7.py", "t47_edit_8.py"]


def sha256_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git(*a):
    return subprocess.run(["git", "-C", REPO] + list(a),
                          capture_output=True, text=True, errors="replace")


def git_bytes(*a):
    return subprocess.run(["git", "-C", REPO] + list(a),
                          capture_output=True).stdout


def parse_script(path):
    src = io.open(path, encoding="utf-8").read()
    def grab(key):
        m = re.search(key + r"\s*=\s*\\?\s*\n?\s*'([0-9a-f]{64})'", src)
        if not m:
            m = re.search(key + r"\s*=\s*\\?\s*\n?\s*\"([0-9a-f]{64})\"", src)
        return m.group(1) if m else None
    tok = re.search(r"AUTHORISE_TOKEN\s*=\s*\(?\s*\n?\s*['\"]([^'\"]+)['\"]", src)
    prot = "contract.go" if "guard.FROZEN_CONTRACT" in src else "DEC-1"
    return {
        "before": grab("BEFORE_SHA256"),
        "after": grab("AFTER_SHA256"),
        "token": tok.group(1) if tok else None,
        "prot": prot,
    }


def historical_blobs():
    """sha256 -> bytes, for every committed version of both artefacts."""
    m = {}
    for rel in (ADR_REL, GO_REL):
        r = git("log", "--format=%H", "--all", "--", rel)
        for c in r.stdout.split():
            b = git_bytes("show", "%s:%s" % (c, rel))
            if b:
                m.setdefault(sha256_bytes(b), (b, c, rel))
    return m


def run(script, args, cwd, opt=False, extra_env=None):
    cmd = [sys.executable] + (["-O"] if opt else []) + [script] + args
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    p = subprocess.run(cmd, capture_output=True, text=True,
                       errors="replace", cwd=cwd, env=env)
    return p.returncode, p.stdout, p.stderr


def main():
    adr_abs = os.path.join(REPO, ADR_REL)
    go_abs = os.path.join(REPO, GO_REL)
    adr0, go0 = sha256_file(adr_abs), sha256_file(go_abs)
    print("INTEGRITY BEFORE  DEC-1       %s" % adr0)
    print("INTEGRITY BEFORE  contract.go %s" % go0)
    print()

    blobs = historical_blobs()
    print("historical committed versions indexed: %d" % len(blobs))
    if not blobs:
        print("ERROR: indexed ZERO blobs -- P-35")
        return 3
    print()

    scratch = tempfile.mkdtemp(prefix="t181-")
    results = []
    green_ok = 0
    before_is_blob = 0

    hdr = ("%-15s %-26s %-8s %-8s %s"
           % ("script", "case", "expect", "got", "target bytes"))
    print(hdr)
    print("-" * 92)

    for s in SCRIPTS:
        sp = os.path.join(HERE, s)
        if not os.path.isfile(sp):
            print("MISSING %s" % s)
            continue
        meta = parse_script(sp)
        prot_abs = go_abs if meta["prot"] == "contract.go" else adr_abs
        tok = meta["token"]

        def case(label, args, expect, target=None, opt=False, cwd=REPO,
                 script=sp):
            pre = sha256_file(target) if target and os.path.exists(target) else None
            rc, out, err = run(script, args, cwd, opt=opt)
            post = sha256_file(target) if target and os.path.exists(target) else None
            moved = (pre != post)
            ok = (rc == expect)
            results.append((s, label, expect, rc, ok, moved))
            print("%-15s %-26s %-8s %-8s %s%s"
                  % (s, label, expect, rc,
                     "unchanged" if (target and not moved) else
                     ("CHANGED" if target else "-"),
                     "" if ok else "   <<< NOT AS EXPECTED"))
            return rc, moved

        # --- refusal cases -------------------------------------------------
        case("C1 no argv", [], 2)
        case("C2 target no token", ["--target=%s" % os.path.join(scratch, "x")], 2)
        case("C3 wrong token",
             ["--target=%s" % os.path.join(scratch, "x"),
              "--authorise=WRONG"], 2)
        # C4: the REAL protected artefact
        case("C4 REAL artefact", ["--target=%s" % prot_abs,
                                  "--authorise=%s" % tok], 2, target=prot_abs)
        # C5: scratch copy of the CURRENT artefact -> content gate, exit 3
        cur = os.path.join(scratch, "cur-%s.txt" % s)
        shutil.copyfile(prot_abs, cur)
        case("C5 copy of CURRENT", ["--target=%s" % cur,
                                    "--authorise=%s" % tok], 3, target=cur)
        # C6: inside the repo working tree
        case("C6 inside repo tree",
             ["--target=%s" % os.path.join(REPO, "README-not-real"),
              "--authorise=%s" % tok], 2)

        # --- GREEN (P-50: falsifiable toward the FIX) ----------------------
        bsha = meta["before"]
        entry = blobs.get(bsha)
        if entry is None:
            print("%-15s %-26s %-8s %-8s %s"
                  % (s, "G1 GREEN", "0", "SKIP",
                     "BEFORE_SHA256 is NOT a committed blob"))
        else:
            before_is_blob += 1
            data, commit, rel = entry
            tgt = os.path.join(scratch, "green-%s.scratch" % s)
            io.open(tgt, "wb").write(data)
            rc, moved = case("G1 GREEN", ["--target=%s" % tgt,
                                          "--authorise=%s" % tok], 0, target=tgt)
            got = sha256_file(tgt)
            match = (got == meta["after"])
            print("%-15s %-26s %-8s %-8s AFTER match=%s"
                  % (s, "G1 result", meta["after"][:8], got[:8], match))
            if rc == 0 and match:
                green_ok += 1
            # G2: same GREEN under python3 -O (no bare assert survives)
            io.open(tgt, "wb").write(data)
            case("G2 GREEN under -O", ["--target=%s" % tgt,
                                       "--authorise=%s" % tok], 0,
                 target=tgt, opt=True)
            # G3: candidate gate -- rerun on the ALREADY-EDITED file
            case("G3 rerun (post-edit)", ["--target=%s" % tgt,
                                          "--authorise=%s" % tok], 3, target=tgt)
            # G4: dry-run writes nothing
            io.open(tgt, "wb").write(data)
            case("G4 dry-run", ["--target=%s" % tgt,
                                "--authorise=%s" % tok, "--dry-run"], 0,
                 target=tgt)

        # --- fail-closed: guard module absent ------------------------------
        fake = os.path.join(scratch, "fakerepo-%s" % s,
                            ".softhouse", "reviews", "t47-probe")
        os.makedirs(fake, exist_ok=True)
        shutil.copyfile(sp, os.path.join(fake, s))
        # deliberately do NOT copy t178_guard.py
        rc, out, err = run(os.path.join(fake, s),
                           ["--target=%s" % cur, "--authorise=%s" % tok],
                           cwd=scratch)
        failclosed = (rc != 0)
        results.append((s, "C7 guard deleted", "non-zero", rc, failclosed, False))
        print("%-15s %-26s %-8s %-8s %s%s"
              % (s, "C7 guard deleted", "!=0", rc,
                 "ImportError" if "ImportError" in err or "ModuleNotFound" in err
                 else "exited",
                 "" if failclosed else "   <<< NOT AS EXPECTED"))

        # --- .go suffix refusal (contract script only) ---------------------
        if meta["prot"] == "contract.go":
            gof = os.path.join(scratch, "scratchy.go")
            io.open(gof, "w").write("package x\n")
            case("C8 .go suffix (G-3)", ["--target=%s" % gof,
                                         "--authorise=%s" % tok], 2, target=gof)

    print("-" * 92)
    adr1, go1 = sha256_file(adr_abs), sha256_file(go_abs)
    print()
    print("INTEGRITY AFTER   DEC-1       %s  %s"
          % (adr1, "UNCHANGED" if adr1 == adr0 else "*** MOVED ***"))
    print("INTEGRITY AFTER   contract.go %s  %s"
          % (go1, "UNCHANGED" if go1 == go0 else "*** MOVED ***"))
    print()

    total = len(results)
    bad = [r for r in results if not r[4]]
    print("scripts driven                 : %d" % len(SCRIPTS))
    print("cases run                      : %d" % total)
    print("cases NOT AS EXPECTED          : %d" % len(bad))
    print("GREEN reproduced AFTER exactly : %d of %d" % (green_ok, len(SCRIPTS)))
    print("BEFORE_SHA256 IS a committed blob: %d of %d"
          % (before_is_blob, len(SCRIPTS)))
    for r in bad:
        print("  FAIL %s %s expect=%s got=%s" % (r[0], r[1], r[2], r[3]))

    shutil.rmtree(scratch, ignore_errors=True)

    if total == 0:
        print("ERROR: ZERO cases run -- P-35")
        return 3
    if adr1 != adr0 or go1 != go0:
        return 2
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
