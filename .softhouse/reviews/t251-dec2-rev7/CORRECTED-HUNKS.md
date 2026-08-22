# T251 — corrected hunks for DEC-2 revision 7

**PROPOSAL ONLY. `T251` did not apply any of this.** `docs/adr/DEC-2-gl-accounting-adapter.md` is
untouched on this branch, as G-14's recorded scope requires.

Measured at **`2871f17`** (`git merge-base main HEAD` = `2871f17`, i.e. this is my fork point).
`main` moved to **`d6dd8d0`** while I worked; both files below are **byte-identical between the two**
(`docs/adr/...` blob `26a06ef3…`, `.softhouse/conformance.sh` blob `2bf91723…`), so every figure here
holds at `main` `d6dd8d0` as well.

---

## C-1 (from F-T251-1, HIGH) — three stale `conformance.sh` citations in LANDING text

T247's guard **ordinals are correct and must not be changed**: eight guards invoked, seven tallied,
`guard_ledger_invariants` the sixth tallied. I re-derived that from `run_guards`' body at `2871f17`.
Only the **line numbers** are stale, because `T248` (merge `fb9c18b`) grew `conformance.sh` from
**2544** to **2574** lines after `T247` measured at `9b6c596`.

| citation in revision 7 | measured at `9b6c596` | **TRUE at `2871f17` / `d6dd8d0`** | what the stale number now points at |
|---|---|---|---|
| defines `guard_ledger_invariants` | `:1300-1339` | **`:1300-1339` — UNCHANGED, correct** | — |
| `run_guards` | `:1474-1500` | **`:1504-1530`** | `LC_ALL=C sort "$got.raw" >"$got"` |
| the seven tallied invocations | `:1489-1495` | **`:1519-1525`** | `warn` strings in the fail-open handler |
| `guard_ledger_invariants`' invocation | `:1494` | **`:1524`** | `warn "conformance: The pin is FAILOPEN_PIN_FILE_LIST …"` |
| `guard_no_fail_open_instruments` | `:1495` | **`:1525`** | `warn "conformance: EXIT 2 — no verdict is available…"` |

Verbatim from `run_guards()` at `2871f17`:

```
 1504| run_guards() {
 1505|   local failed=0
 ...
 1514|   guard_graded_root_is_this_tree || {          <- short-circuits, does NOT join the tally
 ...
 1519|   guard_no_float_in_vectors           || failed=1     (1st tallied)
 1520|   guard_no_float_in_harness           || failed=1     (2nd)
 1521|   guard_gofmt                         || failed=1     (3rd)
 1522|   guard_no_float_in_capture_requests  || failed=1     (4th)
 1523|   guard_no_narrow_catch_in_capture_rigs || failed=1   (5th)
 1524|   guard_ledger_invariants             || failed=1     (6th)  <- the one cited
 1525|   guard_no_fail_open_instruments      || failed=1     (7th)
 1526|   if [ "$failed" -ne 0 ]; then
 ...
 1530| }
```

**Sites to correct — BOTH are landing text, not commentary:**

1. `REVISION-7-PROPOSED.md` **L303-307**, inside H-1's `— AFTER —` (banner fact 3).
2. `REVISION-7-PROPOSED.md` **L901-902**, inside H-14's `— AFTER —` (§8.1 fact 3), which says the
   citations are "re-stamped exactly as in the banner's fact 3" and repeats them.

### C-1 corrected text for H-1 fact 3

Replace, in H-1's AFTER:

```
>    [RE-MEASURED by `T247` at `9b6c596`: `.softhouse/conformance.sh:1300-1339` defines it,
>    `:1474-1500` is `run_guards`, `:1489-1495` are the seven tallied invocations and `:1494` is this
>    one. **Revisions 3–6 said *"seven guards … the seventh is `guard_ledger_invariants`"* with
>    `:1152-1187` / `:1189-1213` / `:1209`; those were stamped at `2e97162`, are correct there, and
>    are STALE here — `T243` wired an eighth guard, `guard_no_fail_open_instruments`, at `:1495`. An
>    ordinal used as an identifier goes wrong silently; a name does not.**]
```

with:

