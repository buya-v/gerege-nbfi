# OWNER: **T522**, and it owns BOTH directories deliberately.

*Filed because `guard_capture_namespace` refused the bar with
`T522 -> 2 directories; ownership records required 1, present 0`. That refusal is the
guard working exactly as designed: an id prefixing more than one evidence directory must
be DECLARED, never left for a reader to guess.*

---

## 1. The fact

| | |
|---|---|
| **Directories** | `.softhouse/capture/t522-review-t515/` and `.softhouse/reviews/t522-review-t515/` |
| **Owner** | **T522** — both of them |
| **Filed by** | the driver, reconciling the tree after cloud fire `cloud-20260906-2000` |

## 2. Why there are two, and why that is not a collision to repair

This is NOT the T255/T256 shape. Those two records exist because a directory's NAME was
wrong — it carried one task's id while another task owned it, and the record's job is to
correct the misattribution without renaming committed evidence.

Here nothing is misnamed. T522 is a REVIEW task, and a review task produces two different
kinds of artefact that this repository keeps in two different trees by convention:

* `.softhouse/capture/t522-review-t515/` — the EVIDENCE the review gathered.
  `RUNLOG.md`, `ledger-invariants.txt`, `zz_t522_enum_test.go.txt`: what was run and what
  came back.
* `.softhouse/reviews/t522-review-t515/` — the REVIEW ITSELF. `REVIEW.md`: the judgement
  formed from that evidence.

Splitting them is the point. Evidence is a recording and must stay immutable; a review is
an argument over it and may be superseded. Collapsing the two into one directory would put
a rewritable document in the same tree as the observations it cites.

## 3. What this record does NOT claim

It does not say the review is correct, complete, or accepted. It says only WHO OWNS THE
TWO DIRECTORIES, which is the single question `guard_capture_namespace` asks.
