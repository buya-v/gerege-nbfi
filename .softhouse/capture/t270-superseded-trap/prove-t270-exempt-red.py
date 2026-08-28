#!/usr/bin/env python3
"""T270 — drive the FOUR exemption-register fixes RED. Transcript: RED-GREEN-T270-EXEMPT.txt

  python3 prove-t270-exempt-red.py    -> exit 0 only if every arm behaves as asserted

T263 raised four defects in T164's `PARSE-FLOAT-EXEMPT.txt` / `guard-parse-float-ast.py`,
and T270's brief ordered them (d) first because it is the one a reviewer cannot audit:

  (d) F-6  `reproduces:` ACCEPTED AN ABSOLUTE PATH OUTSIDE THE REPOSITORY, so an
           untracked, deletable, unreviewable out-of-tree file could license an in-tree
           unguarded money load.
  (b) F-4  a brand-new unguarded money-shaped loader could be MINTED into the register in
           two commands, naming evidence it never produced.
  (c) F-5  `produced:` was EXISTENCE-ONLY — swap it for any other existing file and the
           guard stayed green.
  (a) F-4  the exemption died on an edit but did not STAY dead: `manifest.py write`
           revived it.

EVERY ARM IS DRIVEN AGAINST BOTH GUARDS WHERE IT MATTERS — the version at `git HEAD`
(before T270) and the delivered version — because "the fix works" is only meaningful
beside "the defect was real". ARMS THAT REMAIN OPEN ARE ASSERTED OPEN, not quietly
dropped: a red-drive that only demonstrates successes is the same fail-open shape this
whole task is about.

Every arm runs in a throwaway temp tree. Nothing writes to the committed tree; the
reference oracle is not contacted.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RIG = os.path.join(REPO, ".softhouse", "capture", "tierA-a2")
GUARD = "guard-parse-float-ast.py"
REGISTER = "PARSE-FLOAT-EXEMPT.txt"
EVIDENCE = ("RED-GREEN-A2-7-guards.txt", "PROVENANCE-A2-15.txt", "MANIFEST.sha256")
EVIDENCE_SUB = ("req/a2-7-loan-220-resolved.json",)

FAILURES = []
CASES = 0


def check(label, cond, detail=""):
    global CASES
    CASES += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("\n         " + str(detail))
                                                        if detail else ""))
    if not cond:
        FAILURES.append(label)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def scratch():
    """A throwaway copy of the rig: every .py, the register, the named evidence."""
    d = tempfile.mkdtemp(prefix="t270-exempt.")
    for n in sorted(os.listdir(RIG)):
        p = os.path.join(RIG, n)
        if os.path.isfile(p) and (n.endswith(".py") or n == REGISTER or n in EVIDENCE
                                  or n == "CAPTURE-PLAN.md"):
            shutil.copy(p, os.path.join(d, n))
    for rel in EVIDENCE_SUB:
        src = os.path.join(RIG, rel)
        if os.path.exists(src):
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            shutil.copy(src, os.path.join(d, rel))
    return d


def head_guard():
    """The guard as it was at git HEAD, i.e. BEFORE T270. Written to a temp file."""
    p = subprocess.run(["git", "-C", REPO, "show",
                        "HEAD:.softhouse/capture/tierA-a2/" + GUARD],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("cannot read the pre-T270 guard from git HEAD: " + p.stderr)
    fd, path = tempfile.mkstemp(prefix="head-guard.", suffix=".py")
    os.write(fd, p.stdout.encode())
    os.close(fd)
    return path


def run_guard(root, guard=None):
    p = subprocess.run([sys.executable, guard or os.path.join(RIG, GUARD),
                        "--root", root], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def legacy6(root):
    """Strip field 7 — the register exactly as it was BEFORE T270.

    The pre-T270 guard requires EXACTLY 6 fields, so every arm that drives the old guard
    must hand it the old format; otherwise it refuses on the format and the arm would
    'reproduce' nothing. Getting this wrong is how a red-drive fakes its own red.
    """
    reg = os.path.join(root, REGISTER)
    out = []
    for ln in open(reg).read().split("\n"):
        body = ln.split("#")[0].strip()
        if body and len(body.split("|")) == 7:
            ln = "|".join(ln.split("|")[:-1]).rstrip()
        out.append(ln)
    open(reg, "w").write("\n".join(out))


def git_scratch(root, add_all=True):
    """Make `root` a git work tree, so the tracked-file control actually runs."""
    subprocess.run(["git", "-C", root, "init", "-q"], capture_output=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t270@local"],
                   capture_output=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "T270"],
                   capture_output=True)
    if add_all:
        subprocess.run(["git", "-C", root, "add", "-A"], capture_output=True)


def append_register(root, line):
    with open(os.path.join(root, REGISTER), "a") as f:
        f.write(line + "\n")


def rewrite_manifest(root):
    """What `manifest.py write` does to the digests the guard reads: regenerate them."""
    lines = []
    for dirpath, _dn, fns in os.walk(root):
        for fn in sorted(fns):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            if rel == "MANIFEST.sha256":
                continue
            lines.append("%s  %s" % (sha256(p), rel))
    with open(os.path.join(root, "MANIFEST.sha256"), "w") as f:
        f.write("\n".join(sorted(lines)) + "\n")


# ===================================================================== (d) F-6
def arm_d_absolute_path():
    print("\n(d) F-6 — `reproduces:` and an ABSOLUTE PATH OUTSIDE THE REPOSITORY")
    print("    THE ONE A REVIEWER CANNOT AUDIT: an untracked out-of-tree file licensing an")
    print("    in-tree unguarded money load, its meaning changing whenever that file does.")

    outside = tempfile.mkdtemp(prefix="t270-OUTSIDE-THE-REPO.")
    with open(os.path.join(outside, "external.py"), "w") as f:
        f.write("import json\n\n\ndef g(p):\n    return json.load(open(p))\n")
    target_line = 5

    def rig_with_absolute():
        d = scratch()
        with open(os.path.join(d, "measurer.py"), "w") as f:
            f.write('import json\n\n\ndef m(p):\n    return json.load(open(p))\n')
        append_register(d, "measurer.py | 5 | REPRODUCTION-T207 | "
                           "return json.load(open(p)) | reproduces:%s/external.py:%d | "
                           "an out-of-tree file nobody can review | -"
                        % (outside, target_line))
        return d

    old = head_guard()
    d = rig_with_absolute()
    legacy6(d)
    rc, out = run_guard(d, old)
    check("REPRODUCE: the PRE-T270 guard ACCEPTS the out-of-tree licence and exits 0",
          rc == 0 and "DECLARED REPRODUCTION-T207" in out, "rc=%d" % rc)
    check("REPRODUCE: and it prints the outside path as though it were auditable",
          outside in out)
    shutil.rmtree(d)

    d = rig_with_absolute()
    rc, out = run_guard(d)
    check("FIXED: the delivered guard REFUSES an absolute `reproduces:` target (exit 2)",
          rc == 2, "rc=%d" % rc)
    check("FIXED: and it says WHY — a money guard may not be licensed from outside the tree",
          "ABSOLUTE path" in out and "outside the tree" in out)
    shutil.rmtree(d)

    # `..` reaches the same place by a different spelling.
    d = scratch()
    with open(os.path.join(d, "measurer.py"), "w") as f:
        f.write('import json\n\n\ndef m(p):\n    return json.load(open(p))\n')
    rel_escape = os.path.relpath(os.path.join(outside, "external.py"), d)
    append_register(d, "measurer.py | 5 | REPRODUCTION-T207 | "
                       "return json.load(open(p)) | reproduces:%s:%d | "
                       "the same escape spelled with .. | -" % (rel_escape, target_line))
    rc, out = run_guard(d)
    check("FIXED: a RELATIVE path that escapes the root via `..` is refused too — the "
          "check is on realpath, not on the spelling", rc == 2 and "escapes the root" in out,
          "rc=%d" % rc)
    shutil.rmtree(d)

    # And the fix must not be "refuse everything".
    d = scratch()
    with open(os.path.join(d, "measurer.py"), "w") as f:
        f.write('import json\n\n\ndef m(p):\n    return json.load(open(p))\n')
    os.makedirs(os.path.join(d, "sub"))
    with open(os.path.join(d, "sub", "target.py"), "w") as f:
        f.write("import json\n\n\ndef t(p):\n    return json.load(open(p))\n")
    append_register(d, "measurer.py | 5 | REPRODUCTION-T207 | "
                       "return json.load(open(p)) | reproduces:sub/target.py:5 | "
                       "a legitimate in-tree reproduction | -")
    rc, out = run_guard(d)
    check("CONTROL: a legitimate REPO-RELATIVE, in-tree reproduction still passes — the "
          "fix rejects the escape, not the feature",
          rc == 0 and "DECLARED REPRODUCTION-T207" in out, "rc=%d" % rc)
    shutil.rmtree(d)
    shutil.rmtree(outside)
    os.unlink(old)


# ===================================================================== (a) F-4
def arm_a_stays_dead():
    print("\n(a) F-4 — DOES THE EXEMPTION STAY DEAD? `manifest.py write` used to revive it.")
    victim = "verify-provenance-a2-15.py"

    def edited_rig():
        d = scratch()
        p = os.path.join(d, victim)
        src = open(p).read()
        open(p, "w").write(src + "\n# an edit, so the file is no longer frozen\n")
        return d

    old = head_guard()
    d = edited_rig()
    legacy6(d)
    rc, _ = run_guard(d, old)
    check("REPRODUCE step 1: PRE-T270 guard, frozen file edited -> exit 2 (it dies)",
          rc == 2, "rc=%d" % rc)
    rewrite_manifest(d)
    rc, out = run_guard(d, old)
    check("REPRODUCE step 2: regenerate MANIFEST.sha256 -> PRE-T270 guard exits 0 again. "
          "THE EXEMPTION CAME BACK TO LIFE with the edit still in place.",
          rc == 0, "rc=%d" % rc)
    shutil.rmtree(d)

    d = edited_rig()
    rc, _ = run_guard(d)
    check("FIXED step 1: delivered guard, frozen file edited -> exit 2 (it dies)",
          rc == 2, "rc=%d" % rc)
    rewrite_manifest(d)
    rc, out = run_guard(d)
    check("FIXED step 2: regenerate MANIFEST.sha256 -> IT STAYS DEAD, exit 2",
          rc == 2, "rc=%d" % rc)
    check("FIXED: and the refusal names the register pin as the reason, so the next "
          "reader knows regenerating the manifest is not the remedy",
          "THIS REGISTER pins" in out and "will NOT revive" in out)
    shutil.rmtree(d)

    # The legacy 6-field shape must still be ACCEPTED (T164's frozen red-driver appends
    # 6-field records) but must be GRADED as the weaker thing it is.
    d = scratch()
    reg = os.path.join(d, REGISTER)
    src = open(reg).read()
    lines = []
    for ln in src.split("\n"):
        body = ln.split("#")[0].strip()
        if body and len(body.split("|")) == 7:
            ln = "|".join(ln.split("|")[:-1]).rstrip()
        lines.append(ln)
    open(reg, "w").write("\n".join(lines))
    rc, out = run_guard(d)
    check("LEGACY: a 6-field record is still accepted (T164's frozen red-driver depends "
          "on it) and still exits 0", rc == 0, "rc=%d" % rc)
    check("LEGACY: but every such record is printed `MANIFEST-ONLY -- WEAK`, naming the "
          "revival hole rather than reading as equivalent",
          "MANIFEST-ONLY -- WEAK" in out and "REVIVES it" in out)
    shutil.rmtree(d)
    os.unlink(old)


# ===================================================================== (c) F-5
def arm_c_produced_provenance():
    print("\n(c) F-5 — `produced:` was EXISTENCE-ONLY. What is it now?")
    old = head_guard()

    # Unpinned evidence: the floor T270 added.
    d = scratch()
    with open(os.path.join(d, "NOT-PINNED.txt"), "w") as f:
        f.write("an ordinary file nothing vouches for\n")
    reg = os.path.join(d, REGISTER)
    s = open(reg).read().replace("produced:PROVENANCE-A2-15.txt",
                                 "produced:NOT-PINNED.txt")
    open(reg, "w").write(s)
    legacy6(d)
    rc, out = run_guard(d, old)
    check("REPRODUCE: PRE-T270, `produced:` pointing at an unpinned file is accepted, "
          "exit 0 — the field existence-checks and nothing more", rc == 0, "rc=%d" % rc)
    shutil.rmtree(d)

    d = scratch()
    with open(os.path.join(d, "NOT-PINNED.txt"), "w") as f:
        f.write("an ordinary file nothing vouches for\n")
    reg = os.path.join(d, REGISTER)
    s2 = open(reg).read().replace("produced:PROVENANCE-A2-15.txt",
                                  "produced:NOT-PINNED.txt")
    open(reg, "w").write(s2)
    rc, out = run_guard(d)
    check("FIXED: the delivered guard DENIES evidence that MANIFEST.sha256 does not pin",
          rc == 2 and "does not pin the evidence" in out, "rc=%d" % rc)
    shutil.rmtree(d)

    # T263's exact attack: swap for CAPTURE-PLAN.md, which IS pinned.
    d = scratch()
    reg = os.path.join(d, REGISTER)
    s = open(reg).read().replace("produced:PROVENANCE-A2-15.txt",
                                 "produced:CAPTURE-PLAN.md")
    open(reg, "w").write(s)
    rc, out = run_guard(d)
    check("STILL OPEN, ASSERTED NOT HIDDEN: T263's exact attack — swapping `produced:` "
          "for CAPTURE-PLAN.md — STILL leaves the guard green, because that file is "
          "itself MANIFEST-pinned. The pin requirement is a floor, not a fix.",
          rc == 0, "rc=%d" % rc)
    check("MITIGATED: but the record is now GRADED `ASSERTED ONLY` on the verdict line, "
          "so the field no longer reads as an audit trail it is not",
          "ASSERTED ONLY" in out)
    shutil.rmtree(d)

    # And the grading must discriminate, or it means nothing.
    d = scratch()
    rc, out = run_guard(d)
    named = out.count("evidence NAMES its producer")
    asserted = out.count("ASSERTED ONLY")
    check("THE GRADE DISCRIMINATES: on the unmodified rig it is not a constant — 3 "
          "records verify and 3 do not. A grade that said the same thing about every "
          "record would be P-22 again.",
          named == 3 and asserted == 3, "NAMES=%d ASSERTED=%d" % (named, asserted))
    check("AND THIS REFUTES T263 F-5's PREMISE, which said requiring the evidence to name "
          "its producer would hold 'for all six live records today'. It holds for 3.",
          asserted == 3,
          "req/a2-7-loan-220-resolved.json is a JSON request body and PROVENANCE-A2-15.txt "
          "does not name verify-provenance-a2-15.py; neither could be made to.")
    shutil.rmtree(d)
    os.unlink(old)


# ===================================================================== (b) F-4 R2
def arm_b_minting():
    print("\n(b) F-4 R2 — CAN A BRAND-NEW UNGUARDED MONEY LOADER STILL BE MINTED?")
    old = head_guard()
    newfile = "t270_newmoney.py"
    body = ('import json\n\n\ndef amounts(p):\n    return json.load(open(p))\n')

    def minted(root, seven=True):
        """The two-command mint: drop in the loader, add a record. `seven` selects the
        register format, because the PRE-T270 guard rejects a 7-field record outright and
        an arm that 'reproduced' a FORMAT refusal would be reproducing nothing."""
        with open(os.path.join(root, newfile), "w") as f:
            f.write(body)
        rec = ("%s | 5 | FROZEN-T114 | return json.load(open(p)) | "
               "produced:RED-GREEN-A2-7-guards.txt | evidence it never produced" % newfile)
        if seven:
            rec += " | %s" % sha256(os.path.join(root, newfile))
        append_register(root, rec)

    d = scratch()
    legacy6(d)
    minted(d, seven=False)
    rewrite_manifest(d)
    rc, out = run_guard(d, old)
    check("REPRODUCE: PRE-T270, a new unguarded loader + a record + a manifest write is "
          "MINTED — exit 0, for a file that produced nothing", rc == 0, "rc=%d" % rc)
    shutil.rmtree(d)

    # The tracked-file control only means anything inside a git work tree, so the arm
    # builds one. Everything EXCEPT the minted file is committed.
    d = scratch()
    git_scratch(d)
    minted(d)
    rewrite_manifest(d)
    rc, out = run_guard(d)
    check("RAISED: the delivered guard REFUSES it, because the file is UNTRACKED in git "
          "and so cannot have produced committed evidence",
          rc == 2 and "UNTRACKED in git" in out, "rc=%d" % rc)
    shutil.rmtree(d)

    # The residual hole, proven to EXIST rather than asserted to be closed.
    d = scratch()
    git_scratch(d)
    minted(d)
    rewrite_manifest(d)
    subprocess.run(["git", "-C", d, "add", "-A"], capture_output=True)
    rc, out = run_guard(d)
    check("STILL OPEN, PROVEN NOT ASSUMED: once the minted file is `git add`ed it passes "
          "again (exit 0). The minting is RAISED from two commands to three-plus-a-diff, "
          "NOT closed. The remaining control is review of the diff, and saying so is the "
          "point of this arm.", rc == 0, "rc=%d" % rc)
    check("...and the guard prints that record in full, so the diff a reviewer must read "
          "is not hidden from them", newfile in out)
    shutil.rmtree(d)
    os.unlink(old)


if __name__ == "__main__":
    print("=" * 78)
    print("T270 — RED/GREEN for the four PARSE-FLOAT-EXEMPT.txt defects T263 raised")
    print("=" * 78)
    print("Order is the brief's: (d) first — it is the one a reviewer cannot audit.")
    arm_d_absolute_path()
    arm_b_minting()
    arm_c_produced_provenance()
    arm_a_stays_dead()
    print("\n%d assertions, %d failed" % (CASES, len(FAILURES)))
    for f in FAILURES:
        print("  FAILED: " + f)
    print("\nOPEN AFTER THIS TASK, STATED AT THE BOTTOM SO IT IS NOT MISSED:")
    print("  * `produced:` can still name evidence the file did not produce, provided that")
    print("    evidence is MANIFEST-pinned. GRADED, not closed. (arm (c))")
    print("  * an exemption can still be minted by someone willing to commit the file.")
    print("    RAISED, not closed. (arm (b))")
    sys.exit(1 if FAILURES else 0)
