import hashlib, json, subprocess, sys

ROOT = "/tmp/t387/t360"
CAP = ROOT + "/.softhouse/capture/t352-a2-next-tranche/out/T352-A09-residue-3dp-readback-cited.json"
VEC = ROOT + "/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"

mode = sys.argv[1]
if mode == "restore":
    subprocess.check_call(["git", "checkout", "--", ".softhouse/"], cwd=ROOT)
    print("restored")
    sys.exit(0)

raw = open(CAP, "rb").read()
assert raw.count(b"100.125000") >= 1, raw.count(b"100.125000")
mut = raw.replace(b"100.125000", b"100.125001")
open(CAP, "wb").write(mut)

if mode == "with-sha-refreshed":
    doc = json.load(open(VEC))
    doc["provenance"]["capture_sha256"] = hashlib.sha256(mut).hexdigest()
    open(VEC, "w").write(json.dumps(doc, indent=2) + "\n")
    print("capture mutated + vector capture_sha256 refreshed to", doc["provenance"]["capture_sha256"])
else:
    print("capture mutated, sha pin left alone")
