# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-000013`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **THIRTEEN DISPATCHED, THIRTEEN COMPLETED, THIRTEEN MERGED, ZERO LIVE AT EXIT.** No isolation violation;
  every branch scope-checked by the driver on the **three-dot** diff before merge.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 46 parity vectors, 7884 cells compared
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
         invariant assertions 4 EXEMPTED BY A VECTOR (each one's reason printed in the run)
         kills named 106 money, 7 structural
--prove              23 passed, 0 failed
go build 0 · go vet 0 · go test -count=1 ok (loanschedule, conformance)
gofmt -l             exactly contract.go   (expected, G-3)
vector store         73c3ea7b43dd75f04884072719a87fc8e1d255c1   (was ce821c63…)
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire, all thirteen** — wave 1: `A2-24`, `T214`, `T217`, `A2-25`, `T193`, `A2-26`, `T116`;
wave 2: `T215`, `A2-27`, `T218`, `T220`, `A2-28`, `A2-29`.

---

# HEADLINE 1: the corpus moved for the first time in three fires — 43 parity vectors → 46

`T116` executed **G-8 option (a)**: three vectors captured fresh from the live oracle at 600.0 % / MNT 0.01.
Two are family B and carry **exactly two** invariant exemptions each; **T100's proposed third
(`balance_roll_forward`) was DROPPED because it holds unexempted**. The third vector is the amortizing cell
**one repayment below the boundary**, promoted with **no exemption at all**, so the exemption cannot be read
as "600 % is exempt". `report.go` now prints every exemption **with its full reason** — previously only a
count appeared anywhere.

It also settled a contradiction rather than picking a side: the **T83-vs-T101/T112 dispute over whether
`invariant_exemptions` is INERT was never a contradiction.** T83's demo ran on a **family-A** case whose own
committed output reads `advanced == repaid == 1`, where every invariant already holds. "INERT" is correct
*about family A*. Both records were right about different families.

`T220` reviewed it independently and **APPROVED** — re-observing the oracle by two disjoint routes rather
than auditing T116's rig. Its own from-scratch probe reproduces all three vectors **cell for cell (1269
money cells, 0 mismatches)**, and T116's committed capture matches it on **1908 cells**.

# HEADLINE 2: family B's MECHANISM, and it changes what Buyan is being asked at G-8

`T220` found what `T116` explicitly could not. **Both sites driver-verified at `426a23544`:**

- `ProgressiveEMICalculator.java:1962` — `.divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(),
  mc.getRoundingMode())` consumes precision **19 as DECIMAL PLACES**.
- `RepaymentPeriod.java:217` — `reduce(BigDecimal.ONE, BigDecimal::add)`, the **two-arg add, NO MathContext**.

So `rateFactorPlus1` carries **20 significant digits inside a precision-19 context**. Accumulated over n
periods the EMI dips below half a minor unit at exactly the observed boundary — `n=103 → 0.005 → 0.01`,
`n=104 → 0.004999999999999999999 → 0.00`. **An EMI of zero means nothing is ever repaid**, and the
last-period fallback drops the whole residual into the final row as interest. **This is DEC-1's known
`MathContext` double-sense producing a money outcome** — G-1 already named `:1962`/`:1979` as the only two
such sites.

