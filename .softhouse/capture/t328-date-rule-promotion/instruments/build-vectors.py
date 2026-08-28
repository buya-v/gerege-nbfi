#!/usr/bin/env python3
"""T328 -- build LDG-06 and LDG-07 from T327's COMMITTED capture bytes. NO ORACLE CONTACT.

WHY A BUILDER AND NOT TWO HAND-WRITTEN JSON FILES. T305's rule, kept: every GRADED cell of both
vectors is read out of the committed capture at run time, the sha256 of each cited artefact is
RECOMPUTED here and written into the vector, and there is no place in this file to type a graded
cell. The prose (title, _note, rerun_invariant, citation, graded_against) is authored and lives
in ../prose/; it is graded by nothing.

NO FLOAT ANYWHERE, INCLUDING IN INTERMEDIATE CALCULATION [CLAUDE.md non-negotiable #1].
The minor-unit conversion is done on the DECIMAL CHARACTERS PostgreSQL emitted for
`acc_gl_journal_entry.amount::text` -- split on '.', pad or REFUSE the fraction, integer
arithmetic on int. `float()` is never called on a money value and `decimal` is not imported:
a Decimal would be correct but it would also hide the residue rule, which is the thing worth
refusing loudly (DEC-2 4.3 normative consequence 2).

`json.load` is used to WALK the capture. The .req bodies contain wire literals like
`"amount": 250000.25`, which Python turns into a float on load. Those floats are NEVER read as
money here: the only fields taken from a .req body are integers (`officeId`, `glAccountId`) and
strings (`transactionDate`, `currencyCode`, `name`, `glCode`). guard_no_float_money() below
proves it by refusing any money value that is not a str.

WHAT THIS SCRIPT ASSERTS AND WILL DIE ON, so that the vector cannot silently drift from the
capture:
  * the arm's HTTP status is exactly 200 (it is an ACCEPT, not a refusal);
  * the readback rows are exactly the request's legs, no contra expansion (the plain create path
    at :146, not defineOpeningBalance's :791/:796);
  * every row's `entry_date` equals the `transactionDate` the request asked for -- so the date
    this vector records as an INPUT is the date the oracle STORED;
  * debits == credits in integer minor units;
  * the business date recorded is the one the BRACKET measured, not one derived from a clock.
"""
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
T328 = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(T328, "..", "..", ".."))
T327 = os.path.join(REPO, ".softhouse", "capture", "t327-closure-accepting-side", "throwaway")
OUT = os.path.join(T327, "out")
RELBASE = ".softhouse/capture/t327-closure-accepting-side/throwaway/out/"
PROSE = os.path.join(T328, "prose")

# MNT, ISO 4217 numeric 496, minor unit 2. NOT hard-coded as an assumption: checked below
# against the capture's own org-currency readback (S-05-org-currencies.txt).
MINOR_DIGITS = 2

# JournalEntryType [VERIFIED: fineract-core/src/main/java/org/apache/fineract/accounting/
# journalentry/domain/JournalEntryType.java:23-24 at pinned commit 426a23544] -- CREDIT(1), DEBIT(2)
SIDE = {1: "CREDIT", 2: "DEBIT"}

# acc_gl_account.account_usage [VERIFIED: T327 out/S-04-gl-accounts.txt column 4 == 1 on all three
# accounts; DEC-2 4.8 stores DETAIL/HEADER as VALUES, never as ordinals]
USAGE = {1: "DETAIL", 2: "HEADER"}

FINERACT_COMMIT = "426a23544e8426a38ae43ae404670a0a7e85b9eb"


