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

- **Re-derive the BLOCKER, not just the finding.** Two consecutive fires recorded N46-1 as "needs a tenant
  write on the shared server", and it sat `TO_BE_CAPTURED` for both. The blocker was **wrong**: on Path B
  the ambient context *is* the threaded object [`LoanScheduleAssembler:753` reads `getMathContext()`,
  `:765` threads that same cached reference], so a tenant write moves both axes together and separates
  nothing. The experiment everyone was waiting for could never have worked, while the one that did needed
  **no server, no tenant write and no database** — just an in-process run setting ambient and threaded
  differently. When a task reports something uncapturable, **the reason is a claim, and it is exactly as
  falsifiable as the finding.** Re-derive it before you plan a fire around it.
- **Two overloads of one helper are two specifications.** `MathUtil.percentageOf(x, p, 19)` takes the
  **ambient** rounding mode; `percentageOf(x, p, mc)` takes the **threaded** one — 7/7 and 7/7. Likewise
  `Money.of(currency, amount)` injects the ambient context while the 3-arg form does not. A porter reading
  one overload and generalising has silently picked a rounding rule. **Grep every overload of any helper on
  a money path, not just the one the call site you are reading happens to use.**
- **A latent defect in the oracle is an active defect in the port.** On the shipped server the ambient and
  threaded contexts are the *same object*, so Fineract never exhibits the charge-rounding leak. It goes live
  the moment a port threads a context — which is precisely the idiomatic Go translation. **"The oracle is
  never wrong here" does not mean "a faithful port cannot be wrong here."** Look for defect classes the
  *translation* introduces, not only those the source exhibits.
- **Check what the seam hard-wires before you design a harness on it.** `ProgressiveLoanScheduleGenerator:81`
  — the Path A embeddable seam — calls `generate(mc, loanApplicationTerms, null, null)`. `loanCharges` is
  **hard-wired null**, so that seam can *never* exercise a charge, and charge conformance can only ever be
  graded on Path B. This was discovered in the same fire that captured 21 charge shapes *through Path B*
  without anyone noticing the other seam was structurally blind to them. **Read the seam's own call, not
  its signature.**
- **Linearity hides a difference.** T48 concluded `chargeCalculationType` 5 needed a multi-disbursement
  product. It did not: `LoanChargeAssembler:190-204` builds one charge per tranche, so `Σ p·tᵢ = p·Σtᵢ` and
  a tranche product is byte-identical to the single-disbursement one — **0 of 302 cells**. What separates it
  is breaking the linearity: tranches summing to less than the principal (`12,345.00` vs `14,814.00`, the
  ratio exactly `1,000,000/1,200,000`), or a `minCap`/`maxCap` that clips per-component. **A shape whose
  components sum to the whole cannot distinguish per-component arithmetic from whole-computation
  arithmetic** — and the premise "we need a richer product" was wrong twice before it was tested.
- **A live slot fed by an inert setting.** Proving the *reader* moves money is not proving the *setting*
  does. T51 traced both readers of the aliased slot and showed each moves money against its own control
  (79/153 and 52/164 cells) — and then showed the product setting that feeds it changes **0 cells** across
  8 shapes on two products matched on 20 SQL columns. The slot is LIVE; the setting is INERT; the value
  arrives from a **tenant-global configuration** in a different scope entirely
  [`LoanScheduleAssembler:370-371`]. **Vary the writer and trace the reader — a finding that does only one
  of the two is half a finding**, and the half it omits is the one that tells a porter what to wire.
- **A false sentence is cheapest to fix before it is frozen.** The driver has now declined ratification
  twice on **no-P0** reviews, both times because a known-false sentence was about to be frozen into
  `contract.go` or the ADR — and both times the next revision proved the sentence really was wrong. One
  of them (§4.9's "no capture exercises it") had already been retired **five revisions and eight review
  rounds** earlier in a *different section*, and leaked the whole time. **Ratification freezes; grep for
  restatements of every claim you correct, in every section that restates it, not only the one the review
  named.**


### Run 1 — local fire `20260820-110001` (oracle REACHABLE; six workers, all six completed)

- **What worked**: six workers dispatched, six completed, all merged, nothing lost, no isolation
  violation, no scope breach. Corpus **32 → 36 parity vectors, 2,495 → 4,034 graded cells**;
  `--prove` **20 → 21 proofs**. Every headline number re-run by the driver, not taken from a report.
- **What the independent reviewer caught** (measured):
  - **T67 REJECTED T65** — a money-path change whose *executable* part was sound and unbreakable, on
    the ground that its **written rule was still false**. The driver confirmed two of the three from
    committed source before ruling: the fold reads `m.minorDigits` (via `minorFromMajor`), which the
    comment's "ONLY these stored fields" list omitted; and the comment filed `period idx` under
    "NOT read" while `calculatedDueInterestMinor` calls `interestChainUpTo(p.idx)` — **`p.idx` is the
    memo's lookup key**, so the stated rule was not even sufficient.
  - **T69 then found a defect in T67's own replacement text** (`ProgressiveEMICalculator.java:247` is
    on the `allowFullTermForTranche` branch; the ordinary path is `:747`), and **refused to assert a
    third reason** for `futureUnrecognizedInterest`, marking it `[UNVERIFIED]` and naming T66.
  - **T68 found the correction document was itself wrong about its own reason, twice** — P-11
    recursing one level up.
- **New patterns**:
  - **P-12 — a right conclusion on a wrong reason recurs in the artefact written to record it.**
    T64 corrected its vector text when the harness refuted its first draft and did not carry the
    correction into `MECHANISM-CORRECTION.md`. When a claim is corrected, **sweep for every
    restatement of it**, including in the document whose subject is the correction. Third recurrence
    of the corrections-leak failure; it is now the single most reliable defect in this pipeline.
  - **P-13 — for a specification-bearing comment, the comment IS the deliverable.** A reviewer that
    verifies the code and waves through the prose has reviewed the cheaper half. T65's diff was
    correct and was still rightly rejected: the rule is what the next contributor checks a new write
    site against, so a rule that is subtly false is a P1, not a nit.
  - **P-14 — a mutation that no vector can distinguish is a blind spot, not an absence.**
    `ZP-RESIDUAL-NO-RECURSION` was green on all 32 vectors and is red at 36. The ungraded path T59
    declined to "optimise" is now graded, and the refusal was vindicated: T67 independently confirmed
    the port's recursion is faithful to `ProgressiveEMICalculator.java:1211-1214`.
- **Vectors added / contexts at parity**: `T64-ZP-A/B/C/D` (zero-principal rows at the rounding
  floor). Tier 0 remains the only context with any parity at all; **nothing is cut over**.
- **Claims marked UNVERIFIED, carried forward**: `futureUnrecognizedInterest`'s closing mechanism
  (T66 settles it by oracle capture); the negative-clamp counterfactual `ZP-PRINCIPAL-NOT-CLAMPED`
  survives all 36 and is still ungraded.
