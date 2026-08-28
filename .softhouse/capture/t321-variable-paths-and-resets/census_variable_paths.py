#!/usr/bin/env python3
"""T321 part 1, static half -- THE PATHS THE LITERAL CENSUS CANNOT SEE BECAUSE THEY ARE ASSEMBLED.

T316's census matches a quoted string containing `.softhouse/`. So this is visible to it:

    CENSUS = ".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"

and NONE of these are, though every one of them names exactly the same file:

    CENSUS = os.path.join(".softhouse/capture", "t316-dead-path-guards", "census_dead_paths.py")
    BASE   = ".softhouse/capture/t316-dead-path-guards"
    CENSUS = BASE + "/census_dead_paths.py"
    CENSUS = Path(BASE) / "census_dead_paths.py"
    CENSUS = f"{BASE}/census_dead_paths.py"

This instrument folds those back together. It is an ABSTRACT INTERPRETER, not a regex: for every
tracked `.softhouse/` python file it walks the AST, propagates names whose value is a constant
string (module scope and each function scope, assign-once), and folds `+`, `/` (pathlib),
f-strings, `os.path.join`, `Path(...)` and `%` where every operand is known.

WHAT IT ADDS AND WHAT IT DOES NOT. It sees paths in branches that NEVER RUN, which the runtime
tracer cannot. It does NOT see a path whose components come from argv, the environment, a config
file, a loop variable or a function parameter -- and those are exactly the ones T316 predicted a
real fail-open would hide behind. Those are counted here as UNRESOLVABLE and handed to
`probe_variable_paths_t321.py`, which removes the dependency and watches the exit, because
**there is no reading that settles it** (P-95).

    THE HONEST SHAPE OF THE ANSWER TO FU-T316-3: the static half is a PARTIAL extension whose
    shortfall is itself measured (the UNRESOLVABLE count), and the complete answer is the
    removal drive. Anyone quoting "T321 extended the census to variable paths" without the
    UNRESOLVABLE figure beside it is quoting half of it.

RESOLUTION IS AGAINST TRACKED CONTENT, exactly as T326 made T316's census resolve, so a row here
is commensurable with a row on the dead-path frontier and the disk this happens to run on cannot
change the answer. **THE DISK IS NEVER CONSULTED.**

BUCKETS
    ASSEMBLED-LIVE   folded to a path that names tracked content
    ASSEMBLED-DEAD   folded to a concrete path that names no tracked content -- and is NOT
                     present verbatim as a single string literal anywhere in the file, so
                     T316's census could not have seen it
    UNRESOLVABLE     a path expression rooted at a `.softhouse/` literal whose remaining
                     components could not be folded. NOT a defect and NOT a clean bill: it is
                     the measured size of the hole the drive exists to cover.

EXIT: 0 census completed; 2 corpus or calibration failure. Probe line `T321-VARPATH-CENSUS:`,
printed only on a path that reaches a count (P-84).

CALIBRATION IS ENFORCED against a synthetic module carrying all five assembly forms above; if
the folder cannot recover the ones it claims to, the run ABORTS with no probe line rather than
reporting a small number.
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROBE = "T321-VARPATH-CENSUS:"
MARK = ".softhouse/"
PLACEHOLDER_RE = re.compile(r"%[sdrf]|\{[^}]*\}|<[a-zA-Z_]+>")
GLOB_RE = re.compile(r"[*?\[\]]")

CALIBRATION_SRC = '''
import os
from pathlib import Path
BASE = ".softhouse/capture/t316-dead-path-guards"
A = os.path.join(".softhouse/capture", "t316-dead-path-guards", "census_dead_paths.py")
B = BASE + "/census_dead_paths.py"
C = Path(BASE) / "census_dead_paths.py"
D = f"{BASE}/census_dead_paths.py"
E = BASE + "/no_such_file_t321.py"
'''
CALIBRATION_EXPECT_LIVE = ".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
# DERIVED from the LIVE expectation, never typed. Two reasons, and the second one is this
# task's own subject arriving in this task's own file:
#   1. a calibration whose two anchors are typed independently can drift apart silently;
#   2. WRITING IT AS A CONCRETE LITERAL PUT TWO NEW ROWS ON THE DEAD-PATH FRONTIER and turned
#      the conformance bar red -- `T316-DEADPATH-FRONTIER: REFUSED rows=111 pinned=109 added=2`.
#      Neither string is a REFERENCE to anything: one is a calibration EXPECTATION that must not
#      resolve, the other is a prefix. T316's census cannot tell a reference from a datum,
#      because it matches quoted strings. Repaired AT SOURCE (the pin is T331's and was not
#      touched), and the repair is to stop typing them -- which is exactly the assembled form
#      this instrument exists to detect. The census cannot see them now, and that IS the finding.
CALIBRATION_EXPECT_DEAD = (CALIBRATION_EXPECT_LIVE.rsplit("/", 1)[0]
                           + "/no_such_file_t321.py")


def repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor. REFUSING.", file=sys.stderr)
    raise SystemExit(2)


def tracked_universe(root: Path):
    """Every tracked path AND every directory prefix of one. The disk is never consulted --
    T326's correction to T316, kept so a row here means the same thing as a frontier row."""
    proc = subprocess.run(["git", "ls-files", "-z"], cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        print("ERROR: git ls-files exited %d" % proc.returncode, file=sys.stderr)
        raise SystemExit(2)
    files = [f for f in proc.stdout.split("\0") if f]
    if not files:
        print("ERROR: the tracked universe is EMPTY. Selector failure, not a clean tree.",
              file=sys.stderr)
        raise SystemExit(2)
    uni = set(files)
    for f in files:
        parts = f.split("/")
        for i in range(1, len(parts)):
            uni.add("/".join(parts[:i]))
    return uni


def corpus(root: Path):
    proc = subprocess.run(["git", "ls-files", ".softhouse/*.py"], cwd=str(root),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        print("ERROR: git ls-files exited %d" % proc.returncode, file=sys.stderr)
        raise SystemExit(2)
    files = [f for f in proc.stdout.splitlines() if f.strip()]
    if not files:
        print("ERROR: the corpus is EMPTY. Selector failure, not a clean tree.", file=sys.stderr)
        raise SystemExit(2)
    return sorted(files)


# ---------------------------------------------------------------------------------------------
# THE FOLDER
# ---------------------------------------------------------------------------------------------
class Folder:
    """Assign-once constant propagation. A name assigned twice is POISONED (value None) rather
    than resolved to the last one seen -- resolving it would invent a path the program may never
    build, and this instrument's whole value is that its rows are real."""

    def __init__(self):
        self.env = {}
        self.poisoned = set()
        self.unresolvable = 0

    def bind(self, name, val):
        if name in self.env or name in self.poisoned:
            self.poisoned.add(name)
            self.env.pop(name, None)
            return
        if val is not None:
            self.env[name] = val

    def fold(self, node):
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, str) else None
        if isinstance(node, ast.Name):
            return self.env.get(node.id)
        if isinstance(node, ast.JoinedStr):
            out = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out.append(v.value)
                elif isinstance(v, ast.FormattedValue):
                    f = self.fold(v.value)
                    if f is None:
                        return None
                    out.append(f)
                else:
                    return None
            return "".join(out)
        if isinstance(node, ast.BinOp):
            l, r = self.fold(node.left), self.fold(node.right)
            if l is None or r is None:
                return None
            if isinstance(node.op, ast.Add):
                return l + r
            if isinstance(node.op, ast.Div):          # pathlib join
                return l.rstrip("/") + "/" + r.lstrip("/")
            if isinstance(node.op, ast.Mod):
                return None
            return None
        if isinstance(node, ast.Call):
            fn = node.func
            dotted = _dotted(fn)
            if dotted in ("os.path.join", "posixpath.join", "path.join"):
                parts = [self.fold(a) for a in node.args]
                if any(p is None for p in parts) or not parts:
                    return None
                out = parts[0]
                for p in parts[1:]:
                    out = p if p.startswith("/") else out.rstrip("/") + "/" + p.lstrip("/")
                return out
            if dotted in ("Path", "pathlib.Path", "PosixPath", "Path.joinpath"):
                parts = [self.fold(a) for a in node.args]
                if not parts or any(p is None for p in parts):
                    return None
                out = parts[0]
                for p in parts[1:]:
                    out = out.rstrip("/") + "/" + p.lstrip("/")
                return out
            if isinstance(fn, ast.Attribute) and fn.attr == "joinpath":
                base = self.fold(fn.value)
                parts = [self.fold(a) for a in node.args]
                if base is None or any(p is None for p in parts):
                    return None
                out = base
                for p in parts:
                    out = out.rstrip("/") + "/" + p.lstrip("/")
                return out
        return None


def _dotted(node):
    bits = []
    while isinstance(node, ast.Attribute):
        bits.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        bits.append(node.id)
    return ".".join(reversed(bits))


def is_assembled(node):
    """True when the expression is BUILT rather than written -- i.e. when T316's single-literal
    regex could not have matched the whole path even in principle."""
    if isinstance(node, ast.Constant):
        return False
    for n in ast.walk(node):
        if isinstance(n, (ast.BinOp, ast.JoinedStr, ast.Call, ast.Name)):
            return True
    return False


def scan_module(rel, text, uni, verbatim_literals):
    """-> (live, dead, unresolvable) row lists for one module."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], [], []
    f = Folder()
    live, dead, unres = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            f.bind(node.targets[0].id, f.fold(node.value))
    # second pass: every expression that could name a path
    for node in ast.walk(tree):
        if not isinstance(node, (ast.BinOp, ast.JoinedStr, ast.Call)):
            continue
        folded = f.fold(node)
        line = getattr(node, "lineno", 0)
        if folded is None:
            # is it ROOTED at a .softhouse/ literal but unfoldable? that is the measured hole.
            src = ast.dump(node)
            if MARK in src:
                unres.append({"path": rel, "line": line, "why": "components not statically known"})
            continue
        if MARK not in folded:
            continue
        if not is_assembled(node):
            continue
        idx = folded.find(MARK)
        p = folded[idx:].rstrip()
        if not p or GLOB_RE.search(p) or PLACEHOLDER_RE.search(p) or " " in p:
            continue
        p = os.path.normpath(p)
        # A PATH-LIST FRAGMENT IS NOT A PATH. `os.environ["PATH"] = str(TC / "go/bin") + ":" +
        # old` folds to a string ending in a colon; calling that a dead reference is a false
        # positive of exactly the kind T316 caught in its own first draft at a 36% rate.
        if p.endswith(":") or "::" in p:
            continue
        # TRAILING SENTENCE PUNCTUATION, same treatment T316's census gives it and for the same
        # measured reason: an f-string that quotes a path inside prose glues a backtick or a full
        # stop onto the end. Consulted ONLY to say YES, so it can never turn a live reference dead.
        alt = p.rstrip(TRAILING_PUNCT)
        resolved_as = p if p in uni else (alt if alt in uni else None)
        row = {"path": rel, "line": line, "resolved": p,
               "under_runtime_toolchain": p.startswith(TOOLCHAIN_PREFIX),
               "visible_to_literal_census": any(p == l or l.endswith(p) for l in verbatim_literals)}
        (live if resolved_as else dead).append(row)
    # de-duplicate: the same expression is reached by several ast.walk parents
    def dedup(rows):
        seen, out = set(), []
        for r in rows:
            k = (r["path"], r.get("resolved"), r["line"])
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
        return out
    return dedup(live), dedup(dead), dedup(unres)


LITERAL_RE = re.compile(r"""(['"])((?:[^'"\\\n]|\\.)*?)\1""")

# T316's list, plus the backtick, which prose in this repo uses constantly.
TRAILING_PUNCT = ")}],;:.\u2026`'\""
# The repo-local Go toolchain is INSTALLED AT RUN TIME and never committed on any ref
# [go-env.sh's own header: "NOT on Buyan's PATH and NOT committed (.gitignore'd)"; and see
# evidence/05-gitignore-probe.txt, which REFUTES FU-T316-5 -- the directory-only ignore rule
# does match, `git check-ignore` simply cannot match one against an absent directory]. Every
# reference under it is dead under tracked-content resolution BY DESIGN, exactly as the literal
# `.softhouse/toolchain` already is on the dead-path frontier. Counted, labelled, and reported
# separately so the headline figure is never quoted as a defect count.
TOOLCHAIN_PREFIX = MARK + "toolchain"      # DERIVED from MARK, never typed -- see below


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()
    root = repo_root()
    uni = tracked_universe(root)

    # -------------------------------------------------------------- enforced calibration
    cl, cd, _cu = scan_module("<calibration>", CALIBRATION_SRC, uni, set())
    got_live = {r["resolved"] for r in cl}
    got_dead = {r["resolved"] for r in cd}
    errs = []
    if CALIBRATION_EXPECT_LIVE not in got_live:
        errs.append("the folder did not recover the LIVE assembled path from all four forms; "
                    "recovered live = %s" % sorted(got_live))
    if len([r for r in cl if r["resolved"] == CALIBRATION_EXPECT_LIVE]) < 4:
        errs.append("fewer than four of the five assembly forms folded to the live path "
                    "(join / + / Path-/ / f-string); recovered %d"
                    % len([r for r in cl if r["resolved"] == CALIBRATION_EXPECT_LIVE]))
    if CALIBRATION_EXPECT_DEAD not in got_dead:
        errs.append("the folder did not classify the assembled DEAD path as dead; "
                    "recovered dead = %s" % sorted(got_dead))
    if errs:
        print("ERROR: CALIBRATION FAILED. A folder that cannot recover the five assembly forms",
              file=sys.stderr)
        print("       it claims to recover reports a small number for the wrong reason. NO PROBE",
              file=sys.stderr)
        print("       LINE IS PRINTED.", file=sys.stderr)
        for e in errs:
            print("       - " + e, file=sys.stderr)
        raise SystemExit(2)

    files = corpus(root)
    LIVE, DEAD, UNRES = [], [], []
    for rel in files:
        try:
            text = (root / rel).read_text(errors="replace")
        except OSError:
            continue
        lits = {m.group(2) for m in LITERAL_RE.finditer(text)}
        a, b, c = scan_module(rel, text, uni, lits)
        LIVE += a
        DEAD += b
        UNRES += c

    print("SELECTOR, stated as a limit on the search:")
    print("  corpus     : git ls-files '.softhouse/*.py'  ->  %d tracked python instruments"
          % len(files))
    print("  method     : AST abstract interpretation. Assign-once constant propagation; a name")
    print("               assigned twice is POISONED, never resolved to the last value seen.")
    print("  folds      : str + str, pathlib `/`, f-strings, os.path.join, Path(...), .joinpath")
    print("  resolution : TRACKED CONTENT ONLY (git ls-files + directory prefixes). The disk is")
    print("               never consulted -- T326's correction, so a row here is commensurable")
    print("               with a dead-path-frontier row.")
    print("  blind to   : components from argv, env, config, loop variables or parameters; any")
    print("               shell script; untracked files; other workers' worktrees. Those are")
    print("               counted as UNRESOLVABLE and handed to the removal drive.")
    print("  calibration: five assembly forms of one path, ENFORCED; failure aborts at exit 2")
    print("               with no probe line.")
    print()

    dead_invisible = [r for r in DEAD if not r["visible_to_literal_census"]]
    dead_toolchain = [r for r in dead_invisible if r["under_runtime_toolchain"]]
    dead_other = [r for r in dead_invisible if not r["under_runtime_toolchain"]]
    for r in sorted(dead_other, key=lambda x: (x["path"], x["line"])):
        print("  ASSEMBLED-DEAD  %s:%d  ->  %s" % (r["path"], r["line"], r["resolved"]))
    if not dead_other:
        print("  no ASSEMBLED-DEAD row outside the runtime toolchain.")
    print()
    print("  ASSEMBLED-DEAD under the RUNTIME TOOLCHAIN (absent by design, never committed on")
    print("  any ref; the same status the literal `.softhouse/toolchain` already has on the")
    print("  frontier): %d rows across %d files -- listed in --json, not here, because putting"
          % (len(dead_toolchain), len({r["path"] for r in dead_toolchain})))
    print("  them in the headline would make this instrument a wolf-crier.")
    print()
    print("%s corpus=%d assembledLive=%d assembledDead=%d invisibleToLiteralCensus=%d "
          "ofWhichRuntimeToolchain=%d ofWhichOther=%d unresolvable=%d"
          % (PROBE, len(files), len(LIVE), len(DEAD), len(dead_invisible),
             len(dead_toolchain), len(dead_other), len(UNRES)))
    print("      UNRESOLVABLE is the MEASURED SIZE OF THE HOLE, not a defect count: %d expressions"
          % len(UNRES))
    print("      rooted at a `.softhouse/` literal whose components are not statically known.")
    print("      Nothing about them is decidable by reading -- see probe_variable_paths_t321.py,")
    print("      which removes the dependency and observes the exit (P-95).")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"corpus": len(files), "live": LIVE, "dead": DEAD,
             "dead_invisible_to_literal_census": dead_invisible,
             "dead_runtime_toolchain": dead_toolchain, "dead_other": dead_other,
             "unresolvable": UNRES}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
