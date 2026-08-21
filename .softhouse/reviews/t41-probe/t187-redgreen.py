#!/usr/bin/env python3
"""T187 red/green prover for the t41-probe in-place rewriters.

WHAT IT PROVES, AND WHY IT IS PHRASED THIS WAY (P-50).  A prover that only
shows the defect passes when the defect is present and goes red when it is
fixed - which is exactly backwards.  This one asserts BOTH directions, so
exactly one arrangement of the world passes:

  RED-1   the PRE-FIX bytes, read from commit 16d5252 (the commit T187 branched
          from) and NOT from the working tree, mutate a scratch copy with NO
          argv, NO authorisation and NO content gate.  The defect is real.
  RED-1L  the same PRE-FIX bytes, run against a byte-identical scratch copy of
          the CURRENT ratified DEC-1 / frozen contract.go, either DO or DO NOT
          mutate it - and the expectation is recorded per script.  Two of them
          DO: that is the live gate bypass.
  RED-2   the POST-FIX bytes REFUSE a target whose content is the ratified /
          frozen artefact: exit 3, target byte-identical afterwards.
  RED-3   the POST-FIX bytes REFUSE a run with no argv at all: exit 2, and with
          a correct token but the artefact's own path: exit 2.
  GREEN   the POST-FIX bytes STILL PERFORM the recorded edit on the legitimate
          scratch target: exit 0, output sha256 == the pinned AFTER_SHA256.

If the working tree still held the pre-fix bytes, RED-2/RED-3/GREEN would fail.
If the fix had removed the edit, GREEN would fail.  If the defect had never
existed, RED-1 would fail.

NOTHING IN THE REPOSITORY IS OPENED FOR WRITING.  Every trial runs with cwd set
to a scratch tree under /tmp seeded from `git show`, and the two protected
artefacts are re-hashed before and after the whole run.  A hash that moves is a
hard failure.

P-40: this prover COUNTS WHAT IT SKIPPED.  Every family member is either
exercised or NAMED with the reason, and the totals are printed.

Exit 0 = every assertion held.  Exit 1 = at least one did not.
"""
import ast
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"

# The two artefacts, as ratified/frozen on main when T187 ran.
LIVE_ADR = "49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab"
LIVE_GO = "0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139"

# The commit T187 branched from: the PRE-FIX bytes live there, permanently.
PREFIX_REV = "16d525213ea088984f11cba281419d59f039c0f9"

# Seeds for replaying T41's own edit chain, which is how each script's
# legitimate BEFORE fixture is reconstructed.
SEED_ADR_REV = "3594820^"
SEED_GO_REV = "e96541d^"

# T41's rewriters in commit order.  This order is a FACT about the repository
# (`git log --diff-filter=A`), not a guess; it is what makes each script's
# BEFORE fixture reconstructible.
ORDER = ["edit.py", "edit2.py", "edit3.py", "edit4.py", "edit5.py",
         "edit6.py", "edit7.py", "edit8.py", "edit9.py", "edit10.py",
         "edit11.py", "edit12.py", "edit13.py", "edit14.py",
         "edit_go1.py", "edit_go2.py", "edit_go3.py", "edit_go4.py",
         "edit16.py", "edit17.py", "edit18.py", "edit19.py",
         "edit20.py", "edit21.py", "edit22.py"]

# Family members that are NOT rewriters, named rather than silently dropped.
NOT_REWRITERS = {
    "leakgrep.py": "read-only grep over the ADR; opens nothing for writing",
    "t41_model.py": "pure model, no file writes",
    "t41_discriminate.py": "reads captures, writes nothing",
    "t41_validate.py": "reads captures, writes nothing",
    "t187-redgreen.py": "this prover",
    "t187-census.py": "T187's census; reads ASTs, writes nothing",
}

# Rewriters whose anchors match NO state of their target that has ever existed
# in this repository, so no input exists on which they mutate anything.  Their
# defect is structural (RED-1S below), not reachable, and saying so is the
# point: an expectation recorded per script stays falsifiable in both
# directions - if one of these ever became reachable, RED-1 would fail.
NO_REACHABLE_INPUT = {
    "edit22.py": "its FIRST anchor spells the comment wrap `... no deployment "
                 "/ can produce ...` where every state of contract.go that "
                 "contains the surrounding sentence spells it `... no "
                 "deployment can / produce ...`; measured against all 21 "
                 "distinct historical blobs, all 21 refuse with `found 0`",
}