- **Verifier**: `go build` 0 · `go test` ok (loanschedule 7.6 s, conformance 6.5 s) ·
  conformance **exit 0, 36 parity vectors, 4,034 cells, 0 inadmissible, 0 harness errors** ·
  six invariants **hold 37 / violated 0 / not-asserted 0** · `--prove` **21 passed, 0 failed** ·
  `gofmt -l` names exactly the frozen `contract.go` (gate G-3, expected).
- **Backlog carried forward**: B-1 (ACT/ACT arm blocks the fold-vs-closed-form question);
  `ZP-PRINCIPAL-NOT-CLAMPED` ungraded; `report.go:113` still prints that no vector separates HALF_UP
  from HALF_EVEN, which **T61 falsified** — a stale fact inside the reporter itself; proof 8b carries
  a literal `self-test fixtures PASS 1`; single-vector-kill fragility for `ZP-RESIDUAL-NO-RECURSION`.
- **Closed as already-satisfied**: T62's follow-up F-1 (wire up a contract-digest guard) —
  `VerifyContractDigest` already fires at `grade.go:237` before `LoadStore`, driver-confirmed.


### P-15 — a rejection is terminal for its task ID, and must name its successor in a FIELD

*Fire 20260820-140000. `rehydrate-check.sh` flagged rejected `T70` as re-runnable, exactly as it flagged
`T65` in fire 20260820-110001.* The two rejections differ and the difference is the point: `T65`'s commits
**were** merged (via `T69`), so `superseded` fit; `T70`'s were **deliberately not merged** and are preserved
on its branch for `T72` to branch from. Both are terminal **for that task id** — this pipeline never re-runs
a rejected id, because the retry carries a new one (`T65`→`T69`, `T70`→`T72`).

That makes a new failure mode possible: a rejection that is terminal, unmerged, and has **nobody assigned to
finish it**. So `rejected` is terminal *only* alongside a guard requiring an explicit `superseded_by`.

**The guard's first draft was a silent false green, and only testing it found that.** It scanned note text
for the rejected id — and `T15`'s note mentions `T70` in passing ("archiving now would freeze the marker"),
which the scan counted as a successor. It **passed with the real successor deleted**. Rewritten to read an
explicit `superseded_by` field and then falsified two ways (successor deleted; field removed), both exiting
1, with the honest state exiting 0.

**An assertion that cannot fail is worse than no assertion** — it converts "not checked" into "checked and
fine". This is `P-14` ("a mutation no vector can distinguish is a blind spot, not an absence") applied to the
scheduler's own state, and `T62`'s silent-false-green defect class recurring in a third place. *Test the
guard, not just the thing it guards.*

### P-16 — the driver's own claims are worker-checkable, and this fire two of them were wrong

*Fire 20260820-140000.* The driver committed a source-derived hypothesis to `.softhouse/reviews/` **before**
dispatching `T66`, precisely so the ruling could not turn on whose report read better. **`T66` refuted it**,
and the driver's error was structural: it reasoned about the live model when the lookup runs on a
**till-date-truncated deep copy**. The driver then **overstated a finding against `T66`** and withdrew it on
checking, and separately **propagated an unchecked line number** (`:1226`, actually `:1224`) out of `T66`'s
own prediction, into its re-derivation, and onward into `T70`'s dispatch prompt — `P-12` recurring in the
document whose job was checking.

Two consequences worth keeping:
1. **Register the driver's reasoning before the worker reports.** It cost nothing and made a refutation
   legible instead of arguable.
2. **A number copied from the artefact under review is not evidence, it is the artefact's claim.** Resolve
   every citation against the pinned source before repeating it — especially in a document whose purpose is
   to check that artefact.


### P-17 — a `parked` list is evidence of a past state, never a work queue

Fire `20260820-170001` dispatched a full opus worker (T76) to close four `P0` items its brief said were
"still open, still blocking vector promotion." **All four had been closed two days earlier** by T30 and T36.
The stale sentence lived in `RESUME.md` *and* in the parked task's own `note` — neither was updated when the
closing work landed, because nothing in the pipeline updates a park list except the task that wrote it.

The worker checked before acting, registered the refutation in a commit that is a **parent** of its evidence
commit, and converted the fire into genuine findings anyway. That recovery is not the lesson; the dispatch is.

> **Rule.** Before dispatching from any park list, deferred-item list, or "still outstanding" paragraph,
> `git log` the artefacts it names and confirm no later commit closed them. Treat such a list as a
> **timestamped observation**, not as state. When you close someone else's parked item, amend the note that
> parked it — a closure recorded only in your own commit message is invisible to the next fire.

### P-18 — when four rounds of enumeration keep failing, the strategy is the defect, not the draft

One comment block took **five drafts**: T65 rejected by T67, T69 fixing it and finding a defect in T67's own
replacement text, T70 rejected by T71, T72 rejected by T73. Every rejection had the same shape — the rule was
**true but insufficient**, and each reviewer found the next hole one call frame further out. Each retry brief
said "fix the reviewer's findings," which produced the next true-but-insufficient enumeration.

The fifth draft was briefed differently: *stop enumerating; state it in closed form.* It worked because a
**closure argument** was available and nobody had looked for one — the entry points to the decisive method
are in bijection with a four-constant enum fixed by the compiler, so a fifth route cannot appear without a
compile-visible edit to the pinned oracle. It also surfaced a third writer of the field that four rounds of
enumeration had missed.

> **Rule.** Two consecutive rejections of the same kind are a signal about the *instruction*, not the worker.
> Before dispatching retry number three, ask what would make the rule **closed** — an exhaustive census, a
> compiler-enforced bound, a bijection — and brief that instead of another round of patches. A rule that
> enumerates safe cases is only as good as the enumerator's imagination; a rule that bounds the space is not.

### P-19 — a green conformance run is silent about regions no vector covers, and that silence reads as safety

This fire's most consequential finding was made by a **reviewer approving someone else's work**, not by any
capture task: inside the graded domain, at a small principal, the reference oracle emits a schedule that
never amortizes to zero while the port returns zero. Conformance was PASS, 42 vectors, 5,576 cells,
**0 invariant violations** — throughout. It was green because nothing pointed at that region.

> **Rule.** "Conformance PASS" means *matches the oracle where we looked.* When reporting it, say what the
> corpus does **not** reach; a bare PASS invites the reader to hear "the port is correct." Reviewers should
> be chartered to probe the region **around** the work, not only to re-check the work — that is where the
> unvectored divergences are, by construction.


### P-20. A driver's dispatch brief is an unreviewed artefact, and it can be WRONG in ways the worker must be free to refuse

**Fire `20260820-200002`.** Two briefs written by the driver carried false premises, and both were caught by
the worker rather than by the driver:

