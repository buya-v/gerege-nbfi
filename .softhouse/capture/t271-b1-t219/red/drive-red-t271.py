#!/usr/bin/env python3
"""T271 -- the RED/GREEN battery for B-1.

WHAT IT HAS TO PROVE, and why each leg exists:

  R1  RED, the defect as it stands.   The committed evidence under the acknowledgement register
      as it exists on main REFUSES with `unacknowledged=4`. Driven, not asserted. If this leg
      ever goes green on its own, the fix is being measured against nothing.
  G1  GREEN, the fix.                 The same file under T271's register exits 0 with
      `unacknowledged=0` AND `acknowledged=4` AND `disagreements=4`. The disagreement COUNT MUST
      NOT DROP: an acknowledgement changes the exit code, never the noise. A green with
      `disagreements=0` would mean the rule stopped looking, and this leg fails on it.
  N1  The fix is not "stop looking", path edition. The identical four pairs at a path no
      acknowledgement names must still REFUSE.
  N2  The fix is not "stop looking", BATCHED edition. The real file (acknowledged) together with
      N1's fixture (not) must REFUSE. This is T262's F-1 shape from the other side: an
      acknowledged file must not switch the refusal off for its neighbours.
  N3  P-76 -- a shape the rule was NOT built from. Different container key, different predicate
      family, different verdict word, row keyed by `name`. Must still REFUSE.
  N4  The sha PIN is real. The register with one byte of its recorded sha256 changed must report
      the block VOID and put the rows back to RED. This is T114/T176 enforced mechanically: you
      cannot make the record agree by pointing an acknowledgement at bytes it does not name.
  N5  NIL COVERAGE still refuses. A file with no inspectable row is not a pass.
  G2  A GREEN that cannot be explained by nil coverage: a populated fixture with no disagreement
      exits 0 with rows>0.

FORWARD COMPATIBILITY, AND WHAT IT IS *NOT*. T268 rewrote the rule on another branch. Every leg is
ALSO run against T268's version, extracted by PINNED BLOB SHA, and must reach the same verdict. If
that blob does not resolve the battery says `fwdCompat=SKIPPED` on its probe line and prints it
loudly -- it is never silently treated as passed.

**T268 WAS SUBSEQUENTLY REJECTED, AND `fwdCompat=RAN fwdFailed=0` IS NOT AN ENDORSEMENT OF IT.**
T281 rejected T268 at `b4272ff`: its own F-3 widening made `walk_rows` yield the FIRST inspectable
dict and return, so any accepted top-level key turns the DOCUMENT ROOT into a row (`seen_rows=1`)
and the nil-coverage guard can then never fire on that file. The retry is T286, from `b6f0a77`.
The pinned blob `0607ecd` is T268's rejected version (branch tip `81eb16f`), retained deliberately:
it is the concrete artefact this task's fix must not be broken BY, and re-pinning it to a
not-yet-existing T286 would be pinning a guess. All these legs establish is that T271's
acknowledgement register produces the SAME verdicts under both versions of the rule -- they say
nothing about T268's own defect, which lives in a shape none of these fixtures has. T269 must
re-run this battery against whatever rule it actually wires.

EXIT: 0 every leg passed; 1 at least one leg failed (a REAL measured negative); 2 error.
PROBE LINE (last line, test PRESENCE before VALUE -- P-83):
    T271-REDGREEN: <STATE> legs=.. passed=.. failed=.. fwdCompat=<RAN|SKIPPED> fwdFailed=..
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
T271 = HERE.parent
ROOT = T271.parent.parent.parent
RULE = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate" / "check_verdict_predicate_agreement.py"
REGISTER = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate" / "boolean-key-register.json"
ACK_MAIN = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate" / "acknowledged.json"
ACK_T271 = T271 / "acknowledged-t219.json"
EVIDENCE = ROOT / ".softhouse" / "capture" / "t219-g8-residual" / "out" / "classify-t219.json"
FIX = HERE / "fixtures"
PROBE = "T271-REDGREEN:"
RUNNER_PROBE = "T271-TARGETS:"   # the target-list runner has its own probe line
# T268's rewritten rule, pinned by blob so it survives that branch moving or merging.
T268_BLOB = "0607ecdb943e84c0ad2ae9f16cd79fc702847c3d"
PROBE_RE = re.compile(r"^T259-VPA: (?P<state>\S+) (?P<rest>.*)$", re.M)


class RuleError(Exception):
    """An ERROR (exit 2), never a measured negative."""


def probe_fields(out: str) -> dict:
    m = PROBE_RE.search(out)
    if not m:
        return {}
    d = {"state": m.group("state")}
    for tok in m.group("rest").split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d


def run_rule(rule_path: Path, ack: Path, targets) -> tuple:
    cmd = [sys.executable, str(rule_path), "--register", str(REGISTER),
           "--acknowledgements", str(ack)] + [str(t) for t in targets]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return p.returncode, p.stdout + p.stderr


def extract_t268(work: Path):
    p = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", T268_BLOB],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None
    dst = work / "rvpa_t268.py"
    dst.write_text(p.stdout)
    return dst


def main() -> int:
    for need in (RULE, REGISTER, ACK_MAIN, ACK_T271, EVIDENCE):
        if not need.exists():
            print(f"ERROR: missing input: {need}", file=sys.stderr)
            return 2

    # INSIDE the repo on purpose: the rule locates the repo root by walking up for a `.git`
    # entry, so a copy of it under /tmp exits 2 with "no .git ancestor" and every
    # forward-compatibility leg would look like a divergence when it is an environment artefact.
    # Measured first, then fixed: the first run of this battery reported fwdFailed=8 for exactly
    # that reason and every one of them said `exit 2 state None`.
    work = Path(tempfile.mkdtemp(prefix=".t271-red-", dir=str(ROOT)))
    try:
        # N4's register: T271's, with one hex digit of the pinned sha256 changed.
        ack_bad = work / "acknowledged-t219-WRONG-SHA.json"
        doc = json.loads(ACK_T271.read_text())
        blk = doc["acknowledgements"][0]
        good = blk["sha256"]
        blk["sha256"] = ("0" if good[0] != "0" else "1") + good[1:]
        ack_bad.write_text(json.dumps(doc, indent=2))

        # N5's file: valid JSON, no inspectable row.
        nil = work / "N5-nil-coverage.json"
        nil.write_text('{"_about": "T271 N5: no list of dicts anywhere.", "note": "nothing here"}\n')

        legs = [
            ("R1-red-baseline-as-on-main", ACK_MAIN, [EVIDENCE], 1,
             {"state": "REFUSED", "unacknowledged": "4", "disagreements": "4",
              "acknowledged": "0", "rows": "11", "nilCoverage": "0"}),
            ("G1-green-with-T271-register", ACK_T271, [EVIDENCE], 0,
             {"state": "GREEN", "unacknowledged": "0", "disagreements": "4",
              "acknowledged": "4", "rows": "11", "nilCoverage": "0"}),
            ("N1-same-pairs-at-an-unnamed-path", ACK_T271,
             [FIX / "X1-unacknowledged-elsewhere.json"], 1,
             {"state": "REFUSED", "unacknowledged": "4"}),
            ("N2-batched-acknowledged-plus-not", ACK_T271,
             [EVIDENCE, FIX / "X1-unacknowledged-elsewhere.json"], 1,
             {"state": "REFUSED", "unacknowledged": "4", "acknowledged": "4",
              "disagreements": "8"}),
            ("N3-P76-shape-not-built-from", ACK_T271,
             [FIX / "X2-novel-container-and-predicate.json"], 1,
             {"state": "REFUSED", "unacknowledged": "1", "rows": "1"}),
            ("N4-sha-pin-void-register", ack_bad, [EVIDENCE], 1,
             {"state": "REFUSED", "unacknowledged": "4", "acknowledged": "0"}),
            ("N5-nil-coverage-refuses", ACK_T271, [nil], 1,
             {"state": "REFUSED"}),
            ("G2-populated-clean-green", ACK_T271, [FIX / "X3-clean-populated.json"], 0,
             {"state": "GREEN", "unacknowledged": "0", "disagreements": "0", "rows": "2"}),
        ]

        t268 = extract_t268(work)
        fwd_state = "RAN" if t268 else "SKIPPED"

        print("T271 -- RED/GREEN battery for B-1")
        print("=" * 100)
        print(f"  rule (live)      : {RULE.relative_to(ROOT)}")
        print(f"  rule (fwd-compat): blob {T268_BLOB} -- {fwd_state}")
        print("  NOTE: that blob is T268's REJECTED version (T281 at b4272ff; retry is T286).")
        print("        fwdFailed=0 means T271's register behaves the SAME under both rules. It is")
        print("        NOT a statement that T268 is sound, and T269 must re-run this battery")
        print("        against whichever rule it actually wires.")
        if not t268:
            print("  !! FORWARD-COMPATIBILITY LEGS DID NOT RUN. The T268 blob did not resolve in")
            print("  !! this repository. This is NOT a pass; it is an absence, and the probe line")
            print("  !! says SKIPPED so no reader can mistake it for one.")
        print(f"  evidence         : {blk['file']}")
        print(f"  evidence sha256  : {good}")
        print()

        passed = failed = fwd_failed = 0
        results = []
        for name, ack, targets, want_rc, want in legs:
            rc, out = run_rule(RULE, ack, targets)
            got = probe_fields(out)
            problems = []
            if not got:
                problems.append("NO PROBE LINE (P-83: presence before value)")
            if rc != want_rc:
                problems.append(f"exit {rc}, wanted {want_rc}")
            for k, v in want.items():
                if got.get(k) != v:
                    problems.append(f"{k}={got.get(k)!r}, wanted {v!r}")
            if name == "N4-sha-pin-void-register" and "ACKNOWLEDGEMENT BLOCK VOID" not in out:
                problems.append("the VOID block was not reported in the body")
            if name == "N5-nil-coverage-refuses" and "NIL COVERAGE" not in out:
                problems.append("nil coverage was not named in the body")

            fwd_note = "-"
            if t268:
                frc, fout = run_rule(t268, ack, targets)
                fgot = probe_fields(fout)
                if frc != rc or fgot.get("state") != got.get("state"):
                    fwd_note = f"DIVERGES exit {frc} state {fgot.get('state')!r}"
                    fwd_failed += 1
                else:
                    fwd_note = f"same (exit {frc})"

            ok = not problems
            passed += 1 if ok else 0
            failed += 0 if ok else 1
            results.append((name, rc, "PASS" if ok else "FAIL", problems, fwd_note, out))

        for name, rc, verdict, problems, fwd_note, _out in results:
            print(f"  {verdict}  {name:<38} exit {rc}   fwd-compat: {fwd_note}")
            for p in problems:
                print(f"          -- {p}")
        print()
        print("  THE FOUR, AS THE RED LEG NAMES THEM:")
        for line in results[0][5].splitlines():
            if "*** DISAGREEMENT" in line or line.strip().startswith("recorded predicate"):
                print(f"    {line.strip()}")
        print()
        # ---- the target-list runner T269 is meant to install -------------------------------
        # Driven separately because it wraps the rule rather than being it: its own failure
        # modes are the ones a wiring task will actually hit.
        runner = T271 / "run_rvpa_over_targets.py"
        tlegs = []
        if runner.exists():
            good_targets = T271 / "targets-proposed-for-T269.json"
            tdoc = json.loads(good_targets.read_text())

            missing = work / "targets-missing-file.json"
            md = json.loads(json.dumps(tdoc))
            md["targets"][1]["file"] = ".softhouse/capture/t219-g8-residual/out/NOT-THERE.json"
            missing.write_text(json.dumps(md, indent=2))

            noack = work / "targets-no-register.json"
            nd = json.loads(json.dumps(tdoc))
            nd["targets"] = [t for t in nd["targets"] if "t219" in t["file"]]
            nd["targets"][0]["acknowledgements"] = []
            noack.write_text(json.dumps(nd, indent=2))

            empty = work / "targets-empty.json"
            empty.write_text(json.dumps({"targets": []}, indent=2))

            tlegs = [
                ("T1-targets-green-both-files", good_targets, 0, "GREEN targets=2 inspected=2"),
                ("T2-target-file-not-on-disk-is-ERROR", missing, 2, None),
                ("T3-target-with-no-register-REFUSES", noack, 1, "REFUSED targets=1 inspected=1"),
                ("T4-empty-target-list-REFUSES", empty, 1, "REFUSED targets=0 inspected=0"),
            ]
            for name, tf, want_rc, want_probe in tlegs:
                p = subprocess.run(
                    [sys.executable, str(runner), "--targets", str(tf)],
                    capture_output=True, text=True, cwd=str(ROOT))
                out = p.stdout + p.stderr
                problems = []
                if p.returncode != want_rc:
                    problems.append(f"exit {p.returncode}, wanted {want_rc}")
                if want_probe is None:
                    if f"{RUNNER_PROBE} " in out:
                        problems.append("an ERROR leg printed a T271-TARGETS verdict line")
                else:
                    if f"{RUNNER_PROBE} {want_probe}" not in out:
                        line = next((l for l in out.splitlines() if l.startswith(RUNNER_PROBE)), "<none>")
                        problems.append(f"probe {line!r}, wanted {RUNNER_PROBE} {want_probe}...")
                ok = not problems
                passed += 1 if ok else 0
                failed += 0 if ok else 1
                print(f"  {'PASS' if ok else 'FAIL'}  {name:<38} exit {p.returncode}")
                for pr in problems:
                    print(f"          -- {pr}")
            print()

        total_legs = len(legs) + len(tlegs)
        print("  legs                 : {}  ({} rule, {} target-list runner)".format(
            total_legs, len(legs), len(tlegs)))
        print("  passed               : {}".format(passed))
        print("  failed               : {}".format(failed))
        print("  fwd-compat divergent : {}  ({})".format(fwd_failed, fwd_state))
        print()
        print("  THIS DOES NOT ESTABLISH: that the four acknowledgements are correct in substance")
        print("  -- only that the disagreement is registered, still printed in full, and that the")
        print("  rule still refuses an unacknowledged one. The substance is re-derived separately")
        print("  by rederive_t219_carriers.py, from the raw capture, in integer minor units.")
        print()
        state = "GREEN" if failed == 0 and fwd_failed == 0 else "REFUSED"
        print(f"{PROBE} {state} legs={total_legs} passed={passed} failed={failed} "
              f"fwdCompat={fwd_state} fwdFailed={fwd_failed}")
        return 1 if (failed or fwd_failed) else 0
    except RuleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
