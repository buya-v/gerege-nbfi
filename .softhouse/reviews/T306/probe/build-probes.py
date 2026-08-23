#!/usr/bin/env python3
"""T306 review probe builder.

Writes four probe vectors into a SCRATCH copy of the store. Nothing under
.softhouse/vectors is touched and no request is sent to the reference oracle.

Every probe reuses REAL committed capture artefacts (path + sha256 + case id)
so that citationReasons cannot be the thing that refuses it -- the measurement
must be about the capability gate at admit.go:300-314 and nothing else.

  P1  ACCEPTANCE, plain create (request.command "")            claims the row
  P2  ACCEPTANCE, request.command "defineOpeningBalance"       claims the row
  P3  REFUSAL declaring codeAccountingClosed, dates consistent,
      but transcribed from a NON-closure capture (A2-346)      claims the row
  P4  REFUSAL declaring codeFutureDate on a defineOpeningBalance
      request -- the two shapes crossed                        claims the row

P1 is the control the driver's comment predicts REFUSED.
P2 is the same acceptance with one request-side field changed.
"""
import json
import os
import sys

store = sys.argv[1]
ROW = "ledger.opening.balance.and.closure"


def load(name):
    with open(os.path.join(store, "ledger", name + ".json")) as fh:
        return json.load(fh)


def write(v, name):
    v["case_id"] = name
    with open(os.path.join(store, "ledger", name + ".json"), "w") as fh:
        fh.write(json.dumps(v, indent=2) + "\n")
    print("wrote", name)


# ---------------------------------------------------------------- P1 and P2
# LDG-01 is a real, committed, ACCEPTED 3-leg manual journal entry on the
# ledger_rest_posting seam -- the only seam that declares "exercised" for this
# row. Adding the row to its capabilities_required is the whole perturbation:
# it is an ACCEPTANCE claiming a capability whose every observation is a
# REFUSAL, which is the FOURTH shape the driver's comment says is refused.
acc = load("LDG-01-manual-je-3leg-minor-units")
acc["capabilities_required"] = list(acc["capabilities_required"]) + [ROW]
acc["title"] = ("PROBE P1 -- an ACCEPTED journal entry claiming " + ROW +
                " on the plain create path. No capture in this store observes an "
                "ACCEPTANCE for this row. The driver's merge comment says this is "
                "refused as DATA.")
p1 = json.loads(json.dumps(acc))
write(p1, "ZZZ-T306-P1-acceptance-plain-create")

# P2: the SAME acceptance, one request-side field flipped to the value arm 1 of
# the gate keys on. contra_gl_account_id is required by admit.go whenever the
# command is defineOpeningBalance, so it is supplied (15 is the real
# financial-activity-300 mapping LDG-REFUSE-03 records on this tenant).
p2 = json.loads(json.dumps(acc))
p2["request"]["command"] = "defineOpeningBalance"
p2["request"]["contra_gl_account_id"] = 15
# REMOVE THE CITATION CONFOUND. LDG-01's capture_ref resolves PART TWO by FILE
# NAME ONLY and its pin is keyed on LDG-01's own case_id, so a renamed copy is
# refused for the citation and the capability gate's answer is hidden behind it.
# LDG-04's response artefact resolves BY ARTEFACT BYTES [admit.go:730], so it
# needs no pin. Swapping it in changes nothing the capability gate reads.
p2["provenance"]["capture_ref"] = \
    ".softhouse/capture/tierA-a2/out/A2-390-db-ledger-state-a2-15.json"
p2["provenance"]["capture_sha256"] = \
    "d694d558fb5956cb1d462a12f8fd9b00d0082f501c98df061b0e43ff515930e8"
p2["provenance"]["capture_case_id"] = "A2-390-db-ledger-state-a2-15"
p2["title"] = ("PROBE P2 -- the SAME ACCEPTANCE as P1 with request.command set to "
               "defineOpeningBalance. Still an acceptance; still no capture in this "
               "store observes one. If P1 is refused and P2 is admitted, the gate is "
               "not refusing ACCEPTANCES at all -- it is refusing plain-create "
               "acceptances only.")
write(p2, "ZZZ-T306-P2-acceptance-openingbalance-command")

# ---------------------------------------------------------------------- P3
# Is the capability claim BOUGHT BY DECLARING AN OUTPUT? A2-346 is the
# manual-adjustments-not-permitted capture. Its vector, LDG-REFUSE-02, does NOT
# and may not claim this row. Here the SAME provenance is kept and only the
# declared refusal code + the three date inputs are changed to the closure
# shape. Nothing in this vector was transcribed from a closure capture.
p3 = load("LDG-REFUSE-02-manual-adjustments-not-permitted")
p3["capabilities_required"] = ["ledger.refusal.parity", ROW]
p3["request"]["transaction_date"] = "2026-01-31"
p3["request"]["business_date"] = "2026-08-23"
p3["request"]["latest_closing_date"] = "2026-01-31"
p3["expect"]["refusal"]["code"] = "error.msg.glJournalEntry.invalid.accounting.closed"
p3["expect"]["refusal"]["message"] = ("Journal entry cannot be made prior to last "
                                      "account closing date for the branch")
p3["title"] = ("PROBE P3 -- the capability claim bought with an OUTPUT DECLARATION. "
               "Provenance, request legs and accounts are A2-346's "
               "manual-adjustments capture, which observes nothing about closures. "
               "Only expect.refusal.code and the three date inputs were edited.")
# graded_against LEFT AS A2-346's so that "graded_against is empty" cannot be
# the reason, and the capability gate's own answer is the one that shows.
write(p3, "ZZZ-T306-P3-code-declared-on-foreign-capture")

# ---------------------------------------------------------------------- P4
# The two shapes crossed: a defineOpeningBalance command declaring the
# FUTURE-DATE code. :717 pre-empts both date guards, so the oracle cannot
# answer the future-date code to a defineOpeningBalance request on a tenant
# with posted entries. Does anything refuse it?
p4 = load("LDG-REFUSE-03-openingbalance-after-posted-entries")
p4["request"]["transaction_date"] = "2026-08-24"
p4["request"]["business_date"] = "2026-08-23"
p4["expect"]["refusal"]["code"] = "error.msg.glJournalEntry.invalid.future.date"
p4["expect"]["refusal"]["message"] = "The journal entry cannot be made for a future date"
p4["title"] = ("PROBE P4 -- a defineOpeningBalance request declaring the FUTURE-DATE "
               "refusal code. :717 runs before :724 and pre-empts both date guards, "
               "so on a tenant carrying posted_non_contra_transaction_ids the oracle "
               "answers the opening-balance code, not this one.")
# graded_against LEFT AS OB-01's, same reason.
write(p4, "ZZZ-T306-P4-openingbalance-declaring-future-date")

# ---------------------------------------------------------------------- P5
# DOES THE GATE ITSELF CHECK ANY REQUEST-SIDE FACT for arms 2 and 3?
# LDG-REFUSE-04 with request.latest_closing_date REMOVED. The closure shape is
# then not present in the request at all. If the capability gate stays SILENT
# and only the date rules speak, the gate delegates its entire request-side
# check to a rule block 80 lines away -- which is the coupling under review.
p5 = load("LDG-REFUSE-04-preclosure-entry-on-closing-date")
p5["request"]["latest_closing_date"] = ""
p5["title"] = ("PROBE P5 -- LDG-REFUSE-04 with the closing date REMOVED. Read WHICH "
               "rule refuses it. If no capability-gate reason appears, the gate reads "
               "only expect.refusal.code.")
write(p5, "ZZZ-T306-P5-closure-code-without-the-closing-date")