- **T79** was told *"if the bijection fails, the closed form does not close."* It checked, found the site→Action
  mapping is **not** injective (`EmiChangeOperation.java:64-69`'s `withZeroAmount()` preserves the action, so
  `ProgressiveEMICalculator.java:1751`'s `addDisbursement` can carry `CAPITALIZED_INCOME`; `:1107` is a further
  call site) — and **refused the framing**, showing closure rests on the grep-reproducible call-site *count*,
  not on injectivity.
- **T81** was told *"`bash` via an `sh` symlink and `bash --posix` are legitimate runs that must not trip the
  guard."* On this machine `/bin/sh` **is** bash 3.2.57, and bash 3.2 disables process substitution in POSIX
  mode — so both genuinely fail. It feature-tested the **capability** instead of the shell name and flagged the
  contradiction. T86 verified the binaries and confirmed it.

Both workers were right, and a compliant worker would have shipped the driver's error into a specification or a
grading harness.

> **Rule.** Write briefs so a premise can be refused: state the driver's reasoning as reasoning, mark which
> claims are unverified, and say explicitly that refuting the brief is a valid outcome. When a worker refutes
> one, record it as the control working — and correct it **at source** before the next task inherits it.

### P-21. Correcting a defect where it was *named* leaves it where it is *restated* — including one level up, in the attestation

**Fire `20260820-200002`, four independent instances.** A grep for the corrected *value* cannot find a
restatement that vouches for it by *count* or renders it in a different *shape*:

- **T88** fixed a grep count in the two places it appeared, then T89 found `emi.go:928`'s
  `[VERIFIED at T78: all five counts re-derived by grep…]` — an attestation certifying, in T78's name, a
  number T78 never produced. T88 had raised this exact hazard itself (F-T88-3) and still walked into it.
- **T82** swept for a stale census with two regexes tuned to a banner's phrasing; T87 found a **fourth** copy
  rendered as a markdown table, inside a file T82 had edited twice, contradicting line 217 of that same file.
  P-12 landing inside the task assigned to close P-12.

The remedy that worked (T98) was to **split the search space rather than weaken the pattern**: a bare-numeral
net over prose assuming no phrasing, plus shape-free structural nets — and to **write the blind spots down**,
including the two that grep cannot close at all (a census with no number; a census spelled out in words).

> **Rule.** A correction task must sweep for the finding's *restatements and its attestations*, not its
> numerals, and must publish what its sweep structurally could not have found. A brief that names one location
> invites the leak; say "and every restatement of it."

### P-22. A guard, a canary, or a control that cannot fail is worse than none — because it is believed

**Fire `20260820-200002`, the fire's dominant theme, found five separate times.**

- A **canary** that printed a sha256 without ever comparing it certified `HALF_UP` **on a HALF_EVEN JVM** (T77→T80).
- An **abort** that wrote FAIL to stderr while the gate grepped a stdout-only `tee` let a capture be taken on the
  wrong tenant and filed under the right tenant's name (T77→T80).
- A **precondition** whose table was built by looping over the very ids it then checked had an empty domain, and
  it was advertised as the fix for defaulting (T75→T82).
- A **green control** with zero discriminating power printed that it had some — `main` produced identical output
  (T87→T98). The author called it an honesty-rule breach.
- An `attest.py` that stamped provenance **before** testing its gate printed *"no capture attempted, no
  attestation written"* while having already mislabelled 11 captures (T85→T80).

Every one was found by someone **attacking** the rig, never by reading it. Two were found inside the task sent
to fix the previous one.

> **Rule.** Ship no guard you have not personally driven **red**. State the input that makes it fail, and commit
> the transcript. For a fix, run the counterproof against the **real pre-fix bytes** (`git show main:`), because
> a proof that only shows the "after" cannot distinguish a fix from a no-op. And a guard that inspects zero
> files must be an error, not a pass.

### P-23. A measurement can be perfectly reproduced and its CONCLUSIONS still be false — scope every claim to the family it holds for

**Fire `20260820-200002`, T84 on T83.** T84 reproduced T83's capture byte-identically (canonical sha256
`01b41d9c…`), re-derived the boundary table row for row with its own classifier, and re-asked 12 boundary cells
with different tenant ids and reversed ordering — 12/12 identical. It then **REJECTED**, because three
conclusions T83 had written into `gates.md` — *the artefact the decision-maker reads* — were false as stated:

- G-8 is **two phenomena**, not one. A second family (600 % p.a., MNT 0.01, n ≥ 104, 22 cells) fails to sum at
  all and survives a forced memo recompute, so it is a genuine non-amortization — refuting the driver's
  reframing on the driver's own stated discriminator.
- "`invariant_exemptions` is inert, so option (a) needs a port change" holds only on the sub-family where the
  port diverges; elsewhere the exemption yields PASS with **zero port change**.
- "Everything is far below one MNT" was false at **MNT 1.09 / 3.6 % / n=360** — an ordinary 30-year term.

> **Rule.** Grade the write-up as a separate artefact from the measurement, and grade it hardest where it feeds
> a `user` gate. Every sentence must name the domain it was measured over and say what was not swept. A
> reviewer that only re-runs the numbers has reviewed half the deliverable.


### P-24. An assertion about what happens ON MERGE can only be tested BY MERGING

**Fire `20260820-200002`, T87 → T98 → the driver.** T87 observed that T82's counterproofs used the moving ref
`main:` as their baseline, so *on merge* all seven would flip to failing against the rig itself. T98 fixed it
by pinning to `git merge-base main HEAD` and reported it as "the immutable fork point `8da4b83`" — verifying
**on the branch**, where that is exactly what it resolves to.

On merged `main`, `HEAD == main`, so `git merge-base main HEAD` is the **merge commit itself** and every
counterproof compares the fixed code against itself. The driver merged, ran `prove-guards-go-red.sh`, and got
**"18 as expected, 7 not as expected"** — the same seven rows, the time bomb relocated rather than removed.
The merges were unpushed and were backed out; `main` never carried it.

Three competent parties looked at this — the reviewer who predicted it, the author who fixed it, and the
driver who charged it — and all three would have missed it, because every one of them tested in the state
where the bug is invisible.

> **Rule.** When a property is asserted about the *post-merge* state, verify it on a **scratch merge into
> current main**, never on the branch. And prefer a literal immutable sha to any ref that is computed from
> `main`: a baseline that can follow `main` will follow it exactly when you stop watching. The driver's
> post-merge re-run of the artefact — not of conformance, of the *artefact* — is what caught this; make it
> a standing step.

### P-25. The no-floating-point rule binds ANALYSIS scripts too — a float there is a money defect one remove

**Fire `20260820-230001`, gate G-8, found by the driver correcting itself on `main`.** The non-negotiable is
stated as *money is integer minor units — no floating point in any monetary code path, struct field, schema
column, API field, or test fixture.* Every worker read that list as exhaustive, and the list does not contain
**the scripts that analyse the captures**.

