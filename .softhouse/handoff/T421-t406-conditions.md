# T421 — T406's six conditions on T391, driven

**Branch:** `softhouse/T421-t406-conditions` — seven commits, incremental.
**All six conditions closed, plus T406's informational.** One cardinal of T406's own
is corrected, and one of its findings is enlarged from ten branches to eleven.

---

## 0. WHEN I OBSERVED, AND AGAINST WHAT

The oracle edits itself, so every measurement carries its instant.

| | |
|---|---|
| worktree | `/Users/buv/gerege-nbfi/.claude/worktrees/agent-a2ec6f3a1824454b2` |
| `main` at start | `8a5a2e54` (T391 already merged) |
| pinned Fineract | `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` — verified by `git -C … rev-parse`, and `AccountingConstants.java` verified clean vs that sha before I read a line number out of it |
| host UTC | `2026-08-28T18:30Z … 18:51Z` = `2026-08-29 02:30…02:51 +08` Asia/Ulaanbaatar |
| oracle health | `{"status":"UP","groups":["liveness","readiness"]}` at `18:31:57Z` |
| database | PostgreSQL 18.3, container `fineract-db-1`, `fineract_gerege`, tenant `gerege` |
| counters at `18:33:42Z` **and again at `18:51:25Z`** | command source **379/379**, journal entries **109/113**, loan transactions **24/34** — identical to T406's review figures. **Nothing moved.** |

**The T406 review is NOT on `main`.** The brief says to read it at
`.softhouse/reviews/t406-review-t391/REVIEW.md` on `main`; that path does not exist on
`main`. It exists only on `softhouse/T406-review-t391` at commit `8c7d9cee`, which is
unmerged. I read it with `git show 8c7d9cee:…`. **The driver should merge that review or
correct the next brief**, because a task told to read a path that is not there is one
`cat` away from proceeding without the review.

---

## 1. F-T406-1 — the synthesised `captured_at`

### The corrected values, and their observed sources

| vector | was | now | read out of | digest re-verified |
|---|---|---|---|---|
| `LDG-ACC-01` | `2026-08-29T09:00:00Z` | **`2026-08-28T17:10:23Z`** | `T391-A01-je-L29.http` `captured-at-utc` | `e89ab942…` == the digest the vector itself cites |
| `LDG-ACC-02` | `2026-08-29T09:00:00Z` | **`2026-08-28T17:10:28Z`** | `T391-A02-je-L30.http` | `d4eae856…` == cited |
| `LDG-ACC-03` | `2026-08-29T09:00:00Z` | **`2026-08-28T17:10:28Z`** | `T391-A04-je-L32.http` | `aaafcf8f…` == cited |

The emitter (`bin/60-apply-vector-corrections.py`) **hashes each `.http` record and compares
it with the digest the vector cites BEFORE reading the header out of it**, and aborts
otherwise. So the instant comes from the artefact the citation *names*, not from a file that
merely shares its name — the failure mode T243 closed for citations, applied to provenance.

I also verified the three `.json` response bodies' digests match (`4ac271a9…`, `360ed3eb…`,
`d933e7a1…`), so the whole three-part citation resolves.

Each vector now **says in its own `provenance.citation`** where `captured_at` came from, and
what was wrong with the value it replaces. A handoff is not where a later reader looks.

### The search for other round-hour or future timestamps — where I looked

`bin/timestamp-sweep.py`, transcripts `out/T421-TS-01-sweep-BEFORE.txt` and `-02-AFTER.txt`.

The search states its own extent rather than its conclusion:

* **every one of the 72 `.json` files under `.softhouse/vectors`** — `ledger/` (17),
  `loanschedule/` (50), `_selftest/` (1), plus `PIN.json`, `PIN-ledger.json`,
  `capabilities.json`, `capabilities-ledger.json`;
* **every key whose name contains `captur`, wherever it sits in the tree** — not just
  `oracle.captured_at`, so a timestamp hidden one level deeper could not escape;
