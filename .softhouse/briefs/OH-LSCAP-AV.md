# OH-LSCAP-AV — CAPTURE ONLY. A disbursement inside a LATER repayment period.

Worktree: `/Users/buv/oh-gerege-lscap` (branch `feat/OHLSCAPav`)
Work ONLY in that directory. **A run works ONLY in its own worktree.** The driver pushes; never
exercise the push gate. A parallel run (`OH-WOPAID-AU`) holds the running oracle SERVER; **this seam
never touches it** — it is an in-process library call on the pinned image (see below).

## Read first — do not search
1. `.softhouse/maps/loanschedule.md`.
2. `.softhouse/findings/F-2026-09-11-loanschedule-graded-coverage.md` §5.2 — the target.
3. `.softhouse/capture/README-pass3i.md` and `README-pass3b.md` — the rig. **Pass 3i is your template.**

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE
**Do NOT write a vector, a drive, or any `.go` file.** A later run grades it.

## WHY
The committed loanschedule corpus reaches every reference money rule — except one reachable path:
`emi.go:1529`, the `inPeriodM1` **non-first** arm, which fires only when a disbursement falls inside a
LATER repayment period. All 50 vectors disburse within period 0 (the largest offset is P-03, disbursed
ON the first due date, still period 0 under M1's inclusive `<=`). `REFUSE-04` disburses after maturity
and is refused. **No capture has a disbursement strictly after the first due date and before the last.**

## THE OBJECTIVE
Add **pass 3j** = pass 3i's rig with ONE new case group, exactly as 3i was 3h's:
* `.softhouse/capture/src/Capture3j.java` — copy `Capture3i.java`, change ONLY the case list: keep the
  rig calibrations pass 3i runs (so the pass proves the rig still reproduces known outputs), and add a
  group of **later-period disbursement** cases built with the existing `prodDates(...)` helper
  (`Capture3i.java:176`) at production settings (precision 19, HALF_UP, the tenant's settings that
  helper already uses). Suggested, using the date the rig's other cases use:
  * start 2024-01-01, 6 monthly repayments, disbursed **2024-02-15** (inside period 1);
  * same, disbursed **2024-04-10** (inside period 3);
  * same, disbursed **2024-03-01** (ON the second due date — period 1 under M1's inclusive `<=`: the
    boundary the triage names).
  Use a principal with a non-round minor unit (the rig's other cases show the convention).
* `.softhouse/capture/src/run-pass3j.sh` — copy `run-pass3i.sh`; every precondition kept, **not one
  weakened** (image id, pinned commit, clean checkout, seam-class byte identity, …).
* `.softhouse/capture/README-pass3j.md` — what differs from 3i, in the same style.
* Run it. Commit the outputs, the attestation sidecar and the hashes exactly as 3i did.

If the generator REFUSES or returns an all-zero schedule for a case, **that is the result** — keep it,
say which case and what the output was. Do not change a date to make a case "work".

## Rules of evidence
- The capture is the oracle's code running in its own image; **never hand-edit an output**.
- Money is integer minor units in anything you write; never a sub-minor value.
- "The oracle" is the Fineract reference; **Oracle Database is prohibited.** PostgreSQL only (this seam
  opens no database).
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/`, or `.softhouse/maps/`.**

## The bar and the budget
The bar must still pass on your tree: `go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` —
exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. A capture adds files; it must not move either number.
~300 iterations. **Commit the Java + script first, then the outputs.**
**Write commit messages to a file (`git commit -F`). Never commit TASK.md.**