T84's prediction/analysis script computed `B·a` in double precision, read a residual of `+4.8e-20` as an exact
tie, and put a **wrong refutation count — 18 instead of 22 — into the gate write-up Buyan reads.** The port was
never wrong. The vectors were never wrong. The number that reached the product owner was.

The script never touches production, so no reviewer graded it as money code; and its output is a *count*, not
an amount, so it does not look like money at all. That is precisely why it got through.

> **Rule.** The rule binds anything whose output is used to reason about money — analysis scripts, prediction
> scripts, boundary classifiers, sweep summarisers, the one-off `python3 -c` in a handoff. Use `decimal` or
> integers, and at the tenant's ratified `MathContext(19, HALF_UP)` when the quantity is derived from an amount.
> The test is not "does this run in production", it is **"if this number is wrong, does a wrong money claim
> reach a human?"** An exact-tie test written in binary floating point is the canonical instance: `a == b` on
> two doubles is not the question anyone meant to ask.

### P-26. Sweep for the CONCEPT and the NUMBERS, not for the sentence — and state what the sweep could not have found

**Fires `20260820-200002` and `20260820-230001`, T101 → T112; the second occurrence of P-21 by a new route.**
P-21 already said a correction lands where the defect was *named* and not where it is *restated*. T112 met the
sharper version: T100 had **scoped the discriminator table correctly** and left the **prose restatement nine
lines later** unscoped, so `gates.md:1040` claimed "family A exists at all 12 rates swept" while the table at
`:925` showed 11 of 12 — the missing rate being 600.0 %, **the rate that defines family B**. The document
contradicted itself inside ten lines, and a grep for the corrected sentence would have found neither site.

> **Rule.** After any correction, sweep for the **concept** and for the **numbers**, never for the wording — the
> restatement that does damage is the one phrased differently. Grep the figures (`12`, `all 12`, `every rate`),
> grep the entity (`family A`), and read every hit. Then **write down what the sweep could not have found**: a
> claim restated as a chart, as a count in a summary table, in another file, or as a silence where a
> qualification should be. A sweep whose limits are unstated reads as exhaustive.

### P-27. Do not keep a second copy of a document you are correcting

**Fire `20260820-230001`, T112.** An evidence directory held `g8-section.md`, a working copy of the gate section
from `gates.md`. It had already drifted from the original, and it carried the false F-1 sentence **verbatim** —
so correcting `gates.md` would have left a fully-formed, plausible, wrong copy sitting in the committed evidence
for the next reader to cite. T112 deleted it.

> **Rule.** A worker that wants a working copy of a document reads the document; it does not fork it. Where a
> second copy genuinely must exist, it is generated from the first at build time, or it carries a loud pointer to
> the original and no substantive prose of its own. **Two copies of a claim is one claim and one time bomb**, and
> it is the same failure as P-21 with the drift built in from the start.

### P-28. A rescued branch with no handoff is indistinguishable from an abandoned one — the ledger must say which

**Fire `20260821-080001`, at entry.** The previous fire ended with three workers killed mid-flight. The wrapper's
worktree sweep did its job and rescued all three to `rescued-agent-*` branches — the mechanism built after the
2026-08-18 incident that stranded 4,482 insertions worked exactly as designed.

What did not work was the **ledger**. All three tasks still read `in_progress`, which tells the next fire that
work is happening when nothing is; none named its rescue branch; and the branches were named after opaque agent
ids, not tasks. So the next fire's cheapest reading of the state was *"three tasks are mid-flight"* — and its
second-cheapest was *"three tasks were abandoned, re-do them."*

Both were wrong, and expensively so. Re-opening the rescues showed **T107's was a substantially complete 575-line
independent review** carrying a MICRO-FIX verdict and all nine rulings its brief asked for, including the one
that mattered most — *zero of 42 promoted parity vectors depend on the unhardened gate*. T99's was seven commits
and 3,533 insertions covering all four of its findings with red/green proof scripts. **The only thing either was
missing was the handoff that says "I am finished."** Discarding them would have thrown away most of a fire.

> **Rule.** Rescuing the bytes is half the job; the other half is the ledger. A killed worker's task becomes
> `needs_retry` — never `in_progress` — with a note naming its rescue branch and stating **completeness
> unverified**. Re-point the real task branch at the rescue so the work is findable by task id rather than by
> agent id. And the next fire's first move on a rescue is to **read it before judging it**: the handoff is the
> last thing a worker writes, so its absence says nothing whatever about how much of the work was done.

**And then audit it, because a rescued document is a CLAIM, not a finding.** Re-running T107's review found its
substance and its verdict entirely correct — and still turned up a `[VERIFIED: my own runs]` badge on a claim
that **cannot be true on this host** (a silent-miss attributed to `ugrep`, which is not installed here, and whose
`PATH` entry `/pkg/env/global/bin` does not exist), plus six factual errors in file counts, line ranges and
attribution. The killed worker never got to the step where it would have checked its own tags.

> **Corollary.** Rescue the file; do not rescue its badges. Every `[VERIFIED]` in rescued work is downgraded to
> `[UNVERIFIED]` until somebody re-runs it — the tag asserts a measurement was made, and the one thing you know
> about a killed worker is that it stopped partway through making them.

### P-29. A COUNT is a weak tripwire: a narrow scope is green on the edit that widens it, and a line count is green on a cancelling pair

**Fire `20260821-080001`, T96, closing T89's F-T89-4.** The `futureUnrecognizedInterest` block defends its closure
argument with five grep censuses. T96 was sent to add a sixth — `:743` is the sole caller of
`calculateEMIOnNewModelAndMerge` — and to prove the new tripwire fires. It did. Then it asked the same question
of the five that already shipped, and **two of them could not detect their own defining edit**:

- **A file-scoped grep is green on the edit that leaves the file.** Graphs 2 and 3 were scoped to one file. Change
  `private` → `public` and add a caller elsewhere and the block's own command still reads **9 on a tree with five
  call sites** into the very method the argument is about. The closure-critical count, silently green. Graph 1 was
  scoped to 2 of 28 `src/main` trees.
