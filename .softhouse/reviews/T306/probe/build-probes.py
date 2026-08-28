#!/usr/bin/env python3
"""T306 probe builder — writes probe vectors into a SCRATCH COPY of the store.

Nothing under .softhouse/vectors is touched and no request is sent to the
reference oracle. Every probe reuses REAL committed capture artefacts (path +
sha256 + case id) so that a citation reason cannot be the thing that refuses it:
the measurement has to be about the capability gate and the leg rules, and
nothing else.

THE PROBE SET, and what each one is for.

  P1  ACCEPTANCE, plain create (request.command "")           claims the row
      T296's arm, preserved. Must stay INADMISSIBLE with the CAPABILITY GATE as
      the reason: nothing in this store observes an entry accepted at either
      DATE boundary.

  P2  ACCEPTANCE, request.command "defineOpeningBalance"      claims the row
      The probe that measured the driver's comment FALSE: under the merged gate
      it was ADMITTED AND GRADED, 15 cells / 5 money. Under the adjudicated gate
      the CAPABILITY arm admits it -- correctly, because LDG-05 observed exactly
      that command with exactly that expectation -- and the question becomes
      whether anything else in the file still refuses a forged acceptance. Read
      the reasons, do not read the verdict alone.

  P3  a REFUSAL declaring codeAccountingClosed with consistent dates, but
      transcribed from a NON-closure capture (A2-346)          claims the row
      T306-F-6, the stated limit. Admitted by the driver's rule AND by this one.

  P4  a defineOpeningBalance request declaring the FUTURE-DATE code
      The two shapes crossed.

  P5  LDG-REFUSE-04 with request.latest_closing_date REMOVED   claims the row
      THE F-2 MEASUREMENT. Under the driver's output-keyed arm the capability
      gate contributes NO REASON AT ALL and the only refusal comes from the date
      rules ~80 lines away. Under the request-keyed arm the gate speaks too.

  P6  an ACCEPTANCE at the PRE-CLOSURE boundary                claims the row
  P7  an ACCEPTANCE at the FUTURE-DATE boundary                claims the row
      THE FOURTH SHAPE, post-T305. LDG-05 made the ACCEPTING side of the
      COMMAND observed; the accepting side of the two DATE boundaries is still
      backlog B-1/B-2 and NOTHING in this store observes it. If either of these
      is admitted, the widening reopened exactly the hole T296 measured shut.

  P8  LDG-05 with ONE expect leg deleted (5 legs for 3 request legs)
  P9  LDG-05 with one expect amount duplicated a third time
      RED-DRIVE FOR T305's TWO NEW LEG RULES, which shipped with none.
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


def clone(v):
    return json.loads(json.dumps(v))


# LDG-04's response artefact resolves BY ARTEFACT BYTES, so it needs no
# case_id-keyed pin and a renamed copy of a vector carrying it is not refused
# for the citation. Every probe built from a pinned vector swaps to it, so that
# the citation rules cannot hide the answer the gate would have given.
UNPINNED = {
    "capture_ref": ".softhouse/capture/tierA-a2/out/A2-390-db-ledger-state-a2-15.json",
    "capture_sha256":
        "d694d558fb5956cb1d462a12f8fd9b00d0082f501c98df061b0e43ff515930e8",
    "capture_case_id": "A2-390-db-ledger-state-a2-15",
}

# ---------------------------------------------------------------- P1 and P2
acc = load("LDG-01-manual-je-3leg-minor-units")
acc["capabilities_required"] = list(acc["capabilities_required"]) + [ROW]

p1 = clone(acc)
p1["title"] = ("PROBE P1 -- an ACCEPTED journal entry claiming " + ROW +
               " on the PLAIN CREATE path. No capture in this store observes an "
               "entry ACCEPTED at either date boundary.")
write(p1, "ZZZ-T306-P1-acceptance-plain-create")

p2 = clone(acc)
p2["request"]["command"] = "defineOpeningBalance"
p2["request"]["contra_gl_account_id"] = 15
p2["provenance"].update(UNPINNED)
p2["title"] = ("PROBE P2 -- the SAME ACCEPTANCE as P1 with request.command set to "
               "defineOpeningBalance. Under the DRIVER's gate this was ADMITTED AND "
               "GRADED (15 cells, 5 money) while P1 was refused, which is how the "
               "comment's claim that acceptances were refused was measured false.")
write(p2, "ZZZ-T306-P2-acceptance-openingbalance-command")

# ---------------------------------------------------------------------- P3
p3 = load("LDG-REFUSE-02-manual-adjustments-not-permitted")
p3["capabilities_required"] = ["ledger.refusal.parity", ROW]
p3["request"]["transaction_date"] = "2026-01-31"
p3["request"]["business_date"] = "2026-08-23"
p3["request"]["latest_closing_date"] = "2026-01-31"
p3["expect"]["refusal"]["code"] = "error.msg.glJournalEntry.invalid.accounting.closed"
p3["expect"]["refusal"]["message"] = ("Journal entry cannot be made prior to last "
                                      "account closing date for the branch")
p3["title"] = ("PROBE P3 -- the capability claim bought with an OUTPUT DECLARATION on a "
               "FOREIGN capture. Provenance, legs and accounts are A2-346's "
               "manual-adjustments capture, which observes nothing about closures; only "
               "expect.refusal.code and the three dates were edited. T306-F-6: this is "
               "admitted by BOTH rules and no capability gate can catch it.")
write(p3, "ZZZ-T306-P3-code-declared-on-foreign-capture")

# ---------------------------------------------------------------------- P4
p4 = load("LDG-REFUSE-03-openingbalance-after-posted-entries")
p4["request"]["transaction_date"] = "2026-08-24"
p4["request"]["business_date"] = "2026-08-23"
p4["expect"]["refusal"]["code"] = "error.msg.glJournalEntry.invalid.future.date"
p4["expect"]["refusal"]["message"] = "The journal entry cannot be made for a future date"
p4["provenance"].update(UNPINNED)
p4["title"] = ("PROBE P4 -- a defineOpeningBalance request declaring the FUTURE-DATE "
               "refusal code. :717 runs before :724 and pre-empts both date guards, so on "
               "a tenant carrying posted_non_contra_transaction_ids the oracle answers the "
               "opening-balance code, not this one.")
write(p4, "ZZZ-T306-P4-openingbalance-declaring-future-date")

# ---------------------------------------------------------------------- P5
p5 = load("LDG-REFUSE-04-preclosure-entry-on-closing-date")
p5["request"]["latest_closing_date"] = ""
p5["provenance"].update(UNPINNED)
p5["title"] = ("PROBE P5 -- LDG-REFUSE-04 with the closing date REMOVED. Read WHICH rule "
               "refuses it. If NO capability-gate reason appears, the gate reads only "
               "expect.refusal.code and delegates its whole request-side check to a rule "
               "block 80 lines away.")
write(p5, "ZZZ-T306-P5-closure-code-without-the-closing-date")

# ----------------------------------------------------------------- P6 and P7
# THE FOURTH SHAPE, POST-T305. An ACCEPTANCE on the plain create path carrying
# the request-side facts of each DATE boundary. Both are shapes NO capture in
# this store observes; the accepting side of both boundaries is backlog B-1/B-2.
p6 = clone(acc)
p6["request"]["transaction_date"] = "2026-01-31"
p6["request"]["business_date"] = "2026-08-23"
p6["request"]["latest_closing_date"] = "2026-01-31"
p6["provenance"].update(UNPINNED)
p6["title"] = ("PROBE P6 -- an ACCEPTED entry claiming " + ROW + " and carrying the "
               "PRE-CLOSURE request facts (transaction_date ON the closing date). The "
               "oracle refuses that request at :636; NO capture in this store observes it "
               "ACCEPTED. THIS IS THE FOURTH SHAPE and it must be refused as DATA.")
write(p6, "ZZZ-T306-P6-acceptance-at-the-preclosure-boundary")

p7 = clone(acc)
p7["request"]["transaction_date"] = "2026-08-24"
p7["request"]["business_date"] = "2026-08-23"
p7["provenance"].update(UNPINNED)
p7["title"] = ("PROBE P7 -- an ACCEPTED entry claiming " + ROW + " and carrying the "
               "FUTURE-DATED request facts. The oracle refuses that request at :630; NO "
               "capture in this store observes it ACCEPTED. THE FOURTH SHAPE again, on "
               "the other boundary.")
write(p7, "ZZZ-T306-P7-acceptance-at-the-future-date-boundary")

# ----------------------------------------------------------------- P8 and P9
# RED-DRIVE FOR T305's TWO NEW LEG RULES. LDG-05 is the only accepted
# opening-balance vector; both rules were written for it and neither shipped
# with an arm that fires.
ldg05 = load("LDG-05-openingbalance-accepted-empty-ledger")

p8 = clone(ldg05)
p8["expect"]["legs"] = p8["expect"]["legs"][:-1]
p8["provenance"].update(UNPINNED)
p8["title"] = ("PROBE P8 -- LDG-05 with ONE expect leg deleted: 5 expect legs for 3 "
               "request legs. saveAllDebitOrCreditOpeningBalanceEntries persists the leg "
               "at :791 AND its contra at :796 inside the per-leg loop, so an accepted "
               "opening balance stores EXACTLY 2*legs. RED-DRIVE for T305's length rule.")
write(p8, "ZZZ-T306-P8-openingbalance-five-expect-legs")

p9 = clone(ldg05)
extra = clone(p9["expect"]["legs"][0])
p9["expect"]["legs"].append(extra)
p9["provenance"].update(UNPINNED)
p9["title"] = ("PROBE P9 -- LDG-05 with one expect amount carried a THIRD time (7 legs). "
               "Each request amount must occur EXACTLY twice among the expect legs. "
               "RED-DRIVE for T305's multiset rule; it also exercises the length rule, so "
               "read BOTH reasons.")
write(p9, "ZZZ-T306-P9-openingbalance-amount-three-times")
