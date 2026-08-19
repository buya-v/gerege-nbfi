# Softhouse learned patterns — Gerege NBFI (Fineract → Go migration)

Softhouse reads this file during pre-flight and applies it when planning. Anything above the markers is hand-written project knowledge; everything between the markers is appended automatically by each run's postmortem.

Seeded from the proven Digital Coop Bank pipeline. The money/Mongolia constraints are inherited; the migration-specific rules are new.

## Project constraints

Rules a worker agent must not violate. These get grepped against diffs during review.

### Money and the ledger (inherited — non-negotiable)

- **No floating-point in any monetary path** — not in struct fields, DB columns, API fields, test fixtures, or intermediate calculation. Integer minor units only (MNT, ISO 4217 numeric 496, minor unit 2).
- **Balances are derived, never written.** Any diff assigning to a balance column directly is a rejection.
- **The ledger is append-only.** Corrections are reversing entries. An `UPDATE`/`DELETE` of a posted entry is a rejection.
- **Holds alter `available` only, never posted `balance`.** This was the exact defect that failed adversarial review twice on the sister project (an inverted hold formula that made pledged collateral spendable). Re-derive hold math with the sign forced.
- **`Idempotency-Key` mandatory on every money-movement POST.** No exceptions for "internal" transfers.

### Migration method (new — non-negotiable)

- **Fineract is the ORACLE and FALLBACK.** No Go context is "correct" until its golden vectors match Fineract's captured outputs to the defined rounding. Prove parity; never assert it.
- **The reviewer re-derives money math, it does not read it.** The sister project's headline lesson: a plausible-but-wrong ledger formula survived two adversarial reviews and fooled one of three fresh auditors — only the ones who recomputed through the source conventions caught it. For a money conflict, the synthesizer re-derives from source, never tallies votes.
- **Contract-first:** the frozen adapter contract is the boundary. Behind it is Fineract-JVM or the Go module, switched per context by config. A worker that needs a contract change STOPs — that is a `user` task.
- **Schema-first:** adopt/prune Fineract's PostgreSQL schema; a shared DB enables shadow/differential testing.
- **Cutover is a `user` gate**, never an `agent` task — requires vectors passing + a clean shadow-parity window + regulatory/parallel-run sign-off.

### Scope (amended 17 August 2026 — full-codebase program)

- **The program target is the WHOLE Fineract codebase**, ported in tiers in strangler order. `.softhouse/program.json` is authoritative for the context list, tier, measured LOC, dependencies and per-context state. Tier 0 harness/PoC → Tier A money core → Tier B remaining business contexts (savings/deposits, working-capital-loan, investor, branch, loan-origination, shares, collateral, clients/groups) → Tier C platform → Tier D test corpus as vectors.
- **Scope guard is per RUN, not per program.** One bounded context per run; a diff touching files outside the run context's `fineract_paths` is a rejection. "Everything is in scope eventually" is never a licence to widen a task.
- **Tier C is map-first.** `fineract-core` and `fineract-provider/infrastructure` are largely plumbing (auth, tenancy, command bus, jobs) that Nexus already provides. Port only a demonstrated gap, and the handoff must say what Nexus lacks. An unjustified plumbing port is a rejection.
- **Deposit-taking: port yes, activate no.** Savings/deposit code is portable and must ship **disabled by config**; enabling deposit-taking behavior in a live environment is a `user` licensing gate (FRC / Bank of Mongolia). The "never insured/protected/guaranteed" rule below is unchanged and applies to every string this code returns.
- **Tier D is a vector source, not a port target.** Fineract's ~321k test LOC and the e2e suites are mined into golden vectors; do not port JUnit into Go tests one-for-one.

### Database — PostgreSQL only (new — non-negotiable)

