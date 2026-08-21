#!/usr/bin/env python3
"""Drive manifest.py's THREE BLIND SPOTS red against the REAL pre-fix bytes, then green
against the fixed script.

A2-4's D-3 said `manifest.py verify` is blind three ways:
  (i)   vacuous on empty input — "OK: 0 files match", exit 0;
  (ii)  non-recursive — a fabricated observation dropped in out/<subdir>/ is laundered;
  (iii) covers neither CAPTURE-PLAN.md, nor the rig, nor itself — the reviewer appended
        "MNT rounds HALF_EVEN and money may be stored as float" to the analysis doc and
        verify stayed GREEN.

P-22 requires the counterproof to run against the real pre-fix bytes, because a proof
that only shows the "after" cannot distinguish a fix from a no-op. The pre-fix manifest.py
is therefore read from its immutable git blob and its sha256 checked before use.

Every attack runs in a throwaway sandbox that mimics this capture's shape. NOTHING under
the real out/, req/ or sql/ is read, written or hashed by this prover.
prove-manifest-red.py separately proves the hash comparison itself is failable against the
real tree; this prover proves the manifest COVERS WHAT MATTERS.

Run:  python3 prove-manifest-blind-red.py
Exit 0 only if the pre-fix tool was blind to every attack AND the fixed tool caught it.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))

# Immutable git blob of manifest.py as it stood BEFORE this fix.
PRE_BLOB = "cbc888d4698cb8211a8ceec31494314dc64d1a67"
PRE_SHA256 = "65e54af93a201fe7beb3c679f0fe15dabb2753d44287c69250adc1a6a1380a8b"

# The exact sentence the A2-4 reviewer appended to CAPTURE-PLAN.md while verify stayed green.
POISON = "MNT rounds HALF_EVEN and money may be stored as float\n"

ATTEMPT1 = [
    "attempt1-A2-prod-060-cash-with-channel-override",
    "attempt1-A2-prod-067-duplicate-channel",
]


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def pre_fix_source():
    r = subprocess.run(["git", "cat-file", "blob", PRE_BLOB], cwd=DIR, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"cannot read pre-fix blob {PRE_BLOB}: {r.stderr.decode()}")
    got = sha256(r.stdout)
    if got != PRE_SHA256:
        raise SystemExit(f"pre-fix blob sha256 mismatch: {got} != {PRE_SHA256}")
    return r.stdout


def build(tool_src, populate=True):
    """A miniature of this capture directory, with the tool under test as manifest.py."""
    sb = tempfile.mkdtemp(prefix="man-red-")
    for d in ("out", "req", "sql"):
        os.mkdir(os.path.join(sb, d))
    if populate:
        w(sb, "out/A2-001-observation.json", '{"glAccountId":7,"name":"real observation"}\n')
        w(sb, "out/A2-001-observation.status", "200\n")
        w(sb, "out/A2-001-observation.http", "POST /glaccounts\ncaptured-at-utc: 2026-08-21T06:00:00Z\n")
        for n in ATTEMPT1:
            w(sb, f"out/{n}.json", '{"developerMessage":"real oracle refusal"}\n')
            w(sb, f"out/{n}.status", "400\n")
            w(sb, f"out/{n}.http", "POST /loanproducts\nbody-file: req/stale.json\n")
        w(sb, "req/acct-001.json", '{"name":"asset header","type":1}\n')
        w(sb, "sql/q1-final-state.sql", "SELECT id, classification_enum FROM acc_gl_account;\n")
    w(sb, "CAPTURE-PLAN.md", "# A2 capture plan\n\nFinding 3: MNT rounding mode is HALF_UP (tenant-pinned).\n")
    w(sb, "DEFECTS-FOUND-BY-REVIEW.md", "# Defects\n\nD-1: the attempt1-* recipes are provably false.\n")
    w(sb, "FLAGGED-NOT-REPRODUCIBLE.txt",
      "# flagged, real bytes, false recipes (D-1)\n" + "".join(f"out/{n}.json\n" for n in ATTEMPT1))
    w(sb, "cap.sh", "#!/bin/sh\n# capture rig\nB=https://localhost:8443/fineract-provider/api/v1\n")
    w(sb, "env.sh", "#!/bin/sh\nT='Fineract-Platform-TenantId: gerege'\n")
    with open(os.path.join(sb, "manifest.py"), "wb") as f:
        f.write(tool_src)
    return sb


def w(sb, rel, text):
    p = os.path.join(sb, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


def run(sb, cmd):
    r = subprocess.run([sys.executable, os.path.join(sb, "manifest.py"), cmd],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()


# ---------------------------------------------------------------- the attacks
def atk_empty(sb):
    """(i) zero inspected files: an empty capture and an empty manifest."""
    for d in ("out", "req", "sql"):
        shutil.rmtree(os.path.join(sb, d))
        os.mkdir(os.path.join(sb, d))
    open(os.path.join(sb, "MANIFEST.sha256"), "w").close()


def atk_subdir(sb):
    """(ii) a fabricated observation one level down."""
    w(sb, "out/sub/A2-999-fabricated.json", '{"fabricated":true,"amount":1250000}\n')


def atk_plan(sb):
    """(iii) the reviewer's poison sentence appended to the analysis doc."""
    with open(os.path.join(sb, "CAPTURE-PLAN.md"), "a") as f:
        f.write(POISON)


