# T423's own ARM F red drive, re-driven by T433 — and why the second run EXITS 1

C-T423-1 item 3 says: *"Find it under `.softhouse/reviews/t423-review-t393/`, re-drive it."*
Done, at **both** refs, with `.softhouse/reviews/t423-review-t393/instruments/61-t423-armf-red-drive.sh`
**unmodified**.

| run | `T423_AFTER` | drive exit | transcript |
|---|---|---|---|
| **pre-ARM-F** | `b102875c` (main tip, section 10 with five arms) | **0 — PASS** | `61-T423-REDRIVE-pre-armf.txt`, details in `t423-redrive/pre-armf/` |
| **with ARM F** | `7df613d1` (T433) | **1 — FAIL** | `61-T423-REDRIVE-with-armf.txt`, details in `t423-redrive/with-armf/` |

## The EXIT 1 is the LANDING PROOF, not a regression

`61-t423-armf-red-drive.sh` grades **two** things on the same laundered repository and its
exit-0 condition requires **both**:

```
section 10 (verify-capture-integrity.py)  EXPECTED exit 0, VERDICT: PASS   (the gap)
60-t423-birth-arm-reaches-residual.py     EXPECTED exit 1, the file NAMED  (the close)
```

At `7df613d1` the second still holds — ARM F exits 1 and names
`out/A2-200-glaccounts-live-precheck.http`. The **first** no longer does, and cannot, because
**ARM F is now section 8 of section 10's own grader**. So the script prints
`*** section 10 did not behave as T393 disclosed` and returns 1.

**T423 wrote this outcome down before it happened.** `.softhouse/reviews/t423-review-t393/REVIEW.md`,
condition C-1, verification column, verbatim:

> `61-t423-armf-red-drive.sh` → exit 0 requires section 10 **PASS** and ARM F **FAIL-by-name**
> on the same laundered repository; **once section 10 carries the arm, the drive requires
> section 10 itself to go red there.**

Reading the pair top to bottom:

- **`0` at `b102875c`** reproduces T423's finding independently: the residual is REAL — section
  10 exits 0 / PASS on a post-fork observation mutated with its `MANIFEST.sha256` row laundered
  in the same commit — **and** it is CLOSABLE, because the birth-blob arm reaches it.
- **`1` at `7df613d1`** is the statement that it has been closed: the gap T423's script was
  built to demonstrate is gone, so the script that demonstrates the gap can no longer pass.

## Do not "fix" this by relaxing the script

Changing `61-t423-armf-red-drive.sh` to expect section 10 to fail would delete the only
committed artefact that still reproduces the ORIGINAL gap at the pre-ARM-F ref. It is a
review record with a ref parameter; run it at `b102875c` to see the defect, and at
`7df613d1` to see that it is fixed. Both transcripts are committed here.

T433's own in-situ drive —
`.softhouse/capture/t433-t423-c1/instruments/20-t433-armf-in-situ-drive.sh` — is the
forward-looking replacement: it grades the *shipped* file at both refs and expects
`0 → 1`, so it stays green as the correct guard and goes red if ARM F is ever removed.
