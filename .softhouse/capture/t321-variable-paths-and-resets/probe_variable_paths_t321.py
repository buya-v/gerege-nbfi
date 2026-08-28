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
import signal
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


def run(args, cwd, env=None, timeout=90):
    """Own PROCESS GROUP, and the whole group is killed on timeout.

    `subprocess.run(timeout=)` kills only the direct child and then calls `communicate()` again;
    if a GRANDCHILD still holds the pipe -- and a shell guard that spawns `git grep` always does
    -- that second call blocks forever. Measured here: an instrument that should have been cut
    off at 180 s ran for over ten minutes and the probe could not finish. `timeout(1)` is ABSENT
    ON THIS HOST (T299's defect #3, still true), so the group kill is done directly. A timeout is
    recorded as the string `TIMEOUT` and never as an exit code, so it cannot be silently counted
    as a pass."""
    try:
        pr = subprocess.Popen(args, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env, start_new_session=True)
    except OSError as e:
        return "LAUNCHFAIL", "", str(e)
    try:
        out, err = pr.communicate(timeout=timeout)
        return pr.returncode, out, err
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(pr.pid), signal.SIGKILL)
        except OSError:
            pass
        try:
            out, err = pr.communicate(timeout=15)
        except Exception:
            out, err = "", ""
        return "TIMEOUT", out, err


