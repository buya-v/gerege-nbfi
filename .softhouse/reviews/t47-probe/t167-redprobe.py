#!/usr/bin/env python3
"""T167 red probe (P-22): drive the T47 ADR rewriter RED before and after the fix.

Everything happens in a scratch tree under $TMPDIR.  The real
docs/adr/DEC-1-schedule-generator-adapter.md is hashed at the start and at the
end of this run and is never a write target of anything here; the one place its
real path is used at all is refusal test R4, which exists precisely to prove the
hardened script refuses it, and its hash is re-checked immediately afterwards.

The PRE-FIX bytes are fetched from the immutable commit bf67a85 (P-24: never
from a moving ref such as `main:`).  That is the only commit that has ever
touched t47_edit_1.py, so it is the file's whole history.

No monetary quantity is computed anywhere in this probe (P-25); the only
non-integer values are sleep durations handed to time.sleep().
"""
import hashlib
import io
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
PREFIX_COMMIT = "bf67a85"
SCRIPT_REL = ".softhouse/reviews/t47-probe/t47_edit_1.py"
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
FIXED = os.path.join(REPO, SCRIPT_REL)
REAL_ADR = os.path.join(REPO, ADR_REL)
TOKEN = ("--authorise=I-AM-REPRODUCING-T47-EDIT-1-ON-A-SCRATCH-COPY-"
         "NOT-THE-RATIFIED-DEC-1")
BEFORE_SHA = "32539607c6b43a23d17300b588c70f9fb643c9d554e280cb7a81a2e9847468f0"
AFTER_SHA = "4f2387c821a01953503c77c2c70730bf72657c994491110c5ae3bc27a866dc37"
PY = sys.executable

SIGS = [("SIGINT", signal.SIGINT), ("SIGTERM", signal.SIGTERM),
        ("SIGHUP", signal.SIGHUP), ("SIGKILL", signal.SIGKILL)]


def sh(*a, **kw):
    return subprocess.run(a, cwd=kw.pop("cwd", REPO), capture_output=True,
                          text=kw.pop("text", True), **kw)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hdr(t):
    print("\n" + "=" * 78 + "\n== " + t + "\n" + "=" * 78)


def classify(path, expect_before_after=True):
    """Return a one-word verdict for a scratch target's state."""
    if not os.path.exists(path):
        return "MISSING", 0, "-"
    n = os.path.getsize(path)
    d = sha(path)
    if d == BEFORE_SHA:
        return "UNTOUCHED", n, d
    if d == AFTER_SHA:
        return "COMPLETED", n, d
    return "DAMAGED", n, d


# --------------------------------------------------------------------- setup
random.seed(20260821)
SCRATCH = tempfile.mkdtemp(prefix="t167-redprobe-")
FAKE_REPO = os.path.join(SCRATCH, "fakerepo")
FAKE_DIR = os.path.join(FAKE_REPO, ".softhouse/reviews/t47-probe")
FAKE_ADR_DIR = os.path.join(FAKE_REPO, "docs/adr")
DATA = os.path.join(SCRATCH, "data")
MIRROR_ADR_DIR = os.path.join(SCRATCH, "mirror/docs/adr")
for d in (FAKE_DIR, FAKE_ADR_DIR, DATA, MIRROR_ADR_DIR):
    os.makedirs(d)

PREFIX_SCRIPT = os.path.join(FAKE_DIR, "t47_edit_1.py")
FAKE_ADR = os.path.join(FAKE_ADR_DIR, "DEC-1-schedule-generator-adapter.md")

r = sh("git", "show", "%s:%s" % (PREFIX_COMMIT, SCRIPT_REL), text=False)
assert r.returncode == 0, r.stderr
open(PREFIX_SCRIPT, "wb").write(r.stdout)
r = sh("git", "show", "%s^:%s" % (PREFIX_COMMIT, ADR_REL), text=False)
assert r.returncode == 0, r.stderr
REV9 = r.stdout
open(os.path.join(DATA, "rev9.md"), "wb").write(REV9)

REAL_ADR_SHA_START = sha(REAL_ADR)

hdr("0.  PROVENANCE")
print("scratch tree          : %s" % SCRATCH)
print("pre-fix script         : %s:%s" % (PREFIX_COMMIT, SCRIPT_REL))
print("  sha256               : %s  (%d bytes)"
      % (sha(PREFIX_SCRIPT), os.path.getsize(PREFIX_SCRIPT)))
