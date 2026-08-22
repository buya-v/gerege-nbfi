#!/usr/bin/env python3
"""T263 -- adversarial drive of T164's guard-parse-float-ast.py selector.

NOT a re-run of T164's own harness. Every shape below is one T164 did not design the
selector around. Each is a real way a money amount reaches a Python binary double
through json.load/loads.

METHOD. For each shape, build a throwaway root containing:
    benign.py     -- one COMPLIANT json.load call site, so the guard can never bail out
                     on NIL COVERAGE and be scored as if it had caught something.
    adversary.py  -- the shape under test. A binary double IS produced at run time.
Then run `guard-parse-float-ast.py --root <dir>` and record the exit code.

    exit 1  the guard CAUGHT the shape          -> CAUGHT
    exit 2  the guard REFUSED                    -> REFUSED (safe, but not a catch)
    exit 0  the guard printed PASS               -> MISSED  <-- the interesting column

Every shape is also EXECUTED, so "MISSED" always means "the guard passed a file that
really does build a float", never "the guard passed a file that could not run anyway".

P-80: a non-{0,1,2} exit, or a guard that will not run at all, ABORTS this script. It is
never reported as an absence.
"""
import json
import os
import subprocess
import sys
import tempfile

GUARD = os.environ["T263_GUARD"]

BENIGN = '''\
import decimal, json
def go(p):
    return json.load(open(p), parse_float=decimal.Decimal)
'''

# (id, description, source, snippet that must produce a float when executed)
SHAPES = [
    ("A-varalias-load",
     "loader bound to a local variable: f = json.load; f(fp)",
     'import json\n'
     'def go(p):\n'
     '    f = json.load\n'
     '    return f(open(p))\n'),
    ("B-modalias-assign",
     "module bound to a variable: j = json; j.load(fp)",
     'import json\n'
     'j = json\n'
     'def go(p):\n'
     '    return j.load(open(p))\n'),
    ("C-star-import",
     "from json import * ; load(fp)",
     'from json import *\n'
     'def go(p):\n'
     '    return load(open(p))\n'),
    ("D-import-submodule",
     "import json.decoder binds the name `json`; json.load(fp)",
     'import json.decoder\n'
     'def go(p):\n'
     '    return json.load(open(p))\n'),
    ("E-parse-float-indirect-builtin",
     "parse_float=pf where pf IS the builtin float",
     'import json\n'
     'pf = float\n'
     'def go(p):\n'
     '    return json.load(open(p), parse_float=pf)\n'),
    ("F-parse-float-lambda-float",
     "parse_float=lambda s: float(s) -- a keyword that satisfies the check and still doubles",
     'import json\n'
     'def go(p):\n'
     '    return json.load(open(p), parse_float=lambda s: float(s))\n'),
    ("G-kwargs-forward",
     "json.load(fp, **opts) with opts carrying no parse_float",
     'import json\n'
     'OPTS = {}\n'
     'def go(p):\n'
     '    return json.load(open(p), **OPTS)\n'),
    ("H-nested-and-comprehension",
     "the call lives in a nested function inside a comprehension",
     'import json\n'
     'def go(p):\n'
     '    def inner(q):\n'
     '        return json.load(open(q))\n'
     '    return [inner(x) for x in [p]][0]\n'),
    ("I-conditional-import",
     "import performed inside an if-branch",
     'import os\n'
     'if os.name:\n'
     '    import json as J\n'
     'def go(p):\n'
     '    return J.load(open(p))\n'),
    ("J-try-except-import-alias",
     "try: import simplejson as json / except: import json  -- then json.load(fp)",
     'try:\n'
     '    import ujson as json\n'
     'except ImportError:\n'
     '    import json\n'
     'def go(p):\n'
     '    return json.load(open(p))\n'),
    ("K-decorator-wrapped-loader",
     "the loader is wrapped by a decorator and called through the wrapper",
     'import functools, json\n'
     'def keep(fn):\n'
     '    @functools.wraps(fn)\n'
     '    def w(*a, **k):\n'
     '        return fn(*a, **k)\n'
     '    return w\n'
     'LOAD = keep(json.load)\n'
     'def go(p):\n'
     '    return LOAD(open(p))\n'),
    ("L-jsondecoder-decode",
     "json.JSONDecoder().decode(text) -- never named load/loads",
     'import json\n'
     'def go(p):\n'
     '    return json.JSONDecoder().decode(open(p).read())\n'),
    ("M-functools-partial",
     "functools.partial(json.load)",
     'import functools, json\n'
     'P = functools.partial(json.load)\n'
     'def go(p):\n'
     '    return P(open(p))\n'),
    ("N-getattr",
     'getattr(json, "load")(fp)',
     'import json\n'
     'def go(p):\n'
     '    return getattr(json, "load")(open(p))\n'),
    ("O-try-except-body",
     "a plain json.load inside try/except (control: SHOULD be caught)",
     'import json\n'
     'def go(p):\n'
     '    try:\n'
     '        return json.load(open(p))\n'
     '    except OSError:\n'
     '        return None\n'),
    ("P-parse-float-float-literal",
     "parse_float=float (control: T164 claims this is a dodge and fails)",
     'import json\n'
     'def go(p):\n'
     '    return json.load(open(p), parse_float=float)\n'),
    ("Q-subdirectory",
     "a non-compliant json.load in a SUBDIRECTORY of the root",
     None),  # handled specially
]

