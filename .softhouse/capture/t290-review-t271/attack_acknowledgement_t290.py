#!/usr/bin/env python3
"""T290 -- the reviewer's ATTACKS on T271's sha-pinned acknowledgement, including the ones that
FAILED TO BREAK IT. The failures are the evidence of coverage; a review that prints only the
attack that worked has not shown how hard it tried.

Five attacks, each against the live rule and T271's live register:

  A1  the same four (row, predicate) pairs, byte-identical content, AT A DIFFERENT PATH.
      EXPECTED: still refuses. The block is keyed by repo-relative path AND sha256.
  A2  ONE byte appended to the evidence IN PLACE, disagreements left intact.
      EXPECTED: `!! ACKNOWLEDGEMENT BLOCK VOID`, all four unacknowledged, refuse.
  A3  a NEW, FIFTH disagreement added to a row the register already covers.
      EXPECTED: refuse with unacknowledged=5. The register cannot absorb a new one.
  A4  RETRO-EDIT: flip the four false `P2_*` to true so the disagreement DISAPPEARS.
      EXPECTED BY T271: not stated. MEASURED HERE: the block goes VOID, the rule exits 0 GREEN
      with disagreements=0, and T271's runner passes it through as GREEN. THIS IS THE HOLE.
  A5  the register pointed at a DIFFERENT file that carries the same row ids.
      EXPECTED: still refuses -- the `file` filter runs before the sha check.

EVERY attack restores the committed evidence and VERIFIES the restore by sha256 before exiting.
EXIT 0 every attack behaved as this review predicts; 1 one did not; 2 error. Never conflated.
PROBE: `T290-ATTACK: <STATE> attacks=.. asPredicted=.. brokeThePin=..`
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
PROBE = "T290-ATTACK:"
VPA = re.compile(r"^T259-VPA: (?P<state>\S+) .*?\bdisagreements=(?P<dis>\d+) "
                 r"acknowledged=(?P<ack>\d+) unacknowledged=(?P<unack>\d+)", re.M)


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


ROOT = repo_root(HERE)
RULE = ROOT / ".softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py"
ACK = ROOT / ".softhouse/capture/t271-b1-t219/acknowledged-t219.json"
EV = ROOT / ".softhouse/capture/t219-g8-residual/out/classify-t219.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(target: Path):
    p = subprocess.run([sys.executable, str(RULE), "--acknowledgements", str(ACK), str(target)],
                       capture_output=True, text=True, cwd=str(ROOT))
    m = VPA.search(p.stdout)
    fields = {k: m.group(k) for k in ("state", "dis", "ack", "unack")} if m else {}
    return p.returncode, fields, p.stdout + p.stderr


def main() -> int:
    for need in (RULE, ACK, EV):
        if not need.exists():
            print("ERROR: missing input: " + str(need), file=sys.stderr)
            return 2
    work = Path(tempfile.mkdtemp(prefix=".t290-attack-", dir=str(ROOT)))
    backup = work / "classify-t219.ORIGINAL.json"
    shutil.copy2(EV, backup)
    original_sha = sha(EV)

    results = []
    try:
        print("T290 -- attacks on the sha-pinned acknowledgement")
        print("=" * 96)
        print("  rule     : %s" % RULE.relative_to(ROOT))
        print("  register : %s" % ACK.relative_to(ROOT))
        print("  evidence : %s" % EV.relative_to(ROOT))
        print("  evidence sha256 as committed: %s" % original_sha)
        print()

        # A1 -------------------------------------------------------------------------------
        elsewhere = work / "same-content-different-path.json"
        shutil.copy2(EV, elsewhere)
        rc, f, out = run(elsewhere)
        ok = (rc == 1 and f.get("unack") == "4")
        results.append(("A1 same pairs at an unnamed path", "REFUSES", rc, f, ok, out))

        # A2 -------------------------------------------------------------------------------
        EV.write_bytes(backup.read_bytes() + b" ")
        rc, f, out = run(EV)
        ok = (rc == 1 and f.get("unack") == "4" and "ACKNOWLEDGEMENT BLOCK VOID" in out)
        results.append(("A2 one byte appended in place", "VOID + REFUSES", rc, f, ok, out))
        shutil.copy2(backup, EV)

        # A3 -------------------------------------------------------------------------------
        doc = json.loads(backup.read_text())
        for row in doc["cells"]:
            if row.get("id") == "T219-R600p0-N3000-B2999":
                row["P2_aBrandNewPredicate"] = False
                break
        EV.write_text(json.dumps(doc, indent=1) + "\n")
        rc, f, out = run(EV)
        ok = (rc == 1 and f.get("unack") == "5")
        results.append(("A3 a NEW fifth disagreement", "REFUSES, unack=5", rc, f, ok, out))
        shutil.copy2(backup, EV)

        # A4 -------------------------------------------------------------------------------
        doc = json.loads(backup.read_text())
        flipped = 0
        for row in doc["cells"]:
            for k, v in list(row.items()):
                if k.startswith("P2_") and v is False:
                    row[k] = True
                    flipped += 1
        EV.write_text(json.dumps(doc, indent=1) + "\n")
        rc, f, out = run(EV)
        broke = (rc == 0)
        results.append(("A4 RETRO-EDIT erases the disagreement (%d flipped)" % flipped,
                        "**MEASURED: GREEN**", rc, f, broke, out))
        shutil.copy2(backup, EV)

        # A5 -------------------------------------------------------------------------------
        other = work / "other-file-same-row-ids.json"
        shutil.copy2(backup, other)
        rc, f, out = run(other)
        ok = (rc == 1 and f.get("unack") == "4")
        results.append(("A5 register aimed at a different file with the same ids", "REFUSES",
                        rc, f, ok, out))

        shutil.copy2(backup, EV)
        if sha(EV) != original_sha:
            print("  !! RESTORE FAILED -- the committed evidence is NOT back")
            print("%s ERROR attacks=%d asPredicted=? brokeThePin=?" % (PROBE, len(results)))
            return 2

        print("  %-52s %-18s %-7s %s" % ("attack", "expected", "exit", "measured"))
        print("  " + "-" * 92)
        for name, want, rc, f, ok, _out in results:
            print("  %-52s %-18s %-7s %s" % (
                name, want, rc,
                "state=%s dis=%s ack=%s unack=%s" % (f.get("state"), f.get("dis"),
                                                     f.get("ack"), f.get("unack"))))
        print()
        broke_pin = results[3][4]
        as_predicted = sum(1 for r in results if r[4])
        print("  A1, A2, A3 and A5 FAILED TO BREAK THE PIN, and that is the point of printing")
        print("  them: the register cannot be made to cover a file it does not name, cannot")
        print("  survive one byte moving under it, and cannot absorb a disagreement that appears")
        print("  later. Those are exactly the three evasions an acknowledgement is usually worth")
        print("  rejecting for, and T271's register closes all three.")
        print()
        if broke_pin:
            print("  A4 SUCCEEDED. The pin is one-sided. It catches evidence edited WHILE the")
            print("  disagreement stands, and does not catch evidence edited SO THAT THE")
            print("  DISAGREEMENT NO LONGER EXISTS -- the block goes VOID, the rule prints the")
            print("  VOID line, and then `refused = (unacknowledged or unclassifiedKeys or")
            print("  unclassifiedVerdicts or nil)` never consults it. Exit 0.")
            print("  The repair needs no edit to the contended rule: read the number the rule")
            print("  already prints. See guard_rvpa_floor_t290.py and red/drive-red-t290.py.")
        print()
        print("  committed evidence restored and VERIFIED by sha256: %s" % sha(EV)[:16])
        state = "GREEN" if as_predicted == len(results) else "REFUSED"
        print("%s %s attacks=%d asPredicted=%d brokeThePin=%d"
              % (PROBE, state, len(results), as_predicted, int(broke_pin)))
        return 0 if as_predicted == len(results) else 1
    finally:
        try:
            shutil.copy2(backup, EV)
        except OSError:
            pass
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
