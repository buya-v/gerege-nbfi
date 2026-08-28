import json, subprocess, sys, copy

ROOT = "/tmp/t387/t360"
DIV = ROOT + "/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"
LDG01 = ROOT + "/.softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json"

mode = sys.argv[1]
if mode == "restore":
    subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/"], cwd=ROOT)
    print("restored")
    sys.exit(0)

if mode == "A5-oracle-accepted-on-parity":
    # smuggle the unrepresentable observation onto an ordinary PARITY vector
    d = json.load(open(LDG01))
    d["oracle_accepted"] = {
        "http_status": 200,
        "observed_amount_texts": ["100.125000"],
        "why_unrepresentable": "smuggled by T387",
        "gate": "G-19",
    }
    open(LDG01, "w").write(json.dumps(d, indent=2) + "\n")

elif mode == "A10-divergence-relabelled-parity":
    # re-badge the divergence as `parity` -- the way to move it INTO the parity tally
    d = json.load(open(DIV))
    d["class"] = "parity"
    open(DIV, "w").write(json.dumps(d, indent=2) + "\n")

elif mode == "A11-port-refusal-kind-on-parity-class":
    d = json.load(open(DIV))
    d["class"] = "oracle-refusal"
    open(DIV, "w").write(json.dumps(d, indent=2) + "\n")

elif mode == "A12-divergence-with-journal-entry-kind":
    d = json.load(open(DIV))
    d["expect"]["kind"] = "journal-entry"
    open(DIV, "w").write(json.dumps(d, indent=2) + "\n")

elif mode == "A13-marker-not-in-observed-text":
    d = json.load(open(DIV))
    d["expect"]["port_refusal"]["marker"] = "carries sub-minor-unit residue at scale 7"
    open(DIV, "w").write(json.dumps(d, indent=2) + "\n")

elif mode == "A14-gate-empty":
    d = json.load(open(DIV))
    d["oracle_accepted"]["gate"] = ""
    open(DIV, "w").write(json.dumps(d, indent=2) + "\n")
else:
    raise SystemExit("unknown mode " + mode)
print("planted", mode)
