import json, subprocess, sys, os, copy

VEC = "/tmp/t387/t360/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"
orig = open(VEC).read()
doc = json.loads(orig)

attacks = {}

# A1 -- expect.legs populated with a fabricated minor-unit value (T352's 10013)
a = copy.deepcopy(doc)
a["expect"]["legs"] = [
    {"gl_account_id": 16, "entry_side": "DEBIT", "amount_minor": "10013",
     "amount_major_text": "100.125000", "gl_account_code": "10300"},
    {"gl_account_id": 21, "entry_side": "CREDIT", "amount_minor": "10013",
     "amount_major_text": "100.125000", "gl_account_code": "99008"},
]
attacks["A1-expect-legs-10013"] = a

# A2 -- total_*_minor populated
a = copy.deepcopy(doc)
a["expect"]["total_debits_minor"] = "10013"
a["expect"]["total_credits_minor"] = "10013"
attacks["A2-totals-minor"] = a

# A3 -- expect.refusal populated (oracle-observed wire refusal on the port side)
a = copy.deepcopy(doc)
a["expect"]["refusal"] = {"http_status": 422, "code": "error.msg.residue",
                          "message": "residue"}
attacks["A3-expect-refusal"] = a

# A4 -- expect.http_status populated
a = copy.deepcopy(doc)
a["expect"]["http_status"] = 422
attacks["A4-expect-http-status"] = a

# A5 -- oracle_accepted moved onto a PARITY vector (LDG-01)
# handled separately below

# A6 -- observed text mutated by ONE digit (no longer verbatim in the capture)
a = copy.deepcopy(doc)
a["oracle_accepted"]["observed_amount_texts"] = ["100.125001"]
attacks["A6-one-digit-mutated"] = a

# A7 -- a REPRESENTABLE amount wearing the divergence badge (vacuity guard)
a = copy.deepcopy(doc)
a["oracle_accepted"]["observed_amount_texts"] = ["100.120000"]
attacks["A7-representable"] = a

# A8 -- short / vacuous marker
a = copy.deepcopy(doc)
a["expect"]["port_refusal"]["marker"] = "residue"
attacks["A8-short-marker"] = a

name = sys.argv[1]
if name == "restore":
    subprocess.check_call(["git", "checkout", "--",
                           ".softhouse/vectors/ledger/"], cwd="/tmp/t387/t360")
    print("restored")
    sys.exit(0)

open(VEC, "w").write(json.dumps(attacks[name], indent=2) + "\n")
print("planted", name)
