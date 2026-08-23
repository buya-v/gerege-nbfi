#!/usr/bin/env python3
"""T291 -- INDEPENDENT ENUMERATION OF EVERY WAY T286's SHIPPED RULE CAN REPORT "CLEAN".

T286 built its own 37-case matrix and said, correctly, that a corpus is not a proof and that the
next reviewer should ADD ROWS rather than re-grep the source. This is that addition: an
independently written enumeration, driven against the NEW arm's PINNED BLOB (never `HEAD:<path>`,
never the working tree), checking the invariant a caller depends on:

    exit 0 => the probe line is PRESENT and says GREEN
    exit 1 => the probe line is PRESENT and says REFUSED
    exit 2 => the probe line is ABSENT

THE EXIT-0 ROWS ARE THE ONLY ROWS THAT MATTER. Every one of them is a claim to have measured a
non-empty population and found nothing wrong. They are printed separately.

Part 2 covers what plain argv cannot reach: signal death, a closed pipe, a named pipe, an
optimised interpreter. Those are for the WRAPPER's benefit -- a caller that tests `rc -eq 1`
instead of `rc -ne 0` misreads every one of them.

NO FLOATING POINT: nothing here computes. Exit codes and counts are ints.
EXIT: 0 no invariant violation; 1 at least one violation; 2 the instrument could not run.
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parent
ROOT = CAP.parent.parent.parent
RULE_DIR = ROOT / ".softhouse/capture/t256-verdict-predicate"
REG = RULE_DIR / "boolean-key-register.json"
ACK = RULE_DIR / "acknowledged.json"
REAL = ROOT / ".softhouse/capture/t229-g8-site3/out/classify-t229.json"
NEW_BLOB = "4f844ed2409bbcde3add574a1160601f4e55b06d"
PROBE = "T259-VPA:"

rows = []
viol = []


def git(*args, check=True):
    p = subprocess.run(["git", "-C", str(ROOT)] + list(args), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError("git %s exited %d: %s" % (" ".join(args), p.returncode, p.stderr))
    return p.returncode, p.stdout


def record(name, rc, out):
    probe = ""
    for ln in (out or "").splitlines():
        if ln.startswith(PROBE):
            probe = ln
    state = probe.split()[1] if probe else ""
    ok = ((rc == 0 and probe and state == "GREEN")
          or (rc == 1 and probe and state == "REFUSED")
          or (rc == 2 and not probe))
    if not ok:
        viol.append((name, "rc=%s probePresent=%s state=%s" % (rc, bool(probe), state)))
    rows.append((name, rc, ("PRESENT/" + state) if probe else "ABSENT"))


def main():
    for p in (REG, ACK, REAL):
        if not p.exists():
            print("ERROR: required path absent: %s" % p, file=sys.stderr)
            return 2
    rc, _ = git("cat-file", "-e", NEW_BLOB + "^{blob}", check=False)
    if rc != 0:
        print("ERROR: the NEW arm blob %s is not in this object store. NOT MEASURED, and NOT "
              "reported as clean." % NEW_BLOB, file=sys.stderr)
        return 2
    scratch = Path(tempfile.mkdtemp(prefix=".scratch-t291e-", dir=str(CAP)))
    try:
        NEW = scratch / "rule.py"
        _, text = git("cat-file", "blob", NEW_BLOB)
        NEW.write_text(text)
        E = scratch / "e"
        E.mkdir()
        BASE = [sys.executable, str(NEW)]
        STD = BASE + ["--register", str(REG), "--acknowledgements", str(ACK)]

        def run(name, argv, env=None, timeout=90):
            try:
                p = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=timeout)
            except subprocess.TimeoutExpired:
                rows.append((name, "TIMEOUT", "ABSENT"))
                viol.append((name, "HUNG -- no exit code at all within %ds" % timeout))
                return
            record(name, p.returncode, p.stdout)

        def std(extra, name):
            run(name, STD + extra)

        def w(n, text, binary=False):
            p = E / n
            if binary:
                p.write_bytes(text)
            else:
                p.write_text(text)
            return p

        # -- 1. missing / unreadable -------------------------------------------------------
        std([str(E / "nope.json")], "target/missing")
        std(["--register", str(E / "nope.json"), str(REAL)], "register/missing")
        noperm = w("noperm.json", '{"cells":[]}')
        os.chmod(noperm, 0o000)
        std([str(noperm)], "target/chmod-000")
        os.chmod(noperm, 0o644)
        std([str(E)], "target/is-a-directory")
        # -- 2. empty / degenerate JSON ----------------------------------------------------
        std([str(w("empty.txt", ""))], "target/zero-bytes")
        std([str(w("ws.json", "   \n\t "))], "target/whitespace-only")
        std([str(w("null.json", "null"))], "target/json-null")
        std([str(w("arr0.json", "[]"))], "target/json-empty-array")
        std([str(w("obj0.json", "{}"))], "target/json-empty-object")
        std([str(w("int.json", "7"))], "target/json-bare-int")
        std([str(w("str.json", '"hello"'))], "target/json-bare-string")
        std([str(w("true.json", "true"))], "target/json-bare-true")
        std([str(w("bad.json", "{"))], "target/malformed-json")
        std([str(w("trail.json", '{"a":1},'))], "target/trailing-garbage")
        # -- 3. scalar / list rows ---------------------------------------------------------
        std([str(w("scal.json", '{"cells":[1,2,3]}'))], "target/list-of-scalars")
        std([str(w("lol.json", '{"cells":[[1,2],[3]]}'))], "target/list-of-lists-of-scalars")
        std([str(w("nulls.json", '{"cells":[null,null]}'))], "target/list-of-nulls")
        std([str(w("vstr.json", '{"cells":["AS PREDICTED"]}'))],
            "target/affirmative-STRING-in-list-no-dict")
        # -- 4. deep nesting / duplicate keys ----------------------------------------------
        deep = '{"cells":[],' + '"a":{' * 40 + '"verdict":"AS PREDICTED"' + "}" * 40 + "}"
        std([str(w("deepmap.json", deep))], "target/verdict-40-deep-via-MAPPING")
        deepl = '{"cells":[],' + '"a":[{' * 40 + '"verdict":"AS PREDICTED"' + "}]" * 40 + "}"
        std([str(w("deeplist.json", deepl))], "target/verdict-40-deep-via-LISTS")
        std([str(w("dupv.json", '{"cells":[{"verdict":"REFUTED","verdict":"AS PREDICTED",'
                                '"P9_x":false}]}'))], "target/duplicate-VERDICT-keys")
        std([str(w("dupp.json", '{"cells":[{"P9_x":false,"P9_x":true,'
                                '"verdict":"AS PREDICTED"}]}'))],
            "target/duplicate-PREDICATE-keys-false-then-true")
        # -- 5. encoding -------------------------------------------------------------------
        std([str(w("badutf8.json", b'{"cells":[{"verdict":"AS PREDICTED\xff"}]}', True))],
            "target/invalid-utf8-bytes")
        std([str(w("bom.json",
                   b'\xef\xbb\xbf{"cells":[{"verdict":"AS PREDICTED","P9_x":false}]}', True))],
            "target/utf8-BOM")
        env_c = dict(os.environ)
        env_c.update({"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"})
        run("target/real-evidence-under-LC_ALL=C", STD + [str(REAL)], env=env_c)
        cyr = w("cyr.json",
                '{"cells":[{"verdict":"AS PREDICTED","P9_x":false,"ovog":"Өвөг"}]}')
        run("target/CYRILLIC-payload-under-LC_ALL=C", STD + [str(cyr)], env=env_c)
        # -- 6. float ingress --------------------------------------------------------------
        std([str(w("nan.json", '{"cells":[{"P9_x":true,"verdict":"AS PREDICTED","v":NaN,'
                               '"r":Infinity}]}'))],
            "target/JSON-NaN-and-Infinity-literals-in-a-GREEN-run")
        std([str(w("e400.json", '{"cells":[{"P9_x":true,"verdict":"AS PREDICTED","v":1e400}]}'))],
            "target/JSON-1e400")
        # -- 7. symlinks -------------------------------------------------------------------
        for n, tgt in (("sl-devnull.json", "/dev/null"), ("sl-dir.json", str(E)),
                       ("sl-broken.json", str(E / "does-not-exist"))):
            p = E / n
            os.symlink(tgt, p)
            std([str(p)], "target/symlink-to-" + Path(tgt).name)
        loop = E / "sl-loop.json"
        os.symlink(str(loop), loop)
        std([str(loop)], "target/symlink-loop")
        # -- 8. recursion ------------------------------------------------------------------
        std([str(w("bomb.json", "[" * 3000 + "]" * 3000))], "target/recursion-bomb-3000")
        std([str(w("bomb2.json", '{"cells":[' + '{"a":[' * 2000 + "]}" * 2000 + "]}"))],
            "target/deep-dict-bomb-2000")
        # -- 9. argv / SystemExit ----------------------------------------------------------
        std([], "argv/no-targets-uses-built-in-default")
        std([str(REAL), str(REAL)], "argv/same-file-twice")
        for a, n in ((["--help"], "argv/--help"), (["-h"], "argv/-h"),
                     (["--nope"], "argv/unknown-flag"),
                     (["--register"], "argv/register-without-value"),
                     ([""], "argv/empty-string-target"), (["--"], "argv/dash-dash-only"),
                     (["-"], "argv/target-named-dash")):
            run(n, BASE + a)
        # -- 10. register / acknowledgement mutations ---------------------------------------
        for n, body, lbl in (("reg-arr.json", "[]", "register/json-array"),
                             ("reg-str.json", '"x"', "register/json-string"),
                             ("reg-null.json", "null", "register/json-null"),
                             ("reg-nopat.json", "{}", "register/no-autoPredicatePattern")):
            std(["--register", str(w(n, body)), str(REAL)], lbl)
        for n, body, lbl in (("ack-arr.json", "[]", "ack/json-array"),
                             ("ack-null.json", "null", "ack/json-null"),
                             ("ack-str.json", '"x"', "ack/json-string"),
                             ("ack-nofile.json", '{"acknowledgements":[{"sha256":"x"}]}',
                              "ack/block-without-file-key"),
                             ("ack-badsha.json",
                              '{"acknowledgements":[{"file":"x","sha256":"y"}]}',
                              "ack/block-file-mismatch")):
            std(["--acknowledgements", str(w(n, body)), str(REAL)], lbl)
        # -- 11. no .git ancestor -----------------------------------------------------------
        outside = Path(tempfile.mkdtemp(prefix="t291-nogit-"))
        try:
            shutil.copy(str(NEW), str(outside / "rule.py"))
            run("env/rule-copied-OUTSIDE-any-git-repo",
                [sys.executable, str(outside / "rule.py"), "--register", str(REG),
                 "--acknowledgements", str(ACK), str(REAL)])
        finally:
            shutil.rmtree(outside, ignore_errors=True)

        print("%-52s %8s %-18s" % ("CASE", "EXIT", "PROBE"))
        print("-" * 82)
        for n, rc_, pr in rows:
            print("%-52s %8s %-18s" % (n, rc_, pr))
        print("-" * 82)
        z = [r for r in rows if r[1] == 0]
        print("cases: %d" % len(rows))
        print("EXIT-0 CASES (%d) -- every one is a claim to have MEASURED a non-empty population:"
              % len(z))
        for n, _rc, pr in z:
            print("    %-48s %s" % (n, pr))
        print()
        print("INVARIANT VIOLATIONS: %d" % len(viol))
        for n, why in viol:
            print("    !! %-46s %s" % (n, why))
        print()

        # ---------------------------------------------------------------- PART 2
        print("=" * 82)
        print("PART 2 -- routes plain argv cannot drive. These are the WRAPPER's problem: a")
        print("caller that tests `rc -eq 1` rather than `rc -ne 0` misreads every row here.")
        print("=" * 82)
        for sig, nm in ((signal.SIGTERM, "SIGTERM"), (signal.SIGKILL, "SIGKILL"),
                        (signal.SIGINT, "SIGINT")):
            p = subprocess.Popen(STD + [str(REAL)] * 400, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
            time.sleep(0.15)
            try:
                p.send_signal(sig)
            except ProcessLookupError:
                pass
            p.communicate()
            print("    %-46s exit=%s" % ("signal/" + nm + " mid-run", p.returncode))
        p = subprocess.Popen(STD + [str(REAL)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True)
        p.stdout.close()
        p.wait()
        print("    %-46s exit=%s" % ("stdout/closed-before-the-probe-line", p.returncode))
        fifo = E / "fifo.json"
        os.mkfifo(fifo)

        def feeder():
            try:
                with open(fifo, "w") as f:
                    f.write('{"cells":[{"P9_x":true,"verdict":"AS PREDICTED"}]}')
            except OSError:
                pass

        threading.Thread(target=feeder, daemon=True).start()
        try:
            r = subprocess.run(STD + [str(fifo)], capture_output=True, text=True, timeout=20)
            print("    %-46s exit=%s" % ("target/FIFO-named-pipe", r.returncode))
        except subprocess.TimeoutExpired:
            print("    %-46s HUNG -- no exit code in 20s. The rule opens the target TWICE"
                  % "target/FIFO-named-pipe")
            print("    %-46s (sha256_of then load_json), so the second read blocks forever."
                  % "")
        env_o = dict(os.environ)
        env_o["PYTHONOPTIMIZE"] = "2"
        r = subprocess.run(STD + [str(REAL)], capture_output=True, text=True, env=env_o)
        print("    %-46s exit=%s" % ("env/PYTHONOPTIMIZE=2", r.returncode))
        print()
        print("    DECLARED, NOT MEASURED: `sha256_of(path)` and `load_json(path)` are TWO reads")
        print("    of the same path, so the sha an acknowledgement is pinned against is not")
        print("    provably the bytes that were graded. The FIFO row above is what makes that")
        print("    two-ness visible; a TOCTOU swap is not drivable deterministically from here.")
        return 1 if viol else 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