```
>    [RE-MEASURED by `T251` at `2871f17`: `.softhouse/conformance.sh:1300-1339` defines it,
>    `:1504-1530` is `run_guards`, `:1519-1525` are the seven tallied invocations and `:1524` is this
>    one. **Revisions 3–6 said *"seven guards … the seventh is `guard_ledger_invariants`"* with
>    `:1152-1187` / `:1189-1213` / `:1209`; those were stamped at `2e97162`, are correct there, and
>    are STALE here — `T243` wired an eighth guard, `guard_no_fail_open_instruments`, now at `:1525`.
>    An ordinal used as an identifier goes wrong silently; a name does not — and so does a LINE
>    NUMBER: revision 7 was itself drafted with `:1474` / `:1494` / `:1495`, measured at `9b6c596`
>    and made stale 30 lines' worth by `T248`'s merge `fb9c18b` before it could land. THE NAMES, THE
>    ORDINALS AND THE COUNTS ABOVE ARE THE DURABLE PART; re-run
>    `.softhouse/capture/t247-dec2-rev7/verify-line-numbers.py` before quoting any `:NNNN` here.**]
```

Apply the same three-number substitution at H-14 fact 3.

**The driver MUST re-run `verify-line-numbers.py` at the actual landing commit and re-measure again
if it reports MOVED.** The script already says this; it is now demonstrated, not hypothetical.

---

## C-2 (from F-T251-2, HIGH) — a 35th site: §4.4's lead paragraph, L804-806

**Not in T247's 34-row edit list, not in its 16-entry HISTORY list, and not discussed in its §B.**
It is nine lines above H-6's target and fifteen above H-7/H-8's.

Live text at `2871f17`:

```
  804|Most of the project's ledger invariants cannot be graded by a `ledger` vector, and **none of them
  805|can be graded today**. Saying which, and saying why the two statements differ, is the honest half of
  806|this contract.
```

**"none of them can be graded today" is FALSE** [MEASURED by `T251` at `2871f17`, own
`VERDICT: PASS (exit 0)` run, `conformance-2871f17.log` L337-348]: `I-1`
(`double_entry_balances`) is asserted and HOLDs on **all four** parity vectors, INDEPENDENT on each;
`I-2` (`splits_sum_to_whole`) HOLDs on **three** — INDEPENDENT on `LDG-02` and `LDG-03`, DEPENDENT on
`LDG-01`, and **N/A on `LDG-04`**.

If revision 7 lands unamended, §4.4 contradicts itself inside twenty lines: L804 will read "none of
them can be graded today" directly above H-7's new cell reading "**YES, SINCE `A2-15`**".

### C-2 proposed AFTER for L804-806

```markdown
Most of the project's ledger invariants cannot be graded by a `ledger` vector. **Revisions 1–6 added
"and none of them can be graded today"; CORRECTED IN REVISION 7 — `I-1` and `I-2` are graded now,
and the rest are not** [MEASURED by `T251` at `2871f17`: `I-1` HOLDs INDEPENDENT on all four parity
vectors; `I-2` HOLDs INDEPENDENT on `LDG-02` and `LDG-03`, DEPENDENT on `LDG-01`, N/A on `LDG-04`].
Saying which, and saying why the two statements differ, is the honest half of this contract — and it
matters more now than when nothing was graded, because a per-row "NO" can no longer be excused by
"the machinery is missing".
```

---

## C-3 (from F-T251-3, MEDIUM) — §5.2's heading and lead, L1726 and L1739

Also absent from T247's edit list and HISTORY list. Both were printed by **T247's own sweep**
(`sweep-dec2-9b6c596.txt`, arm `F7 machinery-5.3`) and did not reach the list.

```
 1726|### 5.2 The decision: EXTEND the machinery — and DEC-2 grades nothing until it exists
 ...
 1739|**(a) is adopted. The machinery is named, it is not built here, and this document does not pretend
 1740|it is anywhere else either.**
```

Revision 7's own H-1 fact 2 asserts "**The machinery was named in §5.2 and built by `A2-15`.**" —
so revision 7 relies on §5.2 while leaving §5.2 asserting the opposite state.

**L1726 (heading) — MEDIUM.** "DEC-2 grades nothing until it exists" is a present-tense state claim
in a section heading; the machinery exists and DEC-2 grades `I-1`/`I-2`.

**L1739-1740 — LOW.** Strictly still true (it is a claim about what *this document* pretends, not
about the world), but it reads as "not built". Same remedy T247 chose for §5.1's heading at H-12b: a
heading kept, plus one stamped sentence so it is not read unscoped.