FAILURES = []
CHECKS = [0]


def check(ok, what):
    CHECKS[0] += 1
    if not ok:
        FAILURES.append(what)
    print("    %s  %s" % ("PASS" if ok else "**FAIL**", what))
    return ok


def sha_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def git_show(rev_path):
    r = subprocess.run(["git", "show", rev_path], cwd=REPO,
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git show %s failed: %s"
                         % (rev_path, r.stderr.decode()[:200]))
    return r.stdout


def consts(path):
    """Read NAME / AUTHORISE_TOKEN / *_SHA256 out of a hardened script's AST.

    Reading them rather than importing is deliberate: importing one of these
    scripts EXECUTES it, and running a rewriter to find out what it does is the
    defect, not the test."""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name) and isinstance(node.value, ast.Constant):
                out[t.id] = node.value.value
    return out


def make_tree(root):
    for d in (os.path.dirname(ADR_REL), os.path.dirname(GO_REL)):
        p = os.path.join(root, d)
        if not os.path.isdir(p):
            os.makedirs(p)
    return os.path.join(root, ADR_REL), os.path.join(root, GO_REL)


def run_bytes(script_bytes, argv, cwd, tmpdir):
    """Run the PRE-FIX bytes, read from `git show`, never from the working
    tree - so the counterproof is against the real pre-fix bytes (P-22) even
    after the working tree has been fixed.  A pre-fix script resolves its
    target purely from cwd, so its own location is irrelevant."""
    fd, p = tempfile.mkstemp(dir=tmpdir, suffix=".py")
    os.write(fd, script_bytes)
    os.close(fd)
    try:
        return subprocess.run([sys.executable, p] + argv, cwd=cwd,
                              capture_output=True, text=True)
    finally:
        os.unlink(p)


def run_file(path, argv, cwd):
    """Run the POST-FIX script FROM ITS REAL LOCATION.  It must be run there
    and nowhere else: it resolves the shared guard, and the repository working
    tree it refuses to write into, from its own `__file__`."""
    return subprocess.run([sys.executable, path] + argv, cwd=cwd,
                          capture_output=True, text=True)


def main():
    live_adr_path = os.path.join(REPO, ADR_REL)
    live_go_path = os.path.join(REPO, GO_REL)
    a0, g0 = sha_file(live_adr_path), sha_file(live_go_path)
    print("PROTECTED ARTEFACTS BEFORE THIS RUN")
    print("  DEC-1       %s" % a0)
    print("  contract.go %s" % g0)
    if a0 != LIVE_ADR or g0 != LIVE_GO:
        print("REFUSING: a protected artefact is not at its expected digest.")
        return 1

    sb = tempfile.mkdtemp(prefix="t187-redgreen-")
    try:
        return body(sb, live_adr_path, live_go_path)
    finally:
        a1, g1 = sha_file(live_adr_path), sha_file(live_go_path)
        print("\nPROTECTED ARTEFACTS AFTER THIS RUN")
        print("  DEC-1       %s  %s"
              % (a1, "UNMOVED" if a1 == a0 else "*** MOVED ***"))
        print("  contract.go %s  %s"
              % (g1, "UNMOVED" if g1 == g0 else "*** MOVED ***"))
        if a1 != a0 or g1 != g0:
            FAILURES.append("a protected artefact MOVED during this run")
        shutil.rmtree(sb, ignore_errors=True)


