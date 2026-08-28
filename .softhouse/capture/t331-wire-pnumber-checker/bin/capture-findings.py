#!/usr/bin/env python3
"""T331 -- capture the checker's findings as REDACTED data, and say why.

THE DEFECT THIS EXISTS TO AVOID, WHICH T331 COMMITTED ONCE AND MEASURED.
T331's first commit checked in the checker's raw `--json` dump and its `--show all`
transcript. Both are VERBATIM TRANSCRIPTS OF EVERY CITATION LINE IN THE REPO, gloss text
included. The moment they were tracked, `git ls-files` handed them straight back to the
checker and the corpus went 9,016 -> 29,684 sites, evidence MISDIRECTING 58 -> 2,897.
Measured, not predicted: .softhouse/capture/t331-wire-pnumber-checker/out/50-*.txt.

That is exactly the reason check-pnumber-citations.py already skips its OWN out/ directory
-- "grading it would double-count every site in the program and grade this instrument against
its own printout; that is a self-reference, not a measurement". But its skip list is a
HARD-CODED PATH PREFIX TUPLE naming only t282-pnumber-drift, so no other task can inherit the
protection, and T331 does not own that file. FILED AS FU-T331-3.

So T331 redacts instead of exempting. This writes a findings file carrying every field its
instruments actually consume -- file, line, kind, cited, best, zone, fatal, high_confidence,
grams, score, cited_score -- and DROPS the three free-text fields that make the file a
citation dump: `detail`, `gloss`, `text`. Nothing is lost that cannot be re-derived by
re-running the checker, and the command that does so is printed into the file itself.

FAIL-CLOSED: the raw JSON is written OUTSIDE the repository (a mkdtemp) so an interrupted run
cannot leave an unredacted dump in the tree, and this script refuses if the checker did not
produce parseable JSON.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3].parent
CHK = ROOT / ".softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"
OUT = ROOT / ".softhouse/capture/t331-wire-pnumber-checker/baseline/10-findings-redacted.json"
DROP = ("detail", "gloss", "text")


def main():
    if not CHK.is_file():
        print("T331-CAPTURE: REFUSED -- checker absent at %s" % CHK)
        return 1
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="t331-findings."))
    try:
        raw = tmp / "raw.json"
        r = subprocess.run(["/usr/bin/python3", str(CHK), "--json", str(raw)],
                           cwd=str(ROOT), capture_output=True)
        if not raw.is_file():
            print("T331-CAPTURE: REFUSED -- the checker wrote no JSON (exit %d)." % r.returncode)
            sys.stdout.write(r.stdout.decode("utf-8", "replace")[-2000:])
            sys.stderr.write(r.stderr.decode("utf-8", "replace")[-2000:])
            return 1
        d = json.loads(raw.read_text(encoding="utf-8"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    kept = []
    for f in d["findings"]:
        kept.append({k: v for k, v in f.items() if k not in DROP})
    d["findings"] = kept
    d["_t331_redaction"] = {
        "dropped_fields": list(DROP),
        "why": ("these three fields carry the cited SENTENCE verbatim; committing them makes "
                "this file a citation dump that the wired guard then re-grades, tripling the "
                "corpus. See this script's docstring and FU-T331-3."),
        "regenerate": ("cd <repo> && /usr/bin/python3 "
                       ".softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py "
                       "--json <path-outside-the-repo>"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("T331-CAPTURE: wrote %s -- %d findings, %d free-text fields dropped per finding."
          % (OUT.relative_to(ROOT), len(kept), len(DROP)))
    print("T331-CAPTURE: counts %s" % json.dumps(d["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
