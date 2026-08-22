#!/usr/bin/env python3
"""T216 -- drive cap.sh's / cap8.sh's missing-QUIT trap RED against the REAL pre-fix
bytes, then GREEN against the fixed script.

THE DEFECT (T168's P-40 skip, closed here). Both scripts do:

    trap 'rm -rf "$TMPD"' EXIT HUP INT TERM

-- no QUIT.  Per T156/T168 (`.softhouse/capture/pathb/t149/prove-exit-trap.py`), bash
does not run a script's EXIT trap on receipt of an UNTRAPPED SIGQUIT (unlike
SIGPIPE/SIGUSR1/SIGALRM); the process dies by the signal's default disposition instead.
Here that means the `mktemp -d` scratch dir ($TMPD) is never removed: a leaked /tmp
directory, not a stranded vector -- this is the LOW-materiality half of the same
concept family T156/T168 already fixed at higher stakes in prove-redgreen.sh.

HOW THIS PROVES IT (P-22: ship no guard you have not driven red).
  * The PRE-FIX bytes are read from an IMMUTABLE GIT BLOB by object sha (not a moving
    ref); the blob's sha256 is checked before use and this prover REFUSES on mismatch.
  * Nothing here touches the real .softhouse/capture/tierA-a2/out/ tree, and no network
    call is made: curl is replaced on PATH by a stub that sleeps briefly and writes a
    canned 200 response, so the test needs no reference oracle.
  * The interruption is a REAL SIGQUIT delivered to the running script's own process
    (os.kill(pid, SIGQUIT)) while curl is "in flight" (sleeping) -- i.e. after $TMPD
    has been created and the trap installed, matching the real interruption window.
  * The scratch TMPDIR root is private to each run (tempfile.mkdtemp), so "did the
    mktemp dir survive" is read by listing that root after the process is confirmed
    dead -- no guessing the dir's name.

Run:
  python3 prove-quit-trap-cap.py --pre    # pinned pre-fix blobs; expect RED (leak) x2
  python3 prove-quit-trap-cap.py --live   # current on-disk cap.sh/cap8.sh; report
                                           #   RED or GREEN per site, no assertion
  python3 prove-quit-trap-cap.py --pre --live   # both (default if no flag given)

Exit 0 if every requested phase completed and read as expected for --pre (RED both);
--live is diagnostic only (reports, does not require GREEN, since it may be invoked
before the fix is applied).
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

SITES = [
    {
        "script": "cap.sh",
        "blob": "22baf85faa50c0531841903c135e32d184f3735e",
        "sha256": "67640ea31eb16c0ba0f929cfd93459f4ced687be3dda0f10db00c1b2d31f542a",
        "tmp_prefix": "cap.",
    },
    {
        "script": "cap8.sh",
        "blob": "62b8406081a1ca5f59adb39a58a15124a27172ff",
        "sha256": "f4c05297c077476a251cd82d1defb1ea3f68c881d6d8a567a05e86472be007fc",
        "tmp_prefix": "cap8.",
    },
]

FAKE_CURL = """#!/bin/sh
# T216 stub curl: no network, sleeps so the QUIT arrives mid-"transport", then writes a
# canned 200 response to whatever -o file was passed.
sleep 1.2
outfile=""
prev=""
for arg in "$@"; do
  if [ "$prev" = "-o" ]; then outfile="$arg"; fi
  prev="$arg"
done
if [ -n "$outfile" ]; then printf '{"ok":true}' > "$outfile"; fi
printf '200'
exit 0
"""

FAKE_ENV = """#!/bin/sh
# T216 stub env.sh: no real oracle contacted (curl is stubbed), values are placeholders.
B=https://127.0.0.1:1/fineract-provider/api/v1
A='Authorization: Basic AAAA'
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
export B A T CT
"""


def read_blob(blob, expect_sha256):
    out = subprocess.run(["git", "cat-file", "-p", blob], cwd=DIR,
                          capture_output=True, check=True)
    got = hashlib.sha256(out.stdout).hexdigest()
    if got != expect_sha256:
        sys.exit("REFUSING: blob %s sha256 mismatch: expected %s got %s"
                  % (blob, expect_sha256, got))
    return out.stdout


def build_sandbox(script_bytes, script_name):
    sb = tempfile.mkdtemp(prefix="t216-sandbox.")
    with open(os.path.join(sb, script_name), "wb") as f:
        f.write(script_bytes)
    os.chmod(os.path.join(sb, script_name), 0o755)
    with open(os.path.join(sb, "env.sh"), "w") as f:
        f.write(FAKE_ENV)
    os.makedirs(os.path.join(sb, "out"), exist_ok=True)
    binp = os.path.join(sb, "bin")
    os.makedirs(binp, exist_ok=True)
    with open(os.path.join(binp, "curl"), "w") as f:
        f.write(FAKE_CURL)
    os.chmod(os.path.join(binp, "curl"), 0o755)
    return sb, binp


def run_case(script_bytes, script_name, tmp_prefix, label):
    sb, binp = build_sandbox(script_bytes, script_name)
    tmproot = tempfile.mkdtemp(prefix="t216-tmproot.")
    env = dict(os.environ)
    env["PATH"] = binp + ":" + env["PATH"]
    env["TMPDIR"] = tmproot
    try:
        proc = subprocess.Popen(
            ["sh", os.path.join(sb, script_name), "SITE-PROBE", "GET", "/x"],
            cwd=sb, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        time.sleep(0.4)  # past mktemp + trap install, into the fake curl's sleep
        os.kill(proc.pid, signal.SIGQUIT)
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
        rc = proc.returncode
        leaked = [n for n in os.listdir(tmproot) if n.startswith(tmp_prefix)]
        verdict = "RED (LEAKED)" if leaked else "GREEN (CLEANED)"
        print("--- %-45s exit=%s leaked-dirs=%s => %s"
              % (label, rc, leaked, verdict))
        return bool(leaked)
    finally:
        shutil.rmtree(sb, ignore_errors=True)
        shutil.rmtree(tmproot, ignore_errors=True)


def main():
    args = sys.argv[1:] or ["--pre", "--live"]
    do_pre = "--pre" in args
    do_live = "--live" in args
    all_ok = True

    if do_pre:
        print("=== PRE-FIX (pinned git blobs) -- expect RED (leak) on both ===")
        for s in SITES:
            blob_bytes = read_blob(s["blob"], s["sha256"])
            leaked = run_case(blob_bytes, s["script"], s["tmp_prefix"],
                               "PRE-FIX  %s (blob %s)" % (s["script"], s["blob"][:12]))
            if not leaked:
                all_ok = False
                print("    UNEXPECTED: pre-fix %s did NOT leak" % s["script"])

    if do_live:
        print("=== LIVE (current on-disk script) -- diagnostic, no assertion ===")
        for s in SITES:
            path = os.path.join(DIR, s["script"])
            with open(path, "rb") as f:
                live_bytes = f.read()
            run_case(live_bytes, s["script"], s["tmp_prefix"],
                      "LIVE     %s (%s)" % (s["script"], path))

    if do_pre and not all_ok:
        sys.exit("RESULT: PRE-FIX PHASE DID NOT REPRODUCE THE DEFECT ON ALL SITES")
    print("RESULT: %s%s" % ("pre-fix reproduced on all sites" if do_pre else "",
                             " / live phase printed above (read verdicts by eye)" if do_live else ""))


if __name__ == "__main__":
    main()