- **PostgreSQL everywhere.** The Fineract reference instance, the Go module, vector capture, shadow/differential runs and CI all use PostgreSQL. Fineract's shipped default is Postgres [VERIFIED: `fineract-provider/src/main/resources/application.properties` → `org.postgresql.Driver`, `jdbc:postgresql://localhost:5432/fineract_tenants`]. Start it with the `postgresql` compose profile (`docker-compose-postgresql.yml` / `config/docker/compose/postgresql.yml`).
- **Oracle Database is prohibited.** Grep rejections: `ojdbc`, `oracle.jdbc`, `OracleDialect`, `oracle.sql`, `:1521`, `SID=`, `tnsnames`.
- **MySQL / MariaDB are prohibited too** — do not use `docker-compose-mysql*.yml` or `docker-compose-mariadb*.yml`; grep rejections: `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`, `MySQLDialect`.
- **Go connects with `pgx`** (`github.com/jackc/pgx/v5`). Money columns are integer minor units — `bigint`, never `float`/`double precision`/`real`/`money`; `numeric` only where Fineract's schema already uses it and the Go side reads it as an exact integer minor-unit value.
- **Schema-first still holds:** adopt/prune Fineract's PostgreSQL schema; both sides read the SAME schema — that shared Postgres database is what makes shadow/differential testing meaningful. A parity claim across two different engines is not a parity claim.
- **Terminology:** "the oracle" in this project = the **Fineract reference implementation** (test-oracle sense), recorded in `.softhouse/reference-oracle.md`. It is never Oracle Database. Write "reference oracle (Fineract)"; reserve "Oracle Database" for the prohibited product.

### Mongolia rules (inherited)

- **Never render member savings as insured/protected/guaranteed** — SCC deposits are not covered; misrepresentation carries criminal exposure. Applies to any API-returned string.
- **No US payment rails.** Mongolia: RTGS (Banksuljee) above MNT 5,000,000, ACH+ at or below, NETC for cards. Threshold set by Governor's order — read from config, never hard-code.
- **No Stripe/Plaid/Lithic/Persona** assumptions — not the Mongolian market.
- **Names are three fields** — ovog, patronymic, given name. A diff introducing `first_name`/`last_name` is a rejection. Match on registration number, never name.
- **National ID is 10 characters** (2 Cyrillic letters + 8 digits); month field carries +20 for births from 2000 onward; check digit unpublished — validate structurally.
- **Two time zones, no DST** — `Asia/Ulaanbaatar` (+08), `Asia/Hovd` (+07). Use the tz library; never hard-code an offset.
- **Formatting:** dates `y.MM.dd`, week starts Monday, 24-hour clock. Currency postfix, zero decimals for display (`1,250,000₮`), 2 decimals stored.

### The honesty rule

Every worker prompt carries it; review enforces it. State only what you verified; mark each material claim `[VERIFIED: fineract source / vector id]` or `[UNVERIFIED]`. A confident invention in money code is the worst possible defect. (Origin: a research agent on the sister project fabricated an e-money licensee list and had to retract it.)

## Environment topology

- **Fineract oracle:** runs alongside for vector capture and shadow/differential testing. `/softhouse-uat conformance` needs it reachable; if it is down, conformance reports exit 2, not a false PASS.
- **Go module:** the migration target, in the Nexus tree, behind the frozen adapter contract.
- **Tests:** `go build ./...`, `go test ./...`, plus `.softhouse/conformance.sh` (golden vectors vs oracle) and property invariants. Grep-based HARD checks prove absence of known-bad patterns, never correctness.
- **Budget/scheduler:** the migration is long; the orchestrator meters the daily token budget, checkpoints all workers at the soft limit, and a scheduled task resumes via `/softhouse resume` at quota reset. See `docs/agent-squad-delivery-and-scheduler.md`.
- **Remote:** only the orchestrator pushes; workers commit to their branch.

## Codebase facts

- Fineract measured at ~544k main Java LOC / 5,317 files / ~321k test LOC / 424 changelog files. The ~321k test LOC is the vector-generation goldmine, not overhead.
- `fineract-progressive-loan-embeddable-schedule-generator` is ~182 LOC and self-contained — the designated proof-of-concept first port.
- Companion planning docs: `docs/gerege-nbfi-fineract-as-module-ideation.md`, `docs/softhouse-engagement-plan.md`, `docs/softhouse-skills-requirements.md`, `docs/agent-squad-delivery-and-scheduler.md`, `docs/softhouse-migration-pipeline.md`.

<!-- LEARNED PATTERNS START -->
<!-- Postmortems are appended below by each /softhouse run. -->