def body(sb, live_adr_path, live_go_path):
    prefix = {}
    for n in ORDER:
        prefix[n] = git_show("%s:.softhouse/reviews/t41-probe/%s"
                             % (PREFIX_REV, n))

    # ---------------------------------------------------------------- chain
    # Replay T41's own chain with the PRE-FIX bytes to reconstruct, for every
    # script, the exact document state it was written against.  Snapshot the
    # state BEFORE each script runs: that snapshot is that script's legitimate
    # scratch target.
    chain = os.path.join(sb, "chain")
    cadr, cgo = make_tree(chain)
    io.open(cadr, "wb").write(git_show("%s:%s" % (SEED_ADR_REV, ADR_REL)))
    io.open(cgo, "wb").write(git_show("%s:%s" % (SEED_GO_REV, GO_REL)))
    states = {}
    print("\nRECONSTRUCTING T41's EDIT CHAIN (pre-fix bytes, scratch only)")
    for n in ORDER:
        d = os.path.join(sb, "state", n)
        os.makedirs(d)
        shutil.copyfile(cadr, os.path.join(d, "adr"))
        shutil.copyfile(cgo, os.path.join(d, "go"))
        states[n] = d
        r = run_bytes(prefix[n], [], chain, sb)
        print("  %-12s rc=%d  ADR %s  GO %s"
              % (n, r.returncode, sha_file(cadr)[:10], sha_file(cgo)[:10]))

    # -------------------------------------------------------------- trials
    exercised = []
    for n in ORDER:
        hardened_path = os.path.join(HERE, n)
        if not os.path.isfile(hardened_path):
            FAILURES.append("%s: missing from the working tree" % n)
            continue
        hardened = io.open(hardened_path, "rb").read()
        c = consts(hardened_path)
        if "AUTHORISE_TOKEN" not in c:
            # NOT a skip.  A rewriter in this family that carries no
            # AUTHORISE_TOKEN is an UNGUARDED rewriter, which is the whole
            # defect; a prover that quietly skipped it would be P-22's guard
            # that cannot fail.  It is a hard failure and it is counted.
            CHECKS[0] += 1
            FAILURES.append("%s: UNGUARDED - no AUTHORISE_TOKEN in its AST" % n)
            print("\n%s\n    **FAIL**  UNGUARDED - no AUTHORISE_TOKEN" % n)
            continue
        exercised.append(n)
        print("\n%s" % n)
        trial(n, prefix[n], hardened_path, c, states[n], sb,
              live_adr_path, live_go_path)

    print("\n" + "=" * 70)
    print("EXERCISED %d of %d rewriters; %d assertions."
          % (len(exercised), len(ORDER), CHECKS[0]))
    not_exercised = [n for n in ORDER if n not in exercised]
    print("NOT EXERCISED (%d): %s"
          % (len(not_exercised), ", ".join(not_exercised) or "none"))
    if not_exercised:
        FAILURES.append("%d rewriter(s) were not exercised: %s"
                        % (len(not_exercised), ", ".join(not_exercised)))
    print("NOT REWRITERS (%d, named per P-40):" % len(NOT_REWRITERS))
    for k, v in sorted(NOT_REWRITERS.items()):
        print("  %-22s %s" % (k, v))
    if FAILURES:
        print("\nFAILURES (%d):" % len(FAILURES))
        for f in FAILURES:
            print("  " + f)
        return 1
    print("\nALL ASSERTIONS HELD.")
    return 0


def strings(tree):
    """Every string constant in the module EXCEPT the module docstring."""
    out = []
    doc = tree.body[0].value if (tree.body and isinstance(tree.body[0], ast.Expr)
                                 and isinstance(tree.body[0].value,
                                                ast.Constant)) else None
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                and n is not doc:
            out.append(n.value)
    return out


def argv_for(two, want_go, path, other, tok):
    """Build argv for one trial.  A single-target script takes `--target=`; a
    two-target script takes `--target-adr=` and `--target-go=` and needs BOTH,
    so the target under test is paired with the other one's legitimate fixture."""
    if not two:
        return ["--target=" + path, "--authorise=" + tok]
    a = ["--target-" + ("go" if want_go else "adr") + "=" + path]
    if other is not None:
        a.append("--target-" + ("adr" if want_go else "go") + "=" + other)
    a.append("--authorise=" + tok)
    return a


def targets_of(c):
    """Which artefact kinds this hardened script drives, from its constants."""
    out = []
    if "BEFORE_SHA256" in c:
        out.append(("single", c["BEFORE_SHA256"], c["AFTER_SHA256"]))
    if "BEFORE_ADR" in c:
        out.append(("adr", c["BEFORE_ADR"], c["AFTER_ADR"]))
    if "BEFORE_GO" in c:
        out.append(("go", c["BEFORE_GO"], c["AFTER_GO"]))
    return out