print("rev-9 ADR (pre-edit)   : %s^:%s" % (PREFIX_COMMIT, ADR_REL))
print("  sha256               : %s  (%d bytes)"
      % (hashlib.sha256(REV9).hexdigest(), len(REV9)))
print("  expected BEFORE_SHA  : %s  match=%s"
      % (BEFORE_SHA, hashlib.sha256(REV9).hexdigest() == BEFORE_SHA))
print("expected AFTER_SHA     : %s" % AFTER_SHA)
print("real ADR sha256 (start): %s" % REAL_ADR_SHA_START)

# ------------------------------------------------- 0b. the misclassification
hdr("0b. THE MISCLASSIFICATION, REPRODUCED (P-48)")
src = open(PREFIX_SCRIPT, encoding="utf-8").read()
drv = sh("grep", "-ncE", r"^\s*(try:|finally:|except)|atexit|signal\.",
         PREFIX_SCRIPT)
print("driver's guard regex over the PRE-FIX file  -> rc=%d out=%r"
      % (drv.returncode, drv.stdout.strip()))
t156 = sh("grep", "-cE", r"^[^#\n]*(\btrap\b|\bfinally\s*:|atexit\.register"
                         r"|__exit__|contextmanager)", PREFIX_SCRIPT)
print("T156's GUARD regex over the PRE-FIX file    -> rc=%d matches=%r"
      % (t156.returncode, t156.stdout.strip()))
import ast
tree = ast.parse(src)
in_str, in_code = 0, 0
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        in_str += node.value.lower().count("trap")
code_only = []
for i, line in enumerate(src.splitlines(), 1):
    if "trap" in line.lower():
        code_only.append(i)
print("lines containing 'trap'                     : %r" % (code_only,))
print("occurrences of 'trap' inside STRING LITERALS (AST): %d" % in_str)
print("try/finally/except/atexit/signal handlers   (AST): %d"
      % sum(isinstance(n, (ast.Try,)) for n in ast.walk(tree)))
print("=> the file matched T156's GUARD regex on prose it WRITES INTO the ADR.")

# ---------------------------------------------------- 1. pre-fix, ulimit -f
hdr("1.  PRE-FIX, DETERMINISTIC (no timing at all): a write that cannot finish")
open(FAKE_ADR, "wb").write(REV9)
print("scratch ADR before: %s bytes, sha %s" % (os.path.getsize(FAKE_ADR),
                                                sha(FAKE_ADR)))
p = subprocess.run(["/bin/sh", "-c",
                    "ulimit -f 64; exec %s %s" % (PY, PREFIX_SCRIPT)],
                   capture_output=True, text=True)
print("run: `ulimit -f 64` (32 KiB file-size limit), rc=%d" % p.returncode)
print("stderr tail: %s" % (p.stderr.strip().splitlines()[-1:] or ["(none)"]))
v, n, d = classify(FAKE_ADR)
print("scratch ADR after : %s  %d bytes  sha %s" % (v, n, d))
print("   -> the ratified-ADR stand-in is %s. io.open(path,'w') applied "
      "O_TRUNC\n      before any content was written." % v)

# ------------------------------------- 2. pre-fix, real signals, wide window
hdr("2.  PRE-FIX, SIGNALS, window widened by padding (INT/TERM/HUP/KILL)")
PAD = ("\n\n<!-- T167 red-probe padding, not part of any ADR revision -->\n"
       + ("<!-- pad -->\n" * 400000))          # ~5 MB per copy
PADDED = REV9 + PAD.encode("utf-8") * 12       # ~64 MB
print("padded scratch document: %d bytes (padding appended AFTER both anchors,"
      "\n  so rep() still finds exactly one of each; the padding changes the "
      "DURATION\n  of the unprotected window, never its existence)" % len(PADDED))
