import json, subprocess, sys

ROOT = "/tmp/t387/t360"
DIV = ROOT + "/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"

mode = sys.argv[1]
if mode == "restore":
    subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/"], cwd=ROOT)
    print("restored")
    sys.exit(0)

d = json.load(open(DIV))

if mode == "A16-graded-on-an-unrelated-refusal":
    # THE ORACLE SIDE IS UNTOUCHED: still 100.125000, still byte-checks against the
    # cited readback, still carries a residue beyond the minor unit.
    #
    # THE REQUEST SIDE IS MADE REPRESENTABLE -- "100.12" -- which still satisfies
    # verbatimInCapture, because bytes.Contains finds it as a PREFIX of the
    # captured "100.125".  The port therefore converts it happily and refuses for
    # a completely different reason: the FUTURE-DATE rule.
    for leg in d["request"]["legs"]:
        leg["amount_major_text"] = "100.12"
    d["request"]["business_date"] = "2026-06-01"
    d["request"]["transaction_date"] = "2026-06-02"
    d["expect"]["port_refusal"]["marker"] = "cannot be made for a future date"
    d["expect"]["port_refusal"]["observed_text"] = (
        "The journal entry cannot be made for a future date")

open(DIV, "w").write(json.dumps(d, indent=2) + "\n")
print("planted", mode)