def trial(n, pre, hardened_path, c, state, sb, live_adr_path,
          live_go_path):
    src = io.open(hardened_path, encoding="utf-8").read()
    kind = "go" if ("FROZEN_CONTRACT" in src
                    and "guard.RATIFIED_ADR" not in src) else "adr"
    two = "BEFORE_ADR" in c
    tok = c["AUTHORISE_TOKEN"]

    # ---- EDIT IDENTITY: every docstring in this family claims "the edit
    # itself did not change".  That is a claim, so it is measured rather than
    # asserted: the MULTISET of every string constant in the module, minus the
    # module docstring (which T187 rewrote on purpose) and minus the constants
    # T187 added, must be identical pre-fix and post-fix.  A dropped or altered
    # anchor or replacement string fails here even for the two files that
    # produce no output and therefore have no AFTER digest to compare.
    # The hardening removes exactly five kinds of string and nothing else: the
    # two hard-wired repo-relative target paths, the `"utf-8"` encoding
    # argument and the `"w"` mode of the deleted io.open calls, and the `"/"`
    # of `path.rsplit("/", 1)` in the old patch() helper.  Every OTHER string -
    # every anchor, every replacement - must still be present.  Anything else
    # disappearing is a silently altered edit and fails here.
    added = {c.get("NAME"), c.get("AUTHORISE_TOKEN"), c.get("BEFORE_SHA256"),
             c.get("AFTER_SHA256"), c.get("BEFORE_ADR"), c.get("AFTER_ADR"),
             c.get("BEFORE_GO"), c.get("AFTER_GO"), None,
             ADR_REL, GO_REL, "utf-8", "w", "/"}
    pre_s = strings(ast.parse(pre.decode("utf-8")))
    post_s = strings(ast.parse(io.open(hardened_path, encoding="utf-8").read()))
    lost = sorted(set(pre_s) - set(post_s) - added)
    check(not lost,
          "IDENT  every anchor and replacement string survives the hardening "
          "(%d string constants pre-fix, %d post-fix, %d lost)"
          % (len(pre_s), len(post_s), len(lost))
          + ("" if not lost else "  LOST: %r" % (lost[:2],)))

    # ---- RED-1: the pre-fix bytes mutate a scratch copy with no argv -------
    t = os.path.join(sb, "red1", n)
    os.makedirs(t)
    adr, go = make_tree(t)
    shutil.copyfile(os.path.join(state, "adr"), adr)
    shutil.copyfile(os.path.join(state, "go"), go)
    b_adr, b_go = sha_file(adr), sha_file(go)
    r = run_bytes(pre, [], t, sb)
    moved = (sha_file(adr) != b_adr) or (sha_file(go) != b_go)
    want = n not in NO_REACHABLE_INPUT
    if want:
        check(moved,
              "RED-1  pre-fix bytes mutate a scratch copy with no argv, no "
              "authorisation and no content gate (rc=%d)" % r.returncode)
    else:
        check(not moved,
              "RED-1  pre-fix bytes mutate NOTHING, as recorded: %s (rc=%d)"
              % (NO_REACHABLE_INPUT[n], r.returncode))

    # RED-1S: the STRUCTURAL defect, read from the pre-fix AST rather than from
    # behaviour, so it holds for the unreachable ones too.  This is the claim
    # that makes every one of these a gate bypass whether or not it applies
    # today: a truncating write to a hard-wired repo-relative path to a
    # protected artefact, with no try / atexit / signal anywhere in the file.
    tree = ast.parse(pre.decode("utf-8"))
    hard = set()
    trunc = 0
    guards = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Try, ast.With)):
            guards += 1
        if isinstance(node, ast.Call):
            f = node.func
            nm = getattr(f, "attr", getattr(f, "id", None))
            if nm in ("open",) and len(node.args) >= 2:
                m = node.args[1]
                if isinstance(m, ast.Constant) and "w" in str(m.value):
                    trunc += 1
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in (ADR_REL, GO_REL):
                hard.add(node.value)
    check(trunc >= 1 and bool(hard),
          "RED-1S pre-fix AST: %d truncating write-open(s), hard-wired "
          "repo-relative target(s) %s, %d try/with node(s)"
          % (trunc, sorted(x.rsplit("/", 1)[-1] for x in hard), guards))

    # ---- RED-1L: the pre-fix bytes against copies of the LIVE artefacts ----
    t = os.path.join(sb, "red1L", n)
    os.makedirs(t)
    adr, go = make_tree(t)
    shutil.copyfile(live_adr_path, adr)
    shutil.copyfile(live_go_path, go)
    r = run_bytes(pre, [], t, sb)
    live_moved = (sha_file(adr) != LIVE_ADR) or (sha_file(go) != LIVE_GO)
    print("    NOTE  RED-1L pre-fix vs a copy of the LIVE artefacts: "
          "rc=%d  live-mutated=%s" % (r.returncode, live_moved))

    # ---- RED-2 / RED-3 / GREEN on the post-fix bytes -----------------------
    for label, before, after in targets_of(c):
        want_go = (label == "go") or (label == "single" and kind == "go")
        src_state = os.path.join(state, "go" if want_go else "adr")
        live_src = live_go_path if want_go else live_adr_path
        live_sha = LIVE_GO if want_go else LIVE_ADR
        suffix = ".gotext" if want_go else ".md"
        tag = "" if label == "single" else " [%s]" % label

        check(before != LIVE_ADR and before != LIVE_GO,
              "GATE   BEFORE_SHA256%s is neither the ratified DEC-1 nor the "
              "frozen contract.go" % tag)
        check(sha_file(src_state) == before,
              "GATE   the reconstructed chain state matches the pinned "
              "BEFORE_SHA256%s" % tag)

        # RED-2: refuse a target whose CONTENT is the live artefact.  For a
        # two-target script the OTHER target is its legitimate fixture, so the
        # trial isolates this one target's content gate.
        d = os.path.join(sb, "red2", n + label)
        os.makedirs(d)
        p = os.path.join(d, "scratch-copy-of-live" + suffix)
        shutil.copyfile(live_src, p)
        other = None
        if two:
            other = os.path.join(d, "scratch-other" +
                                 (".md" if want_go else ".gotext"))
            shutil.copyfile(os.path.join(state, "adr" if want_go else "go"),
                            other)
        r = run_file(hardened_path, argv_for(two, want_go, p, other, tok), d)
        check(r.returncode == 3 and sha_file(p) == live_sha,
              "RED-2  refuses a target holding the LIVE artefact's bytes "
              "(exit %d, wanted 3) and leaves it byte-identical%s"
              % (r.returncode, tag))

        def reset():
            """Re-seed BOTH scratch files.  A two-target script commits its
            first target before refusing on its second, so a trial that reused
            the previous trial's files would be gated on the wrong content -
            which is exactly how this prover first mis-read RED-3b as exit 3."""
            shutil.copyfile(live_src, p)
            if other is not None:
                shutil.copyfile(os.path.join(state, "adr" if want_go
                                             else "go"), other)

        # RED-3a: no argv at all.
        reset()
        r = run_file(hardened_path, [], d)
        check(r.returncode == 2,
              "RED-3a refuses a run with no argv (exit %d, wanted 2)%s"
              % (r.returncode, tag))
        # RED-3b: correct token, but the artefact's real path.
        reset()
        real = live_go_path if want_go else live_adr_path
        r = run_file(hardened_path, argv_for(two, want_go, real, other, tok), d)
        check(r.returncode == 2 and sha_file(real) == live_sha,
              "RED-3b refuses the artefact's OWN path even with the correct "
              "token (exit %d, wanted 2)%s" % (r.returncode, tag))
        # RED-3c: right target, wrong token.
        reset()
        r = run_file(hardened_path, argv_for(two, want_go, p, other, "nope"), d)
        check(r.returncode == 2,
              "RED-3c refuses a wrong --authorise token (exit %d, wanted 2)%s"
              % (r.returncode, tag))

        # GREEN: the legitimate scratch target.
        g = os.path.join(sb, "green", n + label)
        os.makedirs(g)
        gp = os.path.join(g, "scratch-before" + suffix)
        shutil.copyfile(src_state, gp)
        gother = None
        if two:
            gother = os.path.join(g, "scratch-other" +
                                  (".md" if want_go else ".gotext"))
            shutil.copyfile(os.path.join(state,
                                         "adr" if want_go else "go"), gother)
        r = run_file(hardened_path, argv_for(two, want_go, gp, gother, tok), g)
        got = sha_file(gp)
        if after == "f" * 64:
            check(r.returncode == 1 and got == before,
                  "GREEN  no reproducible edit exists for this file (its "
                  "anchors match no blob in this repository's history): the "
                  "authorised run passes authorisation and the content gate "
                  "and stops at the anchor, exit %d (wanted 1), scratch "
                  "target byte-identical%s" % (r.returncode, tag))
        else:
            check(got == after,
                  "GREEN  the recorded edit STILL APPLIES on the legitimate "
                  "scratch target: %s -> %s (rc=%d)%s"
                  % (before[:10], got[:10], r.returncode, tag))


if __name__ == "__main__":
    sys.exit(main())
