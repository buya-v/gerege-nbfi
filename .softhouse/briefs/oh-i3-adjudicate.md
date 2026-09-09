# Adjudicate 42 guard findings — CLASSIFY ONLY, CHANGE NOTHING

WORKING DIRECTORY: /Users/buv/oh-gerege-t509  (read-only for this task)
Write NO code. Edit NO files. Commit nothing. Your entire output is a judgement.

## Why you are being asked
`.softhouse/guards/ledgerguard` was just repaired. It now reports 42 findings
where it reported 4. The repair was made by an agent with no independent
reviewer, and it must not be merged on its author's word. You are the reviewer.

The bar is RED and 16 commits are held behind it. THAT IS NOT A REASON TO
CLEAR FINDINGS. If the findings are real, the right answer is that the tree has
38 more violations than anyone knew, and saying so is the valuable outcome.

## The invariant
DEC-2 §4.4 I-3 / CLAUDE.md: "The ledger is double-entry and append-only.
Balances are derived, never written."

## The property that decides each case
A write violates I-3 only when the value is an AUTHORITATIVE BALANCE OVER A
POSTING STREAM — a running total that is the record of truth, derivable by
summing append-only postings.

It does NOT violate I-3 where there is no posting stream to derive from. A loan
SCHEDULE is a PROJECTION OF THE FUTURE; postings are RECORDS OF THE PAST.
Summation needs something to sum over; a projection has nothing.

Refinement already paid for by an earlier task: the argument "it is a text blob,
not a typed column" FAILS — those cells are serialised into
m_loan_progressive_model.json_model and read back as starting state.
Serialisation alone does not make a value authoritative. The posting-stream test
does.

## Regenerate the findings yourself
  cd /Users/buv/oh-gerege-t509/.softhouse/guards/ledgerguard
  go run . --root /Users/buv/oh-gerege-t509/nexus

## A HYPOTHESIS TO TEST, NOT TO ACCEPT
Six were assessed by the requester, who believes they are FALSE:
  loanproduct/interestperiod.go :277 :288 :327
  loanproduct/repaymentperiod.go :562
  loanschedule/emi.go :1720 :1726

The claim: these are the same construct — roll an outstanding amount forward
from the previous period, add disbursement, subtract what is due, floor at
zero — differing only in spelling (`outstandingMinor` vs
`outstandingLoanBalance`). And neither identifier reaches any INSERT / UPDATE /
Exec / Query (measured: grep count 0 for both).

REFUTE THIS IF YOU CAN. The requester has been wrong twice today by reading a
diff without checking the current tree. Read the actual code.

## Where the requester has NO opinion — your value is highest here
  loan/charge.go        :126 :137 :152 :162 :172 :181 :201 :211 :229 :235 :249
  investor/postgres.go  :108 :199 :202 :205 :208 :211   <- persistence; likely TRUE
  workingcapital/postgres.go :168 :379    <- :379 caught via the TABLE name m_wc_loan_balance
  loanproduct/interestperiod.go :384 :385 :409 :410, repaymentperiod.go :96 :97  <- composite literals
  loanschedule/conformance/exemption_test.go :1446  <- a test fixture; guard policy is
                                                      "TESTS ARE INSPECTED, NOT EXEMPTED"

## Known stale
savings/postgres.go :113 :210 :243 :302 and savings/summary.go :53 were fixed on
main (/Users/buv/gerege-nbfi, commit 738282a6) after this worktree branched.
Confirm that, then mark them STALE — not TRUE, not FALSE.

## Return
A table: file:line — TRUE / FALSE / STALE / UNSURE — one sentence.
Then:
  - counts per verdict
  - the shared property separating FALSE from TRUE, stated precisely enough that
    it could be implemented as a check
  - whether you confirmed or REFUTED the hypothesis, and on what evidence
  - any row where your considered answer differs from your first instinct

Cite file:line. Do not guess. An honest UNSURE naming the evidence that would
settle it is worth more than a confident wrong TRUE.