- **A line count is green on a cancelling add/delete pair.** All six censuses count lines, so one addition offsets
  one deletion — demonstrated twice, graph 3 holding at 9 and graph 5 at 18. **This one is not fixable by a
  scalar at all**, and the honest response was to publish the limit in the block ("reproduce the LINES, not the
  total") rather than to pretend a number covers it.
- **And the new census went silently green twice before it worked.** A comma-less final enum constant, and two
  constants on one line, are both legal Java and both read 4. It took a tokenising form to count what was meant.

> **Rule.** Before shipping a count as a guard, write the edit it exists to detect **and run it**. Then write the
> edit that *should* trip it but won't — a wider scope, a cancelling pair, a legal syntax you didn't parse — and
> **publish that limit next to the number**. A census defends a *claim*; scope it to the claim's blast radius, not
> to the file you happened to be editing. And where no scalar can cover the case, say so in the artefact: a
> tripwire with a stated blind spot is honest, a tripwire with an unstated one is the vacuous guard of P-22 with
> extra arithmetic.

### P-30. The repo-local Go toolchain exists — stop marking results `[UNVERIFIED]` for want of it

**Fire `20260821-080001`, twice in one day (T109, and T91 as caught by T107b).** Two workers reported *"there is no
Go toolchain on this host"* and downgraded `go build` / `go vet` / `go test` / `gofmt -l` to `[UNVERIFIED]` on that
basis. **The premise is false.** A pinned toolchain lives at `.softhouse/toolchain/go/bin/go` (go1.26.6
darwin/arm64) — installed repo-local precisely so an agent need not modify Buyan's machine — and
`conformance.sh` **loads it itself**, which is why both workers' conformance runs were green in the same reports
that claimed no toolchain existed.

The cost is not cosmetic: an `[UNVERIFIED]` tag is how this pipeline records *"nobody has checked this"*, and
spending it on something checkable in one command devalues every honest use of it.

> **Rule.** `[UNVERIFIED]` is for what cannot be measured here, not for what the worker did not find. Before
> tagging one, check whether the tool is in the repo — and name the toolchain path in the brief so nobody has to.

### P-31. Never snapshot a file the orchestrator is actively editing — author no change to it at all

**Fire `20260821-080001`, T122, deviating from its brief and right to.** T122 was told to end its branch with
`tasks.json` **exactly as on current `main`**, to undo an evil merge. It did — then tested by merging (P-24) and
**it conflicted.** `main` had moved three times during the task and edited `tasks.json` in every one.

A snapshot of a moving file is stale the moment it is taken, and taking it *converts a file the branch does not
care about into a merge conflict*. The correct resolution is the opposite of the instruction: set the blob back to
the **merge base**, so the branch authors **no change at all** and any merge into any future `main` takes `main`'s
side with zero conflict.

Read the consequence correctly, because it looks wrong: `git diff main -- tasks.json` on such a branch is **not**
empty — it shows the branch is *behind*. That is exactly right for a file the branch must not touch. **The
post-merge check is the one that matters**, not the three-dot diff.

> **Rule.** For any file owned by the orchestrator rather than the task — `tasks.json`, `program.json`,
> `RESUME.md`, `patterns.md` — a worker branch should author **zero** change: not the current contents, not a
> merge, not a reconciliation. "Take main's copy" is a trap whenever `main` is live. This is P-24's lesson applied
> to a *file* instead of a *ref*: a baseline that can follow `main` will follow it exactly when you stop watching.

### P-32. A committed artefact and its compressed twin are not the same evidence — check which one is the capture

**Fire `20260821-080001`, T122, one step from a third wrong count on gate G-8.** `T84-evidence/out/` holds **both**
`capture-t84-raw.json` (15 captures) **and** `capture-t84-raw.json.gz` (251) — likewise t84b, 14 against 95. The
plain files are strict content-identical **subsets**; the `.gz` are the captures.

T122's first analysis ran over the plain files, found **16 family-B cells and 3 sub-ulp exceptions**, and every
number was self-consistent and plausible. The true figures are **29** and **4**. Nothing in the run looked wrong,
because a subset of a capture is a perfectly well-formed capture.

This gate has already carried two wrong counts into the document Buyan reads — 18-instead-of-22 from a float in an
analysis script (P-25), and the family A/B inversion. This would have been the third, and it would have arrived
inside the task sent to fix the second.

> **Rule.** Before analysing a capture directory, **enumerate every file that could be the evidence and count the
> records in each.** Where a plain and a compressed form both exist, establish which is authoritative and state it
> in the write-up. A plausible, internally consistent result over the wrong file is indistinguishable from a
> correct one — so the check must happen before the analysis, not after it looks odd.

### P-33. A tool claim is a claim about a binary, a version, a locale, an invocation AND an input shape — name all five

**Fire `20260821-080001`, T108, settling a four-way contradiction that had been committed as evidence for three
days.** T80 said BSD `grep -a` silently matches nothing in a UTF-8 locale on a file with an invalid multibyte
sequence. T91 could not reproduce it. T107 said it *had* reproduced it — with `ugrep -I`. T107b could not find
`ugrep` on the host at all and downgraded T107's `[VERIFIED]`. Four workers, four claims, all committed.

**Nobody lied and nobody was careless with a number. On this host the token `grep` names two different programs,
and which one you get depends on where you type it:**

| where `grep` is typed | what runs |
|---|---|
| inside a script (`sh x.sh`, `bash x.sh`) | `/usr/bin/grep` — **BSD grep**. Shell functions are not exported to children. |
| into the Claude Code **Bash tool** | a **shell function** re-execing the `claude` binary with `argv[0]=ugrep` — **ugrep with `-I` hard-coded** |
| `command grep` / `command -v grep` | BSD grep — the function is bypassed **by design** |

And the two programs fail in **opposite** ways: BSD grep goes blind to the rest of **one line** at and right of the
invalid byte, which **`LC_ALL=C` fixes and `-a` does not**; ugrep `-I` skips the **whole file**, which **`-a` fixes
and `LC_ALL=C` does not**. So `LC_ALL=C grep -a` is right, and **both tokens are load-bearing against different
programs** — the hardening was correct all along and only its stated reason was wrong (P-11).

The two failed reproductions failed for reasons worth naming. T91's probe put the poison **after** the match at
end-of-line, and **ran both arms under `LC_ALL=C`** — the very mitigation under test. T107b used `command -v` and
ran from a script: **both blind to a shell function by construction.**

> **Rule.** Before recording a tool's behaviour, pin all five of **binary, version, locale, invocation path and
> input shape**, and put them in the transcript. Use `type -a`, never `command -v`, when the question is *which
> program runs*. Never run both arms of a comparison under the mitigation you are testing. And *N*-of-*N* green
> cells refute nothing unless the failing shape is among the *N* — "I could not reproduce it" is a statement about
> your probe until you have shown your probe can produce the effect at all.

### P-34. Every non-negotiable that has a guard has a guard that can pass without checking — three for three

**Fire `20260821-080001`.** Three separate workers, doing three unrelated tasks, each stumbled onto a guard
protecting a different **CLAUDE.md non-negotiable**, and each guard could report success having verified nothing:

| non-negotiable | guard | how it passes without checking |
|---|---|---|
| **Money is integer minor units, no floating point** | `conformance.sh:184`, `:201` | bare `grep -Eq`, neither `LC_ALL=C` nor `-a` — a float plus one invalid byte earlier on the same line is **invisible to BSD grep** (P-33) |
| **Ratified rounding mode `HALF_UP` (ordinal 4)** | `attest.py:337`, `attest-t40.py:377`, `t36/attest.py:437` | the verdict is computed, written into `attestation.json`, printed — and **gates nothing**; a `HALF_EVEN` JVM attests green |
| **PostgreSQL only; Oracle Database / MySQL / MariaDB prohibited** | `pathb/preconditions.sh` P5/P6/P11 | `grep -icE` over an **empty stream** is `0` and a dead `psql` returns `""` — a `docker` answering nothing printed **three PASS lines having scanned nothing** |

None was found by reading the guard. Each was found by someone attacking a *neighbouring* rig and noticing. And in
the third case, **the sweep written to find that exact class missed two of its own three instances**, because its
pattern was `grep -c\|grep -ac\|wc -l` and the lines were `grep -icE`.

The common shape is that a non-negotiable is *stated* in prose, and everyone downstream assumes the prose is
enforced somewhere. The guard's existence is taken as the enforcement. **Nobody had ever checked the set as a
set** — which is why three-for-three is the finding, not three separate bugs.

> **Rule.** A rule you cannot violate in a test is a rule you are not enforcing. For **every** non-negotiable,
> maintain a register naming its guard, the command that drives that guard **red**, and the date it was last seen
> red — and treat `ABSENT` as a first-class entry, because the non-negotiables with no guard at all are the ones
> this table cannot even list. When a guard is found vacuous, the next question is never "is it fixed" but **"what
> was certified through it while it was blind?"**

<!-- LEARNED PATTERNS END -->

### Run 2026-08-17-run1-harness-schedule-poc — fire `20260819-170001` (local, oracle REACHABLE) — 2026-08-19

- **What worked**: Two structural blockers fell in one fire. (1) The **no-Go-toolchain gap**, open for three
  fires, was closed **without** the durable host change earlier fires correctly declined to make unattended —
  a repo-local `GOROOT` under `.softhouse/toolchain/`, sha256-asserted before extraction, gitignored,
  reversible with one `rm -rf`. The objection was never "is a toolchain allowed"; it was "may an agent modify
  Buyan's machine unattended". Re-scoping the *install location* dissolved the objection without weakening it.
  **Generalise: when a blocker is about blast radius rather than permission, shrink the blast radius.**
  (2) **T7, the bottleneck behind seven tasks, is done and merged.**
- **What the independent reviewer caught** (measure it): no reviewer ran this fire; the **driver** did the
  adjudication and re-derived rather than accepting reports — three catches worth recording:
  - **T55-N1 re-derived from scratch and CONFIRMED digit for digit.** `LB-DEC31` has a **zero** first segment
    and still grades the ACT/ACT arm by **6,015 minor units** (ARM `0/366 + 31/365` → `22014.25`, *observed*
    on all three products; PLAIN `31/366` → `21954.10`, counterfactual). The mechanism is the real result:
    PLAIN takes its denominator from the period-**start** year (366) while ARM assigns days to the year they
    land in (365), so **segment length is irrelevant — year lengths are what matter.** DEC-1's stricter
    wording is therefore known-wrong → gate **G-4**, unamended because a ratified DEC-n is not an agent's call.
  - **`gofmt` wants to rewrite the ratified `contract.go`** (doc-comment list normalisation, inert). Not
    applied → gate **G-3**. The risk was never the output; it was that a `gofmt -w ./...` or a format-on-save
    would mutate a frozen artefact and **read as formatting noise in review**.
  - **D-2, found by re-reading a cited line instead of trusting the citation.** `ProgressiveLoanScheduleGenerator.java:83`
    hard-wires **two** nulls, not one: `loanCharges` (recorded as T50-N2) **and `holidayDetailDTO`** (never
    recorded). Holiday/non-working-day adjustment is a guaranteed **silent no-op** on Path A, null-guarded at
    `DefaultScheduledDateGenerator.java:224`. Also **D-1**: the cite is `:83`, not `:81` — `:81` is a
    different method. **A citation nobody re-opens is a claim, not a fact.**
- **Vectors added / contexts at parity**: 33 Path B leap-boundary captures (T55): **6 discriminating pairs, 5
  proven non-discriminating**, determinism 33/33 byte-identical, negative tests 9/9 breaching, invariants
  I1–I7 on all 33. **Contexts at parity: still zero, and the harness says so out loud** — `conformance.sh`
  exits **2** with *"VERDICT: UNUSABLE — THIS IS NOT A PASS"* and refuses to claim all-pass over an empty
  corpus. **Nothing is promoted yet.**
- **Claims marked UNVERIFIED** (carried forward): D-2a — that Path B reproduces holiday adjustment on the
  **final period only** — is derived from source (`:61` guards `:66`) and **not yet observed**. No T55 shape
  separates precision 19 from 12 or HALF_UP from HALF_EVEN, so `(19, HALF_UP)` is **provenance, not
  discrimination**, on those axes. The Path A seam's blind spots have been found **one at a time** and nobody
  has exhaustively audited every input it drops — expect a third.
- **New knowledge**:
  - **Pair-difference is the WRONG test for whether a vector grades a behaviour (T55-N2).** `LB-F29CROSS` and
    `LB-MULTI3F` report **0 cells** on every pair yet kill naive ports by **17,850** and **71,014** minor
    units, because the setting decides only *whether* the arm fires, never its denominators. A
    non-zero-pair promotion rule would have discarded the **three best graders** in the set. Gradeability is
    *"which named wrong implementations does this vector kill, and by how much"* — now the `graded_against[]`
    schema field. **An all-products-identical capture is not evidence of non-gradeability.**
  - **Seam blindness belongs in DATA, not code** (`capabilities.json`, absent ⇒ **default-deny**). Blind spots
    arrive one at a time; as a table, each new one is a row that immediately refuses every affected vector
    with no schema migration and no code change.
  - **Money must be an integer STRING in JSON.** Most readers (jq included) decode numbers to doubles, so an
    integral JSON *number* can be corrupted by the **reader** even when the writer was exact.
  - **Storing a derivation as an observation is a distinct defect class** — pass 3 never recorded the
    disbursement row's balance; filling it from the contract's own rule would grade the port against the
    harness's assumption. Hence `unrecorded_fields`.
  - **A grader must not contain the thing it grades** — no schedule generation or date stepping in the
    harness, so T10 cannot borrow an implementation from its own conformance runner.
  - **Worker branch names are not guaranteed.** Monitoring `softhouse/<taskid>-*` gave a **false negative**
    for 50 minutes while T55 committed 6 commits to its auto-created `worktree-agent-*` branch. Check the
    worktree's actual HEAD, not the expected branch name. The nudge sent on that false signal was harmless,
    but the panic it nearly caused was not free.
  - **`git diff main..branch` (two-dot) on a stale fork reports the ORCHESTRATOR's newer commits as
    DELETIONS.** T55 appeared to delete 67 lines of `reference-oracle.md`; three-dot showed **zero**
    deletions. Always three-dot for a scope check, exactly as the skill says.
  - **A transient API 529 is not a task failure.** T7 attempt 1 died before its first commit and everything
    was lost; attempt 2, told to commit a WIP within its first few tool calls, survived and produced 19
    commits. **Record infrastructure deaths separately from quality rejections** so they never consume
    `max_retries_per_task`.
- **Verifier**: `go build ./...` **exit 0** · `go vet ./...` **exit 0** · `go test ./...` **ok**
  (conformance 0.582 s) · `gofmt -l internal` → only `contract/contract.go` (**expected**, G-3) ·
  `conformance.sh` → **exit 2, UNUSABLE, not a pass** (correct: no port, nothing promoted) ·
  `conformance.sh --prove` → **10 passed, 0 failed** · driver's own scans: **0** float-shaped JSON numbers in
  the vector store, **0** float types in the loanschedule Go tree. **No cutover, no parity claim.**
- **Backlog carried forward**: promote the corpus into the new store (T8) — **promotion ordering matters:
  promote a covering vector BEFORE flipping `in_graded_domain`, or the run is fatal**; T9 review of harness +
  vectors; T20 (T17 F2–F6); T10 the port, now compilable; **capture D-2a on Path B**; gates **G-2, G-3, G-4**.

---

## Patterns learned — local fire `20260819-200001` (first conformance PASS in the program)

### P-1. A ZERO money margin is not evidence of non-gradeability

T55-N2 established that *pair difference* is the wrong promotion filter. This fire found the same lesson
in a second key: a counterfactual can be **real and unkillable in the money columns**.

`P-02`/`P-02b` grade the month-end re-anchor entirely in `due_date`, because they run `DAYS_30`/`DAYS_360`
and the amounts are therefore **date-independent** — the money columns are byte-identical to `P-00`'s. A port
that clamps `31 Jan → 29 Feb` and then continues from the clamped day emits `2024-03-29` where the oracle
emits `2024-03-31`. **You cannot detect that bug by watching the numbers.** `P-03` grades row ordering the
same way.

The harness had encoded gradeability as strictly money-valued (`margin_minor > 0`), which made its own
`UNBACKED in_graded_domain claims: monthend.reanchor` complaint **unsatisfiable** — pushing whoever hit it
toward fabricating a margin or dropping a capability the corpus genuinely grades. The fix (driver finding
**D-4**) was a `kind: "structural"` counterfactual requiring **named `divergent_cells` and both values in
evidence** — deliberately *harder* to state than a money margin, so it cannot be an escape hatch.

> **Rule.** Before concluding a shape grades nothing, ask which columns it *could* discriminate in. Money is
> one of several.

### P-2. Screen a counterfactual on the PRE-adjustment model, never on the oracle's own output

T57's **N-1**, and the most subtle finding of the fire. T9 screened all 11 vectors for the EMI smoothing loop
by evaluating the guard `|lastEMI − penultimateEMI| > floor(n/2)` on **the oracle's emitted schedule**. That
is the wrong screen: **the loop exists to shrink the very residual the guard measures.** Screening post-loop
therefore rejects shapes the loop actually fired on — it would have rejected `MNT 1,014,632 / 6 × 7.0 %`,
one of the two shapes DEC-1 itself names (post-loop |Δ| 2 against a threshold of 3).

T9's *conclusion* survived (T57 re-established it by direct reproduction), but **the method must not be
reused for capture selection.** Evaluate a guard on the model as it stands *when the guarded code is called*.

### P-3. A green conformance run says nothing about behaviours no vector exercises — so mutate the port

T10 mutated its own port into each named wrong implementation and re-ran the real harness. **Five were
killed; four survived, three of which move money** — including removing the **entire** EMI re-adjust loop,
which passed 11 of 11. The driver reproduced that mutation independently and confirmed exit 0.

After T57 promoted the two shapes that trip the guard, the driver re-ran the **same** mutation: it now FAILS
both new vectors with named cells and margins. That closed loop — *find the blind spot by mutation, capture
the shape that lights it, prove the mutation now dies* — is the cheapest way to learn what a corpus is
actually worth.

> **Rule.** "Conformance is green" is a claim about the corpus as much as about the port. Mutation-test the
> port against every counterfactual the vectors name, and record which mutations survive.

### P-4. Latent harness defects detonate on first real use — the first promotion is a test of the rig

`main` was green (10/10 proofs, `go test` ok) with **three** defects waiting in it, invisible because nothing
had ever exercised the paths:

- **D-4** — `LoadVector` uses `DisallowUnknownFields`, so a new counterfactual field fails at **decode**, not
  admissibility. An `admit.go`-only fix would not have landed it.
- **D-5** — `registry.go`'s replay loader had **three** silent `continue` paths and dropped any vector using
  `unrecorded_fields` on a money cell **with no diagnostic**, then reported "no vector carries this request".
- **D-6** — `conformance_test.go` hard-asserted `ParityPass == 0` ("the store has no promoted capture yet"),
  so `go test` could never be green after **any** successful promotion. A second instance existed in
  `TestGradeabilityIsNotPairDifference` that nobody had reported.

> **Rule.** Do not read a green rig as a verified rig when no artefact has yet travelled its main path.
> Budget for the first real use to break it, and never diagnose that breakage as the new artefact's fault
> without measuring the baseline separately.

### P-5. Cut the worker's worktree from the commit containing the artefact

**Twice this fire** a worker was handed a worktree predating the merge of the thing it was to work on
(T9's **F-9**, T57's **N-5**). T9 was dispatched to review 11 promoted vectors and found only the four
`REFUSE-*` files; it re-cut onto `main` itself. **A reviewer who graded what was in front of them would have
reviewed an empty corpus and reported it clean.**

> **Rule.** A brief must name the branch or commit containing the artefact, and the worker must verify its
> base before starting. "Confirm you can see X before you begin" belongs in every review brief.

### P-6. Re-deriving from the same document three times is one check, not three

Three parties confirmed the pass-3b corpus by re-deriving from **DEC-1's documented rules**. Agreement among
three applications of one method is weak evidence. T9 was therefore scoped to re-derive from **Fineract's
source** instead — re-implementing the algorithm *in the shape the Java writes it* — and that is what
surfaced the two pieces of folklore everyone had been carrying:

- the oracle does **not** use the closed-form EMI; it folds `Π(1+rᵢ)·P / fn`, no `pow`
  [`ProgressiveEMICalculator.java:1838-1840`, fold at `:1819`];
- there is **no** "final principal := remaining balance" — principal is always `EMI − interest`
  [`RepaymentPeriod.java:339-344`], and the residual lands on the **last unpaid period's EMI** [`:1191-1206`].

Both reproduce the current corpus identically, because every promoted vector runs `DAYS_30`/`DAYS_360` so
every rᵢ is equal. **They are not guaranteed to agree at precision 19 once the rᵢ differ.**

> **Rule.** When N parties agree, check whether they used N methods or one. Vary the *method*, not the
> reviewer.

### P-7. A proof that asserts a FACT ABOUT TODAY'S CORPUS goes stale on the next promotion — assert the property

Finding **D-6** recurred **four times in one fire**, in four different places, and twice inside the same
proof. Every instance was a proof or test encoding a true-today fact instead of the invariant it protects:

| # | frozen assertion | what falsified it |
|---|---|---|
| 1 | `ParityPass == 0` — "the store has no promoted capture yet" | the first promotion (T8) |
| 2 | the same, in `TestGradeabilityIsNotPairDifference` | found by T20; nobody had reported it |
| 3 | `parity vectors PASS 11` inside a proof | T57 moved the corpus to 13 |
| 4 | *"withdrawing `P-02`/`P-02b` makes `monthend.reanchor` UNBACKED"* | T58 promoted 16 more vectors, several backing the same capability |

Instance 4 is the instructive one: **the proof failed because coverage was ADDED.** A worker forbidden to
edit the harness reported it rather than discarding 20 measured kills to get green — which was the right
call, and is what surfaced it.

> **Rule.** In a proof, never assert a count, a total, or "X is the only Y". Assert what the guard protects:
> *this vector is refused, by name, with this diagnostic*. Then verify the assertion **discriminates** — it
> must be absent on the pristine store and present on the perturbed one. An assertion that cannot go red is
> decoration.

### P-8. The rig can silently disagree with its own documented contract

`.softhouse/vectors/README.md` states that a cell named in `unrecorded_fields` is **not compared** and is
counted as an ungraded cell. Under `--self-test` that is **false** for a `DISBURSEMENT` row's outstanding
balance: the replay implementation answers `0` for the unrecorded cell and `balance_roll_forward` then
**grades the placeholder**. A vector that declares the cell honestly goes **red** (T58's finding **N-2** —
all 14 affected vectors red, `go test` failing, `--prove` down to 10/20).

Same class as **D-5**, one layer down: the documented behaviour and the implemented behaviour diverge, and
the divergence only appears when an artefact finally exercises the path.

T58's response is the pattern worth copying: it **did not** exempt the invariant — that would have deleted a
check that currently passes — and it did not edit a vector to fit the rig. It **re-observed** every affected
shape on a harness that records the column, then cross-checked the two capture sets: **14 case pairs, 134
rows, 1,698 cells, zero differences**, across two independent Path A harnesses two fires apart. The
workaround produced a free cross-harness control; the underlying defect stays open and is recorded as a task.

> **Rule.** When the rig contradicts its own README, fix one of the two — do not adjust the artefact until
> the contradiction is invisible. And prefer re-observing to exempting: an exemption is permanent, an
> observation is evidence.

---

### P-9. A green corpus can be blind to the TENANT'S OWN ratified configuration

**Fire `20260820-080002`, T61.** The parity corpus stood at 29 vectors and 2,354 cells, all PASS. The driver
then applied one mutation to `roundHalfUpToInt` — the `HALF_EVEN` tie rule, which is **Fineract's stock
default** — and re-ran the real harness:

| `MONEY-QUANTIZATION-HALF-EVEN` | verdict |
|---|---|
| at 29 vectors | **PASS, exit 0**, 2,354 cells |
| at 32 vectors | **FAIL, exit 1** — three vectors, margin 1 minor unit |

So a Go port that **inherited the upstream default instead of reading Buyan's ratified `HALF_UP` tenant pin**
matched the reference oracle on every graded cell. The corpus could not see it because a tie is a measure-zero
event on an arbitrary lattice: you do not hit one by sampling ordinary loans, you hit one by *solving* for it.
T61 got there by source algebra — at 21.6 % on this lattice, period-1 interest is `18·B/1000` minor units, an
exact tie exactly when `B ≡ 250 (mod 500)` — and registered the prediction **one commit before the capture
ran**, in falsifiable terms: *"if the oracle emits `18000.94` the prediction is WRONG and the ratified tenant
rounding mode is not what we think."* The oracle returned `1800095`.

> **Rule.** Every parameter the tenant configures is a place the port can silently inherit upstream's default
> and still pass. For each one, the corpus needs a vector on which **the configured value and the default
> disagree observably** — and for a rounding mode that means solving for an exact tie, not sampling. The
> general question to ask of any green run: *which of our ratified settings would this corpus fail to notice
> we had ignored?*

### P-10. A performance test that grades a PROXY is green on the very defect it is named after

**Fire `20260820-080002`, T59 → T63.** T59 wrote a wall-clock cost test, honestly measured it **flaky** under
load (12.06x / 15.13x / 14.32x against a 16x quadratic figure, no safe threshold), and replaced it with a
load-independent **allocation-count** ratio. Good engineering — and it moved the assertion onto a quantity the
defect need not touch. T63 then found `TestGenerationCostIsNotQuadraticInTheTerm` is **green on a port that is
quadratic, twice over**: `installmentNumberOf` rescans every emitted row inside the emission loop
(`generator.go:459`, `:478-486`) — a Θ(n²) that **allocates nothing** — and the port has a timing cliff at
n=2,000 that the test's two sample points (n=90, n=360) both sit below. *(Driver re-read the source and
confirmed the rescan mechanism; the n=2,000 cliff stands as T63 measured it.)*