* the **9 files carrying no such key are NAMED** in the output, not silently skipped
  (both PIN files, both capabilities files, `SELFTEST-01`, and the four
  `loanschedule/REFUSE-0*`);
* decoded with `parse_float=str` / `parse_int=str`; "round hour" is `v[14:19] == "00:00"`
  and "future" is a lexicographic compare of two `Z`-suffixed ISO-8601 strings — **no
  parsing, no arithmetic**;
* cross-checked independently with a raw `grep -rhoE` over the whole store for every
  `…T..:..:..Z` token in any field, which returned **12 distinct instants**, of which
  `2026-08-29T09:00:00Z` was the only round hour and the only future one.

```
BEFORE   ROUND-HOUR 3   FUTURE 3     (exactly T391's three, nothing else)
AFTER    ROUND-HOUR 0   FUTURE 0     VERDICT: CLEAN
```

The 50 `loanschedule` vectors carry **nanosecond**-precision instants
(`2026-08-18T15:20:53.441500460Z`), which cannot be round hours; the remaining ledger
vectors carry second-precision real instants. `T149-PATHB-TIE` at `2026-08-21T06:16:10Z` is
second-precision but not a round hour.

**Nothing downstream grades this field**, so no pin moved — confirmed by the bar.

---

## 2. F-T406-6 — the sixteenth wrong implementation

`ledger-wrong-mapping-key-ignored` (`impl.go`, `mappingKeyIgnoringPoster`). It resolves
every accounting-path leg to the **first row** of the product's mapping table instead of
**keying** that table by the leg's slot code. It is the exact mirror image of
`ledger-wrong-slot-family-blind`: right slot, wrong account, where that one is right
account, wrong slot. Between them the two demonstrate that the slot and the account are
graded independently.

### RED evidence — re-run, not inherited (`out/T421-W02-arm-mapping-key-ignored.txt`)

```
-ledger-impl ledger-wrong-mapping-key-ignored, FULL committed corpus   -> exit 1
    ledger parity          PASS 7   FAIL 3
    ledger oracle-refusal  PASS 6   FAIL 0
    divergence             PASS 1   FAIL 0
    inadmissible 0 · harness errors 0

  all six legs of all three ACC vectors, and NOTHING ELSE:
    legs[0].gl_account_id:   want 41, got 35    legs[0].gl_account_code: want "T388-1200", got "T388-1000"
    legs[1].gl_account_id:   want 37, got 35    legs[1].gl_account_code: want "T388-4000", got "T388-1000"
    legs[2..5] likewise, want 38/42/39/43, got 35
```

**36 cell differences in the entire run.** 18 `gl_account_id` + 18 `gl_account_code`; zero
`slot_name`, zero money cells, zero sides, zero leg-order. The counts were re-derived from
the transcript by `bin/80-…py`, which **aborts** if the arm moved any cell other than the two
claimed — so the `graded_against` row cannot assert a kill the run did not produce.

**A CARDINAL OF T406'S, CORRECTED.** T406 reported this shape as *"12 account-id cells and
12 code cells"*. I re-ran it rather than inheriting the figure: it is **18 and 18** — three
vectors of six legs each. Same kill, wrong cardinal. Both numbers are recorded in the
`graded_against` note so the next reader can see which was measured here.

**The inertness on the pre-T391 corpus is COUNTED, not assumed**
(`out/T421-W03-vector-mapping-census.txt`): all **fourteen** vectors that predate T391 —
7 parity, 6 oracle-refusal, 1 divergence — carry **zero** `product_mappings` rows, and only
the three ACC vectors carry any (13 each). T406's phrase "all seven pre-T391 vectors" counts
only the parity ones; there are fourteen.

`graded_against` rows added to all three ACC vectors.

### The pin, regenerated by RUNNING (P-83), moved BY NAME

I ran the bar **first with the pin still at 15**, so the value came from the run and not
from arithmetic (`out/T421-BAR-02-pin-still-15.txt`):