def atk_self(sb):
    """(iii) the verifier edits itself."""
    with open(os.path.join(sb, "manifest.py"), "a") as f:
        f.write("# tampered: a verifier that does not hash itself certifies its own edits\n")


def atk_rig(sb):
    """(iii) the capture rig is repointed at another endpoint."""
    p = os.path.join(sb, "cap.sh")
    s = open(p).read().replace("localhost:8443", "some-other-host:8443")
    open(p, "w").write(s)


def atk_dropflag(sb):
    """the D-1 flag on the attempt1-* evidence is quietly dropped."""
    os.remove(os.path.join(sb, "FLAGGED-NOT-REPRODUCIBLE.txt"))


ATTACKS = [
    ("D-3(i)",   "empty manifest, empty capture — a guard that inspects NOTHING",
     atk_empty, True, ("INSPECTED NOTHING",)),
    ("D-3(i-b)", "a manifest written by the OLD tool (out/req/sql only) verified by the new one",
     None, False, ("REFUSING", "does not cover")),
    ("D-3(ii)",  "fabricated observation dropped in out/sub/",
     atk_subdir, False, ("UNTRACKED", "out/sub/A2-999-fabricated.json")),
    ("D-3(iii)", "CAPTURE-PLAN.md poisoned with the reviewer's HALF_EVEN/float sentence",
     atk_plan, False, ("CHANGED", "CAPTURE-PLAN.md")),
    ("D-3(iii)", "manifest.py edits ITSELF",
     atk_self, False, ("CHANGED", "manifest.py")),
    ("D-3(iii)", "the rig (cap.sh) is repointed at a different endpoint",
     atk_rig, False, ("CHANGED", "cap.sh")),
    ("D-1 flag", "FLAGGED-NOT-REPRODUCIBLE.txt deleted — the flag on real-bytes/false-recipes",
     atk_dropflag, False, ("REFUSING", "FLAGGED")),
]


def atk_flag_evidence_deleted(sb):
    """flagged evidence deleted from disk while its manifest line stays."""
    os.remove(os.path.join(sb, f"out/{ATTEMPT1[0]}.json"))


def atk_flag_uncovered(sb):
    """flagged evidence still on disk, but its manifest line stripped out."""
    p = os.path.join(sb, "MANIFEST.sha256")
    keep = [l for l in open(p) if f"out/{ATTEMPT1[0]}.json" not in l]
    open(p, "w").writelines(keep)


def atk_malformed(sb):
    """a manifest line that is not `<sha256>  <path>`."""
    p = os.path.join(sb, "MANIFEST.sha256")
    lines = open(p).readlines()
    lines[0] = "not-a-manifest-line\n"
    open(p, "w").writelines(lines)


# Branches with no pre-fix counterpart to be blind to (they are new refusals, or the
# pre-fix tool happened to catch the same input by a different route). P-22 still says
# ship no guard you have not driven red, so each is driven red on its own.
POST_ONLY = [
    ("D-1 flag", "flagged evidence DELETED from out/ (manifest line left in place)",
     atk_flag_evidence_deleted, ("FLAGGED-BUT-ABSENT",)),
    ("D-1 flag", "flagged evidence left on disk but its manifest line STRIPPED",
     atk_flag_uncovered, ("FLAGGED-BUT-UNCOVERED",)),
    ("parser",   "a malformed MANIFEST.sha256 line",
     atk_malformed, ("MALFORMED",)),
]


