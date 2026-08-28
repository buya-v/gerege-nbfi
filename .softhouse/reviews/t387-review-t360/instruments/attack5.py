import json, subprocess, sys

ROOT = "/tmp/t387/t360"
DIV = ROOT + "/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"

mode = sys.argv[1]
if mode == "restore":
    subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/"], cwd=ROOT)
    print("restored")
    sys.exit(0)

d = json.load(open(DIV))

if mode == "A17-request-prefix-substring":
    # "100.12" is a PREFIX of the captured "100.125", so bytes.Contains finds it and
    # verbatimInCapture is satisfied by a number the caller never sent. Does anything
    # else catch it?
    for leg in d["request"]["legs"]:
        leg["amount_major_text"] = "100.12"

open(DIV, "w").write(json.dumps(d, indent=2) + "\n")
print("planted", mode)