```
conformance: CENSUS wrong ledger implementations — discovered 16 registered as DELIBERATELY
conformance: WRONG-IMPLEMENTATION POPULATION 16, PINNED 15.     -> EXIT 2
conformance: reference oracle (…/actuator/health) probe = up     (probe line PRESENT: 1)
```

The probe line was **present** and reads `up`, so that exit 2 is the hard guard firing, not
an oracle outage — the distinction the brief insists on.

`EXEMPTION_PIN_LEDGER_WRONGIMPLS` then moved **15 → 16** by an anchored
`^SYMBOL=value$` replacement: **1 insertion, 1 deletion**, no surrounding comment reflowed,
no other pin touched. It sits at **`:4476`** on this tree — T406 was right that the brief's
`:4551` is stale, because **T404 is unmerged**. Registration, `graded_against` rows and pin
are **in one commit** (`ef4ae067`).

**One thing I deliberately did NOT do:** the long comment block above the pin narrates each
historical move (`[T294: 6 -> 7]`, `[T295: 7 -> 9]`, `T307 12 -> 13`). I did not add a
`T421 15 -> 16` paragraph, because my grant on `conformance.sh` is **"pin only, BY NAME"**.
T360 (13→14) and T391 (14→15) did not extend it either, so the block is now three moves
behind. **Worth a follow-up task with a wider grant**; it is documentation debt, not a
defect, and the rationale lives in `impl.go` and in the `graded_against` rows instead.

---

## 3. F-T406-2 — the admission drives. **Eleven, not ten, and each driven RED**

New file `nexus/internal/apps/ledger/conformance/slotadmission_test.go`. Modelled on
T294's `openingbalance_test.go`, including its anti-vacuity control as the first sub-test.

**T406's finding names TEN branches. There are ELEVEN.** The list omits
`product_mappings[i].gl_account_id <= 0`, which sits between the duplicate-slot check and
the off-the-chart check and `continue`s past it — so without its own drive, a regression
there would surface as the *wrong reason for the right refusal*. It is arm 11.

GREEN (`out/T421-A01-slot-admission-drives.txt`), control + eleven arms, all PASS:

```
the committed accounting-path vector is ADMITTED           (control: ZERO reasons)
 1 leg carries BOTH gl_account_id and slot_code            REFUSED
 2 leg carries NEITHER                                     REFUSED
 3 NEGATIVE per-leg slot_code                              REFUSED
 4 per-leg slot codes, EMPTY mapping table                 REFUSED
 5 ENTRY-LEVEL slot_code alongside per-leg codes           REFUSED
 6 per-leg slot codes, product_id 0                        REFUSED
 7 mapping table NO leg resolves through (manual vector)   REFUSED
 8 mapping row with slot_code 0                            REFUSED
 9 DUPLICATE slot_code in the mapping table                REFUSED
10 mapping row OFF THE CHART                               REFUSED
11 mapping row with NON-POSITIVE gl_account_id             REFUSED   <-- not in T406's ten
```

Every arm matches the text of **its own** branch, not merely "some reason" — arms 1–3 sit
in one `switch` whose neighbours would otherwise swallow each other.

**RED (`out/T421-A02-admission-arms-RED-drive.txt`), because eleven passing arms only show
the branches fire today.** `bin/50-red-drive-admission-arms.sh` neuters all eleven reason
strings in a **scratch copy** of `admit.go` and re-runs:

```
sub-tests FAILED with the branches neutered: 11   (the eleven arms)
sub-tests PASSED with the branches neutered:  1   (the ADMITTED control)
admit.go RESTORED byte-for-byte (a02a9d41203da818cba448ca8cb45ba1cf11b15ae40d0ed732a21d2c0e7ca2fc)
```

Not one arm survives its branch's removal, so none is decoration. The script restores from
a `trap` and **refuses to exit** unless the digest matches the original.

---

## 4. `admit.go` — THE EXACT LINES I TOUCHED: **NONE**

