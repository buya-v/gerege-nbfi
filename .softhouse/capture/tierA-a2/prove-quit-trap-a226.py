#!/usr/bin/env python3
"""T216 -- drive prove-a2-26-guards-red.sh's missing-QUIT trap RED, then GREEN.

Same defect family as prove-quit-trap-cap.py (see that file's docstring for the full
bash-signal background): pre-fix, `trap 'rm -rf "$TMP"' EXIT HUP INT TERM` (line 23)
had no QUIT, so an untrapped SIGQUIT mid-run leaked the `mktemp -d a226prove.XXXXXX`
scratch dir instead of cleaning it up. Post-fix the same trap (now line 25, after two
comment lines) carries QUIT.

WHY A TRUNCATED COPY, NOT THE REAL SCRIPT
------------------------------------------
The real script's body (after the trap line) runs G1/G2/G3 -- including a REAL request
against the pinned reference oracle and a transient edit to a committed req/ file that
it restores itself.  Driving a real SIGQUIT into that body to test a *trap line* would
risk leaving req/a2-26-admit-p46.json mid-mutation if the interruption lands badly, for
a claim that has nothing to do with G1/G2/G3's own logic.  So this prover extracts the
REAL preamble VERBATIM (lines 1 through the trap statement, read from the actual file
on disk -- never retyped) and appends only `sleep` + `exit 0`.  That reproduces the
exact trap line under test with no risk to committed evidence, and no oracle needed.

Run:
  python3 prove-quit-trap-a226.py --pre    # pinned pre-fix blob; expect RED (leak)
  python3 prove-quit-trap-a226.py --live   # current on-disk file; diagnostic

Exit 0 if --pre reproduces the leak. --live is diagnostic only.
"""
import hashlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = "prove-a2-26-guards-red.sh"
PRE_BLOB = "69d6b13a567e46af324d547e1546364d84ad8613"
PRE_TRAP_LINE_NO = 23   # pre-fix blob: `trap 'rm -rf "$TMP"' EXIT HUP INT TERM` -- verified by `nl -ba`
LIVE_TRAP_LINE_NO = 25  # post-fix (2 comment lines added): `... EXIT HUP INT TERM QUIT` -- verified by `nl -ba`
TMP_PREFIX = "a226prove."


def read_blob(blob):
    out = subprocess.run(["git", "cat-file", "-p", blob], cwd=DIR,
                          capture_output=True, check=True)
    return out.stdout


def truncated_preamble(full_bytes, trap_line_no):
    lines = full_bytes.decode("utf-8").splitlines(keepends=True)
    if trap_line_no > len(lines) or "trap " not in lines[trap_line_no - 1]:
        sys.exit("REFUSING: line %d of %s is not the trap line any more "
                  "(got: %r) -- update the *_TRAP_LINE_NO constant, do not guess"
                  % (trap_line_no, TARGET, lines[trap_line_no - 1] if trap_line_no <= len(lines) else None))
    preamble = "".join(lines[:trap_line_no])
    return preamble + "\nsleep 1.2\nexit 0\n"


def run_case(full_bytes, label, trap_line_no):
    script = truncated_preamble(full_bytes, trap_line_no)
    sb = tempfile.mkdtemp(prefix="t216-a226-sandbox.")
    tmproot = tempfile.mkdtemp(prefix="t216-a226-tmproot.")
    path = os.path.join(sb, TARGET)
    with open(path, "w") as f:
        f.write(script)
    os.chmod(path, 0o755)
    env = dict(os.environ)
    env["TMPDIR"] = tmproot
    try:
        proc = subprocess.Popen(["sh", path], cwd=sb, env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.4)
        os.kill(proc.pid, signal.SIGQUIT)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
        leaked = [n for n in os.listdir(tmproot) if n.startswith(TMP_PREFIX)]
        verdict = "RED (LEAKED)" if leaked else "GREEN (CLEANED)"
        print("--- %-45s exit=%s leaked-dirs=%s => %s"
              % (label, proc.returncode, leaked, verdict))
        return bool(leaked)
    finally:
        shutil.rmtree(sb, ignore_errors=True)
        shutil.rmtree(tmproot, ignore_errors=True)


def main():
    args = sys.argv[1:] or ["--pre", "--live"]
    ok = True
    if "--pre" in args:
        print("=== PRE-FIX (pinned git blob %s) -- expect RED ===" % PRE_BLOB[:12])
        leaked = run_case(read_blob(PRE_BLOB),
                           "PRE-FIX preamble (verbatim lines 1-%d)" % PRE_TRAP_LINE_NO,
                           PRE_TRAP_LINE_NO)
        if not leaked:
            ok = False
            print("    UNEXPECTED: pre-fix did NOT leak")
    if "--live" in args:
        print("=== LIVE (current on-disk file) -- diagnostic ===")
        with open(os.path.join(DIR, TARGET), "rb") as f:
            live = f.read()
        run_case(live, "LIVE preamble (verbatim lines 1-%d)" % LIVE_TRAP_LINE_NO,
                  LIVE_TRAP_LINE_NO)
    if "--pre" in args and not ok:
        sys.exit("RESULT: PRE-FIX DID NOT REPRODUCE THE DEFECT")
    print("RESULT: done")


if __name__ == "__main__":
    main()
