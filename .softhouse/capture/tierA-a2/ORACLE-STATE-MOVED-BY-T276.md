# READ THIS BEFORE CONCLUDING THAT `A2-544` HAS DRIFTED

Written by the **driver**, local fire `20260822-060013b`, from T276's own disclosure. It is here rather than
only in the review because the next fire will meet the symptom in *this* directory and will not think to go
looking in `.softhouse/reviews/` for the cause.

## What happened

T276 reviewed T275's captures **independently**, which for the headline claim meant it could not simply read
the recorded responses — it had to **send the writes itself**. That is the correct behaviour and it is why the
review is worth anything. It also means the review **moved live oracle state**.

T276 restored every value it changed (GL 16, channel `pt2 -> GL 17`, the description), and `A2-521` re-issues
byte-identically again. **But identity is not value, and identity does not restore:**

| | before T276 | after T276 |
|---|---|---|
| product 23 channel mapping row id | **96** | **156** |
| `acc_product_mapping` `max(id)` | **153** | **156** |

**Consequence, stated plainly: `A2-544` no longer re-issues byte-identically.** The diff is **exactly the
row-id cell and the `max(id)` cell** and nothing else.

## What to do about it

**Do not read this as drift, and do not re-capture to make it go green.** It is the recorded, expected
consequence of a review doing its job. The captured bytes remain the true record of what the oracle returned
at capture time; what changed is the sequence counter, which only ever moves forward.

Note the irony worth keeping: the finding T275 landed is that **the oracle reconciles by key and row identity
survives a value change** — and the cost of independently verifying that claim was **a row identity**. Both
facts are true and they do not conflict.

## Two miscounts in T275's handoff, corrected here rather than silently edited

T276 found them and correctly declined to file them as MICRO-FIX, because the driver's brief barred a
micro-fix from touching a number. Both are contradicted by the handoff's **own adjacent enumerations**, so
nothing downstream was ever computed from them:

- handoff says "32 captures"; **34** are committed.
- handoff says "seven files"; **eight** are committed.

The committed artefacts are the record. The prose undercounted them.
