#!/usr/bin/env python3
"""T316 -- of the instruments that name a DEAD path, how many exit 0 anyway?

This is the second half of FU-T299-2's question. The census (`census_dead_paths.py`) answers
"how many name a path that does not resolve". This answers "and how many report success while
doing it".

WHAT THIS IS, AND -- MORE IMPORTANTLY -- WHAT IT IS NOT.

  IT IS a SCREEN. It runs each instrument once, with no arguments, and records the exit status.
  IT IS NOT a verdict that an instrument is fail-open. An instrument can name a dead path and
  exit 0 for at least four innocent reasons:

      (a) the dead literal is one CANDIDATE in an ordered fallback list and a later one resolved
          -- this is exactly `guard_rvpa_floor_t290.py`, and it is why FU-T299-2's premise is
          wrong;
      (b) the dead literal is an OUTPUT path the instrument is about to create;
      (c) the dead literal is scratch/temp that is expected to be absent;
      (d) the dead literal appears in a docstring or a help string.

  So `exit 0 with a dead literal` is a SHORTLIST TO INSPECT BY HAND, never a finding. Every
  number this prints is a screen width, and the file says so beside the number. Reporting the
  screen as a defect count would be manufacturing findings, which is the failure mode this whole
  task is about.

RUN IT IN A THROWAWAY CLONE. It executes 100+ arbitrary instruments, several of which are red
drives that mutate committed evidence and restore it. Never run it against a tree you care about.

`timeout(1)` IS ABSENT ON THIS HOST [verified: `command -v timeout` and `gtimeout` both empty],
which is T299's own defect #3 -- a wrapper that is not installed makes every probe exit 127 and
the drive reports "nothing changed" having executed nothing. subprocess's own `timeout=` is used
instead, and a timeout is recorded as TIMEOUT, never as an exit code.

EXIT: 0 screen completed; 2 setup failure. Probe line `T316-EXITSCREEN:`; absent on exit 2.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROBE = "T316-EXITSCREEN:"
PER_INSTRUMENT_TIMEOUT_S = 20


def repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor", file=sys.stderr)
    raise SystemExit(2)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="exit-behaviour screen over the dead-path census")
    ap.add_argument("--census", required=True,
                    help="the JSON written by `census_dead_paths.py --json`")
    ap.add_argument("--json", default=None, help="write the screen result here (opt-in)")
    args = ap.parse_args(argv)

    root = repo_root()
    # THE FAIL DIRECTION, in the instrument that measures fail direction: a dependency that does
    # not resolve is a REFUSAL, never an empty screen.
    census = Path(args.census)
    if not census.exists():
        print("ERROR: the census JSON does not resolve: %s" % census, file=sys.stderr)
        print("ERROR: REFUSING (exit 2). Run `census_dead_paths.py --json <path>` first.",
              file=sys.stderr)
        return 2
    doc = json.loads(census.read_text())
    targets = doc["deadFiles"]
    if not targets:
        print("ERROR: the census lists zero dead files. Nothing to screen, and that is a "
              "suspicious input rather than a clean one.", file=sys.stderr)
        return 2

    results = []
    for i, rel in enumerate(targets, 1):
        print("  [%d/%d] %s" % (i, len(targets), rel), flush=True)
        p = root / rel
        if not p.exists():
            results.append({"file": rel, "status": "MISSING", "exit": None})
            continue
        cmd = [sys.executable, str(p)] if rel.endswith(".py") else ["bash", str(p)]
        try:
            proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                                  timeout=PER_INSTRUMENT_TIMEOUT_S)
            results.append({"file": rel, "status": "RAN", "exit": proc.returncode,
                            "stdoutBytes": len(proc.stdout), "stderrBytes": len(proc.stderr)})
        except subprocess.TimeoutExpired:
            results.append({"file": rel, "status": "TIMEOUT", "exit": None})
        except OSError as exc:
            results.append({"file": rel, "status": "OSERROR", "exit": None,
                            "error": "%s: %s" % (type(exc).__name__, exc)})

    ran = [r for r in results if r["status"] == "RAN"]
    zero = [r for r in ran if r["exit"] == 0]
    nonzero = [r for r in ran if r["exit"] != 0]
    timeouts = [r for r in results if r["status"] == "TIMEOUT"]
    oserr = [r for r in results if r["status"] == "OSERROR"]

    print("T316 -- exit behaviour of the instruments that name a DEAD path")
    print("=" * 88)
    print("SCREEN DEFINITION (this is a shortlist, not a finding -- see the module docstring)")
    print("  input      : deadFiles from %s  -> %d instrument(s)" % (census, len(targets)))
    print("  invocation : each run ONCE, NO ARGUMENTS, cwd = repo root")
    print("  timeout    : %ds, via subprocess (timeout(1) is ABSENT on this host)"
          % PER_INSTRUMENT_TIMEOUT_S)
    print("  CAVEAT     : a no-argument run is not every instrument's intended invocation.")
    print("               Some need flags and exit non-zero on usage; that is correct behaviour")
    print("               and is NOT evidence of anything. Counted, not judged.")
    print()
    print("RESULTS (both terms -- P-67)")
    print("  ran to completion : %d" % len(ran))
    print("    exited 0        : %d   <- THE SHORTLIST" % len(zero))
    print("    exited non-zero : %d" % len(nonzero))
    print("  timed out         : %d" % len(timeouts))
    print("  failed to launch  : %d" % len(oserr))
    print()
    print("THE SHORTLIST -- named a dead path AND exited 0")
    print("-" * 88)
    for r in sorted(zero, key=lambda x: x["file"]):
        print("  %s" % r["file"])
        for d in doc["perFile"][r["file"]]["dead"]:
            print("      dead-> %s" % d)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"results": results,
                                   "shortlist": sorted(r["file"] for r in zero)},
                                  indent=2, sort_keys=True) + "\n")
        print()
        print("  JSON written to %s" % out)
    print()
    print("%s screened=%d ran=%d exit0=%d nonzero=%d timeout=%d launchFail=%d"
          % (PROBE, len(targets), len(ran), len(zero), len(nonzero), len(timeouts), len(oserr)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
