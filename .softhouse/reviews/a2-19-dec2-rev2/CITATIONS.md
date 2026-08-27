# A2-19 — `[VERIFIED]` spot-check of DEC-2 revision 2

**Pinned checkout confirmed by extraction:** `git -C /Users/buv/fineract rev-parse HEAD` →
`426a23544e8426a38ae43ae404670a0a7e85b9eb` — matches the document's stated pin exactly. Working
tree clean; nothing in that checkout was modified.

**Method.** Citations extracted mechanically with `/usr/bin/grep` (BSD 2.6.0-FreeBSD, `LC_ALL=C`,
`-n -oE '[A-Za-z0-9_$]+\.java:[0-9]+(-[0-9]+)?'`), then each target opened with `sed -n 'START,ENDp'`
against the pinned tree. **No source line was retyped** (P-46). Bare `:NNN` continuation citations
were resolved against the preceding named file and checked too.

**Judgment scale.** **HIT** — the cited lines contain what the document says. **DRIFT** — the content
exists in that file at different line numbers. **WRONG** — the content is not there, or contradicts
the claim.

---

## Hit rate

| population | checked | HIT | DRIFT | WRONG |
|---|---|---|---|---|
| **Fineract Java** (25 named + 22 relative) | **47** | **47** | 0 | 0 |
| **Harness / Go** (opened by me personally) | **15** | **15** | 0 | 0 |
| **In-repo non-Go** (`conformance.sh`, changelog XML) | **2** | 0 | **1** | **1** |
| **TOTAL** | **64** | **62** | **1** | **1** |

**Overall hit rate: 62/64 = 96.9%.** Both misses are in-repo, non-Fineract, and neither touches a
money claim. **Every one of the 47 Fineract citations traced to the pinned checkout at the exact
cited line.**

This corroborates A2-14's result (30+ opened, all traced) on a **fresh and larger sample**, and it
is an unusually clean record — including several hard-to-fake claims (see below).

---

## The two misses

### M-1 — DRIFT: `.softhouse/conformance.sh:843-849` (= review finding **A2-19-F4**)

Cited three times — **banner item 3**, **§4.4.1**, **§8.1 item 3** — for "`run_guards` invokes five
guards and all five are about float, `gofmt` and exception scope".

- **Substance: CORRECT**, verified by extraction. `run_guards()` is at **938-949**, the five
  invocations at **940-944**: `guard_no_float_in_vectors`, `guard_no_float_in_harness`,
  `guard_gofmt`, `guard_no_float_in_capture_requests`, `guard_no_narrow_catch_in_capture_rigs`.
- Lines 843-849 today are a comment block about `sed`/EPIPE polarity inside
  `guard_no_float_in_capture_requests`.
- **Cause traced:** at commit `dd53e87` (T191) `run_guards() {` was at line **843 exactly**, so the
  citation was accurate when A2-16 wrote it. Commit `9ef1c93` (T194) shifted it **+95 lines**.

**Class hazard, worth naming:** the Fineract citations are immune to this because they are pinned to
a frozen SHA. In-repo harness citations are not, and this document's header explicitly claims
§4.4.1's citations were re-taken — they were, and then `main` moved underneath them. **Drift, not
dishonesty**, but 95 lines is well past the header's "stale by a few lines" disclaimer.

### M-2 — WRONG (minor, inherited, and the document's own weakest tier caught it)

**§2.2, B-4 (DEC-2 line 264):** *"`acc_gl_financial_activity_account` is tenant-global — **three
columns plus id**, no office dimension."*

Extracted from `0001_initial_schema.xml:99-109`:

```xml
        <createTable tableName="acc_gl_financial_activity_account">
            <column autoIncrement="true" name="id" type="BIGINT">
            <column defaultValueNumeric="0" name="gl_account_id" type="BIGINT">
            <column name="financial_activity_type" type="SMALLINT">
        </createTable>
```

**Two columns plus id, not three.** The line range is correct and the **load-bearing claim — no
office dimension — is TRUE**.

Two mitigations, and they matter:

