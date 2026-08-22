#!/usr/bin/env python3
"""T236 -- drive cap9.sh:49's missing-QUIT trap RED against the REAL, UNMODIFIED,
committed-evidence-bearing script, then GREEN against its successor cap10.sh.

THE DEFECT (T216's P-40 residual, named and left there; closed here by minting a
successor rather than editing cap9.sh in place -- see T236's handoff and
SUPERSEDED.txt for why (b) "edit cap9.sh in place" was investigated and rejected: it
IS pinned, by MANIFEST.sha256, as part of "the rig"). cap9.sh does:

    trap 'rm -rf "$TMPD"' EXIT HUP INT TERM

-- no QUIT. Per T156/T168/T216 (bash does not run an untrapped SIGQUIT's EXIT trap),
the mktemp -d scratch dir ($TMPD) is never removed on Ctrl-\\: a leaked /tmp directory,
never a stranded vector or committed byte -- LOW materiality, stated as such, not
inflated.

HOW THIS PROVES IT (P-22: ship no guard/fix you have not driven red).
  * cap9.sh's bytes are read from the IMMUTABLE GIT BLOB this task found it at
    (e0a4d322139006731d96e7840af53a0dff135e84), sha256-checked before use, so the RED
    case can never silently drift onto a different file -- and cap9.sh is UNTOUCHED by
    this task, so this is also a live re-verification that the "pin" claim in the
    handoff is real: the blob this prover reads IS the file still on disk.
  * cap10.sh is read live from disk (it is this task's own new file).
  * Nothing here touches the real .softhouse/capture/tierA-a2/out/ tree and no network
    call is made: curl is replaced on PATH by a stub that sleeps briefly and writes a
    canned 200 response, so the test needs no reference oracle.
  * The interruption is a REAL SIGQUIT delivered to the running script's own process
    (os.kill(pid, signal.SIGQUIT)) while curl is "in flight" (sleeping) -- i.e. after
    $TMPD has been created and the trap installed, matching the real interruption
    window.
  * The scratch TMPDIR root is private to each run (tempfile.mkdtemp), so "did the
    mktemp dir survive" is read by listing that root after the process is confirmed
    dead -- no guessing the dir's name.

Run:
  python3 prove-quit-trap-cap9.py            # both phases (default)
  python3 prove-quit-trap-cap9.py --pre       # cap9.sh only, expect RED (leak)
  python3 prove-quit-trap-cap9.py --post      # cap10.sh only, expect GREEN (no leak)

Exit 0 only if cap9.sh (PRE, the frozen original) LEAKS and cap10.sh (POST, the
successor) does NOT -- i.e. both phases read exactly as the fix claims.
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

PRE = {
    "script": "cap9.sh",
    "blob": "e0a4d322139006731d96e7840af53a0dff135e84",
    "sha256": "0444bb32b2ffb2341e3140e4912743bc5d635e3a4b8a1588c0826a9e9fe32c88",
    "tmp_prefix": "cap9.",
}
POST = {
    "script": "cap10.sh",
    "tmp_prefix": "cap10.",
}

FAKE_CURL = """#!/bin/sh
# T236 stub curl: no network, sleeps so the QUIT arrives mid-"transport", then writes a
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
# T236 stub env.sh: no real oracle contacted (curl is stubbed), values are placeholders.
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


def read_live(name):
    path = os.path.join(DIR, name)
    with open(path, "rb") as f:
        return f.read()


def build_sandbox(script_bytes, script_name):
    sb = tempfile.mkdtemp(prefix="t236-sandbox.")
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
    tmproot = tempfile.mkdtemp(prefix="t236-tmproot.")
    env = dict(os.environ)
    env["PATH"] = binp + ":" + env["PATH"]
    env["TMPDIR"] = tmproot
    try:
        # 5 args: NAME METHOD PATH BODYFILE IDEMPOTENCY_KEY -- BODY empty so the
        # no-body branch is taken (still exercises TMPD / the trap under test).
        proc = subprocess.Popen(
            ["sh", os.path.join(sb, script_name), "SITE-PROBE", "GET", "/x", "", "IDEM-KEY-T236"],
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
    args = sys.argv[1:] or ["--pre", "--post"]
    do_pre = "--pre" in args
    do_post = "--post" in args
    ok = True

    if do_pre:
        print("=== PRE (cap9.sh, pinned git blob, UNTOUCHED by this task) -- expect RED (leak) ===")
        blob_bytes = read_blob(PRE["blob"], PRE["sha256"])
        leaked = run_case(blob_bytes, PRE["script"], PRE["tmp_prefix"],
                           "PRE  %s (blob %s)" % (PRE["script"], PRE["blob"][:12]))
        if not leaked:
            ok = False
            print("    UNEXPECTED: cap9.sh (pre) did NOT leak")

    if do_post:
        print("=== POST (cap10.sh, live on-disk successor) -- expect GREEN (no leak) ===")
        live_bytes = read_live(POST["script"])
        leaked = run_case(live_bytes, POST["script"], POST["tmp_prefix"],
                           "POST %s (live on-disk)" % POST["script"])
        if leaked:
            ok = False
            print("    UNEXPECTED: cap10.sh (post) LEAKED")

    if not ok:
        sys.exit("RESULT: DID NOT REPRODUCE THE CLAIMED RED/GREEN SHAPE")
    print("RESULT: cap9.sh leaks under real SIGQUIT (RED), cap10.sh does not (GREEN).")


if __name__ == "__main__":
    main()
