import json, subprocess, sys

ROOT = "/tmp/t387/t360"
DIV = ROOT + "/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"

mode = sys.argv[1]
if mode == "restore":
    subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/"], cwd=ROOT)
    print("restored")
    sys.exit(0)

d = json.load(open(DIV))

if mode == "A15-refusal-for-an-unrelated-reason":
    # The port refuses this request for a reason that has NOTHING to do with the
    # residue: leg 0 points at a GL account the vector's own chart does not carry.
    # The oracle side is untouched and still byte-checks. The marker is the phrase
    # from THAT refusal, 12+ chars, and it is present in observed_text.
    d["request"]["legs"][0]["gl_account_id"] = 99
    d["request"]["accounts"].append({
        "id": 99, "gl_code": "10399", "name": "Not In Chart",
        "usage": "DETAIL", "manual_entries_allowed": True, "disabled": False})
    # ... and then DROP it from accounts so the chart lookup misses.
    d["request"]["accounts"] = [a for a in d["request"]["accounts"] if a["id"] != 99]
    d["expect"]["port_refusal"]["marker"] = "which the vector's chart does not carry"
    d["expect"]["port_refusal"]["observed_text"] = (
        "leg 0 points at GL account 99, which the vector's chart does not carry")

open(DIV, "w").write(json.dumps(d, indent=2) + "\n")
print("planted", mode)
