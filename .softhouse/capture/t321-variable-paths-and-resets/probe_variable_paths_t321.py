#!/usr/bin/env python3
"""T321 part 1 -- FU-T316-3: THE CENSUS SEES LITERALS ONLY. This sees what actually gets touched,
and then REMOVES IT AND WATCHES.

THE TASK. T316's dead-path census matches string literals, so a path assembled at runtime from
variables is invisible to it, and T316 says plainly that this is "the likelier hiding place for a
genuine fail-open, because the literal cases it could see turned out to be dominated by announced
fallbacks". Extend the detection, or say exactly why you cannot.

WHY A WIDER REGEX IS THE WRONG ANSWER, and this is the argued half of the deliverable. The value
of `os.path.join(BASE, name)` is not in the file. It is a function of the environment, the
arguments, the current working directory and whichever branch of the program ran. A static
matcher can recover SOME of those -- and this instrument does, in `census_variable_paths.py`,
which constant-folds what it can -- but it cannot recover the ones that matter most, and any
figure it produced would be a lower bound of unknown depth. So detection is moved to the one
place where the assembled path is a FACT: the moment it is used.

TWO PHASES, and the second is the one that decides anything.

  PHASE 1 -- OBSERVE. Each instrument is run under a runtime path tracer (`tracelib_t321.py`,
  installed as `sitecustomize.py` on PYTHONPATH, so it loads into the instrument and into every
  python3 child a shell guard spawns, with no edit to any instrument) plus `bash -x` for shell.
  Every path touched is recorded with whether it EXISTED at the moment of the call. Subtracting
  the file's own string literals gives THE SET T316's CENSUS CANNOT SEE.

  PHASE 2 -- REMOVE AND OBSERVE THE EXIT. P-95's rule, in the words T316 wrote it in:
  "you cannot distinguish a fail-open from a fallback by reading. You have to run it with the
  dependency removed." So every dependency observed in phase 1 is removed, one at a time, in a
  throwaway clone, and the instrument is re-run. The reading is EXIT STATUS plus PROBE-LINE
  PRESENCE (P-84: "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE
  VALUE."), compared against the same instrument's untouched baseline.

      DIES      exit or probe-presence changed -> the instrument noticed its input vanish
      SURVIVES  byte-identical verdict with the dependency GONE -> A FAIL-OPEN CANDIDATE

  SURVIVES is a CANDIDATE and never a finding, for the reason T316 established at length: an
  instrument can touch a path and not care about it (an optional output dir, an ordered fallback
  whose later candidate resolves, a probe that is meant to tolerate absence). The list is short
  enough to adjudicate by hand and this instrument prints, for every SURVIVES row, the exit and
  the probe line so that the adjudication is checkable.

INTER-ARM RESET, and it is deliberately not hand-rolled. Arms share one clone, so the reset is
load-bearing, and this is the task that just measured what most resets in this repo do not
clear. It is `git reset --hard <BASELINE SHA>` -- a NAMED REF, because arm K10 of the sibling
drive shows a bare `reset --hard` cannot undo a commit -- plus `git clean -fdxq`, AND THEN the
attestation: `.softhouse/guards/repo-state-attest.sh compare <baseline> <after>` with an empty
writ. If that returns anything but 0 the run ABORTS at exit 2 rather than reporting arms whose
independence it cannot vouch for. `git status --porcelain` is printed beside it and is NOT
trusted alone: T318 measured its discriminating power against a committed clobber at zero.

SAFETY. Everything happens in a clone under the system temp dir. The runner REFUSES if that
resolves inside this repository. Nothing is removed from, written to, or run against the live
checkout or any live worktree; five other workers hold worktrees of this repo right now.

EXIT: 0 completed; 1 at least one FAIL-OPEN CANDIDATE survived removal (a result, reported, not
a crash); 2 could not measure. Probe line: `T321-VARPATH:` -- printed only on a path that
reaches a count.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE = "T321-VARPATH:"
HERE = Path(__file__).resolve().parent
LITERAL_RE = re.compile(r"""(['"])((?:[^'"\\\n]|\\.)*?)\1""")
PROBE_LINE_RE = re.compile(r"^([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*):\s")
PS4 = "+T321XTRACE|"


def repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor. REFUSING.", file=sys.stderr)
    raise SystemExit(2)


ROOT = repo_root()


def run(args, cwd, env=None, timeout=180):
    try:
        p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, env=env,
                           timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", ""


# ---------------------------------------------------------------------------------------------
# THE ENFORCED SET -- derived, never typed.
# ---------------------------------------------------------------------------------------------
def enforced_set(root: Path):
    """Instruments whose fail-open would change the colour of the conformance bar: every
    `.softhouse/` script named on a NON-COMMENT line of conformance.sh, plus every guard under
    `.softhouse/guards/`. Transitive callees are not enumerated here -- the TRACE finds them,
    which is the point."""
    conf = root / ".softhouse/conformance.sh"
    named = set()
    if conf.is_file():
        for raw in conf.read_text(errors="replace").splitlines():
            if raw.lstrip().startswith("#"):
                continue
            for m in re.finditer(r"\.softhouse/[\w./-]+\.(?:sh|py|zsh)", raw):
                named.add(m.group(0))
    rc, out, err = run(["git", "ls-files", ".softhouse/guards/"], root)
    for f in out.splitlines():
        if f.endswith((".sh", ".py")):
            named.add(f)
    keep = sorted(p for p in named if (root / p).is_file())
    return keep, sorted(named - set(keep))


def literals_of(path: Path):
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return set()
    return {m.group(2) for m in LITERAL_RE.finditer(text)}


# ---------------------------------------------------------------------------------------------
# PHASE 1 -- the trace
# ---------------------------------------------------------------------------------------------
def trace_once(clone: Path, rel: str, pylib: Path, tracefile: Path):
    if tracefile.exists():
        tracefile.unlink()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pylib) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["T321_TRACE_OUT"] = str(tracefile)
    env["PS4"] = PS4
    if rel.endswith(".py"):
        argv = ["python3", str(clone / rel)]
    else:
        argv = ["bash", "-x", str(clone / rel)]
    rc, out, err = run(argv, clone, env=env)
    touched = []
    if tracefile.exists():
        for line in tracefile.read_text(errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                touched.append((parts[0], parts[1], parts[2]))
    # shell xtrace: every token on a traced line that names a repo path
    for line in err.splitlines():
        if not line.lstrip("+").startswith("T321XTRACE|") and PS4 not in line:
            continue
        for tok in re.findall(r"[^\s'\"]+", line):
            if ".softhouse/" in tok or tok.startswith(str(clone)):
                touched.append(("xtrace", "?", tok))
    return rc, out, err, touched


def normalise(clone: Path, s: str):
    """-> repo-relative path, or None if it is not inside the clone."""
    if not s:
        return None
    p = s
    if not os.path.isabs(p):
        p = os.path.join(str(clone), p)
    p = os.path.normpath(p)
    try:
        rel = os.path.relpath(p, str(clone))
    except ValueError:
        return None
    if rel.startswith("..") or rel in (".", ""):
        return None
    if rel.startswith(".git/") or rel == ".git":
        return None
    return rel


def probe_tokens(stdout, stderr):
    toks = set()
    for line in (stdout + "\n" + stderr).splitlines():
        m = PROBE_LINE_RE.match(line.strip())
        if m:
            toks.add(m.group(1))
    return toks


# ---------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-arms", type=int, default=200)
    ap.add_argument("--json", default=str(HERE / "evidence/40-varpath.json"))
    args = ap.parse_args()

    guard = ROOT / ".softhouse/guards/repo-state-attest.sh"
    if not guard.is_file():
        print("ERROR: %s absent. The inter-arm reset assertion is IMPORTED, not reimplemented"
              " (T213); without it this run cannot vouch for arm independence. REFUSING."
              % guard, file=sys.stderr)
        return 2

    targets, missing = enforced_set(ROOT)
    if not targets:
        print("ERROR: the ENFORCED SET is EMPTY. That is a selector failure, not a clean tree.",
              file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="t321-varpath-"))
    if os.path.realpath(str(tmp)).startswith(os.path.realpath(str(ROOT))):
        print("ERROR: scratch resolves INSIDE the repository. REFUSING.", file=sys.stderr)
        return 2
    clone = tmp / "clone"
    pylib = tmp / "pylib"
    pylib.mkdir(parents=True)
    shutil.copy2(str(HERE / "tracelib_t321.py"), str(pylib / "sitecustomize.py"))
    tracefile = tmp / "trace.tsv"

    print("T321 variable-path probe")
    print("  ENFORCED SET (derived from conformance.sh non-comment lines + .softhouse/guards/):")
    for t in targets:
        print("     %s" % t)
    if missing:
        print("  named but not present in the tree (reported, not silently dropped): %d" % len(missing))
        for m in missing:
            print("     %s" % m)
    print("  scratch: %s" % tmp)

    rc, out, err = run(["git", "clone", "--quiet", "--no-local", str(ROOT), str(clone)], tmp,
                       timeout=600)
    if rc != 0 or not (clone / ".git").exists():
        print("ERROR: clone failed (rc=%s):\n%s%s" % (rc, out, err), file=sys.stderr)
        return 2
    rc, base_sha, _ = run(["git", "rev-parse", "HEAD"], clone)
    base_sha = base_sha.strip()
    print("  clone at %s" % base_sha)

    baseline_snap = tmp / "baseline.attest"
    rc, o, e = run(["bash", str(guard), "snapshot", str(clone), str(baseline_snap)], clone)
    if rc != 0:
        print("ERROR: baseline attestation snapshot failed (rc=%d): %s%s" % (rc, o, e),
              file=sys.stderr)
        return 2

    def reset_and_attest(tag):
        """NAMED-REF reset (K10), then the ATTESTATION -- not a porcelain assertion, which T318
        measured at zero discriminating power against a committed clobber."""
        run(["git", "reset", "--hard", "--quiet", base_sha], clone)
        run(["git", "clean", "-fdxq"], clone)
        after = tmp / "after.attest"
        rc, o, e = run(["bash", str(guard), "snapshot", str(clone), str(after)], clone)
        if rc != 0:
            print("RIG FAILURE: post-arm snapshot refused (rc=%d) after %s" % (rc, tag))
            return False
        arc, ao, ae = run(["bash", str(guard), "compare", str(baseline_snap), str(after)], ROOT)
        prc, po, _ = run(["git", "status", "--porcelain"], clone)
        if arc != 0:
            print("RIG FAILURE: THE INTER-ARM RESET DID NOT RESET after %s." % tag)
            print("  attestation exit=%d; legacy `git status --porcelain` = %r"
                  % (arc, po.strip()))
            for ln in (ao + ae).splitlines()[:20]:
                print("    | " + ln)
            return False
        return True

    if not reset_and_attest("<pre-flight>"):
        print("ERROR: the rig cannot establish a clean starting point. REFUSING.", file=sys.stderr)
        return 2

    # ---------------------------------------------------------------- PHASE 1
    print("\nPHASE 1 -- OBSERVE. Every path touched at run time, and which of them the literal")
    print("  census cannot see. `bash -x` + a sitecustomize path tracer; no instrument edited.")
    obs = {}
    for rel in targets:
        rc, out, err, touched = trace_once(clone, rel, pylib, tracefile)
        loaded = any(k == "tracer-loaded" for k, _x, _p in touched)
        pyish = rel.endswith(".py")
        paths = {}
        for kind, existed, s in touched:
            n = normalise(clone, s)
            if n is None:
                continue
            paths.setdefault(n, set()).add(kind)
        lits = literals_of(ROOT / rel)
        # a touched path is INVISIBLE TO THE LITERAL CENSUS if no string literal in the file
        # names it, verbatim or as a suffix of a literal.
        invisible = set()
        for n in paths:
            if any(n == l or l.endswith(n) or n.endswith(l.lstrip("./")) for l in lits if l):
                continue
            invisible.add(n)
        obs[rel] = {"exit": rc, "n_touched": len(paths), "paths": sorted(paths),
                    "invisible_to_literal_census": sorted(invisible),
                    "tracer_loaded": loaded,
                    "probe_tokens": sorted(probe_tokens(out, err))}
        print("  %-58s touched=%-4d invisibleToLiteralCensus=%-4d tracerLoaded=%s"
              % (rel, len(paths), len(invisible),
                 "yes" if loaded else ("n/a(shell)" if not pyish else "**NO**")))
        if pyish and not loaded:
            print("     REFUSING to report this row: the tracer did not load into a python")
            print("     target, and 'tracer absent' and 'touched nothing' look identical.")
            return 2
        if not reset_and_attest("trace of " + rel):
            return 2

    # ---------------------------------------------------------------- PHASE 2
    print("\nPHASE 2 -- REMOVE AND OBSERVE THE EXIT (P-95). Baseline first, then one removal per")
    print("  arm, each followed by a named-ref reset that is ATTESTED, not asserted.")
    rows = []
    survivors = []
    arms = 0
    for rel in targets:
        argv = ["python3", str(clone / rel)] if rel.endswith(".py") else ["bash", str(clone / rel)]
        brc, bout, berr = run(argv, clone)
        btok = probe_tokens(bout, berr)
        print("\n  %s -- BASELINE exit=%s probeTokens=%s" % (rel, brc, sorted(btok) or "none"))
        if not reset_and_attest("baseline of " + rel):
            return 2
        cands = [p for p in obs[rel]["paths"] if (clone / p).exists()]
        for p in cands:
            if arms >= args.max_arms:
                break
            arms += 1
            target = clone / p
            if target.is_dir():
                shutil.rmtree(str(target), ignore_errors=True)
            else:
                try:
                    target.unlink()
                except OSError:
                    continue
            rc, out, err = run(argv, clone)
            tok = probe_tokens(out, err)
            same = (rc == brc) and (tok == btok)
            verdict = "SURVIVES" if same else "DIES"
            inv = p in obs[rel]["invisible_to_literal_census"]
            rows.append({"instrument": rel, "removed": p, "baseline_exit": brc, "exit": rc,
                         "baseline_probe": sorted(btok), "probe": sorted(tok),
                         "verdict": verdict, "invisible_to_literal_census": inv})
            if verdict == "SURVIVES":
                survivors.append(rows[-1])
            print("     %-8s %-1s exit=%-8s probe=%-28s removed %s"
                  % (verdict, "V" if inv else " ", rc, ",".join(sorted(tok)) or "NONE", p))
            if not reset_and_attest("removal of " + p):
                return 2

    n_inv = sum(len(v["invisible_to_literal_census"]) for v in obs.values())
    n_touch = sum(v["n_touched"] for v in obs.values())
    print("\n  legend: the `V` column marks a dependency INVISIBLE TO THE LITERAL CENSUS --")
    print("          i.e. one only this method could have nominated.")
    print("\n%s instruments=%d touchedPaths=%d invisibleToLiteralCensus=%d removalArms=%d "
          "died=%d survived=%d survivedAndInvisible=%d"
          % (PROBE, len(targets), n_touch, n_inv, len(rows),
             sum(1 for r in rows if r["verdict"] == "DIES"),
             len(survivors),
             sum(1 for r in survivors if r["invisible_to_literal_census"])))
    print("NOTE: SURVIVES is a CANDIDATE, not a finding. An instrument may touch a path it does")
    print("      not depend on. Every row is printed with its exit and probe reading so the")
    print("      adjudication is checkable rather than asserted (T316's four innocent reasons).")

    Path(args.json).write_text(json.dumps(
        {"enforced_set": targets, "named_but_absent": missing, "observed": obs, "arms": rows},
        indent=2))
    shutil.rmtree(str(tmp), ignore_errors=True)
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