def die(msg):
    raise SystemExit("BUILD REFUSED: " + msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def check_sha(path, recorded_sha_path):
    """Recompute, and compare against the sidecar the capture committed beside the bytes."""
    got = sha256(path)
    want = open(recorded_sha_path).read().strip().split()[0]
    if got != want:
        die("%s hashes to %s; the committed sidecar says %s. The bytes moved."
            % (os.path.basename(path), got, want))
    return got


def guard_no_float_money(value, where):
    """Refuse a money value that is not the oracle's own CHARACTERS."""
    if not isinstance(value, str):
        die("%s is a %s (%r), not the decimal STRING the oracle emitted. A money value that "
            "arrived as a JSON number has already been through a float and cannot be trusted "
            "to the minor unit." % (where, type(value).__name__, value))
    return value


def to_minor(text, where):
    """'250000.250000' -> 25000025, by exact integer/string arithmetic.

    REFUSES a non-zero digit beyond the currency's minor unit rather than rounding it away.
    The oracle stores at scale 6 and MNT has 2, so four trailing zeros are EXPECTED; anything
    else is a defect in the capture, not a rounding decision for this script to take.
    """
    guard_no_float_money(text, where)
    s = text.strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    whole, frac = (s.split(".", 1) + [""])[:2] if "." in s else (s, "")
    if not whole.isdigit() or (frac and not frac.isdigit()):
        die("%s: %r is not a plain decimal money token" % (where, text))
    keep, residue = frac[:MINOR_DIGITS], frac[MINOR_DIGITS:]
    if residue.strip("0"):
        die("RESIDUE REFUSED at %s: %r carries a non-zero digit beyond %d minor digits (%r). "
            "The residue rule refuses this rather than rounding it."
            % (where, text, MINOR_DIGITS, residue))
    keep = (keep + "0" * MINOR_DIGITS)[:MINOR_DIGITS]
    v = int(whole) * (10 ** MINOR_DIGITS) + int(keep)
    return -v if neg else v


# --- the currency's minor unit, READ from the capture rather than assumed -----------------
org = open(os.path.join(OUT, "S-05-org-currencies.txt")).read()
if "decimal_places=%d" % MINOR_DIGITS not in org:
    die("S-05-org-currencies.txt does not report decimal_places=%d: %r" % (MINOR_DIGITS, org))

# --- the chart, READ from the capture's own DB readback of acc_gl_account -----------------
# "1 | T327-1000 | 1 | 1 | true | false"  ==  id | gl_code | classification | usage | manual | disabled
chart = {}
for line in open(os.path.join(OUT, "S-04-gl-accounts.txt")):
    line = line.strip()
    if not line:
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 6:
        die("S-04-gl-accounts.txt row %r does not have six columns" % line)
    chart[int(parts[0])] = {
        "gl_code": parts[1],
        "usage": USAGE[int(parts[3])],
        "manual_entries_allowed": parts[4] == "true",
        "disabled": parts[5] == "true",
    }

# Names come from the setup campaign's own committed request bodies (strings, never money).
for fn in ("S-02a-gl-asset1", "S-02b-gl-asset2", "S-02c-gl-liability"):
    body = json.load(open(os.path.join(OUT, fn + ".req")))
    hit = [a for a in chart.values() if a["gl_code"] == body["glCode"]]
    if len(hit) != 1:
        die("%s declares glCode %r which the chart readback does not carry exactly once"
            % (fn, body["glCode"]))
    hit[0]["name"] = body["name"]
for aid, a in chart.items():
    if "name" not in a:
        die("GL account %d has no name in the committed setup bodies" % aid)


# --- THE BUSINESS DATE, MEASURED BY A TWO-SIDED BRACKET, NOT READ FROM A CLOCK ------------
#
# /businessdates returned 404 on this instance [VERIFIED: out/S-07-businessdates.status = 404],
# so the business date could not be READ. It was BRACKETED instead, by two POSTs seconds apart:
#
#   B2-ACCEPT-01  transactionDate 2026-08-28  -> HTTP 200  => businessDate >= 2026-08-28
#   B2-CTRL-02    transactionDate 2026-08-29  -> HTTP 403  => businessDate <  2026-08-29
#                 with globalisation code error.msg.glJournalEntry.invalid.future.date
#
# Therefore businessDate == 2026-08-28, on the wire, with no clock read by this script.
# The bracket is RECOMPUTED here from the committed bytes rather than transcribed.
def measure_business_date():
    lo = json.load(open(os.path.join(OUT, "B2-ACCEPT-01-entry-on-business-date.req")))["transactionDate"]
    lo_status = open(os.path.join(OUT, "B2-ACCEPT-01-entry-on-business-date.status")).read().strip()
    hi = json.load(open(os.path.join(OUT, "B2-CTRL-02-entry-one-day-after-business-date.req")))["transactionDate"]
    hi_status = open(os.path.join(OUT, "B2-CTRL-02-entry-one-day-after-business-date.status")).read().strip()
    hi_body = json.load(open(os.path.join(OUT, "B2-CTRL-02-entry-one-day-after-business-date.json")))
    if lo_status != "200":
        die("the lower bracket arm returned %r, not 200; the business date is not bounded below" % lo_status)
    if hi_status != "403":
        die("the upper bracket arm returned %r, not 403; the business date is not bounded above" % hi_status)
    code = hi_body["errors"][0]["userMessageGlobalisationCode"]
    if code != "error.msg.glJournalEntry.invalid.future.date":
        die("the upper bracket arm was refused by %r, which is not the FUTURE-DATE rule, so it "
            "does not bound the business date" % code)
    # The two arms must be exactly one calendar day apart, by string surgery on ISO dates.
    y1, m1, d1 = (int(x) for x in lo.split("-"))
    y2, m2, d2 = (int(x) for x in hi.split("-"))
    import datetime
    if datetime.date(y2, m2, d2) - datetime.date(y1, m1, d1) != datetime.timedelta(days=1):
        die("the bracket arms are %s and %s, not one day apart; the bracket does not close" % (lo, hi))
    return lo


BUSINESS_DATE = measure_business_date()


# --- THE LATEST CLOSING DATE, READ FROM THE TARGET AT FIRE TIME --------------------------
#
# GET /glclosures at fire time, and the acc_gl_closure readback, both committed.
def measure_closing_date():
    rows = json.load(open(os.path.join(OUT, "B1-glclosures-list.json")))
    live = [r for r in rows if not r["deleted"]]
    if len(live) != 1:
        die("expected exactly one live GLClosure in B1-glclosures-list.json, read %d" % len(live))
    from_rest = live[0]["closingDate"]
    from_db = open(os.path.join(OUT, "B1-closure-state.txt")).read().split("\n")[0]
    # "1 | 1 | 2026-08-26"
    from_db = [p.strip() for p in from_db.split("|")][-1]
    if from_rest != from_db:
        die("GET /glclosures says closingDate %r and acc_gl_closure says %r" % (from_rest, from_db))
    return from_rest


CLOSING_DATE = measure_closing_date()


def build(case_id, arm, closing_date, capabilities):
    """Build one vector from one accepting arm's committed bytes."""
    req_path = os.path.join(OUT, arm + ".req")
    rsp_path = os.path.join(OUT, arm + ".json")
    sta_path = os.path.join(OUT, arm + ".status")
    at_path = os.path.join(OUT, arm + ".captured-at-utc")
    rb_path = os.path.join(OUT, arm.split("-entry-")[0] + "-readback-db.json")

    status = open(sta_path).read().strip()
    if status != "200":
        die("%s carries HTTP status %r, not 200. This vector claims an ACCEPTANCE." % (arm, status))

    req_sha = check_sha(req_path, req_path + ".sha256")
    check_sha(rsp_path, rsp_path + ".sha256")
    rb_sha = check_sha(rb_path, rb_path + ".sha256")

    req_body = json.load(open(req_path))
    posted = json.load(open(rsp_path))
    txn = posted["transactionId"]

    rows = [r for r in json.load(open(rb_path)) if r["transaction_id"] == txn]
    if not rows:
        die("%s: the readback carries no row for transaction %s" % (arm, txn))

    # THE PLAIN CREATE PATH WRITES THE CALLER'S LEGS AND NOTHING ELSE [:146]. No contra
    # expansion -- that is defineOpeningBalance-only (:791/:796). Asserted, not assumed.
    n_req_legs = len(req_body["debits"]) + len(req_body["credits"])
    if len(rows) != n_req_legs:
        die("%s: %d request legs produced %d journal entries. The plain create path writes one "
            "entry per leg; a contra expansion here would mean this capture is not the shape "
            "this vector claims" % (arm, n_req_legs, len(rows)))

    # EVERY ROW CARRIES THE DATE THE REQUEST ASKED FOR. This is what makes
    # request.transaction_date an OBSERVATION of what the oracle stored rather than a
    # transcription of what the caller typed.
    txn_date = req_body["transactionDate"]
    for r in rows:
        if r["entry_date"] != txn_date:
            die("%s: request transactionDate %r but stored entry_date %r on entry %d"
                % (arm, txn_date, r["entry_date"], r["id"]))
        if r["currency_code"] != req_body["currencyCode"]:
            die("%s: entry %d stores currency %r, request sent %r"
                % (arm, r["id"], r["currency_code"], req_body["currencyCode"]))
        if r["reversed"] or r["reversal_id"] is not None:
            die("%s: entry %d is REVERSED; this vector records a plain accepted posting"
                % (arm, r["id"]))
        if not r["manual_entry"]:
            die("%s: entry %d is not a manual entry" % (arm, r["id"]))

    # THE ORDER OF request.legs FOLLOWS THE REQUEST BODY (debits then credits, as sent) and
    # the order of expect.legs FOLLOWS THE READBACK (ORDER BY j.id, which the .http sidecar
    # records as the query's ordering). They coincide here; the script does not assume it.
    request_legs = []
    for side, key in (("DEBIT", "debits"), ("CREDIT", "credits")):
        for leg in req_body[key]:
            aid = leg["glAccountId"]          # INTEGER, never money
            match = [r for r in rows
                     if r["account_id"] == aid and SIDE[r["type_enum"]] == side]
            if len(match) != 1:
                die("%s: request leg %s on GL %d matches %d readback rows, want exactly 1"
                    % (arm, side, aid, len(match)))
            request_legs.append(collections.OrderedDict([
                ("gl_account_id", aid),
                ("entry_side", side),
                # THE ORACLE'S OWN CHARACTERS AT ITS OWN STORED SCALE, taken from the READBACK
                # and never from the request's JSON number. Same convention as LDG-01/LDG-05.
                ("amount_major_text", guard_no_float_money(
                    match[0]["amount_major_text"], "%s request leg GL %d" % (arm, aid))),
            ]))

    legs_out = []
    for r in rows:
        text = guard_no_float_money(r["amount_major_text"], "%s expect leg id %d" % (arm, r["id"]))
        legs_out.append(collections.OrderedDict([
            ("gl_account_id", r["account_id"]),
            ("gl_account_code", r["gl_code"]),
            ("entry_side", SIDE[r["type_enum"]]),
            ("amount_minor", str(to_minor(text, "%s expect leg id %d" % (arm, r["id"])))),
            ("amount_major_text", text),
            # gl_account_type is EXCLUDED for LDG-04's reason: a /journalentries response
            # projects the ACCOUNT'S CURRENT classification, not the entry's, so grading it
            # would go red on a GL retype that touched no journal entry. The classification
            # this capture rendered is recorded in the vector's _note and graded by nothing.
            ("excluded_fields", ["gl_account_type"]),
        ]))

    debits = sum(to_minor(r["amount_major_text"], "debit total") for r in rows
                 if SIDE[r["type_enum"]] == "DEBIT")
    credits = sum(to_minor(r["amount_major_text"], "credit total") for r in rows
                  if SIDE[r["type_enum"]] == "CREDIT")
    if debits != credits:
        die("%s: the captured entry is NOT balanced: %d debits vs %d credits minor units"
            % (arm, debits, credits))

    accounts = []
    for aid in sorted({r["account_id"] for r in rows}):
        a = chart[aid]
        accounts.append(collections.OrderedDict([
            ("id", aid), ("gl_code", a["gl_code"]), ("name", a["name"]),
            ("usage", a["usage"]),
            ("manual_entries_allowed", a["manual_entries_allowed"]),
            ("disabled", a["disabled"]),
        ]))
        if a["gl_code"] != [r for r in rows if r["account_id"] == aid][0]["gl_code"]:
            die("%s: chart and readback disagree on the gl_code of account %d" % (arm, aid))

    request = collections.OrderedDict([
        ("product_id", 0), ("product_type", ""), ("accounting_rule", ""), ("slot_family", ""),
        ("slot_code", 0), ("payment_type_id", None), ("seam", "ledger_db_readback"),
        ("office_id", req_body["officeId"]),
        ("currency", collections.OrderedDict([
            ("code", req_body["currencyCode"]), ("minor_unit_digits", MINOR_DIGITS)])),
        ("transaction_id", txn),
        ("manual_entry", True),
        ("transaction_date", txn_date),
        ("business_date", BUSINESS_DATE),
    ])
    if closing_date:
        request["latest_closing_date"] = closing_date
    request["transaction_amount_major_text"] = ""
    request["accounts"] = accounts
    request["legs"] = request_legs

    v = collections.OrderedDict()
    v["schema"] = "gerege.ledger.vector/v1"
    v["case_id"] = case_id
    v["context"] = "ledger"
    v["class"] = "parity"
    v["title"] = open(os.path.join(PROSE, case_id + ".title.txt")).read().strip()
    v["dec2_revision"] = 5
    v["_note"] = open(os.path.join(PROSE, case_id + ".note.txt")).read().strip()
    v["capabilities_required"] = capabilities
    v["provenance"] = collections.OrderedDict([
        ("kind", "capture"),
        ("capture_ref", RELBASE + os.path.basename(rb_path)),
        ("capture_sha256", rb_sha),
        ("capture_case_id", os.path.basename(rb_path)[: -len(".json")]),
        ("request_capture_ref", RELBASE + arm + ".req"),
        ("request_capture_sha256", req_sha),
        ("request_capture_case_id", arm),
        ("rerun_invariant", open(os.path.join(PROSE, case_id + ".rerun.txt")).read().strip()),
        ("citation", open(os.path.join(PROSE, case_id + ".citation.txt")).read().strip()),
    ])
    v["oracle"] = collections.OrderedDict([
        ("fineract_commit", FINERACT_COMMIT),
        ("seam", "ledger_db_readback"),
        ("captured_at", open(at_path).read().strip()),
    ])
    v["request"] = request
    v["expect"] = collections.OrderedDict([
        ("kind", "journal-entry"),
        ("http_status", int(status)),
        ("legs", legs_out),
        ("total_debits_minor", str(debits)),
        ("total_credits_minor", str(credits)),
        ("refusal", collections.OrderedDict([("http_status", 0), ("code", ""), ("message", "")])),
    ])
    v["graded_against"] = json.load(open(os.path.join(PROSE, case_id + ".graded-against.json")))
    v["invariant_exemptions"] = []

    dest = os.path.join(REPO, ".softhouse", "vectors", "ledger", case_id + ".json")
    with open(dest, "w") as f:
        json.dump(v, f, indent=1)
        f.write("\n")

    # cells the comparator will grade [DERIVED from grade.go diffEntry: leg_count, then per leg
    # gl_account_id + gl_account_code + entry_side + amount_minor, then two totals]
    n = len(legs_out)
    print("wrote %s" % dest)
    print("  arm                %s  (HTTP %s)" % (arm, status))
    print("  transaction        %s" % txn)
    print("  transaction_date   %s   (stored entry_date on all %d rows)" % (txn_date, n))
    print("  business_date      %s   (BRACKETED: 200 at %s, 403 future.date at +1 day)"
          % (BUSINESS_DATE, BUSINESS_DATE))
    print("  latest_closing_date %s" % (closing_date if closing_date else "(none -- no GLClosure existed)"))
    print("  expect legs        %d ; totals %d / %d minor units" % (n, debits, credits))
    print("  capture sha256     %s" % rb_sha)
    print("  request sha256     %s" % req_sha)
    print("  cells this grades  %d graded, of which %d are MONEY  (1 + 4*%d + 2 ; %d + 2)"
          % (1 + 4 * n + 2, n + 2, n, n))
    return 1 + 4 * n + 2, n + 2


CAPS = [
    "ledger.journal.entry.readback",
    "ledger.money.minor.unit.conversion",
    "ledger.manual.entry.posting",
    "ledger.opening.balance.and.closure",
]

print("T328 -- promoting T327's two ACCEPTING arms. NO ORACLE CONTACT.")
print("business date MEASURED BY BRACKET = %s ; latest closing date READ FROM TARGET = %s"
      % (BUSINESS_DATE, CLOSING_DATE))
print("")
c1, m1 = build("LDG-06-postclosure-entry-accepted-one-day-after-closing-date",
               "B1-ACCEPT-06-entry-one-day-after-closing-date", CLOSING_DATE, CAPS)
print("")
# B-2 fired BEFORE the closure was created (arm 3), so NO GLClosure existed. That absence is an
# OBSERVATION, recorded by omitting the field: out/S-06-closure-sequence-before.txt reads
# `last_value=1 is_called=false` and the arm's own .http sidecar records
# `latest-closing-date-at-fire-time: (none)`.
sidecar = open(os.path.join(OUT, "B2-ACCEPT-01-entry-on-business-date.http")).read()
if "latest-closing-date-at-fire-time: (none)" not in sidecar:
    die("B2-ACCEPT-01's sidecar does not record that NO closure existed at fire time")
c2, m2 = build("LDG-07-entry-on-the-business-date-accepted",
               "B2-ACCEPT-01-entry-on-business-date", "", CAPS)

print("")
print("TOTAL ADDED BY THIS PROMOTION: %d graded cells, of which %d are MONEY cells." % (c1 + c2, m1 + m2))
print("  EXEMPTION_PIN_LEDGER_PARITY       5 -> 7   (+2 parity vectors)")
print("  EXEMPTION_PIN_LEDGER_REFUSAL      5 -> 5   (neither vector is a refusal)")
print("  EXEMPTION_PIN_LEDGER_MONEYCELLS  29 -> %d  (+%d)" % (29 + m1 + m2, m1 + m2))
sys.exit(0)