1. It is flagged **`[VERIFIED BY A2-1 AND A2-2 …, NOT RE-OPENED HERE]`** — the document's own
   explicitly weaker third tier. **That tier did exactly the job it was invented for**: it marked the
   one claim in my whole sample that turned out wrong. This is evidence *for* the citation
   convention, not against it.
2. The document **refutes itself in the same sentence**: its own corroboration says `A2-150`'s dump
   *"projects `id, financial_activity_type, gl_account_id`"* — id plus **two** columns. So the
   miscount is visible from inside the bracket.

**Recommendation:** a one-word fix ("two"), correctly classified as a MICRO-FIX — it is not a money
claim, not a graded-domain predicate, and not a number anything depends on.

---

## Notable HITs — claims that would have been easy to fake and were not

- **`AccountingConstants.java:37-62` vs `:95-122`** — cash enum 23 members, accrual 25, colliding at
  codes **22 / 24 / 25**, cash-only 26, accrual-only 7/8/9. Every stated collision confirmed
  verbatim.
- **`PortfolioProductType.java:26-31` vs `:51-59`** — `fromInt` genuinely **permutes** 3/4/5:
  declaration `CLIENT(5)`, `PROVISIONING(3)`, `SHARES(4)` against `case 3 -> CLIENT; case 4 ->
  PROVISIONING; case 5 -> SHARES`.
- **The six-NULL JPQL discriminator count** in `ProductToGLAccountMappingRepository` — counted, six.
- **I-3's cross-file trial-balance trace** — `JournalEntryRepository.java:61` `SUM(je.amount)` is the
  **6th** projection, and `UpdateTrialBalanceDetailsTasklet.java:81` reads `row[5]` into
  `setClosingBalance`. The *signed* sum is a different projection (`row[2]`). The unsigned-sum claim
  is exactly right, and this is the kind of two-file trace that does not survive being invented.
- **B-3's caller set** — `grep -rn` excluding `/build/` returns exactly `:402`, `:404`, `:764`,
  `:1430`, matching the document's enumeration precisely.
- **`JournalEntry.java`** — `grep -in classification` returns **no match** (exit 1), and the
  `@Column` list matches the document's list in file order.
- **`ProductToGLAccountMappingWritePlatformServiceImpl.java:149-151`** — the fenced quote
  `case ACCRUAL_UPFRONT:` / `// Fall Through` / `case ACCRUAL_PERIODIC:` is verbatim.
- **`SavingsProductToGLAccountMappingHelper.java`** — `case ACCRUAL_UPFRONT: break;` at both
  `:192-193` and `:313-314`, and `grep -c 'default:'` = **0**, as claimed.

## Harness / Go citations I opened personally

`vector.go:16-18`, `:279-293`, `:571-583`, `:771-772`; `admit.go:65-66`, `:109-110`, `:115`,
`:119-120`, `:122`, `:130-176`, `:154-171`, `:180-194`, `:517-519`; `enums.go:92-103`;
`capability.go:232-278`. **All 15 HIT.**

Two range notes, neither a miss:

- `vector.go:279-293` — the thirteen `Request` fields occupy **279-291**; the range overshoots by the
  closing brace and a blank line. Field count and content exact.
- `admit.go:154-171` — quoted for the contract-refusal `oracle.seam` rule. The predicate
  `if v.Oracle.Seam != "none" {` is line **171**, inside the range; its message string is 172. The
  citation covers the check.

## One cosmetic ordering note (not counted as a miss)

**§4.8, DEC-2 line 853:** *"The two codes are `CHARGE_OFF_EXPENSE` = 16 and `GOODWILL_CREDIT` = 13 …
[`AccountingConstants.java:48` and `:51` for cash, `:109` and `:112` for accrual]"*.

Extracted: `48: GOODWILL_CREDIT(13)`, `51: CHARGE_OFF_EXPENSE(16)`, `109: GOODWILL_CREDIT(13)`,
`112: CHARGE_OFF_EXPENSE(16)`.

Read as *ordered* pairs the mapping is inverted; read as the unordered citation it actually is
("both are present"), every line is correct and the load-bearing claim — **both codes present with
identical names in both loan enums** — is TRUE. **Not scored as a miss**, recorded for completeness.
