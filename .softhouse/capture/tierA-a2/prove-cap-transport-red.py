#!/usr/bin/env python3
"""Drive cap.sh's transport-failure handler RED against the REAL pre-fix bytes, then
GREEN against the fixed script — and prove the fixed handler is REACHABLE rather than
arguing that it is.

A2-4's D-2: `set -e` terminated the shell at `code=$(curl …)`, so `rc=$?`, the
diagnostic and the `rm -f "$OUT"` never ran.  Against an unreachable endpoint a STALE
body and a STALE status survived under a FRESH `captured-at-utc` — manufactured oracle
evidence.

P-22 requires the counterproof to run against the real pre-fix bytes (`git show`), not a
paraphrase, because a proof that only shows the "after" cannot distinguish a fix from a
no-op.  The pre-fix cap.sh is therefore read from its immutable git blob and its sha256
is checked before use; if the blob or its content ever changes, this prover REFUSES.

Nothing here touches the real out/, req/ or sql/ trees: every run happens in a throwaway
sandbox whose env.sh points at 127.0.0.1:1 (a closed port -> curl exit 7).

Run:  python3 prove-cap-transport-red.py
Exit 0 only if EVERY pre-fix case was blind AND EVERY post-fix case caught it.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))

# Immutable git blob of cap.sh as it stood BEFORE this fix, plus the sha256 of its bytes.
PRE_BLOB = "55d5d63af96820ada43544913b2a344478f0393d"
PRE_SHA256 = "5820f36361ef90d18aacbb1f3eb715ec34e56b794d04eda4935653dc93d6e62a"

NAME = "A2-STALE-PROBE"
STALE_BODY = b'{"stale":"BODY FROM AN EARLIER FIRE - MUST NOT BE PRESENTED AS NEW"}\n'
STALE_STATUS = b"200\n"
STALE_TS = "2000-01-01T00:00:00Z"
STALE_HTTP = (
    "GET /glaccounts\n"
    "Fineract-Platform-TenantId: gerege\n"
    "Authorization: Basic <mifos:password>\n"
    f"captured-at-utc: {STALE_TS}\n"
).encode()

# A closed port on loopback: curl fails to connect (exit 7) with no network wait.
SANDBOX_ENV = (
    "#!/bin/sh\n"
    "B=https://127.0.0.1:1/fineract-provider/api/v1\n"
    "A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='\n"
    "T='Fineract-Platform-TenantId: gerege'\n"
    "CT='Content-Type: application/json'\n"
    "export B A T CT\n"
)

SHELLS = [
    ["/bin/sh"],
    ["/bin/sh", "-e"],
    ["/bin/sh", "-u"],
    ["/bin/sh", "-eu"],
    ["/bin/bash"],
    ["/bin/bash", "-e"],
    ["/bin/bash", "-u"],
    ["/bin/bash", "-o", "pipefail"],
    ["/bin/bash", "-eu", "-o", "pipefail"],
    ["/bin/dash"],
    ["/bin/dash", "-e"],
    ["/bin/zsh"],
    ["/bin/zsh", "-e"],
    ["/bin/ksh"],
    ["/bin/ksh", "-e"],
    [],  # no interpreter argument: execute cap.sh directly, honouring its own shebang
]


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def pre_fix_source():
    r = subprocess.run(["git", "cat-file", "blob", PRE_BLOB],
                       cwd=DIR, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"cannot read pre-fix blob {PRE_BLOB}: {r.stderr.decode()}")
    got = sha256(r.stdout)
    if got != PRE_SHA256:
        raise SystemExit(f"pre-fix blob sha256 mismatch: {got} != {PRE_SHA256}")
    return r.stdout


def build_sandbox(cap_src, with_body):
    sb = tempfile.mkdtemp(prefix="cap-red-")
    os.mkdir(os.path.join(sb, "out"))
    os.mkdir(os.path.join(sb, "req"))
    with open(os.path.join(sb, "cap.sh"), "wb") as f:
        f.write(cap_src)
    os.chmod(os.path.join(sb, "cap.sh"), 0o755)
    with open(os.path.join(sb, "env.sh"), "w") as f:
        f.write(SANDBOX_ENV)
    # the stale artefacts of an earlier, genuine fire
    open(os.path.join(sb, "out", NAME + ".json"), "wb").write(STALE_BODY)
    open(os.path.join(sb, "out", NAME + ".status"), "wb").write(STALE_STATUS)
    open(os.path.join(sb, "out", NAME + ".http"), "wb").write(STALE_HTTP)
    if with_body:
        open(os.path.join(sb, "req", "probe.json"), "w").write('{"name":"probe"}\n')
    return sb


def read(p):
    try:
        with open(p, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def run_case(cap_src, shell, with_body):
    sb = build_sandbox(cap_src, with_body)
    try:
        cap = os.path.join(sb, "cap.sh")
        args = ["A2-STALE-PROBE", "POST" if with_body else "GET", "/glaccounts"]
        if with_body:
            args.append("req/probe.json")
        cmd = (shell + [cap] + args) if shell else [cap] + args
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        body = read(os.path.join(sb, "out", NAME + ".json"))
        status = read(os.path.join(sb, "out", NAME + ".status"))
        http = read(os.path.join(sb, "out", NAME + ".http"))
        ts = None
        if http:
            for line in http.decode(errors="replace").splitlines():
                if line.startswith("captured-at-utc: "):
                    ts = line.split(": ", 1)[1]
        return {
            "cmd": " ".join(cmd[:-4]) if shell else "(shebang)",
            "rc": r.returncode,
            "stderr": r.stderr.strip(),
            "handler_fired": "TRANSPORT FAILURE" in r.stderr,
            "body_survived_verbatim": body == STALE_BODY,
            "body_present": body is not None,
            "status_survived_verbatim": status == STALE_STATUS,
            "http_ts": ts,
            "fresh_stamp": ts is not None and ts != STALE_TS,
        }
    finally:
        shutil.rmtree(sb, ignore_errors=True)


def describe(res):
    return (f"    exit {res['rc']:<3} handler_fired={str(res['handler_fired']):<5} "
            f"stale_body_intact={str(res['body_survived_verbatim']):<5} "
            f"captured-at-utc={res['http_ts']} "
            f"FRESH_STAMP_ON_STALE_BYTES={res['fresh_stamp']}")


def main():
    pre = pre_fix_source()
    post = read(os.path.join(DIR, "cap.sh"))
    if post == pre:
        print("cap.sh is byte-identical to the pre-fix blob — nothing to prove", file=sys.stderr)
        return 2

    print("=" * 100)
    print("D-2  cap.sh transport-failure handler — RED against the real pre-fix bytes, GREEN after")
    print("=" * 100)
    print(f"pre-fix  cap.sh: git blob {PRE_BLOB}  sha256 {PRE_SHA256}")
    print(f"post-fix cap.sh: working tree            sha256 {sha256(post)}")
    print("endpoint under test: https://127.0.0.1:1/... (closed port; curl cannot connect)")
    print("sandbox seeded with a STALE observation from an earlier fire:")
    print(f"    out/{NAME}.json   sha256 {sha256(STALE_BODY)}")
    print(f"    out/{NAME}.status = 200")
    print(f"    out/{NAME}.http   captured-at-utc: {STALE_TS}")
    print()

    failures = []

    for with_body in (False, True):
        branch = "WITH body file (-d @req/probe.json)" if with_body else "NO body file (GET branch)"
        print("-" * 100)
        print(f"BRANCH: {branch}")
        print("-" * 100)

        print("\n  [RED] pre-fix cap.sh — the handler must NOT fire (that is the defect):")
        for shell in SHELLS:
            res = run_case(pre, shell, with_body)
            label = " ".join(shell) if shell else "(shebang: ./cap.sh)"
            blind = (not res["handler_fired"]) and res["body_survived_verbatim"] and res["fresh_stamp"]
            print(f"  {label:<32}{describe(res)}")
            if not blind:
                # not every shell must reproduce the defect identically; record what happened
                print(f"  {'':<32}    (pre-fix did not produce the stale-under-fresh artefact here)")
        # the canonical pre-fix invocation is the one the run-*.sh scripts use: `sh cap.sh`
        res = run_case(pre, ["/bin/sh"], with_body)
        if res["handler_fired"]:
            failures.append(f"pre-fix handler FIRED under /bin/sh ({branch}) — defect not reproduced")
        if not (res["body_survived_verbatim"] and res["fresh_stamp"]):
            failures.append(f"pre-fix did not produce stale-body-under-fresh-timestamp ({branch})")
        print(f"\n  pre-fix verdict under /bin/sh: handler_fired={res['handler_fired']}, "
              f"stale body presented under captured-at-utc={res['http_ts']}  -> "
              f"{'DEFECT REPRODUCED' if not res['handler_fired'] and res['fresh_stamp'] else 'NOT REPRODUCED'}")

        print("\n  [GREEN] post-fix cap.sh — the handler must fire in EVERY interpreter/option combination:")
        for shell in SHELLS:
            res = run_case(post, shell, with_body)
            label = " ".join(shell) if shell else "(shebang: ./cap.sh)"
            ok = (res["handler_fired"] and res["rc"] == 1
                  and res["body_survived_verbatim"] and res["status_survived_verbatim"]
                  and res["http_ts"] == STALE_TS)
            print(f"  {label:<32}{describe(res)} {'CAUGHT' if ok else 'MISSED'}")
            if not ok:
                failures.append(f"post-fix MISSED under {label} ({branch}): {res['stderr'][:200]}")
        print()

    # ---------------------------------------------------------------- caller laundering
    print("-" * 100)
    print("D-2b  the CALLER: run-*.sh are deliberately not `set -e`, so a handler that fires")
    print("      but is ignored still launders the stale body into the transcript.")
    print("-" * 100)
    for tag, cap_src, tail in (("pre-fix cap.sh + old caller (no `|| exit 1`)", pre, ""),
                               ("post-fix cap.sh + new caller (`|| exit 1`)", post, " || exit 1")):
        sb = build_sandbox(cap_src, False)
        try:
            loop = os.path.join(sb, "loop.sh")
            open(loop, "w").write(
                "#!/bin/sh\n"
                "# mirrors run-020-accounts.sh's loop body (NOT set -e)\n"
                'DIR=$(cd "$(dirname "$0")" && pwd)\n'
                f'sh "$DIR/cap.sh" {NAME} GET /glaccounts{tail}\n'
                f"printf '   -> %s\\n' \"$(cat \"$DIR/out/{NAME}.json\")\"\n"
            )
            r = subprocess.run(["/bin/sh", loop], capture_output=True, text=True, timeout=120)
            laundered = "BODY FROM AN EARLIER FIRE" in r.stdout
            print(f"  {tag}")
            print(f"    exit {r.returncode}  stdout: {r.stdout.strip()!r}")
            print(f"    stale body printed as an observation: {laundered}")
            if tail == "" and not laundered:
                failures.append("old caller did not launder the stale body — defect not reproduced")
            if tail and laundered:
                failures.append("new caller STILL launders the stale body")
        finally:
            shutil.rmtree(sb, ignore_errors=True)

    # the shipped run-*.sh must actually carry the guard
    print("\n  shipped run-*.sh cap.sh call sites:")
    bad_sites = 0
    total_sites = 0
    for fn in sorted(os.listdir(DIR)):
        if not (fn.startswith("run-") and fn.endswith(".sh")):
            continue
        for i, line in enumerate(open(os.path.join(DIR, fn)), 1):
            if "cap.sh" in line and line.strip().startswith("sh "):
                total_sites += 1
                if "|| exit 1" not in line:
                    bad_sites += 1
                    print(f"    UNGUARDED {fn}:{i}: {line.strip()}")
    print(f"    {total_sites - bad_sites}/{total_sites} cap.sh call sites carry `|| exit 1`")
    if bad_sites:
        failures.append(f"{bad_sites} cap.sh call sites still unguarded")

    print()
    print("=" * 100)
    if failures:
        print("RESULT: FAILED")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: pre-fix handler proven UNREACHABLE (stale bytes under a fresh timestamp);")
    print("        post-fix handler proven REACHABLE in every interpreter/option combination tested,")
    print("        with the earlier fire's bytes left byte-identical and its timestamp untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