def case(tool_src, attack, empty, pre_written_by=None):
    sb = build(tool_src, populate=not empty)
    try:
        if pre_written_by is not None:
            # the manifest is produced by the OLD tool, then verified by the tool under test
            tmp = os.path.join(sb, "manifest.py")
            cur = open(tmp, "rb").read()
            open(tmp, "wb").write(pre_written_by)
            run(sb, "write")
            open(tmp, "wb").write(cur)
        else:
            rc, out = run(sb, "write")
            if rc != 0 and not empty:
                return None, f"setup failed: {out}"
        if attack is not None:
            attack(sb)
        return run(sb, "verify")
    finally:
        shutil.rmtree(sb, ignore_errors=True)


def main():
    pre = pre_fix_source()
    post_path = os.path.join(DIR, "manifest.py")
    post = open(post_path, "rb").read()
    if post == pre:
        print("manifest.py is byte-identical to the pre-fix blob — nothing to prove", file=sys.stderr)
        return 2

    print("=" * 100)
    print("D-3  manifest.py verify — RED against the real pre-fix bytes, GREEN after")
    print("=" * 100)
    print(f"pre-fix  manifest.py: git blob {PRE_BLOB}  sha256 {PRE_SHA256}")
    print(f"post-fix manifest.py: working tree           sha256 {sha256(post)}")
    print("all attacks run in a throwaway sandbox; the real out/ req/ sql/ are never touched.")
    print()

    failures = []
    for tag, title, attack, empty, expect in ATTACKS:
        print("-" * 100)
        print(f"{tag}  {title}")
        print("-" * 100)

        pre_written = pre if attack is None else None
        rc_pre, out_pre = case(pre, attack, empty, pre_written_by=pre_written)
        rc_post, out_post = case(post, attack, empty, pre_written_by=pre_written)

        print(f"  [RED ] pre-fix  verify -> exit {rc_pre}")
        for line in (out_pre or "(no output)").splitlines():
            print("           " + line)
        blind = rc_pre == 0
        print(f"         pre-fix verdict: {'BLIND (passed the attack)' if blind else 'caught it'}")
        if not blind:
            failures.append(f"{tag} {title}: pre-fix was NOT blind (exit {rc_pre}) — nothing proven")

        print(f"  [GREEN] post-fix verify -> exit {rc_post}")
        for line in (out_post or "(no output)").splitlines():
            print("           " + line)
        caught = rc_post != 0 and all(e in out_post for e in expect)
        print(f"         post-fix verdict: {'CAUGHT' if caught else 'MISSED'} "
              f"(expected exit!=0 and {' + '.join(expect)})")
        if not caught:
            failures.append(f"{tag} {title}: post-fix MISSED it")
        print()

    for tag, title, attack, expect in POST_ONLY:
        print("-" * 100)
        print(f"{tag}  {title}   (new refusal — driven red on the fixed tool alone)")
        print("-" * 100)
        rc, out = case(post, attack, False)
        for line in (out or "(no output)").splitlines():
            print("           " + line)
        caught = rc != 0 and all(e in out for e in expect)
        print(f"         exit {rc} -> {'CAUGHT' if caught else 'MISSED'} (expected {' + '.join(expect)})")
        if not caught:
            failures.append(f"{tag} {title}: MISSED")
        print()

    # control: the fixed tool must still go GREEN on an untampered sandbox, or every RED
    # above is just a tool that always fails.
    print("-" * 100)
    print("CONTROL  untampered sandbox — the fixed tool must still pass, or the REDs prove nothing")
    print("-" * 100)
    rc, out = case(post, None, False)
    for line in out.splitlines():
        print("           " + line)
    print(f"         exit {rc} -> {'GREEN' if rc == 0 else 'THE FIXED TOOL CANNOT PASS ANYTHING'}")
    if rc != 0:
        failures.append("post-fix tool fails on an untampered sandbox")

    print()
    print("NOT DRIVEN RED, stated rather than claimed: the second zero-input refusal")
    print("('found 0 files ... INSPECTED NOTHING') is unreachable in practice, because")
    print("manifest.py is itself covered and therefore always present in the scanned set.")
    print("It is belt-and-braces for a future edit that narrows the scan, not a proven guard.")
    print()
    print("=" * 100)
    if failures:
        print("RESULT: FAILED")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: all three D-3 blind spots reproduced on the real pre-fix bytes and closed by the fix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