### C-3 proposed

Heading L1726 →

```markdown
### 5.2 The decision: EXTEND the machinery — and (revisions 1–6) "DEC-2 grades nothing until it exists"
```

and append immediately after L1740, in H-12b's shape:

```markdown
> **⚠ REVISION 7: THE MACHINERY DESCRIBED BELOW WAS BUILT.** This section was written while
> `gerege.ledger.vector/v1` did not exist, and its heading and its *"not built here … nor anywhere
> else"* framing are preserved as the record of the decision, not as a statement of today's world.
> `A2-15` built it; six vectors are promoted and green [MEASURED by `T251` at `2871f17`].
> **Requirements 1–7 below are NORMATIVE and are UNCHANGED by revision 7** — they are the standard
> `A2-15`'s work is to be judged against, and §5.3's revision-7 note records that no task has yet
> re-derived that each was met.
```

---

## C-4 (from F-T251-4, MEDIUM) — H-10's AFTER overstates `I-2`, and contradicts H-8

H-10's AFTER says:

```
… it grades I-1 and I-2, on four vectors, and grades I-3, I-4 and
I-5 by nothing** [MEASURED by `T247` at `9b6c596`].
```

`I-2` is **not** graded on four vectors. `LDG-04` reports `splits_sum_to_whole  N/A (0 assertion(s))`
— the harness declines to assert it on a 2-leg entry. H-8, in the same revision, states the honest
count itself: *"So the honest count is 2 independent assertions, not 4"*. H-10 contradicts it, in the
unsafe direction (overstating coverage), inside a document whose stated purpose is to stop coverage
being over-read.

### C-4 proposed

Replace that clause with:

```markdown
… it grades `I-1` on all four parity vectors and `I-2` on three of the four — INDEPENDENTLY on two —
and grades `I-3`, `I-4` and `I-5` by nothing** [MEASURED by `T251` at `2871f17`; `LDG-04` reports
`splits_sum_to_whole N/A`, and `LDG-01` reports it `DEPENDENT`, which is not a second piece of
evidence — see the `I-2` row above].
```

---

## C-5 (from F-T251-5, LOW — MICRO-FIX class) — a dangling cross-reference

`REVISION-7-PROPOSED.md` **L182**, in §B-4:

```
See `## C. How the caution survives` at the end of this file.
```

**No such section exists.** The file's top-level headings are exactly `## A. The site-by-site edit
list`, `## B. What revision 7 must NOT do, and did not`, `## C. The hunks`, `## D. Where the ratifier
should start`. The file ends at line 985.

The *substance* is present — H-2's AFTER (`REVISION-7-PROPOSED.md` L376-395) carries the caution and
its denominator in full — so this is a dangling pointer, not a missing argument. Worth fixing
because this is a document about stale cross-references.

Suggested: `See **H-2**'s `— AFTER —` block in `## C. The hunks`, which carries the caution in full.`

---

## C-6 (LOW, informational — no change proposed)

* `REVISION-7-PROPOSED.md` H-5b is titled *"Replaces line **711**"* but its `— BEFORE —` block quotes
  **L709-711**. L709-710 are carried forward verbatim in the AFTER, so the intent is right; a driver
  applying hunks by line span should know the quoted block is three lines, not one.
* `.softhouse/vectors/capabilities-ledger.json` also carries `dec2_revision: 5`, which T247's §B-3
  discusses only for `PIN-ledger.json`. I found no code that compares the **registry's**
  `dec2_revision` to anything — `admit.go:51-52` compares vector-to-pin only, and
  `capability.go:111-113` only requires the pin's value be positive [searched: `git grep -P
  'dec2_revision|DEC2Revision' -- nexus .softhouse/conformance.sh .softhouse/guards` at `2871f17`].
  So B-3's conclusion — no re-stamp needed, nothing enters revision 7's diff — **holds for this file
  too**; it is simply not stated.
* `docs/adr/DEC-2-gl-accounting-adapter.md:2237` — *"`I-1`/`I-2` are **money** kills with non-zero
  margins once P-5 exists"* — is a future-conditional whose antecedent is now satisfied (the harness
  prints `ledger kills named 6 money, 10 structural`). Reads as forward-looking design prose rather
  than a measured-fact claim, so I did not classify it as a site.