```
$ git diff main -- nexus/internal/apps/ledger/conformance/admit.go
(0 lines)
```

**Zero.** The T416 contention on `verbatimInCapture` / `tokenBoundedIndex` (its hunks are at
`:1443`, `:1454`, `:1456`, `:1565`, `:1568`) is not a conflict but a disjointness: F-T406-2
needed a **test**, not a rule change, so T421 adds a new file and changes nothing T416 reads
or writes. I read `git diff main...softhouse/T416-t405-conditions` before starting, as
instructed. The RED drive's mutation of `admit.go` lived for the length of one `go test`
inside a scratch copy and was reverted and digest-checked before any commit; `git status`
was clean at every commit boundary.

Also untouched: `loanschedule/conformance/report.go` (T416's other file), and
`nexus/internal/apps/ledger/slots.go:170` — which is **outside my grant** and, per T406,
**correct as it stands** because it cites `fromInt`.

---

## 5. The three prose/citation corrections

**F-T406-3 — the wrong line range, in five committed artefacts.** Re-verified against
`/Users/buv/fineract` @ `426a23544` myself rather than inheriting T406's reading:

```
:37      public enum CashAccountsForLoan {
:39-:61  the CONSTANTS -- values 1-6 and 10-26; FEES_RECEIVABLE(25) :60, PENALTIES_RECEIVABLE(26) :61
         NO 7, 8 or 9 anywhere in it                                      <-- the claim, TRUE
:79-:89  intToEnumMap + fromInt                                           <-- what T391 cited. NO constant.
:95      public enum AccrualAccountsForLoan {
:97-:121 INTEREST_RECEIVABLE(7) :103, FEES_RECEIVABLE(8) :104, PENALTIES_RECEIVABLE(9) :105
```

(T406 gives the constants as `:38-61`; `:38` is a blank line — the constants are `:39-61`.
Immaterial to the finding, recorded because I checked.)

**I took the durable form the brief prefers: the range is DELETED and the citation names the
SYMBOL.** All five now cite `AccountingConstants.CashAccountsForLoan` and
`AccountingConstants.AccrualAccountsForLoan`, and each **says what the wrong range actually
pointed at**, because a range that has rotted once will rot again and the next reader
deserves to know how:

| artefact | done |
|---|---|
| `LDG-ACC-01/02/03` `_note` | ✅ |
| `nexus/internal/apps/ledger/conformance/impl.go` (was `:1384`) | ✅ |
| `nexus/internal/apps/ledger/conformance/vector.go` (was `:685`) | ✅ |
| `nexus/internal/apps/ledger/slots.go:170` | **untouched — correct, and out of grant** |

`git grep 'AccountingConstants.java:79-89'` still returns hits in those five files: they are
now the string **quoted in order to be named as wrong**. The only *asserting* use left is
`slots.go:170`, where it is right.

**Residual, outside my grant:** `.softhouse/handoff/T391-accrual-promotion.md:228` and
`.softhouse/capture/t391-accrual-promotion/bin/50-emit-vectors.py:236` still carry the bad
range. The emitter is **digest-pinned in that rig's `MANIFEST.sha256`**
(`a18baba2…  ./bin/50-emit-vectors.py`), so correcting it would break a verified manifest for
a comment — I judge that a worse trade and left it. It is a one-shot record of how T391
emitted, not a live generator. Flagging it rather than silently leaving it.

**F-T406-4 — the false float illustration.** `LDG-ACC-02` and `LDG-ACC-03` said "a float
prints **24000.0**", which is `LDG-ACC-01`'s number. Now **20195.38** and **12356.34**.
Measured once and only once (`out/T421-F04-float-renderings.txt`, whose header states in
full that these are the WRONG answers the sentence warns about, are never used as money and
are never compared with a money cell). `LDG-ACC-01` keeps `24000.0`, which is its own and is
true.

**F-T406-5 — "TEN cash products" with an eleven-item list.** Re-measured live by me
(`out/T421-S01-gl16-and-counters.txt`, captured `2026-08-28T18:33:42Z`):

```
gl 16 mapped by 11 products:
  22 23 27 46 54 55 56 57 58 60   accounting_type 2 CASH,             slot 1   = the TEN
  28                              accounting_type 3 ACCRUAL_PERIODIC, slot 9   = the eleventh
```

All three vectors now list exactly the ten, and say **why the query prints eleven rows** —
the eleventh is accrual product 28, which is the *other half of the same sentence*. That is
better than deleting `28`, because the next reader who runs `T391-S01 §4c` will see eleven
rows and needs to know the list is not the query.

---

## 6. INFORMATIONAL — what moved the READ census by +18

`out/T421-C01-read-census-plus18.txt`, `bin/70-explain-read-census-plus18.py`. **Counted,
not reasoned:**

```
T391-A01-je-L29.json   6 legs   6 amount tokens NOT byte-preserved
T391-A02-je-L30.json   6 legs   6
T391-A04-je-L32.json   6 legs   6
                              = 18
```

Fineract emits journal-entry amounts at **scale 6** (`24000.000000`, `20195.380000`), and no
ordinary JSON renderer reproduces six trailing decimals — so **one amount per leg, six legs
per body, three bodies = 18**. T186 §7 A4 forbids re-scaling an oracle observation, so
byte-fidelity is simply not the verdict property for these; the count is printed to STATE the
blind spot. Confirmed by a second route: committed bar transcripts carry
`86 of them are NOT byte-preserved` as the immediately preceding value, and **86 + 18 = 104**,
which is what the bar prints today. The predicate is decided by **string surgery** (strip
trailing zeros, compare) with `parse_float=str` — nothing became a float while explaining a
census about things that must not.

**A second derived READ moved, and I am naming it before anyone asks.** The deadpath census
`corpus=` count went **1430 → 1433** across my three commits: it counts files in the
repository, and I added the sweep scripts, the drives and the evidence. **`deadOccurrences`
is 108, unchanged**, and that is the graded figure.

---

## 7. VERIFICATION

```
go build ./...            exit 0     (module root is nexus/; `go build -C nexus ./...`)
go test -count=1 ./...    exit 0
    ok  .../internal/apps/ledger                  0.515s
    ok  .../internal/apps/ledger/conformance      4.578s
    ok  .../internal/apps/loanschedule            3.050s
    ok  .../internal/apps/loanschedule/conformance 30.443s
```

**THE FINAL BAR**, from a CLEAN tree after `git add -A` and commit, `bash` never `sh`
(`out/T421-BAR-04-FINAL.txt`):

```
bash .softhouse/conformance.sh                    ->  EXIT 0
grep -c 'probe = '                                ->  1        (PRESENCE before value)
conformance: reference oracle (…/actuator/health) probe = up

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
    ledger parity           PASS 10  FAIL 0
    ledger oracle-refusal   PASS 6   FAIL 0
    divergence vectors      PASS 1   FAIL 0
    T316-DEADPATH-CENSUS: corpus=1433 deadFiles=75 deadOccurrences=108 …
    exemption census READ: LEDGER parity vectors        = 10 == pinned 10
    exemption census READ: LEDGER money cells compared  = 63 == pinned 63
    exemption census READ: LEDGER oracle-refusal vector = 6  == pinned 6
    exemption census READ: LEDGER declared exemptions   = 0  == pinned 0
    CENSUS wrong ledger implementations — discovered 16 … pinned at 16
    all 16 wrong ledger implementations DIED through this harness, not by hand.
```

Against the brief's baseline: **exit 0 ✓, 46 parity / 7884 cells ✓, ledger parity PASS 10 ✓,
money cells 63 == 63 ✓, deadOccurrences 108 ✓.** The only pinned number that moved is
`EXEMPTION_PIN_LEDGER_WRONGIMPLS` 15 → 16, which is this task's deliverable. The only other
figures that moved are two derived READs (`corpus` 1430→1433, explained above) — no pin.

**FLOAT SWEEP of my whole 4,458-line diff.** Added non-comment lines matching
`float64|float32|big.Float|ParseFloat|FormatFloat|%f|Double|math.Round`: **no hits.** Every
added line containing `float` in any case is prose, `parse_float=str`, bar output, or the one
deliberately-labelled counterexample artefact. The bar's own guard agrees: *"0 forbidden
identifiers, 0 floating-point or imaginary LITERALS, 0 forbidden imports"* over 65 Go files,
and *"CENSUS float-shaped tokens … ALTERED by a binary-double round trip 0"*.

---

## 8. WHAT I DID NOT DO

* **I moved no oracle state.** `grep -rnE '\-X (POST|PUT|DELETE|PATCH)|--data|-d @|curl'`
  over the entire T421 rig returns **nothing** — the rig has no `curl` at all; it is
  `psql` `SELECT`s and one `curl` health probe issued from the shell, not from a script.
  My `capsql-readonly.sh` is a copy of T391's write-refusing wrapper and **I drove its guard
  RED myself** (`out/T421-G01`): five write shapes refused at exit 2 with nothing executed,
  and a bare `SELECT` admitted, so the guard discriminates rather than refusing everything.
  Counters identical at `18:33:42Z` and `18:51:25Z`; **no promoted account moved** — gl
  41/42/43 and 37/38/39 still six legs each, gl 18 and 22 still 0, gl 16 still 21, gl
  40/44/45/46/47 still 0.
* **I touched no file outside my grant.** Grant was `.softhouse/vectors/ledger/`,
  `nexus/internal/apps/ledger/conformance/`, `.softhouse/conformance.sh` (pin only, by name),
  `.softhouse/capture/t421-t406-conditions/`. Every changed path is inside it.
* **I did not re-emit or re-scale any oracle capture.** Nothing under
  `.softhouse/capture/t391-accrual-promotion/` was written; its `MANIFEST.sha256` is intact.
* **I did not merge to `main`.**

## 9. FOR THE NEXT TASK

1. **Merge `softhouse/T406-review-t391`, or stop citing it as being on `main`.** A brief
   that names a path that does not exist is a brief a worker can silently proceed without.
2. **The `EXEMPTION_PIN_LEDGER_WRONGIMPLS` comment block is three moves stale**
   (T360 13→14, T391 14→15, T421 15→16 are all unnarrated). Needs a wider grant than
   "pin only".
3. **`AccountingConstants.java:79-89` survives in two out-of-grant artefacts** — T391's
   handoff `:228` and the digest-pinned emitter `:236`. Correcting the emitter breaks that
   rig's `MANIFEST.sha256`; the handoff is free.
4. **T406's "12 and 12" and "all seven pre-T391 vectors" are both understated** (18/18 and
   fourteen). Recorded here and in the `graded_against` note; the review file itself is
   unmerged and uncorrected.

---

## 10. `main` MOVED WHILE I WORKED — re-checked, and it changes nothing

`main` went `8a5a2e54` → **`d3b93690`** during this task (T393/T402/T398/T414 recorded,
T423–T427 filed). I re-checked rather than assuming:

```
git diff --stat 8a5a2e54 main -- nexus/ .softhouse/conformance.sh .softhouse/vectors/
    (EMPTY)
git show main:.softhouse/conformance.sh | grep -n '^EXEMPTION_PIN_LEDGER_WRONGIMPLS='
    4476:EXEMPTION_PIN_LEDGER_WRONGIMPLS=15
git merge-tree --write-tree main HEAD    -> exit 0, tree 37f323a6, ZERO conflicts
```

The move touched **no Go source, no vector and not the bar** — only handoffs, reviews,
`patterns.md` and `tasks.json`. So the pin is still at `:4476` on `main`, my by-name move
still lands on it, and `out/T421-BAR-05-FINAL-clean-tree.txt` remains representative of the
merge result. `merge-tree` is read-only: no scratch worktree was created and `main` was never
touched.