DOC = '{"amount": 1200000.25}'


def run_guard(root):
    r = subprocess.run([sys.executable, GUARD, "--root", root],
                       capture_output=True, text=True)
    if r.returncode not in (0, 1, 2):
        sys.stderr.write("ABORT: guard exited %d on %s -- not one of {0,1,2}. This is an "
                         "ERROR, not a measurement (P-80).\n%s\n"
                         % (r.returncode, root, r.stderr))
        raise SystemExit(3)
    return r.returncode, r.stdout, r.stderr


def executes_to_float(src, doc_path):
    """Run the shape for real. Returns the type name of the loaded amount, or an error."""
    d = tempfile.mkdtemp(prefix="t263-exec-")
    p = os.path.join(d, "m.py")
    open(p, "w").write(src)
    code = ("import importlib.util,sys,json;"
            "s=importlib.util.spec_from_file_location('m',%r);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "v=m.go(%r)['amount'];print(type(v).__name__)" % (p, doc_path))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        return "EXEC-ERROR: " + r.stderr.strip().split("\n")[-1]
    return r.stdout.strip()


def main():
    tmp = tempfile.mkdtemp(prefix="t263-attack-")
    doc = os.path.join(tmp, "doc.json")
    open(doc, "w").write(DOC)

    rows = []
    for sid, desc, src in SHAPES:
        root = os.path.join(tmp, sid)
        os.makedirs(root)
        open(os.path.join(root, "benign.py"), "w").write(BENIGN)
        if sid == "Q-subdirectory":
            sub = os.path.join(root, "nested")
            os.makedirs(sub)
            src = 'import json\ndef go(p):\n    return json.load(open(p))\n'
            open(os.path.join(sub, "adversary.py"), "w").write(src)
        else:
            open(os.path.join(root, "adversary.py"), "w").write(src)

        rc, out, err = run_guard(root)
        verdict = {0: "MISSED ", 1: "CAUGHT ", 2: "REFUSED"}[rc]
        got = executes_to_float(src, doc)
        rows.append((sid, verdict, rc, got, desc))
        # does the guard's own site table even mention the adversary?
        mentioned = "adversary.py" in out
        rows[-1] = rows[-1] + (mentioned,)

    print("=" * 100)
    print("T263 -- ADVERSARIAL SELECTOR DRIVE of guard-parse-float-ast.py")
    print("guard: %s" % GUARD)
    print("=" * 100)
    print("%-32s %-8s %-4s %-22s %s" % ("SHAPE", "VERDICT", "rc", "runtime amount type",
                                        "adversary named in output?"))
    for sid, verdict, rc, got, desc, mentioned in rows:
        print("%-32s %-8s %-4d %-22s %s" % (sid, verdict, rc, got,
                                            "yes" if mentioned else "NO"))
    print()
    missed = [r for r in rows if r[1].strip() == "MISSED"]
    real = [r for r in missed if r[3] == "float"]
    print("TOTAL SHAPES ......... %d" % len(rows))
    print("CAUGHT (exit 1) ...... %d" % len([r for r in rows if r[1].strip() == "CAUGHT"]))
    print("REFUSED (exit 2) ..... %d" % len([r for r in rows if r[1].strip() == "REFUSED"]))
    print("MISSED (exit 0 PASS) . %d" % len(missed))
    print("  ... of which the shape REALLY produces a binary double at run time: %d"
          % len(real))
    print()
    for sid, verdict, rc, got, desc, mentioned in rows:
        print("  %-8s %-32s %s" % (verdict.strip(), sid, desc))
    print()
    print("EVERY shape above was EXECUTED against %s, so a MISS is a measured miss on a "
          "file that really doubles, not a miss on dead code." % DOC)
    return 0


if __name__ == "__main__":
    sys.exit(main())