**CONSEQUENCE: family B is NOT a property of "600 %" or of "n ≥ 104".** It is the EMI falling below half a
minor unit, so **the boundary moves with principal, rate and term**. Every statement of G-8's region in
`gates.md` is in rates and terms (MNT 0.23, MNT 2.91, MNT 5.01 @ n=1000, MNT 10.01 @ n=3000) — those
describe **the cells that happened to be swept**, not the phenomenon. Options (b) and (c) would narrow the
graded domain **by describing a region**, and a region described in the wrong variables cannot be narrowed
correctly. → **`T223`** (and **`T219`**, which measures T159's figure).

# HEADLINE 3: G-11 — rev 3 REJECTED, and holding `A2-15` was right

The previous `RESUME.md` said `A2-15` was unblocked because rev 3 exists. **The driver held it** and sent
`A2-25` at G-11's own stated unblocking condition instead. `A2-25` **REJECTED** revision 3 on four claims
false about `main`, and its **F-3 vindicates the hold**: it authored the exact vector §5.2 **requirement 6**
specifies — *the requirement that would have graded `A2-15`* — and ran it. It dies at **strict decode**
(`unknown field "product_id"`) before either mandated refusal is reachable; `inadmissible` stays **0**.
**Neither mandated refusal fires.** The only bytes that emit both are a loanschedule-shaped vector in a
ledger costume — §5.1.1's own retracted defect. **The requirement written to close the vacuous-control hole
re-opened it through its own text.** A dispatched `A2-15` would have hit an impossible instruction and
improvised toward exactly that.

`A2-28` wrote **revision 4** addressing all seven items. **G-11 stays `OPEN — NOT RATIFIABLE`** until
**`A2-31`** reviews rev 4 clean.

# HEADLINE 4: G-12 raised and MEASURED in one fire — a SECOND SOURCE OF TRUTH

`A2-26` found `acc_gl_journal_entry` carries `office_running_balance`. `CLAUDE.md` says balances are
**derived, never written** *and* says **adopt Fineract's PostgreSQL schema** — the two instructions collide
in that column. The driver raised **G-12** with **no recommendation deliberately**, because a cache and a
second source of truth have nothing in common for the port.

`A2-29` measured it. **It is a second source of truth.** Drift of **MNT 2,000,000.00** on the live oracle,
surviving **four** organisation-wide recomputes, on rows Fineract itself flagged
`is_running_balance_calculated = true`, **propagating into a freshly computed row**, and served at the
contract boundary. The writer **seeds each incremental recompute from its own prior STORED output**.
And **driver-verified**: `/glaccounts?fetchRunningBalance=true` is **HTTP 500 on PostgreSQL** —
`GLAccountReadPlatformServiceImpl.java:130-131` uses MySQL-only `GROUP BY … DESC`, so **that
contract-boundary reader has never worked on the only database this program permits**.

**Driver recommendation, Buyan may overrule:** **(a)** for behaviour without qualification — derive, never
read those columns back — plus a **narrowed (b)** for storage: keep the columns at the DDL default, ship no
recompute. **Against (c)**, which narrows the graded domain and is unnecessary. **Price, stated:** a
table-level parity diff must **exclude** these columns, and that exclusion has to be written down.

---

## Corrections made against the DRIVER this fire — read before trusting its numbers

**P-67 — the driver certified a figure "EXACT" and propagated it to four files without measuring the
denominator.** The claim *"three of its **four** detection classes inspect an empty population"* was the
previous fire's HEADLINE 1(b). **The guard declares SEVEN classes** — `I3-FIELD-WRITE`, `I3-PKG-STATE`,
`I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML`, `I6-HOLD-BALANCE`, `OPAQUE-SQL`. Origin: §4.4.1's *"four things
the guard cannot see"* — four **blind spots** — read as four **classes**. Caught by `A2-25`; corrected in
`program.json`, `patterns.md`, `tasks.json` and here. `A2-28` then went further: only **two** of the three
NIL-COVERAGE sites actually fire, and it **refused to claim a corrected numerator for `I4-BUILDER`** because
it had not established that population.

**`T214` corrected the driver three times**: four coincidental basename hits, not three; *"the other 19
branches need nothing"* is true of **paths** and over-claims for **content** — 10 novel same-path/
different-content blobs, **four targeting `contract.go` or the DEC-1 ADR, which are ratified and frozen**,
so landing them would have been a **gate bypass**, and it correctly did not; and **`T22` is not one of the
four branches**.

**`A2-26`**: the driver's list of journal-entry observations was **7 of 9**.
**`A2-27`**: the evidence path in its brief does not exist.

## STANDING INSTRUCTIONS

- **Before recording that a dependency, file, vector, guard or citation DOES NOT EXIST, state where you
  looked (P-66/P-70).** Four claims this fire were true about a *search* and false about the *world*.
  A sweep must also name its **scope** — the DEC-2 claim survived one FILE over precisely because every
  previous sweep was scoped to the ADR.
- **Use `python3 .softhouse/bin/ready-tasks.py`, not your eye on `tasks.json`.** Completed tasks are
  archived into `.softhouse/runs/*.tasks.json`; edges pointing there resolve to nothing in the current file.
- **Before certifying a ratio, count BOTH terms in the live artefact and say where you counted (P-67).**
- **A measured claim has a shelf life shorter than a busy fire (P-69).** Census figures moved between two
  workers *inside this fire* and neither was wrong. Stamp claims with the commit measured at.
- **Ask "unreachable in WHICH observable?" (P-68).** A defect that cannot change the exit status can still
  change every number a human reads.
- **Re-derive every figure from the live artefact at the moment of dispatch (P-63).**
- **Before calling an arm RED, prove the arm RAN (P-64).**
- **A regression probe must bind by CONTENT, not line number** — `T215` and `T218` both hit drifted line
  numbers this fire; T127's citations had moved twice.
- The canonical vector-store digest is `git rev-parse HEAD:.softhouse/vectors` (**P-61**). Publish any
  digest **with its recipe** (P-38).
- **Verify a refusal by what it SAYS and what population SURVIVES, never by exit code (P-62).**
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The shell's working directory persists between tool calls.**
- **Never execute a promote or rewriter script from the repo root**, and a `/tmp` copy **cannot run** (P-36).
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root. Invoke the harness
  with **`bash`**, never `sh` (exit 3 = wrong-interpreter refusal). **Never `gofmt -w` `contract.go`** (G-3).
- **Do not modify `.softhouse/bin/fire-program.sh` while a fire runs.** Merging is safe: git **renames**.
  `T217`'s bounded push and 5 s stop grace take effect **next fire**.

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** It prints READY, dispatched, unresolved edges, and
**open CONTRACT gates beside the ready list** — because dependency-ready and *permitted* are different
questions, and this driver was conflating them.

1. **`A2-31` — the G-11 unblocker.** Independent review of DEC-2 **rev 4**. Fourth revision; rev 1, 2 and 3
   were all rejected, twice for the **same** defect class. It must also adjudicate `A2-28`'s **re-measure
   gate** (P-69).
2. **`A2-15` remains GATED** and must not be dispatched while G-11 is open. When it is dispatched, its brief
   must carry **`A2-30`**'s five items — above all that **`glAccountType` is NOT a stable cell** (entry id 4
   / GL 2 renders `ASSET` in `A2-088` and `INCOME` in `A2-320`, no entry edited).