> **Rule.** When flakiness forces a test onto a proxy metric, prove the proxy still discriminates — mutate in
> the defect the test is named for and watch it go red. A test that cannot fail on its own subject is worse
> than the flaky one it replaced, because it reports confidence instead of noise. And two sample points
> cannot characterise a curve with a cliff.

### P-11. The code can be RIGHT and its stated reason WRONG — and the reason is what the next contributor checks

**Fire `20260820-080002`, T63 P1-2.** T59's memo is sound, over ~74,000 adversarially generated shapes with no
divergence and no seventh unguarded write site. But its stated soundness rule — *"step i is a function of
periods 0..i and of nothing later"* — is **false of the reference oracle**, which writes later→earlier in four
places (`ProgressiveEMICalculator.java:1725-1739`, `:1258-1309`, `:1202-1203`, `:1243-1251`). The memo is
sound for a different reason: it caches a pure function of *currently stored fields*, so the real condition is
**every write to a fold input on period j is preceded by `invalidateFrom(j)`**.

A correct implementation resting on a false rule is a latent defect with a delay fuse: the next contributor
adds a write site and checks it against the rule that is written down.

> **Rule.** Review the *justification* as a separate artefact from the code, and re-derive it from source.
> "It works and the tests pass" does not establish that the reason given for why it works is true — and the
> reason is the part that gets reused.