# ---------------------------------------------------------------------------------------------
# THE ENFORCED SET -- derived, never typed.
# ---------------------------------------------------------------------------------------------
def enforced_set(root: Path):
    """Instruments whose fail-open would change the colour of the conformance bar. DERIVED from
    `conformance.sh`, never typed, from three sources -- and the third is this task's subject
    arriving inside the graded harness itself:

      (a) every script under `.softhouse/guards/` (the wired guards)
      (b) a `.softhouse/` path assigned to a shell local on a NON-COMMENT line whose variable is
          later invoked as `bash "$V"` / `python3 "$V"` / `/usr/bin/python3 "$V"`
      (c) AN ASSEMBLED INVOCATION: `local script="$REPO_ROOT/<dir>/$1"` inside a function, whose
          concrete value only exists once the function's CALL SITES are read. conformance.sh has
          one, `_run_capture_guard`, and it runs TWO HARD-TIER guards through it. Neither of
          those two paths appears as a string literal anywhere in the tree, so T316's census
          cannot see either -- FU-T316-3, in the file that grades the money.

    conformance.sh itself is EXCLUDED FROM THE RUN SET and the exclusion is declared rather than
    quiet: it contacts the reference oracle and takes minutes, so a removal arm under it would
    be a whole bar run per arm.
    """
    conf = root / ".softhouse/conformance.sh"
    if not conf.is_file():
        return [], [], {}
    lines = conf.read_text(errors="replace").splitlines()
    nc = [("" if l.lstrip().startswith("#") else l) for l in lines]
    text_nc = "\n".join(nc)
    INVOKE = r'(?:bash|zsh|python3|/usr/bin/python3)\s+"\$%s"'

    found = {}

    rc, out, err = run(["git", "ls-files", ".softhouse/guards/"], root)
    for f in out.splitlines():
        if f.endswith((".sh", ".py")):
            found[f] = "guards dir (wired)"

    for l in nc:
        for m in re.finditer(r'(\w+)="\$REPO_ROOT/(\.softhouse/[\w./-]+\.(?:sh|py|zsh))"', l):
            var, rel = m.group(1), m.group(2)
            if re.search(INVOKE % re.escape(var), text_nc) and (root / rel).is_file():
                found.setdefault(rel, "assigned to `%s` and invoked" % var)

    assembled = {}
    fn = None
    for i, l in enumerate(nc):
        m = re.match(r"^([A-Za-z_]\w*)\(\)\s*\{", l)
        if m:
            fn = m.group(1)
        m2 = re.search(r'(\w+)="\$REPO_ROOT/(\.softhouse/[\w./-]+)/\$(\d)"', l)
        if m2 and fn:
            var, dirpart = m2.group(1), m2.group(2)
            if not re.search(INVOKE % re.escape(var), text_nc):
                continue
            for cl in nc:
                cm = re.match(r"\s*%s\s+(\S+)" % re.escape(fn), cl)
                if cm:
                    arg = cm.group(1).strip('"\'')
                    rel = dirpart + "/" + arg
                    assembled.setdefault(rel, "%s() at line %d, argument $1" % (fn, i + 1))
                    if (root / rel).is_file():
                        found.setdefault(rel, "ASSEMBLED at run time via %s() -- INVISIBLE TO "
                                              "THE LITERAL CENSUS" % fn)

    # THE ARGUMENTS MATTER AS MUCH AS THE PATH. Running a guard with NO ARGUMENTS is not the
    # invocation conformance.sh performs, and a usage error is evidence of nothing -- T316 hit
    # exactly this and printed the caveat beside its own exit-screen figure. So the argv TAIL is
    # derived from the invocation line too: the tokens after `"$VAR"` up to the first redirection
    # or subshell close. `$REPO_ROOT` is substituted; any token still carrying an unresolved `$`
    # is DROPPED and the drop is recorded, never silently passed through as a literal.
    argv_tail = {}
    dropped = {}
    for rel, why in list(found.items()):
        var = None
        m = re.search(r"assigned to `(\w+)`", why)
        if m:
            var = m.group(1)
        elif why.startswith("guards dir"):
            var = "g"
        elif why.startswith("ASSEMBLED"):
            var = "script"
        if not var:
            continue
        for l in nc:
            mm = re.search(r'(?:bash|zsh|python3|/usr/bin/python3)\s+"\$%s"(.*)$'
                           % re.escape(var), l)
            if not mm:
                continue
            tail = mm.group(1)
            tail = re.split(r"[>|)]|2>&1", tail)[0]
            toks, drop = [], []
            for t in re.findall(r'"[^"]*"|\S+', tail):
                t = t.strip('"')
                if not t:
                    continue
                if t == "$REPO_ROOT":
                    toks.append("$REPO_ROOT")
                elif "$" in t:
                    drop.append(t)
                    # a flag whose VALUE was dropped must go too, or the target gets a dangling
                    # `--tool` and usage-errors -- which would look exactly like a refusal.
                    if toks and toks[-1].startswith("-"):
                        drop.append(toks.pop())
                else:
                    toks.append(t)
            if toks and rel not in argv_tail:
                argv_tail[rel] = toks
                if drop:
                    dropped[rel] = drop
            break

    keep = sorted(k for k in found if (root / k).is_file()
                  and k != ".softhouse/conformance.sh")
    absent = sorted(k for k in found if not (root / k).is_file())
    return keep, absent, {"derivation": found, "assembled": assembled,
                          "argv_tail": argv_tail, "argv_dropped": dropped}


def literals_of(path: Path):
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return set()
    return {m.group(2) for m in LITERAL_RE.finditer(text)}