### Run 1 (`2026-08-17-run1-harness-schedule-poc`) — Tier 0, cloud fire 20260817-2000

**Both artefacts under review were REJECTED. Neither reviewer read back the author's conclusions; both re-derived, and the re-derivation is what caught the defects.**

- **A passing golden test is not evidence that the reading is right.** Fineract threads one `MathContext` and consumes it in two incompatible senses — significant digits in `multiply/divide(…, mc)`, and *decimal places* in `setScale(mc.getPrecision(), …)` (`ProgressiveEMICalculator.java:1962`, `:1979`). The shipped conformance vector cannot tell the two apart, yet across a 560-config grid 189 configurations diverge, several in a **payable amount**. Before trusting any vector as a grading standard, ask what it *fails to discriminate* — a corpus that cannot detect a defect class will report green through it forever. When a contract field's meaning is contested, capture a **discriminating vector** on purpose; do not accept the existing corpus as coverage.
- **A rounding step described as "redundant" is the highest-yield thing to re-derive.** Both money defects in this run hid behind a step an author had dismissed as a no-op. `setScale(precision-as-scale)` is not merely lossy — on a small quantity like a rate factor it is *always strictly lossier* than significant-digit rounding, because it discards the digits the leading zeros would have bought.
- **Corrections leak: an author fixes the section the review named and leaves the sections that restate the same claim.** Attempt 2 corrected month-end stepping in §4.4 but not §7.4 or the vector matrix, and "cancels to 1" in §4.2 but not §7.4 — so a reader following the document to build the port still met the original wrong instruction. **Remedy: after any correction, grep the whole document for restatements of the corrected claim.** Review a rewrite for *consistency*, not just for whether the named line changed.
- **Two independent reviewers converging on the same finding from different artefacts is the strongest signal available.** T3b (reviewing the analysis) and T5 (reviewing the contract), with no shared context, both refuted the claim that `allowFullTermForTranche` is dead: the builder setter reaches it (`LoanApplicationTerms.java:606`) and the guard (`ProgressiveEMICalculator.java:142-144`) never consults `isMultiDisburseLoan()`. A "dead/unreachable field" claim used to justify dropping an input from a frozen contract must be re-verified against source every time — it is an amendment gate later if wrong.
- **Hidden second rounding context.** `MoneyHelper` carries its own `MathContext` (`PRECISION = 19` in production, **mocked to 12 in the tests**) and is reached through at least four silent fallbacks — 2-arg `Money.of`, static `roundToMultiplesOf(BigDecimal, Integer)`, `Money.getMc()`, and 2-arg `Money.zero`. **A live capture therefore runs a different precision than produced the literals the tests assert.** Capture must *assert* the precision and tenant rounding mode actually in force, never inherit them.
- **`[VERIFIED]` may never contain a hedge.** A tag reading "verified: cited by upstream agent, not independently re-read" is an unverified claim wearing a verified badge. It appeared once, was caught, and the ban is now explicit in the worker brief.
- **Transcription is not derivation.** For vector mining, a value may be *transcribed* from a source literal with `file:line`, never computed, extrapolated or interpolated. Uncovered behaviour is marked `TO_BE_CAPTURED`. A plausible invented number that reaches the vector store looks exactly like a real one and silently poisons every parity claim above it.

**Process, not money:**

- **An unreachable oracle is a routing fact, not a blocker.** `.softhouse/reference-oracle.md` recorded "Status: UP" as a global fact when it was true only of localhost on one machine; a cloud fire read it and had to probe to learn otherwise. Reachability is now recorded **per fire**. Conformance stays exit 2 and never becomes a PASS.
- **Do not run a build inside the source checkout while reviewers are grepping it.** Gradle writes `build/` into the module under audit and can pollute a reviewer's `find`/`grep`. Sequence it after the reviews, or build elsewhere.
- **Correcting an UNRATIFIED draft is agent work; only a RATIFIED DEC-n is a user gate.** Worth stating plainly — the distinction decides whether the driver retries or parks.
- **Worker isolation held this fire.** All four workers ran in real worktrees on `softhouse/*` branches, so `git diff --stat main..<branch>` scope checks worked and the previous fire's isolation violation was not repeated.