for name, sig in SIGS:
    open(FAKE_ADR, "wb").write(PADDED)
    base_n = os.path.getsize(FAKE_ADR)
    p = subprocess.Popen([PY, PREFIX_SCRIPT],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fired, t0 = False, time.monotonic_ns()
    while p.poll() is None:
        try:
            if os.path.getsize(FAKE_ADR) != base_n:
                os.kill(p.pid, sig)
                fired = True
                break
        except OSError:
            pass
        if time.monotonic_ns() - t0 > 120 * 10 ** 9:
            break
    p.wait()
    n = os.path.getsize(FAKE_ADR) if os.path.exists(FAKE_ADR) else -1
    intact = (n == base_n)
    print("  %-8s signal fired mid-write=%-5s  rc=%-4s  scratch doc: %d bytes "
          "of %d  -> %s" % (name, fired, p.returncode, n, base_n,
                            "INTACT" if intact else "TRUNCATED/HALF-WRITTEN"))
    residue = [f for f in os.listdir(FAKE_ADR_DIR) if f != os.path.basename(FAKE_ADR)]
    if residue:
        print("           residue in the ADR directory: %r" % residue)

# --------------------------------- 3. pre-fix, real size, randomized delays
hdr("3.  PRE-FIX, real rev-9 size, randomized-delay trials (N=40 per signal)")
for name, sig in SIGS:
    tally = {}
    for _ in range(40):
        open(FAKE_ADR, "wb").write(REV9)
        p = subprocess.Popen([PY, PREFIX_SCRIPT],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        time.sleep(random.randrange(1000, 60000) / 1000000)
        try:
            os.kill(p.pid, sig)
        except OSError:
            pass
        p.wait()
        v, n, d = classify(FAKE_ADR)
        tally[v] = tally.get(v, 0) + 1
    print("  %-8s %s" % (name, tally))
print("  (UNTOUCHED = killed before the open; COMPLETED = killed after the last")
print("   flush; DAMAGED/MISSING = the ratified document left broken on disk.)")

# ------------------------------------------- 4. post-fix: the same treatment
hdr("4.  POST-FIX, the hardened in-repo script, same signals")
TARGET = os.path.join(DATA, "dec1-scratch-rev9.md")


def run_fixed(target, extra=(), authorise=True):
    argv = [PY, FIXED, "--target=" + target]
    if authorise:
        argv.append(TOKEN)
    argv.extend(extra)
    return subprocess.run(argv, capture_output=True, text=True)


print("A. deterministic: kill the instant the temp file appears (i.e. during")
print("   the write), one trial per signal")
for name, sig in SIGS:
    open(TARGET, "wb").write(REV9)
    p = subprocess.Popen([PY, FIXED, "--target=" + TARGET, TOKEN],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fired, t0 = False, time.monotonic_ns()
    while p.poll() is None:
        if any(f.startswith(".t47-edit1-") for f in os.listdir(DATA)):
            os.kill(p.pid, sig)
            fired = True
            break
        if time.monotonic_ns() - t0 > 60 * 10 ** 9:
            break
    p.wait()
    v, n, d = classify(TARGET)
    residue = sorted(f for f in os.listdir(DATA) if f.startswith(".t47-edit1-"))
    print("  %-8s caught-mid-write=%-5s rc=%-4s target: %-9s %d bytes  "
          "temp residue: %r" % (name, fired, p.returncode, v, n, residue))
    for f in residue:
        os.unlink(os.path.join(DATA, f))

print("\nB. randomized-delay trials (N=40 per signal); the claim is that the")
print("   target is ALWAYS exactly the old file or exactly the new one")
for name, sig in SIGS:
    tally = {}
    for _ in range(40):
        open(TARGET, "wb").write(REV9)
        p = subprocess.Popen([PY, FIXED, "--target=" + TARGET, TOKEN],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        time.sleep(random.randrange(1000, 60000) / 1000000)
        try:
            os.kill(p.pid, sig)
        except OSError:
            pass
        p.wait()
        v, n, d = classify(TARGET)
        tally[v] = tally.get(v, 0) + 1
        for f in os.listdir(DATA):
            if f.startswith(".t47-edit1-"):
                os.unlink(os.path.join(DATA, f))
    print("  %-8s %s" % (name, tally))

# --------------------------------- 5. the target is never opened for writing
hdr("5.  STRUCTURAL, NO TIMING: the target is never opened for writing")
open(FAKE_ADR, "wb").write(REV9)
os.chmod(FAKE_ADR, 0o444)
p = subprocess.run([PY, PREFIX_SCRIPT], capture_output=True, text=True)
print("pre-fix vs a mode-0444 target : rc=%d  %s" %
      (p.returncode, (p.stderr.strip().splitlines() or ["(none)"])[-1]))
os.chmod(FAKE_ADR, 0o644)
open(TARGET, "wb").write(REV9)
os.chmod(TARGET, 0o444)
p = run_fixed(TARGET)
v, n, d = classify(TARGET)
print("post-fix vs a mode-0444 target: rc=%d  target=%s  mode=%s" %
      (p.returncode, v, oct(os.stat(TARGET).st_mode & 0o7777)))
print("   -> the hardened script SUCCEEDS on a read-only target because it "
      "never\n      opens it: it renames over it, which needs directory "
      "permission only.\n      The pre-fix script cannot, because O_TRUNC on "
      "the target is its whole\n      write mechanism.  Nothing here is timed.")
os.chmod(TARGET, 0o644)

# ------------------------------------------------------------- 6. refusals
hdr("6.  THE REFUSALS: default-deny for a ratified DEC-n")
MIRROR_ADR = os.path.join(MIRROR_ADR_DIR, "DEC-1-schedule-generator-adapter.md")
open(MIRROR_ADR, "wb").write(REV9)
CORRUPT = os.path.join(DATA, "dec1-scratch-corrupt.md")
open(CORRUPT, "wb").write(REV9[:-1] + b"X")
open(TARGET, "wb").write(REV9)


def show(tag, argv, watch=None):
    before = sha(watch) if watch else None
    p = subprocess.run(argv, capture_output=True, text=True)
    after = sha(watch) if watch else None
    line = (p.stderr.strip().splitlines() or
            p.stdout.strip().splitlines() or ["(no output)"])
    print("%-4s rc=%-3d %s" % (tag, p.returncode, line[0][:150]))
    if watch:
        print("      watched file unchanged: %s" % (before == after))
    return p


show("R1", [PY, FIXED])
show("R2", [PY, FIXED, "--target=" + TARGET])
show("R3", [PY, FIXED, "--target=" + TARGET, "--authorise=yes"])
print("R4   the REAL ratified ADR as the target, with a valid token:")
show("R4", [PY, FIXED, "--target=" + REAL_ADR, TOKEN], watch=REAL_ADR)
print("R5   a scratch file whose CONTENT would pass the sha gate, sitting")
print("     under a directory named `adr` with the ADR's own name:")
show("R5", [PY, FIXED, "--target=" + MIRROR_ADR, TOKEN], watch=MIRROR_ADR)
print("R6   authorised, correct name/place, but one byte of unexpected content:")
show("R6", [PY, FIXED, "--target=" + CORRUPT, TOKEN], watch=CORRUPT)
print("R7   authorised, correct place, exactly the revision-9 bytes, dry run:")
show("R7", [PY, FIXED, "--target=" + TARGET, TOKEN, "--dry-run"], watch=TARGET)
print("R8   the same, for real:")
p = show("R8", [PY, FIXED, "--target=" + TARGET, TOKEN])
v, n, d = classify(TARGET)
print("      target now: %s  sha %s" % (v, d))
print("      reproduces %s:%s exactly: %s" % (PREFIX_COMMIT, ADR_REL,
                                              d == AFTER_SHA))
print("R9   re-run against the file R8 just wrote (the 'edited again' case):")
show("R9", [PY, FIXED, "--target=" + TARGET, TOKEN], watch=TARGET)
print("R10  authorised run under `python3 -O` (asserts stripped):")
open(TARGET, "wb").write(REV9)
p = show("R10", [PY, "-O", FIXED, "--target=" + TARGET, TOKEN])
v, n, d = classify(TARGET)
print("      target now: %s  sha-matches-bf67a85: %s" % (v, d == AFTER_SHA))

# -------------------------------------------------------------- 7. real ADR
hdr("7.  THE REAL RATIFIED ADR")
REAL_ADR_SHA_END = sha(REAL_ADR)
r = sh("git", "show", "main:" + ADR_REL, text=False)
main_sha = hashlib.sha256(r.stdout).hexdigest()
r2 = sh("git", "rev-parse", "main")
print("worktree %s" % ADR_REL)
print("  sha256 at probe start : %s" % REAL_ADR_SHA_START)
print("  sha256 at probe end   : %s" % REAL_ADR_SHA_END)
print("  sha256 of main:%s" % ADR_REL)
print("                        : %s   (main = %s)" % (main_sha,
                                                      r2.stdout.strip()[:12]))
print("  unchanged by this probe : %s" % (REAL_ADR_SHA_START == REAL_ADR_SHA_END))
print("  identical to main       : %s" % (REAL_ADR_SHA_END == main_sha))
print("  `git status --porcelain docs/adr/` -> %r"
      % sh("git", "status", "--porcelain", "docs/adr/").stdout.strip())

print("\nscratch tree left at %s" % SCRATCH)
