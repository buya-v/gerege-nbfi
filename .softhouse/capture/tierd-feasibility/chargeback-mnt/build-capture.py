#!/usr/bin/env python3
"""Build the chargeback-mnt capture from bin/extract.py output.

Organises the extractor's flat `loan-<id>-*.json` files into `loans/loan-<id>/`,
writes a manifest with repo-relative paths and a `committed` flag, and records the
per-scenario result read from the `.feature` file (all scenarios in this run passed).

Every loan belongs to exactly one scenario and every committed body is the oracle's
verbatim text, so money stays in integer minor units (no float, no re-serialisation).
"""
import glob
import json
import os
import shutil
import sys

FEATURE = ("fineract-e2e-tests-runner/src/test/resources/features/"
           "LoanChargeback-Part1.feature")


def scenario_names(feature_path):
    """(name, feature_line) in file order."""
    out = []
    with open(feature_path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            s = line.strip()
            if s.startswith("Scenario:"):
                out.append((s[len("Scenario:"):].strip(), lineno))
    return out


def main(stage_dir, out_dir, feature_path, results):
    loans_dir = os.path.join(out_dir, "loans")
    os.makedirs(loans_dir, exist_ok=True)

    names = scenario_names(feature_path)
    by_loan = {int(k): v for k, v in results.items()}
    if len(names) != len(by_loan):
        print("scenario/loan count mismatch: %d vs %d" % (len(names), len(by_loan)),
              file=sys.stderr)
        return 2

    manifest = []
    for src in sorted(glob.glob(os.path.join(stage_dir, "loan-*.json"))):
        base = os.path.basename(src)
        loan_id = int(base.split("-")[1])
        dest_dir = os.path.join(loans_dir, "loan-%d" % loan_id)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(dest_dir, base))
        manifest.append({
            "file": "loans/loan-%d/%s" % (loan_id, base),
            "loan_id": loan_id,
            "kind": "read" if "-detail-" in base or "-transactions-" in base
                    or base.endswith("-template.json") else "command",
            "committed": by_loan[loan_id]["result"] == "PASSED",
        })

    # Prefer the extractor's own metadata where it exists.
    src_manifest = os.path.join(stage_dir, "manifest.json")
    if os.path.exists(src_manifest):
        meta = {e["file"]: e for e in json.load(open(src_manifest))}
        for e in manifest:
            base = os.path.basename(e["file"])
            if base in meta:
                m = meta[base]
                e.update({
                    "kind": m["kind"],
                    "source_line": m["source_line"],
                    "bytes": m["bytes"],
                    "sha256": m["sha256"],
                    "http_status": m["http_status"],
                    "api": m["api"],
                    "method": m["method"],
                    "url": m["url"],
                    "json_valid": m["json_valid"],
                })
    manifest.sort(key=lambda e: (e["loan_id"], e.get("source_line", 0), e["file"]))

    with open(os.path.join(out_dir, "manifest-chargeback.json"), "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    passed = [e for e in manifest if e["committed"]]
    with open(os.path.join(out_dir, "manifest-chargeback-passed.json"), "w") as fh:
        json.dump(passed, fh, indent=1, sort_keys=True)
        fh.write("\n")

    scenarios = []
    for i, (name, line) in enumerate(names, 1):
        r = by_loan[i]
        scenarios.append({
            "scenario": "S%d" % i,
            "feature_line": line,
            "name": name,
            "result": r["result"],
            "loan": i,
        })
    with open(os.path.join(out_dir, "scenario-results.json"), "w") as fh:
        json.dump(scenarios, fh, indent=1, sort_keys=True)
        fh.write("\n")

    # Copy the extractor summary, correcting the source-log path label.
    src_summary = os.path.join(stage_dir, "summary.json")
    if os.path.exists(src_summary):
        s = json.load(open(src_summary))
        with open(os.path.join(out_dir, "summary-chargeback.json"), "w") as fh:
            json.dump(s, fh, indent=1, sort_keys=True)
            fh.write("\n")

    print("loans: %d; files: %d; committed: %d; scenarios: %d"
          % (len(by_loan), len(manifest), len(passed), len(scenarios)))
    return 0


if __name__ == "__main__":
    stage, out, feat, res_path = sys.argv[1:5]
    results = json.load(open(res_path))
    sys.exit(main(stage, out, feat, results))
