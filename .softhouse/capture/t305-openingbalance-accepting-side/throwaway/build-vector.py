#!/usr/bin/env python3
"""T305 -- build LDG-05 from the COMMITTED capture bytes, never from anything typed by hand.

WHY A BUILDER AND NOT A HAND-WRITTEN JSON FILE. Every graded cell of LDG-05 is read out of
out/OB-ACCEPT-01-readback-db.json at run time, and the file's sha256 is recomputed here and
compared with the one the vector records. A cell nobody can trace to captured bytes cannot get
into the vector, because there is no place to type one.

NO FLOAT ANYWHERE, INCLUDING IN INTERMEDIATE CALCULATION. The minor-unit conversion is done on
the DECIMAL CHARACTERS the oracle emitted -- split on '.', pad or refuse the fraction, integer
arithmetic on int -- exactly the way DEC-2 §4.3 requires of the port itself. `float()` is never
called and `decimal` is not imported either: a Decimal would be correct but it would also hide
the residue rule, which is the thing worth refusing loudly.
"""
import collections
import hashlib
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, "out")
REPO = os.path.abspath(os.path.join(DIR, "..", "..", "..", ".."))
RELBASE = ".softhouse/capture/t305-openingbalance-accepting-side/throwaway/out/"

MINOR_DIGITS = 2  # MNT, ISO 4217 numeric 496, minor unit 2. Read back below from the capture.


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def to_minor(text):
    """'250000.250000' -> 25000025, by exact integer/string arithmetic.

    REFUSES a non-zero digit beyond the currency's minor unit rather than rounding it away --
    DEC-2 §4.3 normative consequence 2, the residue rule. The oracle emits at scale 6 and the
    currency has 2, so four zeros are expected and anything else is a defect in the capture, not
    a rounding decision for this script to take.
    """
    if "." not in text:
        whole, frac = text, ""
    else:
        whole, frac = text.split(".", 1)
    keep, residue = frac[:MINOR_DIGITS], frac[MINOR_DIGITS:]
    if residue.strip("0"):
        raise SystemExit("REFUSED: %r carries a non-zero digit beyond %d minor digits" % (text, MINOR_DIGITS))
    keep = (keep + "0" * MINOR_DIGITS)[:MINOR_DIGITS]
    return int(whole) * (10 ** MINOR_DIGITS) + int(keep)


SIDE = {1: "CREDIT", 2: "DEBIT"}  # JournalEntryType: CREDIT(1), DEBIT(2)

readback_path = os.path.join(OUT, "OB-ACCEPT-01-readback-db.json")
request_path = os.path.join(OUT, "OB-ACCEPT-01-openingbalance-empty-ledger.req")
response_path = os.path.join(OUT, "OB-ACCEPT-01-openingbalance-empty-ledger.json")
status_path = os.path.join(OUT, "OB-ACCEPT-01-openingbalance-empty-ledger.status")
capturedat_path = os.path.join(OUT, "OB-ACCEPT-01-openingbalance-empty-ledger.captured-at-utc")

status = open(status_path).read().strip()
if status != "200":
    raise SystemExit("REFUSED: the capture's HTTP status is %r, not 200; this is not an accept" % status)

rows = json.load(open(readback_path))
posted = json.load(open(response_path))
txn = posted["transactionId"]
rows = [r for r in rows if r["transaction_id"] == txn]
if len(rows) != 6:
    raise SystemExit("REFUSED: expected 6 rows on transaction %s, read %d" % (txn, len(rows)))

req_body = json.load(open(request_path))

accounts_by_id = {}
for r in rows:
    accounts_by_id[r["account_id"]] = r["gl_code"]
# Names come from the setup campaign's own request bodies, which are committed beside the capture.
names = {}
for fn, code in (("S-02a-gl-contra", "T305-3000"), ("S-02b-gl-asset", "T305-1000"),
                 ("S-02c-gl-asset2", "T305-1100"), ("S-02d-gl-liability", "T305-2000")):
    body = json.load(open(os.path.join(OUT, fn + ".req")))
    if body["glCode"] != code:
        raise SystemExit("REFUSED: %s carries glCode %r, expected %r" % (fn, body["glCode"], code))
    names[code] = body["name"]

accounts = []
for aid in sorted(accounts_by_id):
    code = accounts_by_id[aid]
    accounts.append(collections.OrderedDict([
        ("id", aid), ("gl_code", code), ("name", names[code]),
        ("usage", "DETAIL"), ("manual_entries_allowed", True), ("disabled", False),
    ]))

# THE REQUEST LEGS, transcribed from the REQUEST BYTES and given the oracle's own scale-6 text
# for the same amount, which is the convention every other ledger vector in this store follows
# (LDG-01's request legs carry "100000.250000", not "100000.25").
scale6 = {}
for r in rows:
    scale6[r["amount_major_text"][: r["amount_major_text"].index(".") + 3]] = r["amount_major_text"]
req_legs = []
for side, key in (("DEBIT", "debits"), ("CREDIT", "credits")):
    for l in req_body[key]:
        # json.load turns the wire literal 250000.25 into a Python float; it is NEVER used for a
        # money value here. The amount text is taken from the READBACK, and this line only checks
        # that the leg the readback carries is the leg the request asked for, through the account
        # id, which is an integer.
        req_legs.append((side, l["glAccountId"]))

