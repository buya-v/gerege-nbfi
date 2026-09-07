# OWNER: **T523**, and it owns BOTH directories deliberately.

*Filed because `guard_capture_namespace` refused the bar with
`T523 -> 2 directories; ownership records required 1, present 0`. That refusal is the
guard working as designed: an id prefixing more than one evidence directory must be
DECLARED, never left for a reader to infer.*

---

## 1. The fact

| | |
|---|---|
| **Directories** | `.softhouse/capture/t523-review-t509/` and `.softhouse/reviews/t523-review-t509/` |
| **Owner** | **T523** — both of them |
| **Filed by** | the driver, reconciling the tree after cloud fire `cloud-20260906-2000` |

## 2. Why there are two, and why this is not a misattribution

This is NOT the T255/T256 shape. Those records exist because a directory's NAME was
wrong — it carried one task's id while another owned it, and the record corrects the
attribution without renaming committed evidence.

Nothing here is misnamed. T523 is a REVIEW task, and a review produces two kinds of
artefact that this repository keeps in two trees by convention:

* `.softhouse/capture/t523-review-t509/` — the immutable EVIDENCE the review gathered.
* `.softhouse/reviews/t523-review-t509/` — the ARGUMENT formed over that evidence.

The split is the point. Evidence is a recording and must not change; a review is a
judgement over it and may be superseded. Collapsing them would put a rewritable document
in the same tree as the observations it cites.

## 3. What this record does NOT claim

It does not say the review is correct, complete, or accepted. It answers only the single
question the guard asks: who owns these two directories.