3. **`T223` + `T219`** — restate G-8's region in the variables the phenomenon actually has. **Do this before
   options (b)/(c) are ever put to Buyan.**
4. **`T222`** — no corpus-wide exemption tripwire; a decoration exemption is admissible today.
5. **`T224`** — the retracted claim survives at `conformance.sh:1115-1116`, attached to the very guard whose
   existence refutes it. **`T221`** — `T108.md` still states verbatim the claims its own merged review
   disproved.
6. Then `A2-29`'s residuals, `T145`, `T160`, `T164`, `T174`, `T192`, `T195`, `T207`, `T213`, `T216`, `A2-23`.

## What is NOT true, and must not be inferred from the green bar

**Nothing grades the ledger's money.** The 46 passing vectors are `loanschedule`'s; **zero** touch a GL
account, a mapping, a financial activity or a journal entry. **`A2-26` established that the ledger corpus
could not have supported a useful vector anyway**: every entry in it had exactly **two legs** and every
amount was a **whole tugrik**, so "splits sum to the whole" and all minor-unit handling were graded by
**nothing** — it captured 3- and 4-leg transactions with real minor units to fix that. **Two of the 46
vectors have `principal_amortizes_to_zero` switched OFF**, legitimately and loudly, but the count is not
"46 vectors all asserting every invariant". **G-4, G-5, G-8, G-10, G-12 are OPEN and G-11 is OPEN and NOT
RATIFIABLE.** `A2-29` could not break the uncorrelated seed join and could not reach `LIMIT 10000`,
multi-office, or the NULL predicate. `A2-28` did not establish `I4-BUILDER`'s population. **Nothing was cut
over, and nothing here authorises it.** The gate register at the top of `gates.md` is authoritative.
