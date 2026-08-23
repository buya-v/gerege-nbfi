#!/usr/bin/env python3
"""T290 -- RED DRIVE for the guard condition, and for the one T271 specified in its place.

Every leg runs BOTH conditions over the same tree, in the same second, and prints both:

  T271-SPEC   the condition T271 section 5 tells T269 to pin: run `run_rvpa_over_targets.py`,
              require exit 0 and `unacknowledged=0`, and DO NOT pin `disagreements`.
  T290-GUARD  the same runner, plus a committed FLOOR on `disagreements`, plus a refusal on
              `void acknowledgement blocks > 0`.

THE POINT OF THE BATTERY is leg R2: a tree where T271-SPEC is GREEN and T290-GUARD is RED. If that
leg ever shows them agreeing, this whole review's central finding is wrong and must not be quoted.

IT RESTORES THE EVIDENCE IT EDITS, on every exit path including an exception, and VERIFIES the
restoration by sha256 before it exits. Committed evidence is the one thing a red drive may not
leave moved (T114/T176). If the restore check fails the battery exits 2 and says so at the top of
its output.

EXIT: 0 every leg behaved as this review predicts; 1 a leg did not; 2 an instrument or the restore
failed. Never conflated (P-80).
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-REDGREEN:"


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


ROOT = repo_root(HERE)
GUARD = HERE.parent / "guard_rvpa_floor_t290.py"
RUNNER_CANDIDATES = [
    ROOT / ".softhouse/capture/t256-verdict-predicate/run_rvpa_over_targets.py",
    ROOT / ".softhouse/capture/t271-b1-t219/run_rvpa_over_targets.py",
]
EV219 = ROOT / ".softhouse/capture/t219-g8-residual/out/classify-t219.json"
EV229 = ROOT / ".softhouse/capture/t229-g8-site3/out/classify-t229.json"
ACK219 = ROOT / ".softhouse/capture/t271-b1-t219/acknowledged-t219.json"

TARGETS_RE = re.compile(r"^T271-TARGETS: (?P<state>\S+)", re.M)
VPA_RE = re.compile(r"^T259-VPA: \S+ .*?\bdisagreements=(?P<dis>\d+) acknowledged=(?P<ack>\d+) "
                    r"unacknowledged=(?P<unack>\d+)", re.M)
GUARD_RE = re.compile(r"^T290-RVPA-GUARD: (?P<state>\S+)", re.M)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def runner_path():
    for c in RUNNER_CANDIDATES:
        if c.exists():
            return c
    print("ERROR: run_rvpa_over_targets.py is on neither known path. Looked at:", file=sys.stderr)
    for c in RUNNER_CANDIDATES:
        print("         " + str(c), file=sys.stderr)
    return None


def t271_spec(runner: Path):
    """The condition T271 section 5 specifies: exit 0 and unacknowledged=0. No count pin."""
    p = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True,
                       cwd=str(ROOT))
    out = p.stdout + p.stderr
    if not TARGETS_RE.search(out):
        return "ERROR(no probe line)", out
    m = VPA_RE.search(out)
    if not m:
        return "ERROR(no rule probe line)", out
    ok = (p.returncode == 0 and int(m.group("unack")) == 0)
    return ("GREEN" if ok else "REFUSED"), out


def t290_guard():
    p = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True,
                       cwd=str(ROOT))
    out = p.stdout + p.stderr
    m = GUARD_RE.search(out)
    return (m.group("state") if m else "NO-PROBE-LINE"), out


def flip_false_predicates(path: Path) -> int:
    doc = json.loads(path.read_text())
    n = 0
    for container in doc.values():
        if not isinstance(container, list):
            continue
        for row in container:
            if not isinstance(row, dict):
                continue
            for k, v in list(row.items()):
                if k.startswith("P") and "_" in k and v is False:
                    head = k.split("_", 1)[0]
                    if len(head) > 1 and head[1:].isdigit():
                        row[k] = True
                        n += 1
    path.write_text(json.dumps(doc, indent=1) + "\n")
    return n


def append_byte(path: Path) -> int:
    path.write_bytes(path.read_bytes() + b" ")
    return 1


def consistent_two_file_edit() -> int:
    """The move that survives EVERY rule on EVERY branch: retro-edit the evidence AND re-pin the
    register to the new bytes with its rows removed. Nothing is VOID -- there is nothing left to
    void -- so `voidAcks` cannot see it and `unacknowledged=0` is satisfied. Only a FLOOR on
    `disagreements` catches it. Measured against T286's rewritten rule too, in
    `probe_t286_rule_t290.py`: GREEN on both."""
    n = flip_false_predicates(EV219)
    doc = json.loads(ACK219.read_text())
    doc["acknowledgements"][0]["sha256"] = sha(EV219)
    doc["acknowledgements"][0]["rows"] = []
    ACK219.write_text(json.dumps(doc, indent=2) + "\n")
    return n


def main() -> int:
    runner = runner_path()
    if runner is None:
        return 2
    for need in (GUARD, EV219, EV229):
        if not need.exists():
            print("ERROR: missing input: " + str(need), file=sys.stderr)
            return 2

    backup = Path(tempfile.mkdtemp(prefix=".t290-red-", dir=str(ROOT)))
    orig = {}
    try:
        for ev in (EV219, EV229, ACK219):
            b = backup / ev.name
            shutil.copy2(ev, b)
            orig[ev] = (sha(ev), b)

        legs = [
            # name, mutation, expected T271-SPEC, expected T290-GUARD
            ("R1-clean-tree-both-green", None, "GREEN", "GREEN"),
            ("R2-retro-edit-t219-erases-the-disagreement",
             lambda: flip_false_predicates(EV219), "GREEN", "REFUSED"),
            ("R3-retro-edit-BOTH-targets", lambda: (flip_false_predicates(EV219),
                                                    flip_false_predicates(EV229)),
             "GREEN", "REFUSED"),
            ("R4-one-byte-edit-keeps-the-disagreements",
             lambda: append_byte(EV219), "REFUSED", "REFUSED"),
            ("R5-CONSISTENT-two-file-edit-nothing-is-void",
             consistent_two_file_edit, "GREEN", "REFUSED"),
        ]

        print("T290 -- red drive: the invisible route to green that T271's wiring spec leaves open")
        print("=" * 96)
        print("  runner : %s" % runner.relative_to(ROOT))
        print("  guard  : %s" % GUARD.relative_to(ROOT))
        print("  t219   : %s  sha %s" % (EV219.relative_to(ROOT), orig[EV219][0][:16]))
        print("  t229   : %s  sha %s" % (EV229.relative_to(ROOT), orig[EV229][0][:16]))
        print()
        print("  %-46s %-14s %-14s %s" % ("leg", "T271-SPEC", "T290-GUARD", "verdict"))
        print("  " + "-" * 92)

        passed = failed = 0
        rows = []
        for name, mut, want_spec, want_guard in legs:
            for ev, (s, b) in orig.items():          # always start from the committed bytes
                shutil.copy2(b, ev)
            if mut is not None:
                mut()
            got_spec, out_spec = t271_spec(runner)
            got_guard, out_guard = t290_guard()
            ok = (got_spec == want_spec and got_guard == want_guard)
            passed += ok
            failed += (not ok)
            note = "PASS" if ok else ("FAIL wanted %s / %s" % (want_spec, want_guard))
            print("  %-46s %-14s %-14s %s" % (name, got_spec, got_guard, note))
            rows.append((name, got_spec, got_guard, ok, out_guard))

        print()
        for name, gs, gg, ok, out in rows:
            if name.startswith("R2"):
                print("  ---- R2 IN FULL: this is the finding ----")
                for ln in out.splitlines():
                    if ("T259-VPA" in ln or "T271-TARGETS" in ln or "VOID" in ln
                            or "REFUSED:" in ln or "T290-RVPA-GUARD" in ln):
                        print("    " + ln.strip())
                print()

        # restore and VERIFY, before any verdict is printed
        for ev, (s, b) in orig.items():
            shutil.copy2(b, ev)
        bad_restore = [str(ev.relative_to(ROOT)) for ev, (s, b) in orig.items() if sha(ev) != s]
        if bad_restore:
            print("  !! RESTORE FAILED for: " + ", ".join(bad_restore))
            print("%s ERROR legs=%d passed=%d failed=%d restored=0"
                  % (PROBE, len(legs), passed, failed))
            return 2
        print("  committed evidence restored and VERIFIED by sha256: %d of %d"
              % (len(orig), len(orig)))
        print()
        print("  THIS DOES NOT ESTABLISH that T271's acknowledgements are wrong in substance --")
        print("  they are not; the money re-derives. It establishes that the GUARD CONDITION T271")
        print("  specifies for T269 passes a corpus whose committed evidence has been retro-edited")
        print("  to erase the very disagreement the acknowledgement exists to record.")
        state = "REFUSED" if failed else "GREEN"
        print("%s %s legs=%d passed=%d failed=%d restored=%d"
              % (PROBE, state, len(legs), passed, failed, len(orig)))
        return 1 if failed else 0
    finally:
        for ev, (s, b) in orig.items():
            try:
                shutil.copy2(b, ev)
            except OSError:
                pass
        shutil.rmtree(backup, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