### Run 1 — local fire `20260818-230002` (oracle REACHABLE; four workers, all four completed)

**The fire that closed every open admissibility P0 — and found that the corpus was still blind.**

- **A diagnosis that blames the code you own is worth re-checking against the log.** Two manifests recorded that `fire-program.sh` "dispatches and exits without awaiting its workers", and a fix was designed around that. It was wrong. Every fire that lost work carries the harness line *"Background tasks still running after 600s; terminating. Set `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` to wait indefinitely."* — `claude -p` kills background agents 600 s after the driver's final response. The driver awaited correctly; the harness killed the workers underneath it. **Read the log of the failure before theorising about the failure.** An opus worker doing money-math re-derivation or a capture container build takes 20–25 minutes, so the ceiling is removed, not raised.
- **Tell workers to commit early and often, and the ceiling stops being fatal.** All four workers this fire had commits on their branches within 10 minutes of dispatch. Even a kill would have cost minutes, not the whole task. Cheap insurance; make it standard in the worker brief.
- **A live foreground wait keeps a doomed fire alive.** An orchestrator that cannot change its own process environment can still hold the turn open with bounded foreground polls. That is what let this fire run four 20-minute workers under a ceiling that had killed the previous four fires.

**Money and evidence:**

- **"The corpus passes" has now failed as evidence five consecutive times.** T23, T26, T29, T32 and T34 each found a NEW P0 in a surface no previous round had examined, and in every case the committed corpus reproduced both the right reading and the wrong one. Five wrong readings are now known to be corpus-invisible: ratio-is-always-1, textbook `balance × rateFactor`, wrong-`n`, `RepaymentEvery`-instead-of-`periodRatio`, and the whole-principal pre-disbursement balance. **Plan for the next review to find something; a clean verdict is the surprise, not the default.**
- **Compare every cell, not the headline scalars.** The "13 of 13 observations reproduce" claim compared three scalars per shape — level installment, final installment, total interest — and never a due date or an outstanding balance. The first *observed* defect in DEC-1 lived in exactly the cells that check never looked at, and full-row comparison is what surfaced it. A conformance check's **shape** is part of its strength; state what it compared.
- **Two call sites into the same helper are two different specifications.** The rate factor's third argument is `repaymentEvery` at one entry point and `periodRatio` — a seed-date difference carrying a month-end special case — at the other, and the second is the one the graded path takes. They coincide under regular anchoring, which is why twelve captures and thirteen observations cannot see the difference, while 480 of 480 swept requests in the drift region return different money. **When a contract cites a helper, cite the call site, not the helper.**
- **An observation outranks a re-derivation of the same defect.** T34 raised the pre-disbursement balance from the text alone as a P1; T37 then *observed* it (oracle `0.00` vs the document's `10,548,069.00`). Independent corroboration across a review and a capture, produced with no shared context, is the strongest evidence this pipeline generates — and it upgrades severity.
- **A precondition script is only worth what its negative run proves.** T36's 15 assertions were validated by running them against the stock tenant and watching them **exit 1 with five breaches**. An assertion suite that has never failed has not been tested. Include a **behavioural canary** (a half-cent result that differs by rounding mode), because a configuration row proves what was configured, not what arithmetic is actually in force.
- **Re-emit a capture input-for-input before you add cases to it.** T35 added columns to the pass-3 capture and proved 1560/1560 published values identical before trusting the new ones — then deliberately declined to add new *cases* in the same pass, because that would have destroyed the identity check that makes the re-emission meaningful. New cases belong in a new pass with new ids.
- **A field can be present and still carry no information.** `totalOutstandingAmount` is `"0"` at scale 0 on every capture — not rounding, but a hard-coded `BigDecimal.ZERO` passed straight through. And every fee and penalty in the corpus is `0.00`, so the corpus has **zero** discriminating power over charges. Coverage is what a corpus can *distinguish*, never what it contains.

**Process:**

- **Partition the write surface by directory when running parallel workers over one shared resource.** Three capture workers ran concurrently against one Fineract instance with zero conflicts: one owned the running server, two ran throwaway containers mounting their own worktrees, and each owned a disjoint subtree. Naming the forbidden paths explicitly in each brief — including *which sibling owns them* — cost a paragraph and prevented every collision.
- **Give the shared mutable resource a single owner.** Only one worker was permitted to touch the live server, and it was told why: a restart would have destroyed a sibling's run. It complied, did additive-only work, and both sibling runs completed.


### Run 1 — local fire `20260819-080001` (oracle REACHABLE; five workers)

**The fire that turned the last re-derived P0 into an observation, and found the corpus blind to a whole field family.**

**Process — a new way to lose a worker's output:**

- **A finished worker whose output is never merged is lost exactly as thoroughly as a killed one.** The previous fire raised T38, dispatched it, and the worker committed a complete DEC-1 revision 7 to `softhouse/T38-dec1-v7` — then the fire exited without merging it and left `tasks.json` saying `pending`. This fire's dispatch would have redone fifteen commits of opus work. It was caught only because the worker was told to check for an existing branch first. **STEP 5.5 is not just about killed workers: `tasks.json` must be made truthful about branches that already carry finished work.** Cheap defence, now standard in the worker brief: *run `git branch --list 'softhouse/<taskid>*'` before starting; if it has commits, branch a superset and verify instead of duplicating.*
- **Verifying a sibling's finished work is a better use of a worker than redoing it.** T38 pass 2 spent its whole budget re-opening every cited `file:line`, re-running all seven committed probes, and hand-re-deriving the key figure — and found **two defects in revision 7 itself**, including a provenance clause ("no live oracle was reachable when this revision was written") that was **false**, because three sibling capture tasks had contacted the live oracle in the same fire. A document's claims about its own provenance go stale when the fire around it does more than the document's author did.
- **Merge selectively when a worker's branch predates the orchestrator's own commits.** All three branches this fire showed `main`-side files as "changed" in `git diff main..branch` purely because the branch was behind. Merging wholesale would have silently reverted the orchestrator's gate triage, manifest and fire log. **Check what the worker *authored* (`git diff --name-only $(git merge-base main <branch>)..<branch>`), not what differs.**

**Evidence — what this fire proved:**

- **An observation can confirm a re-derivation exactly, and it is still worth taking.** T34 re-derived the `periodRatio` defect and the orchestrator confirmed it from source; T39 then *observed* it — **415 of 415 disagreeing cells to `periodRatio`, 0 of 415 to `RepaymentEvery`**, with T34's worst re-derived gap (MNT 398,967.73) reproduced digit for digit. Nothing changed in the conclusion, and the evidential status changed completely. Re-derivation says what the source means; observation says what the oracle does.
- **Coverage is what a corpus can distinguish.** Every fee and penalty in the entire committed corpus was `0.00`, so charges were ungraded. One capture task closed it and immediately found: `totalRepaymentExpected` **omits every charge applied in the main schedule loop** (invariant fails 15 of 21; the progressive generator never calls `addTotalRepaymentExpected` [`ProgressiveLoanScheduleGenerator.java:367-382`] where the cumulative one does [`AbstractCumulativeLoanScheduleGenerator.java:504`] — **the two generators disagree**), and **two ways to lose a charge silently at HTTP 200**, byte-identical to a zero-charge response, where an otherwise identical *flat* charge on the same date is paid.
- **The three-scalar comparison failed again, and this time on a whole field family.** Level installment, final installment and total interest were identical to the control on **all 21** charge captures. Every one of the findings above lives outside those three cells. Full-cell comparison is not a refinement of the check — on some defect classes it is the only version of the check that exists.
- **Attestation can attest the wrong thing.** `patterns.md` already said a configuration row proves what was configured, not what arithmetic is in force. T39 showed the program's own attestations partly fell into it: forcing the tenant mode to `DOWN` changed `MoneyHelper.getMathContext()` **on the oracle's own testimony** and left all 16 observed blocks byte-identical, while forcing the **threaded** context moved 15 of 16. **Only the threaded context is evidence about money.** Ask not "did the oracle report the setting" but "did the setting move a number".
- **A parameter can be ratified and still unobservable.** Threaded precision 19 vs 12 is indistinguishable across all 16 shapes tried. That does not make the ratified value wrong; it makes it **ungraded**, and the honest move is to say so and mark a separating shape `TO_BE_CAPTURED` rather than let "attested" imply "witnessed".
- **Two findings can look like one until you measure their shapes.** The `periodRatio` defect and the month-end special case seemed to be the same vector's job. Over 51,729 same-month pairs × 3 terms the special case fires on 210, and on **zero** of those does `start ≠ disbursement` — **disjoint**, so one vector cannot discharge both. Before writing "one vector covers X and Y", measure whether X and Y ever co-occur.


### Run 1 — local fire `20260819-080001`, rounds 3–5 (eight workers, all merged)

**The round where the pipeline started catching the orchestrator.**

- **A worker refusing a wrong instruction is the control working, not friction.** The orchestrator's brief
  to T47 stated the month-end consequence **transposed** — packed-without-the-special-case identical,
  naive-with not. Both halves were backwards. T47 re-derived, found exactly one wrong combination of four
  (`packed ∧ no special case`), **wrote what the measurement said and flagged the brief.** The orchestrator
  then re-verified the direction from T46's committed output before merging. Write briefs that carry the
  *evidence* and not only the *conclusion*, so a worker can catch you; and when one does, check its claim
  against the artefact rather than against your own memory of it.
- **The orchestrator's own files need auditing too.** `reference-oracle.md` was corrected **twice in one
  fire** by workers auditing edits the orchestrator had folded in from a handoff — a miscounted
  `MathContext` inventory (9 sites, not 13, with two precision-8 sites omitted, one of them in **share
  accounts** rather than savings) and a wiring row citing two lines that do not call `generate`. A handoff
  is a claim, not a fact; folding one into a durable file inherits its errors.
- **Ratification freezes, so "no P0" is not the bar.** T43 returned ACCEPTED WITH REQUIRED CHANGES with no
  P0 — the first such round in eight — and **recommended ratifying**. The driver declined, because a ratified
  DEC-n cannot be amended by an agent without a gate and one finding was a **known-wrong sentence about
  money**. Two revisions later the same finding was not merely corrected but **refuted by the corpus**
  (revision 8's reading reproduces the charge rows on 13 of 21 captures, revision 9's on 21 of 21). *A
  reviewer may recommend policy; it does not set it.*
- **"Not captured" and "not capturable" are different facts, and shipping the first when the second is true
  is a defect.** T46 proved the month-end special case cannot be separated at all — closed form (the special
  case **is** the compensation for packed whole-months), an exhaustive sweep over all **112,147,776** ordered
  date pairs 2000–2040 inside the pinned image, and observation closing the one escape route (the `YEARS` arm
  could separate it but throws). Revision 10 **withdrew** the `TO_BE_CAPTURED`. A backlog item that can never
  be closed is worse than no item: it reads as work remaining forever.
- **A task that refutes its own premise has done its job.** T48 was told the "deliberate exactness" at
  `:1969-1980` was the most interesting thing to confirm. It found the site **unreachable** — the sole caller
  passes the literal `BigDecimal.ONE`, so a port that rounded there would not diverge — and said so, saving a
  future fire from chasing it. Brief the hypothesis; reward the refutation.
- **Every capture set proves something narrower than its handoff claims.** T44 audited three sets and found
  no synthesised number and no wrong conclusion, but **three coverage claims** that did not hold. The
  capturer is the worst-placed party to state the limits of its own capture.
- **Independent convergence keeps being the strongest signal.** T43 and T44, with no shared context, both
  found that a citation used four times to prove two generators *differ* points at the line they *share*.
  T44 also reached two findings twice across its own legs.
- **Absence beats difference as an evidentiary technique.** To test whether a context is read, do not change
  it and look for movement — **remove it and see whether anything throws**. T42 registered a tenant but never
  initialised its rounding mode, so any ambient read would fail; schedules still generated on 11 of 13 shapes.
  That is a stronger statement than "changing it moved nothing", and it is what upgraded three later findings.
- **A ratified parameter can still be unobservable — until someone looks harder.** Precision 19 vs 12 was
  indistinguishable across 16 shapes (T39), then separated on an ordinary loan at 360 periods (T42). Note the
  separation is **not monotone in principal**, so there is no threshold to reason from. "We could not find a
  separating shape" is a statement about the search, not about the parameter.

<!-- LEARNED PATTERNS END -->
