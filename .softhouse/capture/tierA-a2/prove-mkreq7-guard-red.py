#!/usr/bin/env python3
"""Drive the A2-7 recipe guards RED, then GREEN. Transcript: RED-GREEN-A2-7-guards.txt

P-22: a guard you have not personally driven red is worse than no guard, because it is
believed. D-1 in this very capture directory is the defect these guards exist to prevent
— mkreq2.py silently rewrote request bodies that captures had already been taken
against, stranding 30 real oracle responses with recipes that cannot regenerate them.

Every case runs in a throwaway temp directory against a COPY of the real mkreq7.py /
resolve7.py, so the committed evidence is never touched. Nothing here contacts the
oracle.

  python3 prove-mkreq7-guard-red.py     -> exit 0 only if every case behaves as asserted
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
FAILURES = []
CASES = 0


def check(label, cond, detail=""):
    global CASES
    CASES += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("  " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


def sandbox(script):
    d = tempfile.mkdtemp(prefix="a2-7-prove.")
    shutil.copy(os.path.join(DIR, script), os.path.join(d, script))
    os.makedirs(os.path.join(d, "req"), exist_ok=True)
    return d


def run(d, script, *args):
    p = subprocess.run([sys.executable, os.path.join(d, script), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def snapshot(reqdir):
    return {n: open(os.path.join(reqdir, n), "rb").read() for n in sorted(os.listdir(reqdir))}


def prove_mkreq7():
    print("mkreq7.py — the request-body generator")

    # --- GREEN 1: empty req/ -> writes everything, exit 0.
    d = sandbox("mkreq7.py")
    rc, out, err = run(d, "mkreq7.py")
    first = snapshot(os.path.join(d, "req"))
    check("GREEN empty req/ writes and exits 0", rc == 0 and len(first) > 0,
          f"rc={rc} files={len(first)}")

    # --- GREEN 2: rerun is a proven no-op, byte for byte.
    rc, out, err = run(d, "mkreq7.py")
    second = snapshot(os.path.join(d, "req"))
    check("GREEN rerun is byte-identical and exits 0",
          rc == 0 and second == first and "unchanged" in out, f"rc={rc}")

    # --- RED 1: a body on disk differs -> abort, exit 1, name it, write NOTHING.
    victim = "a2-7-prod-210-cash-nine-mandatory.json"
    body = json.loads(first[victim])
    body["fundSourceAccountId"] = 99999          # the D-1 mutation, in miniature
    with open(os.path.join(d, "req", victim), "w") as f:
        json.dump(body, f, indent=2)
        f.write("\n")
    perturbed = snapshot(os.path.join(d, "req"))
    rc, out, err = run(d, "mkreq7.py")
    after = snapshot(os.path.join(d, "req"))
    check("RED  a differing body makes it exit 1", rc == 1, f"rc={rc}")
    check("RED  the refusal NAMES the offending file", victim in err)
    check("RED  the refusal cites D-1", "D-1" in err)
    check("RED  it leaves every byte on disk alone", after == perturbed)

    # --- RED 2: abort happens BEFORE any write — a missing sibling stays missing.
    absent = "a2-7-recovery-230.json"
    os.remove(os.path.join(d, "req", absent))
    rc, out, err = run(d, "mkreq7.py")
    check("RED  it aborts before writing: a deleted sibling is NOT recreated",
          rc == 1 and not os.path.exists(os.path.join(d, "req", absent)), f"rc={rc}")

    # --- GREEN 3: restore the perturbed byte and the deleted file returns, exit 0.
    with open(os.path.join(d, "req", victim), "wb") as f:
        f.write(first[victim])
    rc, out, err = run(d, "mkreq7.py")
    restored = snapshot(os.path.join(d, "req"))
    check("GREEN restoring the byte lets it complete, and rebuilds only the missing file",
          rc == 0 and restored == first, f"rc={rc}")
    shutil.rmtree(d)


def prove_resolve7():
    print("resolve7.py — the observed-value resolver")
    d = sandbox("resolve7.py")
    tmpl = os.path.join(d, "tmpl.json")
    obs = os.path.join(d, "obs.json")
    out_p = os.path.join(d, "resolved.json")
    json.dump({"clientId": 1, "productId": "__PRODUCT_ID__"}, open(tmpl, "w"))

    # --- RED 1: the observation carries no such key -> refuse, do not invent one.
    json.dump({"errors": [{"developerMessage": "nope"}]}, open(obs, "w"))
    rc, o, e = run(d, "resolve7.py", tmpl, obs, "resourceId", out_p)
    check("RED  a response with no resourceId is refused, not guessed",
          rc == 1 and not os.path.exists(out_p), f"rc={rc}")
    check("RED  the refusal says there is no observation to resolve from",
          "no observation to resolve from" in e)

    # --- GREEN: a real observation resolves.
    json.dump({"resourceId": 46}, open(obs, "w"))
    rc, o, e = run(d, "resolve7.py", tmpl, obs, "resourceId", out_p)
    body = json.load(open(out_p)) if os.path.exists(out_p) else {}
    check("GREEN an observed resourceId is substituted verbatim",
          rc == 0 and body.get("productId") == 46, f"rc={rc} body={body}")

    # --- RED 2: a DIFFERENT observation would rewrite an existing resolved body.
    json.dump({"resourceId": 47}, open(obs, "w"))
    rc, o, e = run(d, "resolve7.py", tmpl, obs, "resourceId", out_p)
    body = json.load(open(out_p))
    check("RED  it refuses to rewrite an existing resolved body with a different id",
          rc == 1 and body.get("productId") == 46, f"rc={rc} body={body}")

    # --- RED 3: a template with no placeholder is a mis-wired call, not a silent copy.
    flat = os.path.join(d, "flat.json")
    json.dump({"clientId": 1, "productId": 46}, open(flat, "w"))
    rc, o, e = run(d, "resolve7.py", flat, obs, "resourceId", os.path.join(d, "x.json"))
    check("RED  a template with no __PLACEHOLDER__ is refused",
          rc == 1 and not os.path.exists(os.path.join(d, "x.json")), f"rc={rc}")
    shutil.rmtree(d)


def prove_analyze7_has_no_float():
    """P-25: the no-floating-point rule binds analysis scripts. Prove it structurally."""
    print("analyze7.py — no binary floating point on any amount")
    src = open(os.path.join(DIR, "analyze7.py")).read()
    check("it parses JSON numbers as Decimal", "parse_float=decimal.Decimal" in src)
    check("it never calls bare float()", "float(" not in src.replace("parse_float=", ""))

    # And behaviourally: the oracle's own literal must survive as Decimal, not double.
    import decimal
    v = json.loads('{"amount": 1200000.000000}', parse_float=decimal.Decimal)["amount"]
    check("an oracle amount literal loads as Decimal, not float",
          isinstance(v, decimal.Decimal) and str(v) == "1200000.000000", f"{type(v).__name__} {v}")


if __name__ == "__main__":
    prove_mkreq7()
    prove_resolve7()
    prove_analyze7_has_no_float()
    print(f"\n{CASES} assertions, {len(FAILURES)} failed")
    if FAILURES:
        for f in FAILURES:
            print("  FAILED: " + f)
    sys.exit(1 if FAILURES else 0)