# ---------------------------------------------------------------------------------------------
# PHASE 1 -- the trace
# ---------------------------------------------------------------------------------------------
def trace_once(clone: Path, rel: str, pylib: Path, tracefile: Path, tail=None):
    if tracefile.exists():
        tracefile.unlink()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pylib) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["T321_TRACE_OUT"] = str(tracefile)
    env["PS4"] = PS4
    head = ["python3"] if rel.endswith(".py") else ["bash", "-x"]
    argv = head + [str(clone / rel)] + [
        str(clone) if t == "$REPO_ROOT" else t for t in (tail or [])]
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
    ap.add_argument("--max-per-instrument", type=int, default=8)
    ap.add_argument("--slow-seconds", type=float, default=90.0)
    ap.add_argument("--only", default="",
                    help="restrict the RUN SET to targets matching this ERE. The full derived "
                         "set is still PRINTED, with the excluded rows marked, so a narrowed "
                         "run can never be read as a narrower population.")
    ap.add_argument("--json", default=str(HERE / "evidence/40-varpath.json"))
    args = ap.parse_args()

    guard = ROOT / ".softhouse/guards/repo-state-attest.sh"
    if not guard.is_file():
        print("ERROR: %s absent. The inter-arm reset assertion is IMPORTED, not reimplemented"
              " (T213); without it this run cannot vouch for arm independence. REFUSING."
              % guard, file=sys.stderr)
        return 2

    targets, missing, deriv = enforced_set(ROOT)
    excluded = []
    if args.only:
        rx = re.compile(args.only)
        excluded = [t for t in targets if not rx.search(t)]
        targets = [t for t in targets if rx.search(t)]
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
        print("     %-64s  [%s]" % (t, deriv["derivation"].get(t, "?")))
        at = deriv.get("argv_tail", {}).get(t)
        if at:
            print("        invocation derived from conformance.sh: <script> %s" % " ".join(at))
        if deriv.get("argv_dropped", {}).get(t):
            print("        DROPPED unresolved argument(s), recorded not passed through: %s"
                  % " ".join(deriv["argv_dropped"][t]))
    if excluded:
        print("  EXCLUDED FROM THIS RUN by --only %r (still part of the derived population;"
              % args.only)
        print("  a narrowed run is not a narrower population):")
        for e in excluded:
            print("     %s" % e)
    if missing:
        print("  named but not present in the tree (reported, not silently dropped): %d" % len(missing))
        for m in missing:
            print("     %s" % m)
    print("  scratch: %s" % tmp)

    # `--local` (hardlinked objects), NOT `--no-local`. The safety property that matters is
    # that nothing the clone does can reach the source, and hardlinking preserves it: git never
    # rewrites an existing object file in place, and deleting the clone deletes links, not
    # originals. `--no-local` streams the whole 115 MB pack over the local protocol and was
    # measured at MINUTES per run here, which is what turned this probe into something that
    # could not finish. The trade is speed for nothing.
    rc, out, err = run(["git", "clone", "--quiet", "--local", str(ROOT), str(clone)], tmp,
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
        rc, out, err, touched = trace_once(clone, rel, pylib, tracefile,
                                           deriv.get('argv_tail', {}).get(rel))
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
                    "kinds": {k: sorted(v) for k, v in paths.items()},
                    "invisible_to_literal_census": sorted(invisible),
                    "tracer_loaded": loaded,
                    "probe_tokens": sorted(probe_tokens(out, err))}
        print("  %-52s exit=%-4s touched=%-4d invisible=%-4d tracer=%s"
              % (rel, rc, len(paths), len(invisible),
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
    skipped = []
    arms = 0
    for rel in targets:
        tail = [str(clone) if t == "$REPO_ROOT" else t
                for t in deriv.get("argv_tail", {}).get(rel, [])]
        argv = (["python3"] if rel.endswith(".py") else ["bash"]) + [str(clone / rel)] + tail
        import time as _t
        _t0 = _t.time()
        brc, bout, berr = run(argv, clone)
        _dt = _t.time() - _t0
        btok = probe_tokens(bout, berr)
        print("\n  %s -- BASELINE exit=%s probeTokens=%s wall=%.1fs"
              % (rel, brc, sorted(btok) or "none", _dt))
        if _dt > args.slow_seconds:
            print("     SKIPPING removal arms: this instrument takes %.0fs per run, and each arm"
                  % _dt)
            print("     is a full re-run. DECLARED, not quietly omitted -- the paths it touches")
            print("     are still reported in phase 1, and its removal arms are simply NOT")
            print("     EVIDENCE THAT WAS TAKEN. Raise --slow-seconds to include it.")
            skipped.append({"instrument": rel, "seconds": round(_dt, 1),
                            "candidates": len(obs[rel]["paths"])})
            if not reset_and_attest("baseline of " + rel):
                return 2
            continue
        if not reset_and_attest("baseline of " + rel):
            return 2
        # NOT EVERY TOUCH IS A DEPENDENCY. `50-failopen-lint.py` walks the whole corpus and
        # stat()s 1243 files; removing one of them tests nothing about the lint and would spend
        # the whole budget proving it. So a removal candidate must have been OPENED, READ or
        # EXECUTED -- not merely enumerated -- and the ones INVISIBLE TO THE LITERAL CENSUS go
        # first, because they are the ones only this method could have nominated. The per-
        # instrument cap is PRINTED beside the count so nobody reads the arm total as a
        # population (P-67: both terms, always).
        READKINDS = {"open", "Path.open", "Path.read_text", "Path.read_bytes", "argv", "xtrace"}
        kinds = obs[rel]["kinds"]
        inv = set(obs[rel]["invisible_to_literal_census"])
        pool = [p for p in obs[rel]["paths"] if (clone / p).exists()]
        # ORDER, not a filter. A first version FILTERED to the read-kinds and drove ZERO arms on
        # the five shell guards, whose touches arrive as `xtrace` tokens rather than as a python
        # `open` -- a selector that reported "0 removal arms" and looked like a clean result.
        # Ordering keeps every candidate reachable and lets the cap decide; a path that was
        # OPENED or EXECUTED goes first, then one INVISIBLE to the literal census.
        pool.sort(key=lambda p: (0 if (READKINDS & set(kinds.get(p, []))) else 1,
                                 0 if p in inv else 1, p))
        cands = pool[:args.max_per_instrument]
        print("     candidates: %d existing of %d touched; driving %d (cap %d, ordered "
              "opened/executed first, then invisible-to-literal-census)"
              % (len(pool), obs[rel]["n_touched"], len(cands), args.max_per_instrument))
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
            # A BASELINE THAT ALREADY REFUSES CANNOT DISCRIMINATE. `repo-state-attest.sh` with no
            # arguments exits 2 before it looks at anything, so "the verdict did not change when
            # I deleted the vector store" is a fact about the ARGUMENTS, not about the guard. Six
            # such arms would otherwise have been reported as fail-open candidates -- a
            # wolf-cry against a guard this very task recommends adopting. Called INCONCLUSIVE
            # and counted separately; the fix is to drive it with its real invocation.
            if not same:
                verdict = "DIES"
            elif brc != 0:
                verdict = "INCONCLUSIVE"
            else:
                verdict = "SURVIVES"
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
          "died=%d survived=%d inconclusive=%d survivedAndInvisible=%d"
          % (PROBE, len(targets), n_touch, n_inv, len(rows),
             sum(1 for r in rows if r["verdict"] == "DIES"),
             len(survivors),
             sum(1 for r in rows if r["verdict"] == "INCONCLUSIVE"),
             sum(1 for r in survivors if r["invisible_to_literal_census"])))
    if skipped:
        print("  SKIPPED (too slow to drive one removal at a time), DECLARED not omitted:")
        for sk in skipped:
            print("     %s  %.0fs/run, %d touched paths"
                  % (sk["instrument"], sk["seconds"], sk["candidates"]))
    print("NOTE: SURVIVES is a CANDIDATE, not a finding. An instrument may touch a path it does")
    print("      not depend on. Every row is printed with its exit and probe reading so the")
    print("      adjudication is checkable rather than asserted (T316's four innocent reasons).")

    Path(args.json).write_text(json.dumps(
        {"enforced_set": targets, "named_but_absent": missing,
         "derivation": deriv["derivation"], "assembled_invocations": deriv["assembled"],
         "excluded_by_only": excluded, "only": args.only,
         "observed": obs, "arms": rows, "skipped_too_slow": skipped},
        indent=2))
    shutil.rmtree(str(tmp), ignore_errors=True)
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