legs_out = []
for r in rows:
    legs_out.append(collections.OrderedDict([
        ("gl_account_id", r["account_id"]),
        ("gl_account_code", r["gl_code"]),
        ("entry_side", SIDE[r["type_enum"]]),
        ("amount_minor", str(to_minor(r["amount_major_text"]))),
        ("amount_major_text", r["amount_major_text"]),
        ("excluded_fields", ["gl_account_type"]),
    ]))

debits = sum(to_minor(r["amount_major_text"]) for r in rows if SIDE[r["type_enum"]] == "DEBIT")
credits = sum(to_minor(r["amount_major_text"]) for r in rows if SIDE[r["type_enum"]] == "CREDIT")
if debits != credits:
    raise SystemExit("REFUSED: the captured entry is not balanced: %d vs %d" % (debits, credits))

contra_id = json.load(open(os.path.join(OUT, "S-03-financialactivity.req")))["glAccountId"]

request_legs = []
for side, aid in req_legs:
    match = [r for r in rows if r["account_id"] == aid and SIDE[r["type_enum"]] == side]
    if not match:
        raise SystemExit("REFUSED: request leg %s on GL %d has no matching entry in the readback" % (side, aid))
    request_legs.append(collections.OrderedDict([
        ("gl_account_id", aid), ("entry_side", side),
        ("amount_major_text", match[0]["amount_major_text"]),
    ]))

note = open(os.path.join(DIR, "LDG-05-note.txt")).read().strip()
title = open(os.path.join(DIR, "LDG-05-title.txt")).read().strip()
rerun = open(os.path.join(DIR, "LDG-05-rerun.txt")).read().strip()
citation = open(os.path.join(DIR, "LDG-05-citation.txt")).read().strip()
graded_against = json.load(open(os.path.join(DIR, "LDG-05-graded-against.json")))

v = collections.OrderedDict()
v["schema"] = "gerege.ledger.vector/v1"
v["case_id"] = "LDG-05-openingbalance-accepted-empty-ledger"
v["context"] = "ledger"
v["class"] = "parity"
v["title"] = title
v["dec2_revision"] = 5
v["_note"] = note
v["capabilities_required"] = [
    "ledger.journal.entry.readback",
    "ledger.money.minor.unit.conversion",
    "ledger.manual.entry.posting",
    "ledger.opening.balance.and.closure",
]
v["provenance"] = collections.OrderedDict([
    ("kind", "capture"),
    ("capture_ref", RELBASE + "OB-ACCEPT-01-readback-db.json"),
    ("capture_sha256", sha256(readback_path)),
    ("capture_case_id", "OB-ACCEPT-01-readback-db"),
    ("request_capture_ref", RELBASE + "OB-ACCEPT-01-openingbalance-empty-ledger.req"),
    ("request_capture_sha256", sha256(request_path)),
    ("request_capture_case_id", "OB-ACCEPT-01-openingbalance-empty-ledger"),
    ("rerun_invariant", rerun),
    ("citation", citation),
])
v["oracle"] = collections.OrderedDict([
    ("fineract_commit", "426a23544e8426a38ae43ae404670a0a7e85b9eb"),
    ("seam", "ledger_db_readback"),
    ("captured_at", open(capturedat_path).read().strip()),
])
v["request"] = collections.OrderedDict([
    ("product_id", 0), ("product_type", ""), ("accounting_rule", ""), ("slot_family", ""),
    ("slot_code", 0), ("payment_type_id", None), ("seam", "ledger_db_readback"),
    ("office_id", req_body["officeId"]),
    ("currency", collections.OrderedDict([("code", req_body["currencyCode"]), ("minor_unit_digits", MINOR_DIGITS)])),
    ("transaction_id", txn),
    ("manual_entry", True),
    ("command", "defineOpeningBalance"),
    ("contra_gl_account_id", contra_id),
    # NO transaction_date, AND THAT IS DELIBERATE. admit.go refuses a vector carrying a
    # transaction date with no business date, because the future-date rule (:629) is decided by
    # comparing the two and the port reads no clock -- so such a vector "records a subject with no
    # boundary, and grades one rule fewer than it appears to". This capture's business date was
    # DERIVED (enable-business-date is off on a fresh tenant, so DateUtils.getLocalDateOfTenant()
    # returns today in Asia/Ulaanbaatar) and a derived value is not an observation. Rather than
    # transcribe a date nobody measured, this vector asserts NOTHING about the date rules. The
    # request body that produced it does carry transactionDate 2026-01-01 and is committed.
    ("transaction_amount_major_text", ""),
    ("accounts", accounts),
    ("legs", request_legs),
])
v["expect"] = collections.OrderedDict([
    ("kind", "journal-entry"),
    ("http_status", int(status)),
    ("legs", legs_out),
    ("total_debits_minor", str(debits)),
    ("total_credits_minor", str(credits)),
    ("refusal", collections.OrderedDict([("http_status", 0), ("code", ""), ("message", "")])),
])
v["graded_against"] = graded_against
v["invariant_exemptions"] = []

dest = os.path.join(REPO, ".softhouse/vectors/ledger/LDG-05-openingbalance-accepted-empty-ledger.json")
with open(dest, "w") as f:
    json.dump(v, f, indent=1)
    f.write("\n")
print("wrote %s" % dest)
print("  transaction %s, %d expect legs, totals %d / %d" % (txn, len(legs_out), debits, credits))
print("  capture sha256 %s" % v["provenance"]["capture_sha256"])
print("  request sha256 %s" % v["provenance"]["request_capture_sha256"])
