#!/usr/bin/env python3
"""T178 red/green prover for the eight in-place rewriters T167 did not reach.

WHAT IT PROVES, AND WHY IT IS PHRASED THIS WAY.  P-50: a prover must be
falsifiable in the direction of the FIX, not only in the direction of the
defect.  Every case below therefore asserts BOTH halves - that the PRE-FIX
bytes (read from the immutable fork-point commit, never from the moving ref
`main`, P-24/P-41) behave as the defect requires, AND that the POST-FIX bytes
in the working tree behave as the fix requires.  Exactly one arrangement of the
world exits 0: pre-fix defective and post-fix guarded.  Revert either side and
this prover goes red.

IT NEVER TOUCHES A REAL ARTEFACT.  Every run happens inside a throwaway
scratch repository under a temp directory: a directory tree that merely has the
SHAPE `<root>/.softhouse/reviews/t47-probe/` and `<root>/docs/adr/`, so the
scripts' own `dirname`-four-times computation resolves to the scratch root.  The
real `docs/adr/DEC-1-schedule-generator-adapter.md` and
`nexus/internal/apps/loanschedule/contract/contract.go` are sha256'd before and
after the whole run and the prover FAILS if either moved by a single byte.

CASES, per script (R1-R15):
  RED-A  pre-fix, no argv, target = the blob this edit was written against,
         sitting at the script's hard-wired repo path -> exit 0 and the file is
         rewritten.  This is the bypass: an unauthorised in-place amendment of
         a ratified DEC-n / the frozen contract, with no gate of any kind.
  RED-B  pre-fix, no argv, target = the CURRENT ratified DEC-1 / frozen
         contract.go.  For `t47_edit_4.py` this is exit 0 and a CHANGED file -
         a LIVE gate bypass today.  For the other seven it is exit 1 and an
         unchanged file: inert TODAY, which is a fact about today's document
         and not a guarantee, which is why all eight are hardened.
  RED-C  pre-fix, interrupted at the instant `io.open(path, "w")` returns -
         i.e. immediately after O_TRUNC and before any byte is written.  The
         target is left EMPTY (0 bytes).  Post-fix, the identical interruption
         leaves the target byte-identical to its input, because the guard never
         opens the target for writing at all.
  R1-R15 the post-fix refusal matrix and the GREEN legitimate run, including
         the content gate that is what actually closes RED-B, a candidate-gate
         falsification, a `python3 -O` run (no bare `assert` survives -O), and
         a fail-closed check with the guard module removed.

SELF-FALSIFICATION, and WHAT IT DOES NOT COVER.  `--falsify` re-runs R1-R15
against the PRE-FIX bytes and requires the battery to go RED; it exits 0 only
if it found failures.  Measured: 96 of 120 post-fix cases go red, 12 per
script.  The three that do NOT are stated here rather than left to be
discovered (P-29, P-40):

  * R13 and R14 deliberately build their own post-fix copies (a tampered one
    and one with the guard module deleted), so `--falsify` cannot reach them.
    They are falsified by construction instead: R13's mutation is applied by
    this prover and R14's deletion is performed by this prover, so each case
    IS its own counterproof.
  * R12 passes in `--falsify` for the seven scripts that are inert today,
    because the pre-fix script exits at its anchor check before it ever opens
    anything, leaving R12's separate scratch file untouched - which the case
    reads as "whole".  R12 is a genuine test only in normal mode, where its
    force comes from the contrast with RED-C on the SAME harness.

Exit 0 = every case as expected (normal mode) / the battery went red as
required (`--falsify`).  Exit 1 = at least one case not as expected (normal) /
the pre-fix bytes passed the refusal matrix (`--falsify`).
Exit 2 = a real protected artefact moved (stop and report).
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

# The immutable fork point this branch was cut from.  NOT `main`: a baseline
# that can follow `main` will follow it exactly when you stop watching (P-24),
# and `main` moves during a fire (P-41).
FORK = "dfa1bfa96084a2175f0d89d0a401a8c105d9a35f"

ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"

# Measured by T178 on 21 Aug 2026; re-measured at the start and end of this run.
ADR_MAIN_SHA = "49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab"
GO_MAIN_SHA = "0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139"

# id -> (name, kind, before_sha, after_sha, live_today)
SCRIPTS = [
    ("2", "edit2", "adr",
     "4f2387c821a01953503c77c2c70730bf72657c994491110c5ae3bc27a866dc37",
     "dcb04d14f0c1fba47d4aec9bf9a29596b995c4c740afc32c6640d9b8f3f705c5", False),
    ("3", "edit3", "adr",
     "fc6d17209fd94741c92f22f147a634eaefe0f3468877bdba84eb3621c1d48a0a",
     "5bbf7efb16c740fe91ba8b6933072eca98a54f2e1fe81024c6028f83c48f54da", False),
    ("4", "edit4", "adr",
     "f9deda22fecdcab160559920f40370246c66f1adaa902bb881ec4d772472c564",
     "9385f9070077651f95ded290f4a14976d1731485645d9618314f1507ade6c1ea", True),
    ("4c", "edit4c", "adr",
     "f9deda22fecdcab160559920f40370246c66f1adaa902bb881ec4d772472c564",
     "7b14fa36e5b15f74ec02061bdf4a1fbe6ed526150cb7cce81a0d5f95580e9cda", False),
    ("5", "edit5", "adr",
     "f9deda22fecdcab160559920f40370246c66f1adaa902bb881ec4d772472c564",
     "e0b1a30d7c69d170cf9fe49f453c23e1031be098efa4415a9416b540154fc71f", False),
    ("6", "edit6", "adr",
     "8a39c22620c9036e67cd0750739d1e3c6be2c6e034639d2a2d8292989575cf75",
     "be252dba2218b18b15d10138f9c5802ba6c2026c4c82c100f0e78a024bb2c5fe", False),
    ("7", "edit7", "go",
     "c9a0ad65df3d58f4e1ac451965555554710f0605df68c39dabe201b57242e1af",
     "5cac5f0f0e24c4f515abf0da9bb33b294f4c1ef3fa5eb146408b7caf057d5740", False),
    ("8", "edit8", "adr",
     "92ba7b4761f0c37d3484c376ecf6b1fc6161720faba7d5d536a5ebc02c39d243",
     "9e5c8c3620bff301188bb91ca8795f8b40d0eafab18aeeff1ab68ad5c5bb145d", False),
]

# The blob each script's BEFORE_SHA256 names, as an immutable git ref.
BEFORE_REF = {
    "2": "58dfec2^", "3": "f33af09^", "4": "5041778^", "4c": "5041778^",
    "5": "5041778^", "6": "77b1825^", "7": "aaa6ed0^", "8": "317c1da^",
}

TOKEN = {}
for _id, _name, _kind, _b, _a, _live in SCRIPTS:
    TOKEN[_id] = ("I-AM-REPRODUCING-T47-EDIT-%s-ON-A-SCRATCH-COPY-NOT-THE-%s"
                  % (_id.upper(),
                     "RATIFIED-DEC-1" if _kind == "adr" else "FROZEN-CONTRACT"))

# The interruption harness: wrap io.open so that the first open-for-write
# returns after O_TRUNC has already emptied the file and then raises.  This is
# a faithful, DETERMINISTIC model of an interruption during the write - the
# same failure T167 drove with signals, without the timing race.
INTERRUPT = r'''
import io, runpy, sys
_real = io.open
def patched(*a, **k):
    mode = k.get("mode", a[1] if len(a) > 1 else "r")
    fh = _real(*a, **k)          # O_TRUNC has now already fired for mode "w"
    if "w" in mode:
        fh.close()
        raise KeyboardInterrupt("T178: simulated interruption right after O_TRUNC")
    return fh
io.open = patched
sys.argv = [sys.argv[1]] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name="__main__")
'''

FALSIFY = "--falsify" in sys.argv[1:]
for _a in sys.argv[1:]:
    if _a != "--falsify":
        sys.stderr.write("usage: t178-redprobe.py [--falsify]\n")
        sys.exit(1)

FAILURES = []
LINES = []


def say(msg):
    LINES.append(msg)
    print(msg)


def check(case, ok, detail):
    verdict = "as expected" if ok else "NOT AS EXPECTED"
    say("  %-10s %-15s %s" % (case, verdict, detail))
    if not ok:
        FAILURES.append("%s: %s" % (case, detail))


def sha_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def git_show(ref_path):
    return subprocess.check_output(["git", "-C", REPO, "show", ref_path])


def rel_for(kind):
    return ADR_REL if kind == "adr" else GO_REL


def make_scratch_repo(tmp, sid, kind, content, prefix):
    """A directory tree with the SHAPE of the repo, so the scripts' own
    dirname-four-times resolves here and never to the real repository."""
    root = os.path.join(tmp, prefix)
    os.makedirs(os.path.join(root, ".softhouse", "reviews", "t47-probe"))
    os.makedirs(os.path.dirname(os.path.join(root, rel_for(kind))))
    tgt = os.path.join(root, rel_for(kind))
    io.open(tgt, "wb").write(content)
    return root, tgt


def put_prefix(root, sid):
    p = os.path.join(root, ".softhouse", "reviews", "t47-probe",
                     "t47_edit_%s.py" % sid)
    io.open(p, "wb").write(
        git_show("%s:.softhouse/reviews/t47-probe/t47_edit_%s.py"
                 % (FORK, sid)))
    return p


def put_postfix(root, sid):
    d = os.path.join(root, ".softhouse", "reviews", "t47-probe")
    shutil.copy(os.path.join(HERE, "t178_guard.py"),
                os.path.join(d, "t178_guard.py"))
    p = os.path.join(d, "t47_edit_%s.py" % sid)
    shutil.copy(os.path.join(HERE, "t47_edit_%s.py" % sid), p)
    return p


def run(argv, cwd=None):
    r = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def first_line(txt):
    for ln in txt.splitlines():
        if ln.strip():
            return ln.strip()[:96]
    return "(no output)"


# --------------------------------------------------------------------------
# Integrity of the real protected artefacts - before.
# --------------------------------------------------------------------------
def integrity(when):
    a = sha_file(os.path.join(REPO, ADR_REL))
    g = sha_file(os.path.join(REPO, GO_REL))
    say("INTEGRITY %-6s DEC-1 %s" % (when, a))
    say("INTEGRITY %-6s contract.go %s" % (when, g))
    if a != ADR_MAIN_SHA or g != GO_MAIN_SHA:
        sys.stderr.write("T178: a PROTECTED ARTEFACT MOVED - stopping.\n")
        sys.exit(2)


say("T178 red/green prover - eight unguarded in-place rewriters")
say("repo            %s" % REPO)
say("pre-fix bytes   git show %s:.softhouse/reviews/t47-probe/t47_edit_N.py"
    % FORK)
say("")
integrity("BEFORE")
say("")

TMP = tempfile.mkdtemp(prefix="t178-")

for sid, name, kind, before_sha, after_sha, live_today in SCRIPTS:
    rel = rel_for(kind)
    before_blob = git_show("%s:%s" % (BEFORE_REF[sid], rel))
    current_blob = git_show("%s:%s" % (FORK, rel))
    say("=== t47_edit_%s.py  (%s, target %s)" % (sid, name, rel))

    # ---------------- RED-A: pre-fix, unauthorised, in-place --------------
    root, tgt = make_scratch_repo(TMP, sid, kind, before_blob, "A-%s" % sid)
    scr = put_prefix(root, sid)
    rc, out = run([sys.executable, scr])
    got = sha_file(tgt)
    check("RED-A", rc == 0 and got == after_sha,
          "pre-fix, NO argv: exit %d, %s -> %s (%s)"
          % (rc, before_sha[:8], got[:8], first_line(out)))

    # ---------------- RED-B: pre-fix against the CURRENT artefact ---------
    root, tgt = make_scratch_repo(TMP, sid, kind, current_blob, "B-%s" % sid)
    scr = put_prefix(root, sid)
    pre_now = sha_file(tgt)
    rc, out = run([sys.executable, scr])
    got = sha_file(tgt)
    if live_today:
        check("RED-B", rc == 0 and got != pre_now,
              "LIVE BYPASS: pre-fix rewrites the CURRENT ratified artefact: "
              "exit %d, %s -> %s" % (rc, pre_now[:8], got[:8]))
    else:
        check("RED-B", rc == 1 and got == pre_now,
              "inert TODAY: exit %d, %s unchanged (%s)"
              % (rc, pre_now[:8], first_line(out)))

    # ---------------- RED-C: interruption right after O_TRUNC -------------
    root, tgt = make_scratch_repo(TMP, sid, kind, before_blob, "C-%s" % sid)
    scr = put_prefix(root, sid)
    hook = os.path.join(root, "interrupt.py")
    io.open(hook, "w").write(INTERRUPT)
    rc, out = run([sys.executable, hook, scr])
    size = os.path.getsize(tgt)
    check("RED-C", rc != 0 and size == 0,
          "pre-fix interrupted at O_TRUNC: exit %d, target left %d bytes "
          "(was %d)" % (rc, size, len(before_blob)))

    # ---------------- post-fix: the refusal matrix ------------------------
    # The post-fix script is exercised AT ITS REAL PATH in this working tree,
    # not from a copy in a scratch repo.  That matters and the first draft of
    # this prover got it wrong: the "target is inside the repository working
    # tree" refusal is computed from the SCRIPT's own location (four dirnames
    # up), so a copy of the script in a scratch tree protects the SCRATCH
    # tree, and R5 passed a real-repo path straight through - exit 0, written.
    # Nothing was damaged (the file was a throwaway the prover created and
    # removed) but the case was vacuous, which is P-22 inside the prover.
    # LIMIT, stated rather than hidden: containment protects the tree that
    # contains the script.  A copy of one of these scripts moved elsewhere
    # still cannot reach the ratified ADR or the frozen contract, because the
    # basename / directory-name / `.go`-suffix refusals and the sha256 content
    # gate are absolute and location-independent - R4 and R8 below are run
    # against the REAL artefact path and its REAL current bytes.
    root, _ = make_scratch_repo(TMP, sid, kind, current_blob, "P-%s" % sid)
    put_postfix(root, sid)          # used by R13/R14, which need a mutable copy
    if FALSIFY:
        # --falsify: drive R1-R15 against the PRE-FIX bytes.  The battery MUST
        # go red; a prover whose green half cannot fail is P-22 again, one
        # level up.  In this mode the prover exits 0 only if it DID find
        # failures.
        scr = put_prefix(root, sid)
    else:
        scr = os.path.join(HERE, "t47_edit_%s.py" % sid)
    outside = os.path.join(TMP, "outside-%s" % sid)
    os.makedirs(outside)

    def scratch(namepart, blob):
        p = os.path.join(outside, namepart)
        io.open(p, "wb").write(blob)
        return p

    tok = "--authorise=%s" % TOKEN[sid]
    legit = scratch("legit-%s.txt" % sid, before_blob)

    rc, out = run([sys.executable, scr])
    check("R1", rc == 2, "no argv -> exit %d (%s)" % (rc, first_line(out)))

    rc, out = run([sys.executable, scr, "--target=%s" % legit])
    check("R2", rc == 2 and sha_file(legit) == before_sha,
          "--target with no --authorise -> exit %d, target untouched" % rc)

    rc, out = run([sys.executable, scr, "--target=%s" % legit,
                   "--authorise=WRONG"])
    check("R3", rc == 2 and sha_file(legit) == before_sha,
          "wrong token -> exit %d, target untouched" % rc)

    real = os.path.join(REPO, rel)
    real_before = sha_file(real)
    rc, out = run([sys.executable, scr, "--target=%s" % real, tok])
    check("R4", rc == 2 and sha_file(real) == real_before,
          "--target = the REAL protected artefact -> exit %d, real file "
          "untouched (%s)" % (rc, first_line(out)))

    inside = os.path.join(HERE, ".t178-inside-scratch.tmp")
    io.open(inside, "wb").write(before_blob)
    rc, out = run([sys.executable, scr, "--target=%s" % inside, tok])
    check("R5", rc == 2 and sha_file(inside) == before_sha,
          "--target inside the repo working tree -> exit %d" % rc)
    os.unlink(inside)

    if kind == "adr":
        d = os.path.join(outside, "some", "adr")
        os.makedirs(d, exist_ok=True)
        p = scratch(os.path.join("some", "adr", "copy.txt"), before_blob) \
            if False else os.path.join(d, "copy.txt")
        io.open(p, "wb").write(before_blob)
        rc, out = run([sys.executable, scr, "--target=%s" % p, tok])
        check("R6", rc == 2 and sha_file(p) == before_sha,
              "--target under a directory named `adr` -> exit %d" % rc)

        p = os.path.join(outside, os.path.basename(ADR_REL))
        io.open(p, "wb").write(before_blob)
        rc, out = run([sys.executable, scr, "--target=%s" % p, tok])
        check("R7", rc == 2 and sha_file(p) == before_sha,
              "--target named like the ratified ADR -> exit %d" % rc)
    else:
        d = os.path.join(outside, "some", "contract")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "copy.txt")
        io.open(p, "wb").write(before_blob)
        rc, out = run([sys.executable, scr, "--target=%s" % p, tok])
        check("R6", rc == 2 and sha_file(p) == before_sha,
              "--target under a directory named `contract` -> exit %d" % rc)

        p = os.path.join(outside, "anything.go")
        io.open(p, "wb").write(before_blob)
        rc, out = run([sys.executable, scr, "--target=%s" % p, tok])
        check("R7", rc == 2 and sha_file(p) == before_sha,
              "--target is a `.go` file (G-3) -> exit %d" % rc)

    cur = scratch("current-%s.txt" % sid, current_blob)
    cur_sha = sha_file(cur)
    rc, out = run([sys.executable, scr, "--target=%s" % cur, tok])
    check("R8", rc == 3 and sha_file(cur) == cur_sha,
          "CONTENT GATE: a scratch copy of the CURRENT artefact -> exit %d, "
          "untouched. This is what closes RED-B." % rc)

    rc, out = run([sys.executable, scr, "--target=%s" % legit, tok,
                   "--dry-run"])
    check("R9", rc == 0 and sha_file(legit) == before_sha,
          "--dry-run on the legitimate target -> exit %d, nothing written"
          % rc)

    rc, out = run([sys.executable, scr, "--target=%s" % legit, tok])
    got = sha_file(legit)
    check("R10", rc == 0 and got == after_sha,
          "GREEN: legitimate scratch target -> exit %d, %s -> %s (%s)"
          % (rc, before_sha[:8], got[:8], first_line(out)))

    legit2 = scratch("legit-O-%s.txt" % sid, before_blob)
    rc, out = run([sys.executable, "-O", scr, "--target=%s" % legit2, tok])
    check("R11", rc == 0 and sha_file(legit2) == after_sha,
          "GREEN under `python3 -O` (no bare assert survives -O) -> exit %d"
          % rc)

    # The interruption harness fires on the FIRST open-for-write.  For the
    # pre-fix script that is the TARGET itself (RED-C above: 0 bytes left).
    # For the post-fix script it is the mkstemp TEMP FILE, reached through
    # os.fdopen, which is io.open - so the identical interruption at the
    # identical primitive leaves the target WHOLE.  That contrast is the
    # atomicity proof.
    legit3 = scratch("legit-int-%s.txt" % sid, before_blob)
    hook = os.path.join(root, "interrupt.py")
    io.open(hook, "w").write(INTERRUPT)
    rc, out = run([sys.executable, hook, scr, "--target=%s" % legit3, tok])
    got = sha_file(legit3)
    check("R12", got in (before_sha, after_sha) and os.path.getsize(legit3) > 0,
          "post-fix under the SAME interruption harness -> exit %d, target is "
          "whole (%s)" % (rc, "unchanged" if got == before_sha else "completed"))

    tampered_root, _ = make_scratch_repo(TMP, sid, kind, current_blob,
                                         "T-%s" % sid)
    tscr = put_postfix(tampered_root, sid)
    txt = io.open(tscr, encoding="utf-8").read()
    marker = 'guard.commit(s)\n'
    txt = txt.replace(marker, 's = s + "T178 TAMPER\\n"\n' + marker)
    io.open(tscr, "w", encoding="utf-8").write(txt)
    legit4 = scratch("legit-tamper-%s.txt" % sid, before_blob)
    rc, out = run([sys.executable, tscr, "--target=%s" % legit4, tok])
    check("R13", rc == 4 and sha_file(legit4) == before_sha,
          "CANDIDATE GATE: a tampered edit -> exit %d, target untouched" % rc)

    noguard_root, _ = make_scratch_repo(TMP, sid, kind, current_blob,
                                        "N-%s" % sid)
    nscr = put_postfix(noguard_root, sid)
    os.unlink(os.path.join(os.path.dirname(nscr), "t178_guard.py"))
    legit5 = scratch("legit-noguard-%s.txt" % sid, before_blob)
    rc, out = run([sys.executable, nscr, "--target=%s" % legit5, tok])
    check("R14", rc != 0 and sha_file(legit5) == before_sha,
          "FAIL CLOSED: guard module removed -> exit %d, nothing written" % rc)

    rc, out = run([sys.executable, scr, "--target=%s" % legit, tok,
                   "--nonsense"])
    check("R15", rc == 2, "unknown argument -> exit %d" % rc)
    say("")

integrity("AFTER")
shutil.rmtree(TMP, ignore_errors=True)

say("")
say("mode           %s" % ("--falsify (R1-R15 driven against the PRE-FIX "
                           "bytes; failures are REQUIRED)" if FALSIFY
                           else "normal"))
say("cases run      %d" % (len(SCRIPTS) * 18))
say("NOT AS EXPECTED %d" % len(FAILURES))
for f in FAILURES:
    say("  - %s" % f)

if FALSIFY:
    if FAILURES:
        say("")
        say("FALSIFICATION OK: the post-fix half of this prover goes red when "
            "the fix is removed, so its green is not vacuous.")
        sys.exit(0)
    say("")
    say("FALSIFICATION FAILED: the pre-fix bytes passed the refusal matrix. "
        "This prover cannot tell a fix from a no-op.")
    sys.exit(1)
sys.exit(1 if FAILURES else 0)
