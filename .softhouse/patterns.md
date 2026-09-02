# Softhouse learned patterns — Gerege NBFI (Fineract → Go migration)

> **CITATION HAZARD — two `P-n` series exist in this repo, and `P-1`…`P-5` are each defined TWICE.**
> Verified by exact heading match, local fire `20260821-134344`:
>
> | id | **this file** — a *learned pattern* | **`.softhouse/gates-proposed-answers.md`** — a *ratified decision* |
> |---|---|---|
> | P-1 | A ZERO money margin is not evidence of non-gradeability | Installment rounding to a multiple → launch WITHOUT it |
> | P-2 | Screen a counterfactual on the PRE-adjustment model | DEC-1 ratification → agent-decidable on a clean review |
> | P-3 | A green conformance run says nothing about unexercised behaviours | Reporting cadence → exceptions only |
> | P-4 | Latent harness defects detonate on first real use | Stop revising the contract — ratify with obligations |
> | P-5 | Cut the worker's worktree from the commit containing the artefact | **Close tier 0 — obligations, not fifth drafts** |
> | P-6 | Re-deriving from the same document three times is one check, not three | Freeze a gate write-up once its measurements reproduce |
>
> **`P-6` JOINED THE COLLISION, EXACTLY AS THE PARAGRAPH BELOW PREDICTED IT WOULD.** This banner used to end
> *"`P-6`…`P-39` are defined only here and are unambiguous"*, and that sentence was **false** — measured by
> `T282` at sha `4d695ba8bb56`: `gates-proposed-answers.md:195` defines `P-6`, so the decision series
> reached 6 and the banner's own forecast (*"no collision could occur until the decision series reached 5"*)
> came due one id later without anyone updating the sentence it invalidated. **The claim of unambiguity is
> now `P-7`…`P-39`, and it is a MEASUREMENT that goes stale, not a fact** — re-run
> `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py`, which prints
> `cross-register-collisions=` on every run, rather than trusting this line.
>
> **Always cite the file, never the bare number** — write "P-5 (`gates-proposed-answers.md`)" or
> "P-5 (`patterns.md`)". A worker told to act "under P-5" with no file could apply the worktree-cutting rule
> when the user meant *close tier 0*, or the reverse. This was latent until 21 Aug 2026: `patterns.md`'s P-5
> existed but **nothing had ever cited it**, so no collision could occur until the decision series reached 5.
> It is recorded rather than renamed because the decision headings are the user's own text.

> **SECOND SERIES HAZARD — `patterns.md` ALSO COLLIDES WITH ITSELF.** `P-12` and `P-13` are each defined
> **twice in this file**, and neither had ever been recorded until `T282` measured it:
>
> | id | first definition | second definition |
> |---|---|---|
> | P-12 | `:315` — *a right conclusion on a wrong reason recurs in the artefact written to record it* | `:1385` — *an ID SERIES that restarts in a second file is a name collision waiting for its first citation* |
> | P-13 | `:320` — *for a specification-bearing comment, the comment IS the deliverable* | `:1412` — *grepping the store for a VALUE does not answer what the store KILLS* |
>
> Read `P-12`'s **second** definition again and note what it is: *"an ID SERIES that restarts in a second
> file is a name collision waiting for its first citation."* **That rule is defined at the id it is itself
> colliding on.** The register restated its own series and rotted, which is `P-80` (*a corrected cardinal
> rots in every place it was restated*) and `P-86` (*the pattern ids themselves rotted, in the file that
> names the rot*) reaching the same conclusion a third time, one layer further in.
>
> These two are **DECLARED, not renumbered.** Renumbering would rewrite the cardinal under every citation
> already published against it — the exact defect `P-80` names. The declaration below is machine-read by
> the citation checker so a **NEW** collision is fatal while these two stay quiet; a declaration for an id
> that is *not* actually colliding is itself fatal, so this list cannot rot into a silencer.
>
> `PNUMBER-REGISTER-DECLARED-COLLISIONS: 12, 13`
>
> **Cite these two by FILE AND LINE, never by bare id** — "P-12 (`patterns.md:1385`)".

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

### Repository hygiene (new — 21 Aug 2026)

- **Raw capture dumps are artefacts, not source.** A capture output over ~5,000 lines is stored as its **recipe + SHA-256 + the derived vectors**, never committed whole. Two negative-control files (`t46-perturbed-reemission.json`, `t46-corrupted-canary-payload.json`) alone are 351k lines; captures total 1.33M of the repo's 1.58M lines, and every clone and every cloud fire pays for that. The vector STORE (`.softhouse/vectors/`) is committed; multi-hundred-thousand-line probe dumps are regenerable and must be regenerable — if a dump cannot be reproduced from its recorded recipe, that is a defect in the recipe.
- **Clean up worktrees after merging.** `/softhouse` STEP 9 requires `git worktree remove` + `prune`; it was not happening. On 21 Aug 2026 the tree held **121 worktrees / 12 GB**; 97 were clean and fully merged. A fire that merges a branch removes its worktree in the same step.
- **A worktree with unmerged commits is a claim on attention.** 24 remain, each holding commits not on main (rescued branches, rejected drafts, and several `softhouse/T3x`–`T1xx` task branches). Each must end as merged, explicitly abandoned with a reason in `tasks.json`, or re-dispatched. Silent accumulation of unmerged branches hides lost work — the exact failure this program has already hit three times.

### Ratified artefacts are write-protected (new — 21 Aug 2026)

- **No committed script may write to a ratified artefact.** Found by T167: nine committed probe scripts (`.softhouse/reviews/t47-probe/t47_edit_1..8.py`) hard-wire `docs/adr/DEC-1-schedule-generator-adapter.md` and call `open(DOC, "w").write(...)`. DEC-1 is RATIFIED, and amending a ratified DEC-n is a hard `user` gate — so an unguarded in-place rewriter is a **gate bypass**, whether or not anyone runs it. "Nobody happened to execute it" is not a control.
- **Probe scripts read and report. They never write.** A probe that needs to show a proposed edit prints a diff; it does not apply one.
- **Grep rejections** on any committed script: `open(` … `"w"` combined with a path under `docs/adr/`, `.softhouse/vectors/`, or a ratified DEC-n; also `sed -i`, `>` redirection, or `Path.write_text` against those paths.
- **Edits to a ratified artefact happen in exactly one way:** a task whose plan-gate check confirms the `user` gate is open, producing a new revision entry. Any other path is a rejection.
- **This rule is retroactive** — existing tooling gets swept, not grandfathered.

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

  > **CORRECTION — `T228`, measured at `f8436b4`. THE PARENTHETICAL ABOVE IS T84's OBSERVED SET, NOT A
  > DEFINITION OF THE FAMILY, and it is left byte-identical because every figure in it is correct over that
  > domain.** *"600 % p.a., MNT 0.01, n ≥ 104, 22 cells"* was the whole of what anybody had asked on
  > 20 August 2026. **`T223` has since observed family B at `36.0 %` p.a. (MNT 0.50, n = 1324) and at
  > `300.0 %` (MNT 0.02, n = 800), so family B is NOT a property of 600 %**, and it derived the term edge as
  > `n* ≈ 19/log10(1+r)` — **a property of the RATE**, which makes `n ≥ 104` the edge *at 600 % only* and not
  > a fact about the family. `T229` and `T219` then added principals to **4499 minor units**. The live
  > statement of the region is `gates.md` § `G-8`; read it there, never from this parenthetical.
  >
  > **This is the pattern's own rule failing on the pattern's own example.** P-23 says *"every sentence must
  > name the domain it was measured over"* — and its illustrative parenthetical did not, so it read as a
  > definition and stayed readable as one for two days after it was falsified. **An example inside a pattern
  > is a claim with the pattern's authority behind it, and it must carry a domain like any other.**
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

> **CORRECTION — `T228`, measured at `f8436b4`. The incident's NUMBERS stand; the phrase *"the rate that
> defines family B"* does not.** Family A being absent at 600.0 % — 11 of 12, not 12 of 12 — is exactly what
> T101 measured and it is untouched. But 600.0 % **does not define family B**: `T223` observed family B at
> `36.0 %` p.a. and at `300.0 %`, and derived the region in variables that contain no particular rate. At the
> time of the T101 → T112 incident 600.0 % was **the only rate anybody had asked**, which is why the phrase
> was written and why it read as a definition. Substitute *"the only rate at which family B had then been
> observed"*. `[VERIFIED: T223's capture; live statement in `gates.md` § `G-8`.]`

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
| `command grep …` | BSD grep — `command` **does** bypass the function when *running* it |
| `command -v grep` | **reports the shell function.** It does NOT bypass it — see the correction below |

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

> **CORRECTION (T131, same fire).** The first version of this pattern — written by the driver — asserted that
> `command -v grep` *bypasses* the shell function. **It does not: `command -v` reports the function.** Verified by
> construction: define `myfn(){ :; }` and `command -v myfn` prints `myfn`. The *rule* survives untouched — `type -a`
> is still the right instrument, because it shows the function **and** the binary and their order — but the stated
> mechanism was wrong, and it was wrong in a pattern written to warn against exactly this. The driver then repeated
> the false mechanism in T131's own dispatch brief, which is the propagation this pattern describes, one layer out.
>
> **Second silent-miss mode, and neither token fixes it (T131 F-T131-2).** The Bash-tool `grep` function carries
> `--ignore-files`, so it honours `.gitignore` — and this repo's `.gitignore` contains `.claude/worktrees/`. A
> `grep -rl '<string>' .` from the repo root therefore returns **exit 1 and no output** for a string that exists in
> a sibling worktree. That is the exact command shape census and sweep tasks use, so **every repo-wide sweep run
> through the Bash tool has been blind to every worktree and every gitignored path.** When a sweep must be
> exhaustive, run it through `/usr/bin/grep` or `git grep`, and say in the artefact which one you used.
>
> Same string, same start point, same moment, two tools, opposite answers:
> ```
> Bash-tool  grep -rl '<canary>' .                 -> exit 1, NO OUTPUT
> BSD  LC_ALL=C command grep -arl '<canary>' .     -> 2 hits, exit 0
> ```
> **Neither `LC_ALL=C` nor `-a` recovers it** — this is a third failure mode the two-token rule does not cover, and
> the mechanism is *descent*, not the file: restarting the search below the ignore file finds the hits again.
>
> Two details make it worse than an ordinary wrong answer. **The blind arm is also the fast arm** — the seeing arm
> took over two minutes across a 135 MB tree while the blind one returned "not found" instantly, so an agent under
> time pressure will prefer the fast wrong answer. And in the run that demonstrated it, **one of the two missed hits
> was the review document doing the demonstrating**: the sweep an auditor runs to find restatements of a claim is
> exactly the sweep that cannot see them. That is P-26's failure mode with the blindness built into the instrument.

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

### P-35. Every vacuous guard in this repo is a NEGATIVE assertion — and that is the whole diagnosis

**Fire `20260821-080001`, T134, auditing all 19 CLAUDE.md non-negotiables and 38 guard sites at once.** Three
workers had each stumbled onto a guard that could pass having checked nothing (P-34). Auditing the set as a set
produced the reason they are all the same bug:

> **A guard phrased as "I found nothing wrong" is vacuous on no input, by construction.**
> `count == 0` · `[ -z "$x" ]` · `grep found no match` · `exit status was not failure`

Every guard that survived attack was phrased **positively**: *this specific thing is present, AND it equals this
specific value.* Every guard that fell was phrased negatively. It is not a coincidence and it is not three bugs.

The register measured **FIRES 16 · VACUOUS 6 · UNGATED 1 · ABSENT 15** — and, most tellingly, **five of the sixteen
FIRES sites are simultaneously vacuous at an entry point**: they discriminate correctly on real input and pass
silently on starved input. That combination is exactly what gets a guard believed.

Two consequences worth carrying:

- **`ABSENT` is the biggest bucket and the quietest.** Eight of nineteen non-negotiables have no executable guard at
  all — the append-only ledger, holds→available, `Idempotency-Key`, the never-insured/protected/guaranteed string
  rule, three-part names, the national-ID shape, the RTGS threshold, deposit-activation-disabled. A vacuous guard
  at least appears in a register; a missing one appears nowhere, and prose in `CLAUDE.md` reads to everyone
  downstream as if it were enforced.
- **A guard can be blind to the *form* of a violation rather than its presence.** Both no-float guards inspect
  **identifiers**, so `rate := 0.036 / 12.0` — a float *literal*, `token.FLOAT` — builds, passes the test, and
  takes conformance to exit 0. *(Driver-verified: the shell guard's regex does not fire on the injected literal.)*
  The rule was "no floating point"; the guard implemented "no float-typed identifiers".

> **Rule.** Write every guard as a positive assertion — *N items were inspected, and each equalled its expected
> value* — and make **zero inspected** an error. The reviewer's one-line test: **if the PASS sentence would still
> print on empty input, it is not a guard.** Then ask the second question, which the first does not cover: *does
> this guard detect every FORM the violation can take, or only the form I happened to think of?*

### P-36. An experiment whose input never arrives is a NULL CONTROL — and it looks exactly like a result

**Fire `20260821-080001`, T130, retroactively invalidating four rounds of argument in one paragraph.** Four workers
fought over whether a probe's `IFS=` prefix prevented a false refusal. T106 said it did. T113 refuted that and
shipped a replacement reason. T121 refuted *that* and brute-forced **448** `IFS` values across three bash versions
to settle it. Every one of them ran their rows as:

```
env IFS=… bash harness      # <- delivers nothing
```

**bash resets `IFS` to the default at startup and ignores an inherited one** — in plain mode, under `--posix`, with
`argv[0]=sh`, and under `POSIXLY_CORRECT=1` alike. So **every row in all four experiments was a null control**, and
not one of those workers ever tested the claim they were arguing about. The routes that do deliver are a `BASH_ENV`
startup file and being sourced. T130 nearly shipped a third wrong reason on top of the first two.

What makes this class dangerous is that a null control **does not look like an error**. It produces rows, counts,
and a coherent table; 448 green cells read as overwhelming evidence. The experiment failed silently in exactly the
way P-35's guards do — and for the same underlying reason, since "the probe did not fail" and "the probe never ran"
are the same observation.

> **Rule.** Before believing an experiment, prove the manipulated variable **reached the subject**. Assert the
> delivery, do not assume it: read the value back from inside the process under test, or vary it and show the
> *unmitigated* case changes. Every experiment needs a **positive control** — a condition known to produce the
> effect — and if the positive control is flat, the apparatus is broken and the negative rows mean nothing. State
> the delivery route in the write-up, because that is the line a later reader can check.

### P-37. A reviewer's site list is a STARTING POINT, never the sweep

**Fire `20260821-080001`, T140 — the fourth consecutive task on one section to be handed a list of sites and find
more.** T129 reviewed the G-8 write-up, rebuilt a 117-row scope table, and named **five** places carrying a
superseded claim. T140 was dispatched to fix those five. Grepping the *concept* — `wholesale`, `main's copy`,
`reset it to`, `diff main -- tasks.json`, `tasks.json … empty` — across every `.md`/`.txt`/`.json`/`.sh`/`.py`
under `.softhouse/` found **seven**.

That is P-26 landing **inside the task sent to close P-26's third occurrence**, which is the fourth round running
on this one section. The mechanism is not carelessness: a reviewer reads to *judge*, hits enough instances to be
sure the claim is false, and stops — because finding a sixth would not change the verdict. The fixer's job is the
opposite one, and needs the opposite reading.

> **Rule.** When a review hands you file:line sites, fix those and then **run the sweep yourself, on the concept and
> the numbers** (P-26), and report the count you found against the count you were given. Include **your own change
> of mind** in the sweep: T122's leaked claim described an approach it had itself abandoned mid-task. And state
> what the sweep structurally could not have found — remembering (P-33) that the Bash tool's `grep` cannot see a
> gitignored path at all.

### P-38. A digest claim is a claim about a CANONICALISATION — name the recipe or the digest is uncheckable

**Fire `20260821-080001`, T140.** This program pins evidence with lines like *"canonical sha256 `01b41d9c…`"*, and
readers treat them as re-runnable. T140 tried to re-run two of them and **both mismatched** — not because the bytes
had changed, but because it serialised with `json.dumps(..., ensure_ascii=False)` while the original used the
recipe at `run-t84.sh:109`. Under the original recipe both matched exactly.

A digest over *bytes on disk* is self-describing. A digest over a **re-serialised data structure** is a digest of
one particular serialiser's output — separator spacing, key ordering, `ensure_ascii`, float repr, trailing
newline — and none of that is recoverable from the hex string. So "canonical sha256 X" without the recipe is not a
check anybody can perform; it is a number that will mismatch for the next reader, who will then have to decide
whether the evidence moved or their `json.dumps` differs.

This is **P-33 generalised from tools to digests**: a tool claim needs binary, version, locale, invocation and
input shape; a digest claim needs **the exact canonicalisation and where it lives**.

> **Rule.** Every published digest names what it is over and **how that was serialised**, by file and line — or it
> is a digest of raw file bytes and says so. When you cannot reproduce a published digest, suspect the recipe
> before you suspect the evidence, and record which it turned out to be.

### P-39. A program embedded in a doc comment is subject to the FORMATTER — write it indentation-insensitive

**Fire `20260821-080001`, T146.** The `futureUnrecognizedInterest` block publishes census commands inside `emi.go`'s
doc comments so a future reader can re-run them. T146 needed a real parser for one of them (no line-oriented
pipeline can count Java enum constants — nested braces in constructor arguments and class bodies, `/* */` spanning
lines, the first constant on the header line, the last comma optional), and wrote it in **Python**.

`gofmt -l` immediately named `emi.go`. **`gofmt` reflows doc comments and flattens any line indented deeper than
the block's base** — so an indentation-significant program embedded in a comment is not merely reformatted, it is
**silently destroyed by the next `gofmt` run**, and the destruction reads as whitespace noise in review. Three
constructs had to be re-authored flat; the census shipped as 45 lines of POSIX `awk`.

The same task then found the sharper half by attacking its own fix: its first `awk` draft read a constant written
with a `,` escaped comma as **4, silently green** — the exact defect it was sent to close, reappearing inside
the fix. JLS 3.3 resolves `\uXXXX` *before* lexing, so the census now **refuses** any `\u` input rather than answer
it, and publishes that refusal as a stated limit.

> **Rule.** Anything executable that lives inside a comment must survive the formatter — no significant
> indentation, no trailing-whitespace dependence, no line-continuation the reflow can join. Prove it by running
> the formatter and by **extracting the program back out of the committed comment and running the extracted
> bytes** (T146 did: 45 lines, `cmp` byte-identical, all eleven inputs re-run against the extract). A published
> command nobody has round-tripped is a claim, not a check.


### Run 2026-08-21-run2-tierA-gl-accounting-A2 — fire 20260821-054355 (2nd of the day)

- **What worked**: seven worktree-isolated workers, seven completions, zero live at exit. The driver
  re-ran every load-bearing measurement itself in scratch worktrees instead of quoting a worker.
- **What the independent reviewer caught / what workers caught above them**: A2-12 overturned its own
  reviewer A2-9 (a defect measured at 3-of-48 is 6-of-96; A2-9 swept only one of two entry points, and the
  second carries the MIRROR-IMAGE bug). T163 showed A2-11's committed prover exits 0 against the DEFECTIVE
  script. T157 showed T154's committed "fail-closed" characterisation is backwards. T169 showed "0 errored"
  was unfalsifiable across the program's whole history.
- **Vectors added / contexts at parity**: none added. 43 parity vectors, 5664 cells, unchanged and
  re-verified by the driver before and after every merge.
- **Claims marked UNVERIFIED (carried forward)**: cap8.sh has never talked to Fineract; the cause of the
  oracle's non-deterministic StackOverflowError; whether any committed claim resting on the two vacuous
  Python checks is unsupported.
- **Verifier**: build 0 · vet 0 · go test ./... ok (incl. ledger) · conformance PASS exit 0, probe = up ·
  invariants 0 violations · gofmt -l names exactly contract.go (G-3).
- **Backlog carried forward**: T171-T177 raised from this fire's findings.

**P-49 — A guard developed against a tree that does not exist yet inherits none of that tree's collisions.
Test the MERGE, not the branches.**

T166 widened the no-float root to the whole Go module while `internal/apps/ledger/` was still unmerged, so
its worktree never contained the tree it was about to start guarding. A2-12's own conformance run was green
for the mirror-image reason: the guard was still `loanschedule`-only when it ran. Both branches were
individually correct and individually green. Merged, they were a **permanent HARD-guard failure** — A2-8's
in-package float scanner writes its forbidden table and red fixtures with the spellings UNSPLIT
(`"float64": true`), which is exactly what `nofloat.go` documents as a self-reference trap and solves by
splitting. Five hits, exit 2, no verdict.

Nothing either worker could have done would have found this, and no reviewer reading either diff would
either. **The driver found it by building the merged world in a scratch worktree and running the harness
there before merging anything.** That step is now mandatory whenever a change widens what a guard inspects:
widening a guard's DOMAIN is a change to every file that domain newly contains, including files that do not
exist on your branch.

Corollary, and the reason this is a pattern rather than an anecdote: **a guard's blast radius is not visible
in the guard's own diff.**

**P-50 — An assertion phrased to pass when the bug is PRESENT is a demonstration, not a regression test, and
its exit code lies to every reader after you.**

`.softhouse/reviews/A2-11/prove-resolve7-float-red.py` is committed evidence that a money-corruption defect
exists. Run it against the defective script and it prints `FAILURES: 0` and **exits 0**, because its
assertions read `PASS RED: resolve7.py accepts every one of them, exit 0 — it cannot refuse a float`. The
assertion is true *because the bug is there*. Driver-reproduced on main.

Two consequences, both bad. Any automation reading the exit code reads **health**. And after the fix, the
same prover would go RED — so the next reader sees a fix "breaking" the prover that proved the bug.

The P-35 rule ("phrase positively; report what you INSPECTED") has a second half this makes explicit:
**a prover must be falsifiable in the direction of the FIX, not only in the direction of the defect.** The
repair shape is T163's: assert internally that the pre-fix bytes drive the battery RED **and** the post-fix
bytes drive it GREEN, so exactly one arrangement of the world passes. Widen such a prover rather than
replacing it — the original demonstration is still the evidence that the defect was real.

**P-51 — "N errored: 0" from a handler that cannot see the error class is not a wrong number. It is an
unfalsifiable one, and it retroactively weakens every claim built on it.**

The shared capture rig caught `RuntimeException`. `StackOverflowError` is an `Error`. T169 found two
independent routes by which a throwing cell produced **no integrity line at all** — the `Error` escaped
`main()` and killed the JVM before any JSON, and the caught-and-`printStackTrace` path tripped every
runner's refuse-on-stderr rule. **No completed run in this program's history could have printed any value
but `0 errored`.**

A measurement that cannot come out any other way is not a measurement. The distinction T169 drew, and it is
the honest one: T117's `287 asked / 287 observed / 0 errored` is **true about the run**. What is unsupported
is the **inference** it carried — that the sweep covers its region. **Report the inference as unsupported;
do not adjust the number, which was never wrong.**

Fix shape: a throw is a FIRST-CLASS OUTCOME, distinct from success and from absence — `asked / observed /
threw / skipped`, the tally must close, and a threw cell may neither be graded nor vanish.

**P-52 — Before calling a guard broken because it ignored your probe, read its selftest. It may be
correctly scoped, and you may be the one testing the wrong thing.**

The driver planted a 35th capture rig with a narrow `catch (RuntimeException)` at T169's new lint and it was
not flagged — which looked exactly like the vacuous-guard failure this program keeps finding. It was not.
The lint deliberately flags only catches that wrap the **measured seam**, and its own selftest case (c)
asserts it must NOT be over-broad. The driver's plant called a method the seam markers do not name. Replanted
with a real seam marker, the lint refused it: exit 1, named at file:line.

The instinct to distrust a green guard is right and has paid out repeatedly here. **The discipline that must
go with it: a guard that declines your probe is either vacuous or correctly scoped, and its selftest
distinguishes those two in one command.** Publishing the first reading without running the second would have
sent a task to "fix" a guard that was working.

**P-53 — A REGEX SWEEP HAS NO SINGLE ANSWER: THE SAME PATTERN TEXT SCORED 3 IN PYTHON `re` AND 0 IN FOUR
POSIX ERE ENGINES, ON THE SAME BYTES.** T156's `GUARD` pattern, lifted out of its own source by `ast` and
run against the immutable pre-fix blob `bf67a85:.softhouse/reviews/t47-probe/t47_edit_1.py`:

| engine | matches |
|---|---|
| Python `re` (the engine T156 shipped) | **3 → GUARDED** |
| `/usr/bin/grep -E`, shell `grep -E`, `/usr/bin/awk`, `/usr/bin/sed -nE` | **0, 0, 0, 0 → UNGUARDED** |

Two independent incompatibilities in one pattern, each isolated by measurement rather than asserted
[VERIFIED: `.softhouse/reviews/t179-guard-classifier/engine-divergence-output.txt`]:

1. **`[^#\n]` is not the same bracket expression.** Python honours the `\n` escape (*not `#`, not newline*);
   POSIX has no escapes inside brackets, so it reads *not `#`, not backslash, not the letter `n`*. The
   anchored `[^#\n]*` then cannot cross a letter `n`, and every `trap` in the corpus sits after one
   (`One trap worth…`). Isolated on two one-line inputs: `a trap here` → grep 1; `One trap worth naming` →
   grep 0, Python 1 in both.
2. **`\b` is not a word boundary in POSIX ERE.** `awk` scores 0 even on the line with no letter `n`, so
   awk's zero has a *different* cause than grep's. One pattern, two engine-specific readings, three verdicts.

*Rules:*
1. **A count produced by a regex sweep is only quotable together with the engine that produced it.** Record
   the interpreter in the transcript. "The sweep found N" is not a measurement; "Python `re` found N" is.
2. **Never port a regex sweep between Python and shell and carry its numbers across.** Re-derive them. The
   port is not a refactor; it is a different instrument.
3. **This is the P-33 class reached from a new direction** — an unsupported feature returning zero looks
   exactly like absence — so the demonstration script must FAIL when the engines agree, or it is P-22 again.

> ### ⚠ P-53 AMENDED TWICE — the driver, local fire `20260822-060013`, at `main` `8275f8b`
>
> **(A) THE DEFECT IS NOT RECALL-ONLY. `git grep -E` FABRICATED A HIT.** Every statement of this pattern in
> the repo — here, and `P-12`'s second measurement — describes the literal-`b` reading as *lost* matches.
> That is understated. Driver-measured on a three-line fixture (`x main y` / `bmainb` / `HEAD`) for
> `\bmain\b`: `git grep -E` **missed line 1 and MATCHED LINE 2** — because it read the pattern as literal
> `b`,`main`,`b`, and `bmainb` genuinely contains that. So a sweep run under this engine can report a
> **POSITIVE THAT DOES NOT EXIST**. The practical consequence is the one that bites: *"my instrument
> returned hits, so it works"* is **not a valid calibration**. `P-72` says calibrate on a known positive;
> after this, **also calibrate on a known negative.** Independently found by `T239` (its finding 3) and
> re-derived by the driver.
>
> **(B) THE ENGINE ROSTER IN THIS REPO WAS WRONG IN BOTH DIRECTIONS.** `RESUME.md` told four workers this
> fire that "BSD grep and ugrep both honour the escapes; ripgrep 14.1.1 is also present — five engines, not
> three." Measured:
>
> | engine | `\bmain\b` on the fixture | verdict |
> |---|---|---|
> | `git grep -E` | matched **line 2 `bmainb`** | **BROKEN BOTH WAYS** — misses the true hit *and* fabricates |
> | `git grep -P` | line 1 | **SOUND — PCRE *is* available in git here** |
> | `git grep` (basic) | line 1 | sound |
> | `/usr/bin/grep -E` (BSD) | line 1 | sound |
> | `/usr/bin/grep` (basic BSD) | line 1 | sound |
> | `rg` 14.1.1 (rev `939d4325be`) | line 1 | sound — **but see the correction below: present at a PROMPT, absent in every SCRIPT** |
> | `python3 re` | line 1 | sound |
> | **`ugrep`** | — | **NOT INSTALLED** — `command -v ugrep`/`ug` empty across all 13 PATH dirs |
> | `/usr/bin/grep -P` | — | option does not exist; **exit 2, silent** |
>
> **`git grep -P` is sound, available, and was never recorded.** The lore only ever said `/usr/bin/grep -P`
> does not exist, and a reader generalised that to "no PCRE here". Inside a git tree it is the cheapest
> sound route. That omission is a **`P-73`** instance: the working engine was there the whole time, unfiled.
>
> **(C) A CITATION THIS INVALIDATES — do not restate it as settled.** `RESUME.md` exonerates `T224`'s zero
> with *"it ran under ugrep where `\b` works"*. **ugrep is not on this machine.** That exoneration is now
> **`[UNVERIFIED]`**. `T224`'s "two mechanisms, one zero" is **one measured mechanism** (right-anchoring an
> inflected stem) **plus one unverified claim about the engine**. Flagged by `T239`; the driver re-derived
> the absence and is recording it here rather than in a handoff, because here is where the next sweep author
> will be standing (`P-73`).

**P-54 — DETECTING A GUARD IS AN AST QUESTION, AND "IS THERE A GUARD IN THIS FILE?" IS THE WRONG QUESTION.
THE RIGHT ONE IS "IS A GUARD REACHABLE FROM THIS MUTATION?"** T179 replaced T156's file-level regex with a
parser (`.softhouse/reviews/t179-guard-classifier/guard_classify.py`). Three defect shapes fall out, and only
the first is the one P-48 named:

- **prose-only** — guard words exist solely inside string literals. Re-derived at `4484cf1b`: of the 9 python
  files T156 scores GUARDED, **4 carry zero guard nodes of any kind** — `try/finally` 0, live handlers 0,
  restoring context managers 0. Two of them are **T158's own drive scripts**, written *by the review that
  discovered this class*.
- **right node, wrong place** — a real `ast.Try` with a `finalbody`, or a real `atexit.register`, that does
  not enclose the mutation and is not on a live path. A naive AST check ("does the file contain a Try?")
  reproduces T156's verdict exactly. The classifier's red fixture `red_guard_elsewhere.py` exists for this.
- **target read from the wrong scope** — T156 matched its TARGET regexes anywhere in the file, so a file that
  merely *mentions* `.softhouse/vectors` counted as mutating the vector store, and its `SANDBOXY` regex
  excused a whole file for containing `tempfile.` once. Per-site resolution puts **272 of 410** sites in
  SCRATCH at `4484cf1b`. The trap worth naming: **this repo's sandboxes mirror the repo layout**, so
  `<tmp>/.softhouse/capture/newrig/src/` reads as a trusted capture path unless `mkdtemp` /
  `TemporaryDirectory` / `"/tmp/…"` bindings are propagated through assignments — measured on
  `capture/lib/check_no_narrow_catch.py`, whose `--selftest` sandbox was scored TRUSTED until they were.

*Rules:*
1. **A guard is a NODE on the mutation's ancestor chain** (`try/finally`, a restoring context manager) **or a
   process handler proven reachable from module execution.** Anything else is a word.
2. **Say which kind.** `GUARDED-FINALLY` and `GUARDED-PROCESS` are not the same claim: the second says a
   handler is registered, never that it restores *this* artefact. Collapsing them re-creates the false
   comfort the regex gave.
3. **Refuse what you cannot parse, and COUNT the refusals.** There is no shell parser in the stdlib and
   `bashlex` is not installed, so all **250** `.sh` files under `.softhouse` are `REFUSED-SHELL-NO-PARSER` —
   named, tallied, and excluded from every conclusion. **"The unguarded population is N" is therefore not
   derivable at all while half the population is unparsed**; a single N was only ever available because the
   regex was willing to answer a question it could not read.
4. **Both directions or it is half an instrument (P-50).** The selftest asserts the prose-guarded file is
   refused *and* that five genuinely guarded shapes — `try/finally`, live `atexit`, a local restoring context
   manager, `mkstemp`+`os.replace`, and an indirectly guarded helper — all pass.
5. **Make the instrument pass its own measurement.** `guard_classify.py`'s single write is atomic, so its own
   verdict on itself is ATOMIC and not UNGUARDED.

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

### P-12. An ID SERIES that restarts in a second file is a name collision waiting for its first citation

This repo runs two `P-n` series — learned patterns here, ratified decisions in
`.softhouse/gates-proposed-answers.md`. They coexisted harmlessly while the decision series was short and
`patterns.md`'s low numbers were never cited. On **21 Aug 2026** the decision series reached **P-5**, the user
ratified it, and within one fire the driver wrote ~100 references to "P-5" meaning *close tier 0* — into
`obligations.md`, `RESUME.md`, `tasks.json`, `program.json` and four commit messages — while `patterns.md`
went on defining P-5 as *cut the worker's worktree from the commit containing the artefact*.

Nothing broke, because every reference the driver wrote names its file. **That is the whole defence, and it is
one careless sentence from failing** — the next worker to write "as required by P-5" hands the reader a
coin flip between two unrelated rules, both of which are real, both of which are in force.

**The measurement is the finding.** Grepping for the collision is how it was found, and the first grep was
WRONG: `git grep -E '\bP-5\b' <commit>` returned **0 hits** on a file that provably contains the string,
because git's default regex engine does not support the GNU `\b` word boundary. Reported as "the collision is
new and entirely mine", which would have been a false all-clear on a real hazard. Caught by re-testing the
tool against a case whose answer was already known (`git show … | grep`).

- **Two IDs from different namespaces must not be typographically identical.** If they already are, the fix
  is a citation convention plus a table at the top of both files — not a rename, when one side is the user's
  own ratified text.
- **Before trusting a grep's ZERO, prove the grep can find something you know is there.** A zero result from
  an unsupported regex feature is indistinguishable from a zero result from absence. This is the P-22 class
  ("a guard that cannot fail") wearing a search tool's clothes: the query could not have found a hit, and
  reported that as evidence of none.

### P-13. Grepping the store for a VALUE does not answer what the store KILLS

The driver briefed T149 with: *"0 of 46 vectors carry either tie answer — **so** nothing in the parity corpus
would notice a port that inherited Fineract's stock `HALF_EVEN`."* The worker measured it instead of accepting
it and came back with the refutation: **false by three vectors.** `T61-HE-A/B/C` are exact ties at the same
quantization on other principals, and their named counterfactual was *already* `MONEY-QUANTIZATION-HALF-EVEN`.
Mutation `M7` over the 42-vector store: `KILLED | parity PASS 39 FAIL 3`.

**The count was never wrong; the inference was.** T136 wrote it correctly — *"0 of 46 … **but** `REFUSE-02`
makes HALF_EVEN a contract refusal"*. T147 restated it with **"so no *parity* vector discriminates the mode"**,
and the driver's T149 brief inherited that "so" and hardened it. **One conjunction, replaced twice, turned a
true measurement into a false claim about coverage** — and it was heading for a vector's own note, where it
would have become documentation of the corpus's blindness at the exact moment the corpus was proving otherwise.

- A vector does not need to **contain** a value to **discriminate** on it. Grep answers *what is written*;
  only a mutation answers *what would be caught*. They are different questions and only one of them is about
  coverage.
- **Coverage claims are measured with mutation, never with search.** If you are about to write "no vector
  would notice X", run the mutation that does X and read the count.
- When a source hedges with **"but"**, the hedge is usually the load-bearing half. Dropping it to "so" is not
  a compression — it inverts the claim.

**The worker refused to write the sentence its brief required, and said why.** That is the behaviour this
pipeline wants: the brief is not evidence, and a task that can only be completed by asserting something false
should come back refuted rather than complete. Fifth time a worker has caught the driver (P-20).


---

### Run 2026-08-21-run2-tierA-gl-accounting-A2 — slice A2 + carried money work (21 Aug 2026, local fire `20260821-054355`)

- **What worked**: seven workers dispatched, **seven completed, zero live at exit**, no isolation violation,
  no scope breach. `main` moved **42 → 43 parity vectors**, and the 43rd arrived **with** its review.
- **What the independent reviewers caught** — the count that matters, and it was four for four:
  - **T153 → T149**: MICRO-FIX. Two sentences claimed a tighter control than they held. It **measured the
    missing control** (0 money-cell differences) rather than arguing, so both conclusions survived and only
    the wording fell. It also re-observed the tie live and got responses **byte-for-byte identical** to
    T149's, plus a *cleaner* counterfactual than T149 had, and re-derived **all twelve periods in exact
    rational arithmetic** — a check T149 never ran.
  - **A2-10 → A2-5**: found a **P-22 regression the fix task itself introduced** — `islink` clauses made a
    symlinked fabrication invisible to `verify`, which the *pre-fix* code caught. **Third recorded instance
    of a task sent to fix a P-22 defect opening another.** It also adjudicated all three of A2-5's
    deviations by **building the prescribed fix and running it**, not by reasoning about it.
  - **A2-7 → the driver**: refuted the driver's central premise and **acted on its own measurement instead
    of the brief**, creating zero accounts because there were none to create.
  - **A2-2 → A2-1** (carried in): corrected the driver's own `OBL-A3-1` ruling at the mechanism level.
- **Vectors added / contexts at parity**: +1 parity vector (43 total, 5664 cells). No context cut over.
- **Verifier on merged `main`**: probe `up` · conformance **exit 0, 43 PASS / 0 FAIL** · 0 invariant
  violations · 0 assertions NOT RUN · `go1.26.6` build 0 / vet 0 / test ok · `gofmt -l` = exactly
  `contract.go` (G-3, expected).

**P-40 — An enumerator with a bare `except: continue` is a silent-skip guard, and the driver shipped one
inside a gate decision.** To size a gap for G-9, the driver walked `out/**/*`, called `json.load` on each
file inside `try/except Exception: continue`, and matched only dicts carrying **both** `glCode` and `name`.
That swallowed every psql `.txt` dump — which is where the captured state actually lives — and every POST
body, then **reported the surviving subset as the whole with no signal it had skipped anything.** It
produced the confident, false claim *"the corpus holds 2 of the 9 mandatory accounts, and all four accounts
are ASSET"*, when `main` already held **21 accounts across all five classifications** and a product with
**all nine slots mapped**. A2-7 refuted it in its first minutes. *Rule: an enumerator must count what it
skipped and say so. If it cannot parse a file it must name it, not drop it. `except: continue` over a
directory you are measuring is the same defect as a guard that cannot fail — and it is worse in a gate
decision, because the number gets ratified.*

**P-41 — Use `git diff main...branch` (three dots), never two, while a fire is running.** `main` moves
during a fire, and `main..branch` renders **main's own advances as the branch's deletions**. A2-6's
scope check appeared to show it deleting 71 lines of `gates.md` and 84 of `tasks.json`; the merge-base diff
showed exactly two files, both in scope. **The `/softhouse` SKILL.md STEP 5 text prescribes the two-dot
form and is wrong.** Every scope check and every fork-freshness check in this program should use three dots.

**P-42 — A brief's premise is not evidence, and the driver must re-derive its own before dispatch.** The
driver wrote three "already measured" traps into A2-8's brief on A2-1's authority, then re-derived them
from source *before* the task could be acted on. Both A2-1 claims were confirmed exactly — and the check
found **a third hazard nobody had recorded**: across `CashAccountsForLoan`/`AccrualAccountsForLoan` the
name↔code relation is **not a function in either direction** (`FEES_RECEIVABLE` is 25 under cash, 8 under
accrual), so keying on the code cross-maps *and* keying on the name cross-maps. The fourth trap was
deliberately **not** checked and was marked as unconfirmed rather than half-verified. *Rule: re-derive the
premises you author before a worker spends a run on them; mark what you did not check as not checked.*

**P-43 — Consolidate colliding tasks; do not run three workers over one defect surface.** T120, T132 and
T143 were three views of the same guard with overlapping `files_hint`. Three concurrent workers would have
produced contradictory guards; merged into T154 with a paired reviewer, all three legs landed coherently and
each brief number reproduced exactly. *Corollary: the superseded rows stay in `tasks.json` and
`obligations.md` marked `superseded_by`, never deleted — the content is the evidence.*

**P-44 — Register the paired reviewer when you notice it missing, not after the work lands.** The driver
dispatched A2-5 as a `coder` with **no paired reviewer** — the identical plan-gate rule-1 violation that
left T149 unmerged. Caught mid-flight by running the plan gate over the driver's *own* additions, and A2-10
was registered while A2-5 was still working. A2-10 then found a real regression. *Rule: run the plan gate
over tasks you add yourself, with the same rigour as over a planner's output — the driver is not exempt from
its own checklist.*

**P-45 — A test-only guard is not a guard.** T154's float-literal census is called from **`Run`**, not only
from the Go test, because `conformance.sh` never invokes `go test` — a test-only fix would have left the
third silent green standing while looking fixed. *Rule: when hardening a check, verify the path that
actually executes in CI/conformance calls it, not merely that a test does.*

**P-46 — A FABRICATED CAPTURE EXCERPT SURVIVED INTO MERGED EVIDENCE, AND ONLY THE PAIRED REVIEWER CAUGHT
IT.** A2-7's handoff printed a JSON block *attributed to capture `A2-211`* whose last three lines
(`"paymentChannelToFundSourceMappings": null` and two siblings) **do not occur in the capture at all** —
each key name appears **0** times, and the literal string `null` appears **0** times in the whole file. A2-7
then reasoned *from the invented lines* to a conclusion — "the collection-valued mapping fields behave the
opposite way: they are present with the value `null`" — which is **false**, and which the coder A2-8 was
actively consuming when the review landed. Caught by A2-11, re-verified by the driver against the raw bytes,
struck from the handoff with the measurement recorded in place, and pushed to A2-8 mid-flight.

This is the honesty rule's exact failure mode, and note *where* it occurred: **not** in a number, and **not**
in a claim marked `[UNVERIFIED]`. A2-7 was, by every other measure, an unusually good worker — it refuted the
driver's central premise, measured before acting, and carried an honest `[UNVERIFIED]` of its own. The
fabrication was three lines of **illustrative quotation**, the part of a handoff that reads as transcription
rather than as assertion, and so gets skimmed.

*Rules, and the first one is the one that would have caught it:*
1. **A quoted capture excerpt is a claim, and must be diffable against the artefact.** Quote by extraction
   (`jq`/`sed` from the file into the doc), never by retyping. A hand-composed "excerpt" is a paraphrase
   wearing quotation marks.
2. **A reviewer must grep the quoted strings against the cited capture**, not merely check that the cited
   capture exists and that its conclusions sound right. `grep -c` on each quoted key is seconds of work.
3. **Absent ≠ null ≠ empty.** In a contract-boundary port these are three different wire shapes, and the
   difference is `omitempty`/pointer-vs-value in Go. A doc that blurs them mis-specifies the port.
4. **The most-skimmed part of a handoff is the most dangerous place for an invention.** Prose gets argued
   with; numbers get re-derived; *quotations get believed.*

**P-47 — THE DRIVER GAVE A WORKER AN INSTRUCTION THAT WOULD HAVE BROKEN PARITY, AND THE WORKER REFUSED THE
RIGHT HALF OF IT.** Mid-flight, the driver told A2-8 to model the colliding loan-account enums separately
(right) *and* to make missing-slot rendering "pick the family that actually applies" (**wrong**). A2-8 took
the first half, **declined the second, and said so**: at codes 22/24/25 that would **diverge from the oracle
on an observable string**. It rendered exactly what the oracle renders — so `A2-224/225/092` grade
message-for-message — and fell back only where the oracle would NPE, carrying both names with the diagnostic
one never on the wire. *The driver has accepted the refusal; the instruction was wrong.*

The error has a specific shape worth naming, because it will recur every time a port meets an oracle bug:
the driver saw a **latent NPE** in Fineract's error-rendering path and reached for the **correct** behaviour.
But **Fineract is the oracle**, and this project grades Go output against what Fineract *emits*, not against
what it *should* emit. **Parity with an oracle bug beats a local improvement**, and an improvement smuggled
in as a bug-fix is a silent divergence that no vector will catch — because the vector was captured from the
oracle, and the port now disagrees with it *on purpose*.

*Rules:*
1. **When the oracle is wrong, reproduce it and record it.** A divergence is a `user` gate or a documented
   deviation with a vector, never a worker's quiet judgement call — and never a driver's.
2. **"Fix the bug" is not a porting instruction.** Before telling a worker to improve on the oracle, ask
   whether the improvement is observable at the contract boundary. If it is, it is a divergence.
3. **A worker refusing half an instruction, with a reason, is the system working.** Record the refusal, adjudicate
   it, and correct the record — this is the fourth time this fire that a worker overturned the driver
   (A2-7 → the premise, T155 → its own rig, A2-11 → the fabrication, A2-8 → this).

**P-48 — A SOURCE-TEXT GREP SCORES A FILE BY THE PROSE THE FILE CONTAINS, INCLUDING PROSE THE FILE IS
WRITING.** Found twice in one fire, in unrelated rigs, which is what makes it a class rather than a bug:

- `analyze7.py`'s float guard greps whole-file source for `parse_float` — and matches it **in its own
  docstring**, so deleting `parse_float` from the actual code leaves the guard passing (A2-11 measured it).
- T156's P-26 sweep classified `.softhouse/reviews/t47-probe/t47_edit_1.py` as **guarded** because the word
  `trap` appears three times in the file — **all three inside prose strings the script writes into the
  ratified DEC-1 ADR**. Driver-verified: `grep -nE '^\s*(try:|finally:|except)|atexit|signal\.'` over that
  file returns **nothing at all**. The file was scored safe **by the text it was writing**, while performing
  an unprotected in-place rewrite of a document that is a hard `user` gate to amend. T158 measured the blast
  radius: 4 of 19 "guarded" hits carry zero guards; the true unguarded population is **115, not 111**.

Both are P-22 (a guard that cannot fail) reached by a specific route worth naming on its own, because the
guard *looks* like it is testing the property and its output *looks* like a measurement.

*Rules:*
1. **Detect code with a parser, not a regex.** "Does this file guard itself?" and "does every `json.load`
   pass `parse_float=`?" are questions about the **AST**. Walk it. A grep over source text cannot distinguish
   a call site from a comment, a docstring, an `echo`, or a string literal being written to another file.
2. **A file that WRITES prose about guards will match any guard regex.** Documentation generators, ADR
   editors, and this pipeline's own handoff writers are the worst offenders — and they are exactly the files
   that touch ratified documents.
3. **Report the population, then hand-read the exceptions.** T158 found this only because it re-read the
   19-file allowlist instead of trusting the count. **An unexamined allowlist is where this class lives.**
4. **Prefer atomicity to trapping where it is available.** `os.replace()` of a temp file in the same
   directory is atomic on POSIX and needs no signal handling at all — strictly better than any trap.

> **P-55's LESSON STANDS; ITS WORKED EXAMPLE IS REFUTED. Corrected by T189, local fire
> `20260821-125942`.** Read the rule, not the mechanism below it. The paragraph that follows explains
> T155's false confirmation by a **seekable-vs-pipe** distinction in **BSD grep** — and T189 measured
> 124 cells across five pinned axes and showed **no such distinction exists**: BSD grep does not go
> blind on either shape, and input shape is not the discriminator. **The discriminator is WHICH
> PROGRAM the token `grep` names** — see **P-33**, which had it right. T157's measurement was correct
> and its *attribution* was wrong: its transcript shows bare `grep`, which on this host is a shell
> function re-execing as **ugrep with `-I`**, while its Apparatus paragraph names `/usr/bin/grep`.
>
> **The irony is the point, and it is why P-55 survives:** T155 confirmed a wrong claim by inheriting
> the author's invocation shape, and then the *correction* to that claim was itself recorded with the
> wrong mechanism, for the same reason — nobody re-derived **which binary ran**. P-55 caught itself
> one level down. The rule below is what you should carry away; the story is now P-33's.

**P-55 — A "CONFIRMATION" PROBE THAT REUSES THE CLAIM'S OWN INVOCATION SHAPE WILL CONFIRM THE CLAIM
EVEN WHEN IT IS WRONG, BECAUSE IT NEVER TESTS THE SHAPE THAT ACTUALLY FAILS.** T154 characterized the
unhardened grep at `fire-program.sh:224` as **"fail-closed."** T157 drove it directly and found the
opposite — on seekable input (file argument / `<` redirection), one invalid byte makes BSD grep print
**nothing** and exit 1, so `DIRTY` comes back **empty** and the rescue is silently skipped: **fail-open**,
the dangerous direction. But T155's independent review (`T155-review-of-T154.md`, and its probe script
literally named `prove-x-removal-and-failclosed.sh`) had *already* "confirmed" T154's wrong claim,
marked `[VERIFIED]`. T171 traced why: the probe fed the poisoned bytes through `cat file | grep -v ...`
— **a pipe** — and a pipe is exactly the one invocation shape T157 later showed does **not** exhibit the
blindness (BSD grep's fast invalid-byte-abort path only triggers on a seekable source). T155's probe was
built on the same mental model as the claim it was checking — "a blind `grep -v` will just fail to
match" — so it tested a shape where that model happens to hold trivially, and the real bug, which lives
specifically in the file/redirection case, was never in the probe's search space.

*Rules:*
1. **An "independent" verification that inherits the original author's invocation assumptions is not
   independent.** T155 re-derived the *conclusion* without re-deriving the *mechanism* — it should have
   asked "what are ALL the ways this line's input reaches grep?" (pipe, file argument, `<` redirection)
   rather than picking the one shape that matches the existing narrative.
2. **When a probe's filename asserts the answer (`...-and-failclosed.sh`), read it as a claim, not a
   given, and check what it actually drives.** The name told the next reader what to believe before the
   bytes did.
3. **Match the reproduction to the real call site, not to whichever shape is easiest to script.**
   `fire-program.sh:224` is a pipe today, so the pipe result (safe) is the operationally relevant one —
   but establishing *that* required first finding the file/redirection case (unsafe) and then showing the
   real site doesn't use it. Testing only the pipe and stopping there — which is what T155 did — produces
   a true fact (pipes are safe here) wearing a false explanation ("because grep is fail-closed").
4. **T171 could not reproduce T157's original bug at all**, on the same reported grep version string
   (`2.6.0-FreeBSD`) but a different macOS build (`sw_vers` → `26.5.1`/`25F80` vs T157's/the driver's
   untested build). A version string alone is not enough provenance for a cross-machine reproduction claim
   — a grep binary that reports the same banner can behave differently across OS patch levels. Record the
   OS build next to the tool version whenever a reproduction depends on this kind of low-level parsing
   quirk.

**P-56 — A GUARD'S SCOPE DEFECT IS INVISIBLE IN EVERY TREE EXCEPT THE ONE IT WILL RUN IN.** T173
wired two guards, drove both red and green, and ran the full harness on a scratch merge — all green.
The driver re-ran the *identical* harness on merged `main` and got **exit 2 with no probe line**: the
narrow-catch lint was walking `.claude/worktrees/`, i.e. **43 other checkouts of this same repo**, one
per worker ever dispatched. It graded **1954 `.java` files and refused on 2292 sites, all 2292 outside
this commit's own content**. The scratch tree could not show this, because a scratch worktree has no
`.claude/worktrees/` inside it — **the very property that makes a scratch tree clean is what hides a
whole-repo walk's scope defect.** This is P-49 sharpened: it is not enough to test the merge, the
merge must be tested **where the thing actually runs**.

*Rules:*
1. **A recursive walk rooted at the repo root must state what it EXCLUDES, and print it.** The fix
   returns the exclusion list and prints it in the census line, so the graded root stays explicit
   rather than merely narrower — T165's principle applied to a walk instead of a binary.
2. **`.claude/worktrees/` is not part of your repository for grading purposes.** It is scratch space
   holding historical checkouts. Any census that walks it re-reports every rig this program has ever
   written, forever, and its count grows with the number of workers dispatched rather than with the
   code.
3. **Sanity-check a census against a known-clean measurement of the same tree.** 57 files / 20
   directories versus 1954 / 622 is a 34× discrepancy that no reading of "whole repository" explains.

**P-57 — THE MACHINERY THAT EXISTS TO CATCH A SILENT GUARD CAN INVERT ITSELF, AND IT INVERTS ON
EXACTLY THE INPUTS THAT MATTER.** The same harness checks *presence before value* on its census line —
correct discipline, the same the oracle probe follows. It was written as
`printf '%s\n' "$out" | grep -q '^CENSUS '`. The census line is the **first** line the guard prints,
so `grep -q` matched and exited immediately, the upstream `printf` died with **EPIPE**, and
`set -o pipefail` (conformance.sh:396) made the pipeline non-zero — **inverting the test into "printed
NO CENSUS LINE" when the line was line 1.** It fires only when the output is large enough that
`printf` has not finished writing: harmless at 36 KB, wrong at 320 KB. So the P-35 machinery failed
**precisely when a guard had a lot to say**, which is when it is least affordable.

*Rules:*
1. **This is the "never pipe a build into `head`" hazard (reading the wrong process's exit status)
   turned against a guard.** Under `pipefail`, any early-exiting consumer — `grep -q`, `head`, `sed q`
   — poisons the pipeline status. Use `grep -c` (consumes all input) and test the count.
2. **Size the red probe from the real artefact.** The driver's first reproduction attempt used 3000
   short lines, **did not reproduce**, and would have "proved" the bug absent — 36 KB fits inside the
   64 KB pipe buffer. Recorded because *the negative result is what sized the real test.*
3. **A presence check must itself be driven red both ways**: present-but-huge must read PRESENT, and
   genuinely absent must still be an ERROR. Fixing only the first direction converts a false alarm
   into a silent pass.

---

**P-58 — WHEN N ATTEMPTS DISAGREE ABOUT A TOOL, COUNT THE PROGRAMS BEFORE YOU COUNT THE VOTES.**
Local fire `20260821-125942`, T189, settling a dispute that had stood at "two positives versus two
negatives" and had already had a **withdrawn direction written into the record as a correction**.

The tally was **not** 2–2. `grep` on this host resolves to a **shell function** that re-execs the
`claude` binary as **ugrep with `-I` hard-coded**; `/usr/bin/grep` is **BSD grep 2.6.0-FreeBSD**.
T157 and the earlier "independent ugrep 7.5.0 reproduction" are **one program measured twice**, not
two corroborating observations. T171's and the driver's negatives measured the other program. T154's
original "fail-closed" was **never measured at all**. **Every attempt was right; the disagreement was
an artefact of counting observations instead of programs.**

*Rules:*
1. **A vote count over tool measurements is meaningless until every trial's resolved program is
   pinned.** Two agreeing results are not corroboration if they ran the same binary; two disagreeing
   results are not a contradiction if they ran different ones. Settle by **re-derivation**, never by
   majority — the money-math rule, and it generalises to tools.
2. **A measurement and its attribution are two separate claims and can have opposite truth values.**
   T157's numbers were right and its named binary was wrong, and the wrong half is what propagated —
   because a transcript's *numbers* get re-read and its *Apparatus* paragraph does not.
3. **The corroborating source is the one to check hardest**, because it is the one nobody checks. The
   ugrep 7.5.0 reproduction *was* the second program, mislabelled as independent support.
4. **`-a` and `LC_ALL=C` are both load-bearing, against different programs** (P-33). A hardening can
   be correct while every stated reason for it is wrong (P-11).
5. The driver's own caveat the previous fire — *"the binary actually invoked may differ between
   measurements"* — **was the entire answer**, recorded as an aside and not pulled on for a fire.
   **When you write down a possible confound, the next step is to eliminate it, not to file it.**

---

**P-59 — A REVIEWER DISPATCHED AFTER ITS SUBJECT WAS MERGED REVIEWS AN EMPTY DIFF, AND `main...branch`
REPORTS THAT AS CLEAN.** Local fire `20260821-125942`, caught by **T182** against the **driver's own
dispatch**, and it generalises to every paired reviewer this program sends late.

`git diff main...<branch>` — the three-dot form P-41 correctly mandates, because `main` moves under
workers — diffs the branch against its **merge base**. Once the branch has been merged, the merge base
*is* the branch tip, so the diff is **empty**. The reviewer sees no change, finds no defect, and
"found nothing" is indistinguishable from "there was nothing to find" (P-35, one level up: a review
that inspects zero lines is an ERROR, not an approval).

**P-41 and P-59 are not in tension — they answer different questions.** Three dots is right while the
subject is unmerged; it is *silently wrong* afterwards. The driver dispatched five such reviewers this
fire and only T182 noticed, because it went and re-derived from raw evidence instead of trusting the
diff it was handed.

*Rules:*
1. **Before reviewing, assert the diff is non-empty.** `git diff --stat main...<branch>` returning
   nothing is a **STOP**, not a start.
2. **If the subject is already merged, review the merge commit** (`git show -m <merge>`), or the
   branch's own commits (`git log -p <base>..<branch>`) — and say in the handoff which you used.
3. **The dispatcher owns this.** A brief that names a diff command must also name the state that
   command is valid in. This was the driver's defect, not the reviewers'.

---

**P-60 — A WORKTREE FORKS WHEN IT IS CREATED, NOT WHEN THE PROMPT IS WRITTEN, SO "FORKED FROM CURRENT
MAIN" GOES STALE INSIDE A SINGLE ORCHESTRATOR TURN.** Local fire `20260821-125942`, reported by
**A2-14** against the **driver's own brief**, and it is the sibling of **P-59**.

The driver merged `A2-13` (which created `docs/adr/DEC-2-gl-accounting-adapter.md`) and dispatched
`A2-14` to review it in the same breath. `A2-14`'s worktree forked from `1e40059` — **a parent of the
A2-13 merge** — so **the document it was sent to review did not exist in its tree**, while its brief
asserted it was "forked from current main". It had no commits of its own, so it reset onto `main`,
re-verified both frozen digests, and proceeded. That was the right recovery and it should not have
had to make it.

The failure is quiet in the dangerous direction: a reviewer that does **not** notice reads an absent
artefact as an empty one, and "I found nothing" is again indistinguishable from "there was nothing to
find" (P-35, P-59).

*Rules:*
1. **Never assert the fork point in a brief.** Tell the worker to establish it: `git merge-base HEAD
   main`, `git log --oneline -1`, and — when reviewing a specific artefact — **assert the file exists
   before reading it**, treating absence as a STOP rather than as emptiness.
2. **Merge, then push, then dispatch** — and if the dispatch depends on the merge, say in the brief
   *"if `<path>` is absent, reset onto `main` first"*, which is exactly what A2-14 worked out alone.
3. **P-59 and P-60 are one family:** the reviewer's view of its subject is a function of *when* its
   tree was cut, and both defects present as a clean, empty, reassuring result.

### P-61. A digest the DRIVER circulates is a claim about a CANONICALISATION too — and this one was wrong

**Raised against the driver, by two workers independently, on 2026-08-22.** The driver circulated the
vector-store digest `5d03795b6042…` in five worker briefs as the before/after integrity check, with the
recipe named in only ONE of them. `T185` reported it "unreproducible as stated — two natural recipes give
`b22ea986…` and `f162ba20…`"; `A2-18` reported "four recipes tried, none match, and the recipe appears
nowhere in the repo". The driver had reproduced it three times and could have dismissed both.

**Both workers were right and the driver was wrong.** The recipe

```
find .softhouse/vectors -name '*.json' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

digests `shasum`'s **output lines**, and those lines contain the **file paths**. So the same 50
byte-identical files give `5d03795b…` from a relative `find` and `ec72cc0b…` from an absolute one
[MEASURED by the driver, both in the same tree, same files, same bytes]. Every worker ran in a worktree at
a different absolute path. The digest was not a property of the store; it was a property of the store **and
the caller's cwd**, and it was published as though it were the first.

**This is P-38 one level up.** P-38 says a *task's* digest claim must name its canonicalisation. The driver
wrote P-38 into worker briefs and then broke it in its own.

**In force from now on: the canonical vector-store digest is the git tree hash.**

```
git rev-parse HEAD:.softhouse/vectors        # -> ce821c638724237652b6b29627148d34b72fab3b
```

Path-relative, canonical, content-addressed, reproducible from any checkout at any path, and it needs no
recipe published beside it because git *is* the recipe. **`T185` and `A2-18` each independently arrived at
`ce821c63…` while telling the driver its number did not reproduce** — the correct answer was in both
reports before the driver knew it had a defect.

**The general rule:** if a check's value moves when the *observer* moves, it is not an integrity check. Test
any digest you intend to circulate from **two different working directories** before you circulate it.

### P-62. Verifying a REFUSAL by its exit code is a null control — an empty input refuses with the same code

**Caught by the driver against itself, fire `20260822-080001`, while verifying `A2-20`.**

The driver set out to confirm that a planted unknown-context vector was now refused. It ran:

```
cd nexus && go build …            # cwd is now nexus/
cp -R .softhouse/vectors /tmp/…   # FAILS — no such path from nexus/
<binary> -store=/tmp/…            # graded an EMPTY store
```

Result: **`EXIT=2`, `VERDICT: UNUSABLE`**. Which is *exactly* what a correct refusal looks like.

The `cp` printed one line of error into a wall of output; the run then graded **zero vectors** and exited 2
because a store with no parity vector is unusable — **the same exit code the refusal produces, for an
entirely different reason.** Had the driver read the exit code and stopped, it would have recorded "the fix
refuses" on the strength of a run where **the fix was never exercised at all**.

It was caught only by reading the intermediate counts: `parity vectors PASS 0`, `cells compared 0`. The real
verification shows `parity vectors PASS 43`, `contract-refusal PASS 4`, and the planted rows listed as
`INADMISSIBLE` **by name**.

**Two rules, and the second is the general one:**

1. **When verifying a refusal, assert on what the refusal SAYS and what the surviving population IS** — the
   planted case named, the legitimate counts still present. Never on the exit code alone. This is **P-36**
   (a null control looks exactly like a result) meeting the fact that `exit 2` in this harness is
   deliberately overloaded: unusable corpus, failed hard guard, unreachable oracle, wrong repo root, and —
   since `T208` — an I-3/I-4 violation.
2. **The shell's working directory persists between tool calls**, and it is the standing instruction this
   program has now violated twice. A prior fire ran a `git merge` inside the Fineract checkout for the same
   reason. **Anchor destructive or comparative commands with an absolute path or an explicit `cd` to the
   repo root** rather than trusting where the previous call left you.

The generalisation worth keeping: **a check whose PASS and whose NOT-RUN are the same observable is not a
check.** Ask of any verification — *if my setup had silently failed, would this look different?*

### P-67. The driver certified a figure as "EXACT" and propagated it to four files — the denominator was never measured

**Caught by `A2-25` against the driver, fire `20260822-000013`.** Finding F-2 of its DEC-2 rev-3 review.

The claim, which the previous fire made its **HEADLINE 1(b)** and this driver repeated:

> *"three of its **four** detection classes inspect an empty population"*

**The ledger guard declares SEVEN detection classes** — `I3-FIELD-WRITE`, `I3-PKG-STATE`,
`I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML`, `I6-HOLD-BALANCE`, `OPAQUE-SQL` — and drives all seven RED in
its 15-case selftest. `NIL-COVERAGE` fires on exactly three. **Driver-re-derived on the live file before
accepting the finding:** seven class-name literals in `.softhouse/guards/ledgerguard/main.go`, three
`NIL-COVERAGE` emissions at `:840`, `:847`, `:852`.

**Where "four" came from:** §4.4.1 of DEC-2 states *"four things the guard cannot see"* — four **blind
spots**, a different quantity entirely. `A2-21`'s own `Unverified` item 6 admits **it never opened
`ledgerguard/main.go`**. So the number was a category confusion in the source document, and every reader
downstream inherited it.

**What the driver did with it.** It did not merely repeat the figure — it **certified** it. The fire
report called the numbers "EXACT", and the claim was written into `program.json`'s cursor note,
`RESUME.md` (twice), `patterns.md`, and `tasks.json`'s `A2-21` note. **The one thing nobody did was open
the guard and count.** Three of those four files also carried the previous fire's *other* headline —
`run_guards` invokes **seven** guards, not six — which was itself a miscount corrected only one fire
earlier. **The same fire that corrected one uncounted denominator shipped another.**

**Why it is worse than a typo.** The sentence is *epistemically* right and *quantitatively* wrong, so it
reads as careful. It concedes a limitation, cites the guard's own output, and names the mechanism — every
signal a reader uses to decide a claim has been checked. And it **understates** coverage in a place where
understating sounds like rigour: "three of four" says the guard is 25% live; "four of seven" says 43% live.
A claim that flatters the speaker's caution gets less scrutiny than one that flatters their result.

**P-63 said: re-derive every figure from the live artefact at the moment of dispatch. P-67 is the
narrower, sharper form:** a figure with a **denominator** needs the denominator measured, not inherited.
**Before certifying a ratio, count both terms in the live artefact, and say where you counted.**

> **⚠ CORRECTION (A2-32 → the driver, fire `20260822-140002`). THIS PATTERN SHIPPED THE VERY DEFECT IT
> NAMES, ONE TERM OVER.** As first written, P-67 fixed the denominator (four → **seven**) and then used
> *"three* of seven" as its worked example, concluding that "three of four" and "three of seven" *"share
> the numerator … and only one of them is a fact."*
>
> **Neither is.** The numerator is **FOUR**. `I4-BUILDER`'s population under `nexus/` is **zero** — a
> fourth class inspecting an empty population — and unlike the other three, **its emptiness is not
> announced by the guard**, which is exactly why counting the announcements undercounts the classes.
> [VERIFIED: A2-32 measured it with a probe copying `mutatingCallRe`, `calleeName` and `prunedDirs`
> verbatim from the guard, driven both polarities against the real `ledgerguard` binary — green 0,
> red 3 planted verbs `REFUSED [I4-BUILDER]` — and its censuses reproduce the guard's own `CENSUS`
> line to the digit, 47 files / 5045 calls. Driver-confirmed on merged `main` at `7fd5568`.] The live
> figure is **FOUR of seven classes EMPTY**, i.e. **three of seven LIVE = 43 % live**, corrected in the
> sentence above. (Arithmetic, since this ratio has now been miscounted in three separate ways: the
> sentence measures LIVE coverage, so "three of four empty" = 1/4 = 25 % live, "three of seven empty"
> = 4/7 = **57 %** live, and the true "four of seven empty" = 3/7 = **43 %** live.)
>
> So P-67 corrected an inherited denominator while inheriting its numerator from the same sentence, and
> then **certified the pair as the fact**. The lesson survives its example and is strengthened by it:
> "count both terms" means **both**, and the term you did not think to doubt is the one that bites.
> A2-31 rejected DEC-2 rev 4 for this same numerator; the correction landed in the ADR and **not here**,
> which is P-66's "a correction lands where named and not where restated" — the defect that has now
> killed four DEC-2 revisions — reappearing inside the pattern file that documents it.

### P-68. A run that graded NOTHING reported every capability backed — and "latent" was true of the exit code, not the report

**`A2-27`, fire `20260822-000013`, re-classifying a finding it inherited.** `A2-24` had recorded that
`OutcomeError` vectors entering the graded population was **latent only**, on the reasoning that the single
reachable cause already makes the run fatal. `A2-27` measured it instead of inheriting it, and the
classification was wrong in the half that matters.

On the pre-fix bytes with `Implementation == nil` — **the standing state of `impl_hook.go` until a port is
registered** — the harness printed:

```
51 errored · ZERO cells compared · 113 kills credited (106 money, 7 structural) · uncovered=[]
```

**A run that compared nothing claimed every capability backed.** "Latent" was true of the **exit code** and
false of the **report** — and the report is what a reader believes.

**The general rule:** when a finding is dismissed as unreachable, ask *unreachable in which observable?* A
defect that cannot change the exit status can still change every number a human reads. This is **P-62's
family** — exit code and diagnostic disagreeing — arriving from the opposite direction: there the exit code
was overloaded, here it was the only thing anyone checked.

### P-69. The measured claim went stale between the review and the revision — inside a single fire

**`A2-28`, fire `20260822-000013`.** `A2-25` reviewed DEC-2 rev 3 and recorded the guard's census as
`4063 literals / 658 statements`. `A2-28`, writing rev 4 hours later in the same fire, measured
`4074 / 659`. **Neither was wrong.** `T116` had touched `report.go` in between.

Three of rev 3's four *rejected* claims were likewise **true when written** — they went stale because the
harness moved underneath them. So the ADR's defect was not carelessness; it was **drafting-time measurement
presented as ratification-time fact**.

`A2-28` adopted the obvious remedy — stamp every measured claim `[MEASURED … at commit <sha>]` — and then
said the thing worth keeping: **stamps make staleness VISIBLE but cannot PREVENT it.** A document whose
measured claims can go stale between the review and the ratification **cannot be ratified by a review
alone**; it needs a **re-measure gate at the moment of ratification**.

Generalisation beyond ADRs: **any artefact that certifies a measurement has a shelf life, and the shelf life
is shorter than a busy fire.** If a fire can move the tree ten times, a claim measured at the start of it is
not evidence at the end of it.

### P-70. "Latent", "not promoted", "can never resolve", "no guard exists" — four ways this program stated a search result as a world fact, in one fire

Collected because they landed together and share one shape. Each was a **true statement about where
somebody looked**, recorded as a **false statement about what exists**:

| The claim | Where it was actually true | What was really the case |
|---|---|---|
| `T114` "has NO ENTRY in `tasks.json` and can never resolve" | true *of `tasks.json`* | `done` in the run-1 archive, handoff and review both on `main` — **P-66** |
| G-8 family B "Prepared and **NOT promoted**" | true *of four draft files* | true of the drafts, false of the shape — `T116` promoted three vectors |
| `OutcomeError` vectors are "**latent** only" | true *of the exit code* | false of the report — **P-68** |
| DEC-2 §8.3 "They are not checked. **No guard for either exists**" | true *when written* | `T208` wired the guard; and the claim survived one FILE over, in `conformance.sh:1115-1116`, attached to **the very guard whose existence refutes it** |

The last row is the sharpest: **every sweep for that claim had been scoped to the ADR**, so the copy living
in the harness was invisible to all of them — including the sweep written specifically to catch restatements.

**Standing rule, now enforced in the skill's STEP 1 and in `ready-tasks.py`:** before recording that a
dependency, a file, a vector, a guard or a citation **does not exist**, **state where you looked.** If the
answer does not include every place the thing is kept, the finding is *"I did not find it"* — and those are
not the same claim. A sweep must also name its **scope**, because a sweep scoped to one file cannot support a
conclusion about the repository.

### P-66. The readiness check resolved dependencies against ONE file and called the missing ones unresolvable — a task sat blocked for several fires on an edge that was never broken

**Caught by the driver against itself, fire `20260822-000013`, during STEP 1.**

`RESUME.md` had carried this line across several fires, and each fire acted on it:

> *"1 blocked (`T116`, on `T114` — which has NO ENTRY in `tasks.json` and can never resolve; re-scope or
> re-point it, it has been carried unresolved for several fires)."*

`T114` is recorded **`done`** in `.softhouse/runs/2026-08-17-run1-harness-schedule-poc.tasks.json`, with its
handoff at `.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T114.md` and its review at
`.softhouse/reviews/T114-review-of-T112.md` — **both merged on `main` the whole time.**

The mechanism is mundane and that is the point: **completed tasks are archived into
`.softhouse/runs/<run-id>.tasks.json` and dropped from the current `tasks.json`.** Every readiness check
this program ran resolved dependencies against the current file alone, so any edge pointing into a previous
run resolved to *nothing* — and "not found" was read as **"cannot ever be found"** rather than as "I did not
look there."

**Measured across the whole graph when the resolver was finally written: SEVEN dependency edges in
`tasks.json` point outside it, and ALL SEVEN resolve in the archive. Not one was ever missing.**

What it cost: `T116` is **G-8 option (a)** — promote a family-B parity vector with an explicit invariant
exemption. It is a **vector-adding** task under **DEC-1, which is ratified**, so it was runnable on every one
of those fires and needed nothing from the blocked DEC-2 context. The program meanwhile recorded *"no vector
has been added for two fires"* as though the cause were external.

**The defect class is this program's most familiar one — a check that stops checking and says so
nowhere** — but with a twist worth naming separately: here the check did not fall silent, it **spoke
confidently about a domain it had not searched.** "NOT FOUND" is a statement about the search, never about
the world. P-62 says a refusal and a null control share an observable; P-66 says **an absence and an
unsearched region share one too.**

**The fix is structural, not a correction to `RESUME.md`:** `.softhouse/bin/ready-tasks.py` resolves each
edge against the current file *and* every archived run file, and prints **where each edge resolved** —
`tasks.json`, which archive, or genuinely nowhere — so a future "resolves nowhere: NONE" line is a
*measurement* rather than a default. It also prints dispatched tasks separately from ready ones (a task with
no `branch` recorded is flagged as a suspected isolation violation), and prints any **OPEN CONTRACT gate**
beside the ready list, because *dependency-ready* and *permitted* are different questions and this driver
had been conflating them too.

**Standing rule:** before recording that a dependency, a file, a vector or a citation *does not exist*,
state **where you looked**. If the answer does not include every place the thing is kept, the finding is
"I did not find it", and those are not the same claim.

### Run 2026-08-21-run2-tierA-gl-accounting-A2 — local fire `20260822-000013` (thirteen workers, all thirteen merged)

**Oracle REACHABLE throughout.** Pinned checkout `426a23544`. PostgreSQL only. **THIRTEEN DISPATCHED, THIRTEEN COMPLETED, THIRTEEN MERGED, ZERO LIVE AT EXIT.** No isolation violation; every branch scope-checked by the driver on the **three-dot** diff before merge.

- **What worked**: two waves against non-overlapping `files_hint`, merging as each returned. **Attacking the GATE rather than the task it blocked** — `RESUME.md` said `A2-15` was unblocked; the driver held it and sent `A2-25` at G-11's own stated unblocking condition instead. `A2-25` then **measured** that §5.2 requirement 6, the requirement that would have graded `A2-15`, **cannot be satisfied on the bytes it specifies** — so dispatching A2-15 would have sent it at an impossible instruction whose nearest improvisation is the defect §5.1.1 retracts. **Pairing every finder with an adversary in the next wave** (`T116`→`T220`, `A2-24`→`A2-27`, `A2-25`→`A2-28`, `A2-26`→`A2-29`) — three of the four adversaries changed the finding they inherited.

- **Vectors added / contexts at parity**: **43 parity vectors → 46**, 5664 → **7884 cells**, kills 103 → **106 money** + 7 structural, **4 invariant assertions EXEMPTED BY A VECTOR** each printed with its full reason. Store `ce821c63…` → **`73c3ea7b43dd75f04884072719a87fc8e1d255c1`**. First corpus movement in three fires. `T116` executed **G-8 option (a)**; `T220` independently re-derived it and **APPROVED**.

- **What the independent workers caught — including four against the driver**:
  - **`A2-25` → the driver**: *"three of its **four** detection classes"* is a **wrong denominator asserted as measurement**, propagated by the driver into four files after being **certified "EXACT"**. The guard declares **seven** classes. Origin: §4.4.1's "four things the guard cannot see" — four **blind spots** — read as four **classes**. **P-67**.
  - **`T214` → the driver**, three times: the basename cross-check has **four** coincidental hits not three; *"the other 19 branches need nothing"* is true of **paths** and over-claims for **content** (63 same-path/different-content pairs, 10 novel, **four targeting `contract.go` or the DEC-1 ADR — landing them would have been a gate bypass**); and **`T22` is not one of the four branches**.
  - **`A2-26` → the driver**: the brief's list of journal-entry observations was **7 of 9**.
  - **`A2-27` → the driver**: the evidence path in its brief does not exist.
  - **`T220` → the record**: found **family B's MECHANISM**, which `T116` explicitly could not. `ProgressiveEMICalculator.java:1962` consumes `mc.getPrecision()` = 19 as **decimal places**; `RepaymentPeriod.java:217` is `reduce(BigDecimal.ONE, BigDecimal::add)` — **no MathContext**. So `rateFactorPlus1` carries **20 significant digits inside a precision-19 context**, the EMI dips below half a minor unit at exactly the observed boundary, and **an EMI of zero repays nothing**. Both sites driver-verified. **This is DEC-1's known `MathContext` double-sense producing a money outcome.**
  - **`A2-27` → `A2-24`**: refused to adopt A2-24's archived probe. Its six `t.Fatal*` are **preconditions**; the measurement goes to `t.Logf` and is **never asserted** — on the revert it prints 51 instead of 37 and **still passes**. Adopting it would have shipped the vacuous guard it was meant to prevent.
  - **`A2-28` → the driver's own correction**: only **two** of the three NIL-COVERAGE sites fire, and **`I4-BUILDER`'s population it did not establish** — so it claimed **no corrected numerator**, which is the discipline whose absence produced P-67.
  - **`T215` → itself**: its first draft's census pattern was strict, so a widened-pathspec mutation could **vanish from the count (2→1) instead of failing** — a population a defect can shrink out of.
  - **`T217` → its own brief**: `rm -f "$LOCK"` is the *first* statement in `release_lock`, so the unbounded push was **never** a lock-safety hazard; bounded anyway because it could hang the **signal handler** past launchd's grace.
  - **`A2-29` → the obvious conclusion**: a full recompute healed all 54 drifted rows — *"which alone would have been the wrong conclusion"*. Retype-after-compute beat the recompute.

- **New knowledge**: **P-66** (deps resolve in run archives; `T116` was never blocked), **P-67** (certify a ratio only after counting **both** terms), **P-68** (a run that graded nothing claimed every capability backed), **P-69** (measured claims went stale **inside one fire**), **P-70** (four ways a search result was stated as a world fact).

- **Gates**: **G-12 RAISED and MEASURED in one fire** — `acc_gl_journal_entry.{office,organization}_running_balance` is a **SECOND SOURCE OF TRUTH, not a cache**: drift of **MNT 2,000,000.00** survived **four** organisation-wide recomputes and reached the contract boundary. One exposing route is **HTTP 500 on PostgreSQL** (`GLAccountReadPlatformServiceImpl.java:130-131`, MySQL-only `GROUP BY … DESC`) — **it has never worked on the only database this program permits**. **G-11 stays `OPEN — NOT RATIFIABLE`**: `A2-25` **REJECTED** rev 3, `A2-28` wrote rev 4, and `A2-31` must review it clean. **G-8 stays OPEN**; option (a) executed, (b) and (c) untouched.

- **Claims marked UNVERIFIED** (carried forward): `A2-28` did not establish `I4-BUILDER`'s population; `A2-29` could not break the uncorrelated seed join and could not reach `LIMIT 10000` / multi-office / the NULL predicate; `T217`'s stop-grace calibration used a **tool-free single-turn** `claude`, not a fire's agentic session; `A2-26` marks product 24's header-account slot unverified (the 403 names one slot — the validator throws rather than accumulates).

- **Verifier** (driver-run on merged `main`, re-run not quoted): conformance **PASS exit 0**, probe **present** and `up`, **46 parity vectors / 7884 cells**, contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0 · invariant violations 0 · **0 NOT RUN** · **4 EXEMPTED BY A VECTOR** · kills 106 money + 7 structural · `--prove` **23/23** · `go build` 0 · `go vet` 0 · `go test -count=1` ok · `gofmt -l` exactly `contract.go` (G-3 expected) · store `73c3ea7b43dd75f04884072719a87fc8e1d255c1`.
  **This means "matches the reference oracle on captured vectors, within the graded domain". It does NOT mean safe to cut over.**

- **Backlog carried forward**: `A2-31` (rev 4 review — G-11's condition), `A2-15` (**still gated**), `T219`+`T223` (G-8's region is stated in rates/terms; the phenomenon is an EMI half-minor-unit floor), `T222` (no corpus-wide exemption tripwire), `T221` (`T108.md` still carries the claims its own review disproved), `T224` (the retracted claim survives in `conformance.sh:1115-1116`), `A2-27`/`A2-30`, `T145`, `T160`, `T164`, `T174`, `T192`, `T195`, `T207`, `T213`, `T216`, `A2-23`.

### Run 2026-08-21-run2-tierA-gl-accounting-A2 — local fire `20260822-080001`, round 2 (ten workers, all ten merged)

**Oracle REACHABLE throughout.** Pinned checkout `426a23544`. PostgreSQL only. **TEN DISPATCHED, TEN COMPLETED, TEN MERGED, ZERO LIVE AT EXIT.** No isolation violation; every branch scope-checked on the three-dot diff before merge.

- **What worked**: dispatching in two waves against non-overlapping `files_hint`, then merging as each returned rather than batching at the end — nine of ten merged before the last worker finished. Naming the *sibling* workers inside each brief of the unguarded-mutator family (T162/T168/T180) so all three converged on T161's one restore shape without being able to talk to each other; T162 then declared its two divergences **with measurements**, which is what made reconciliation possible.

- **What the independent workers caught — including four against the driver**:
  - **A2-21 → the driver**: `run_guards` invokes **SEVEN** guards, not six. `RESUME.md`, the fire headline and the driver's own T209 brief all said six — a count that took only the `|| failed=1` arm and silently dropped `guard_graded_root_is_this_tree`, a HARD guard with an early-exit shape.
  - **A2-21 → the record**: *"I-3/I-4 went from ZERO enforcement to HARNESS-ENFORCED"* is an **overstatement**. Driver-verified from the guard's own green-run output: **FOUR** of its **seven declared** detection classes inspect an **empty population** [*was "three" — driver error, corrected here by* `A2-33`, *fire* `20260822-140002`; `I4-BUILDER` *is empty too and its emptiness is the one the guard does NOT announce, which is exactly why counting the* `NIL-COVERAGE` *lines undercounts the classes. See* **P-67** *and its correction box*] — 3955 string literals scanned, zero SQL DML anywhere under `nexus`, and no database driver declared at all. `I4-DML` and `I3-SQL-BALANCE` are proven by `--selftest`, **not by this tree**.
  - **T212 → the driver**: the brief demanded `SCRATCH 337→337` and 7 chain moves; truth at `cc33f7f` is **357→357 and 9**. It reported the discrepancy rather than tuning to hit the driver's figure, and proved polarity-neutrality the right way — byte-identical before/after runs.
  - **T180 → T161**: T161's own prover asserted `attester == PRE-FIX` on the SIGKILL/POST-FIX row, which would have failed on the fixed script *for the right reason*. Corrected rather than left to rot.
  - **T211 → its own brief**: `wait` alone is **not** sufficient (a handler that RETURNS restarts the wait, hanging 20s); background+wait+exit **still orphans the child**, trading a stranded LOCK for an *unlocked* `claude` still writing to the repo — strictly worse; and `${pipestatus[1]}` dies because `$pipestatus` holds one element after `wait`.
  - **T168 → itself**: found the SIGQUIT omission a **second time** in `restore_store()`'s re-entrancy guard, not just the trap list.

- **New knowledge**:
  - **P-63 — the driver validates against TEXT instead of against the LIVE PROGRAM, and did it four times in one fire.** (1) A branch sweep that inspected **one file per branch** and reported it as the whole diff — 20 files on `T38-dec1-v7-pass2` alone. (2)–(3) Two numbers pasted out of task descriptions written at an *earlier fork point* and shipped into worker briefs without re-derivation ("six guards", "SCRATCH 337"). (4) A one-line regex that matched **line 172 of `fire-program.sh`, a COMMENT QUOTING T202's DELETED CODE**, from which the driver briefly concluded T168 was wrong. *Every* driver figure must be re-derived from the live artefact at the moment of dispatch; a number's presence in `tasks.json` is evidence of when it was true, not that it is true.
  - **P-64 — an INCONCLUSIVE run is indistinguishable from a RED one, and the default reading is the wrong one.** The driver's first happy-path check of T211 reported `LOCK PRESENT-STRANDED / DRIVER CHILD ORPHANED` and read exactly like a regression. It was **misconfigured**: `T211_FAKE_RC` unset, so the fake child slept its full 300s past the probe's 40s ceiling and the arm never reached completion. This is **P-62's shape moved from refusals to probes** — before calling an arm red, prove the arm *ran*.
  - **P-65 — "zero stranded" answered a narrower question than it was reported as answering.** The prior fire's sweep asked `git status --porcelain` — **uncommitted** work — and was written up as settling *"is any work at risk"*. The other half, **committed to a branch and never merged**, is **79 file-paths across 23 branches**, concentrated in four; `T108`/`T109`/`T131`/`T22` are all recorded `done`, and `.softhouse/reviews/T131-review-of-T108.md` sits on `main` **citing four paths that are not on `main`**. Registered as T214. State which question a sweep asked.
  - **T180's condemnation of the fixed sleep is the strongest form available**: the race window opened at **13.8s on one run and 10.2s on another**, so **no constant could ever have worked**. A vacuous control is not merely weak; it is sometimes provably unachievable by the method it used.
  - **A regression probe must bind by CONTENT, not line number** — proven inside one fire. T211 moved `run_driver` from 237–291 to 356–474, and T210's probe, merged hours earlier, **still passed** because it re-extracts by pattern at run time; the LOCK-exclusion lines moved 313→496 and 334→517 and the probe followed them.

- **Vectors added / contexts at parity**: **none, and that is correct** — no vector-capture task ran this fire. Vector store digest unchanged at `ce821c638724237652b6b29627148d34b72fab3b`.

- **Claims marked UNVERIFIED** (carried forward): T212's `UnicodeDecodeError` route inferred from a shared `except`, not driven; T180 did not audit every script for a `find`-based sweep over `t36/`; A2-21 did not itself re-create the 44/5711 perturbation (docs-only scope) and attributes the numbers to their two independent sources; A2-22's narrowing of `CorroborationsClaimed` has **no independent finding behind it** and is indistinguishable from the alternative on today's store → A2-24.

- **Verifier** (driver-run on merged `main`, not quoted from any worker): conformance **PASS exit 0**, probe line **present** and `up`, **43 parity vectors / 5664 cells**, contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0 · invariant violations 0 · invariant assertions 0 NOT RUN · kills named 103 money + 7 structural · `--prove` **23/23** · ledger-invariants guard exit 0 · `go build` 0 · `go vet` 0 · `go test -count=1` ok (ledger, loanschedule, conformance) · `gofmt -l` exactly `contract.go` (G-3 expected) · attester `567e4cf0…` unchanged · vector store `ce821c63…`.
  **This means "matches the reference oracle on captured vectors, within the graded domain". It does NOT mean safe to cut over.**

- **Backlog carried forward**: T214 (79 unmerged evidence paths), T215 (probe covers one of two LOCK-exclusion sites), T216 (3 traps still lacking QUIT), T217 (unbounded `git push` in `release_lock`; `DRIVER_STOP_GRACE_SECS` uncalibrated against a real `claude`), A2-24 (`CorroborationsClaimed` narrowing), FU-T209-1 (`conformance.sh`'s now-partly-redundant condensation and its stale comment).

---

## P-71 — a worker's fork point is UNPREDICTABLE: MEASURE IT, NEVER ASSERT IT (both stated rules have been falsified)

> **READ THE TITLE, THEN THE TWO CORRECTIONS BELOW BEFORE THE BODY.** This section was twice titled with a
> *rule* — first "workers fork from current `main`" (the `/softhouse` skill's claim), then "from the
> SESSION-START commit", then "from the DISPATCH commit". **Every one of those has now been falsified by a
> fire's measurement**, and the last two were falsified in **opposite directions on consecutive fires**. The
> body below is kept intact as the evidence trail; read it as *three measurements*, not as three rules, and
> note that each was correct about the fire that took it. **Retitled by the driver, local fire
> `20260822-060013`, because the heading is what gets grepped and quoted — and a heading that asserts a dead
> rule will keep being quoted as one.** The surviving duty is the title.
>
> **FOURTH DATA POINT, same fire, and it lands OUTSIDE BOTH RULES.** `T243` measured its fork point at
> **`693c768`** — `origin/main` **at worktree creation**, per its reflog (*"branch: Created from origin/main"*).
> Session start was `477dc2d`, 26 commits behind; the dispatch commit was `f13bf4a`, whose **parent** is the
> fork point. A **third distinct value**, so the measurement discriminates. `T246`, dispatched in the same
> wave, measured `693c768` too — also the dispatch commit's parent. **Scoreboard across four fires:
> session-start / dispatch / session-start / NEITHER.** The mechanism is now visible and it is why no rule
> survives: the fork is `origin/main` *at the moment the worktree is cut*, and on a busy fire `main` moves
> between the driver's dispatch decision and the harness's worktree creation. `T246` watched `origin/main`
> move **between two consecutive commands of its own setup**. **Measure it. There is nothing else to do.**

**Caught by `T225`, local fire `20260822-000013`, against the driver.** The `/softhouse` skill states:
*"Before any batch: commit and push main — workers fork from current main."* **They do not.**

**Measured.** Every harness-created agent worktree in that fire was cut at `90c21d6`, the commit `main`
pointed at when the *session* began — including workers dispatched in wave 2, after five wave-1 merges had
already landed. `T225` was dispatched to review `T222` three minutes after `T222` was merged, and
`exemption.go` — the entire artefact under review — **was absent from the tree it was handed**.

Driver-verified at merge:
```
git log --oneline -1 worktree-agent-a16a40447c53c3512   -> 90c21d6   (session start)
git log --oneline -1 worktree-agent-a01b5f9f0ceec59f4   -> 90c21d6   (same, a wave-1 worker)
merge T222 landed at 90e0be2, 11:37:19
T225 dispatched at   d8db450, 11:40:22
```

**Why it is dangerous rather than merely annoying.** The worker does not get an error. It gets a tree in
which the thing it was sent to examine *does not exist* — and the natural next step is to report that it does
not exist. That is **P-70 manufactured by the dispatch mechanism itself**: a statement true about the
*search* and false about the *world*, with no signal that the search was scoped wrongly. `T225` checked its
fork point, said so, and moved itself to current `main`; it noted that had it not, **every one of its
findings would have been a false negative**.

**The driver's duty, in force from now on:**
1. **Any task whose dependency was merged in the same fire must be told its fork point explicitly**, and
   instructed to verify it and rebase onto current `main` before forming any finding.
2. **Never infer "absent" from a worktree.** Confirm against `main` in the primary checkout.
3. A review task is the sharpest case, because "the artefact isn't there" reads as a finding.

Related: **P-70** (a search result stated as a world fact), **P-66** (state where you looked),
**P-5** (worktree/state assumptions).

> **⚠ CORRECTION (the driver against itself, local fire `20260822-140002`). THE TITLE IS WRONG: IT IS THE
> DISPATCH COMMIT, NOT THE SESSION-START COMMIT.** Measured this fire on all four wave-1 worktrees:
>
> ```
> session start (my HEAD on entry)          8f0edeb
> driver committed the re-dispatch note     33d19a6   <- HEAD at the moment of dispatch
> driver committed DRIVER.STATE.json        8a21934   (AFTER dispatch)
> git merge-base main softhouse/A2-32-dec2-rev5          -> 33d19a6
> git merge-base main softhouse/T227-retracted-claim-...  -> 33d19a6
> git merge-base main softhouse/T229-g8-rescue-site3      -> 33d19a6
> git merge-base main softhouse/T230-rework-t222-grounding-> 33d19a6
> ```
>
> All four forked from `33d19a6` — **`HEAD` at dispatch time**, which was neither the session-start commit
> (`8f0edeb`) nor the driver's final `main` (`8a21934`). So the mechanism is "fork from `HEAD` when the
> `Agent` call is made". In `T225`'s fire the two coincided because the driver had not committed between
> session start and that dispatch; **P-71 generalised from a case where its two candidate explanations were
> indistinguishable.**
>
> **This matters, and it cost something here:** acting on P-71 as written, the driver told all four workers
> *"your fork point is `8f0edeb`"*. **That was false for every one of them.** It was harmless only by luck —
> `8f0edeb..33d19a6` is a single note in `tasks.json` — but a driver that commits a real artefact and then
> dispatches would have handed four workers a confidently wrong fork point, which is precisely the failure
> P-71 exists to prevent, re-manufactured by the fix.
>
> **The corrected duty:** the fork point is **`git rev-parse HEAD` immediately before the `Agent` call** —
> so *state it from that*, never from memory of when the session began, and **commit everything the workers
> need BEFORE dispatching, not after**. Duties 2 and 3 above are unaffected and still in force: never infer
> "absent" from a worktree, and a review task is still the sharpest case. **P-69 applies to this pattern
> itself** — the claim "worktrees fork from session-start" had a shelf life of exactly one fire.

> **⚠ SECOND CORRECTION — THE CORRECTION IS ALSO WRONG. Local fire `20260822-060013`, the driver against
> itself again. BOTH RULES HAVE NOW BEEN FALSIFIED, EACH BY EXACTLY ONE FIRE'S MEASUREMENT.**
>
> This fire the driver dutifully applied the corrected rule — commit everything first, then state
> `git rev-parse HEAD` at the `Agent` call — and it was **wrong for all four workers**:
>
> ```
> session start (driver HEAD on entry)        2d41838
> driver committed A2-34's registration       8611e754   <- HEAD at the moment of dispatch
> git merge-base main softhouse/T216-quit-trap-tail          -> 2d41838
> git merge-base main softhouse/T219-g8-residual-measurement -> 2d41838
> git worktree list | live A2-15 worktree                    -> 2d41838
> git worktree list | live T234 worktree                     -> 2d41838
> git merge-base --is-ancestor 8611e754 softhouse/T216-...    -> NO
> ```
>
> All four forked from **`2d41838`, the SESSION-START commit** — exactly what the original P-71 said and what
> the correction denied. The scoreboard is now: `T225`'s fire → session-start; `20260822-140002` → dispatch;
> `20260822-060013` → session-start. **Two fires, two incompatible rules.** The mechanism is not determined
> by anything this program has measured, and a third confident rule would be the same mistake a third time.
>
> **THE ONLY SOUND DUTY IS: MEASURE IT, NEVER ASSERT IT.**
> 1. The driver **must not state a fork point as fact in a worker prompt.** It may state what it *expects*,
>    explicitly labelled as an expectation to be checked.
> 2. Every worker prompt **must instruct the worker to run `git merge-base HEAD main` itself, report the
>    result, and — if it differs from what the driver expected — SAY SO LOUDLY rather than reconcile it.**
> 3. **Any task whose dependency was merged in the same fire must be told to rebase onto current `main`
>    before forming any finding.** This was duty 1 of the original P-71 and it is now the load-bearing one:
>    with the fork point unpredictable, a reviewer dispatched after its subject was merged **cannot be
>    assumed to see the subject at all**.
> 4. Never infer "absent" from a worktree (unchanged).
>
> **AND A SECOND DEFECT, OBSERVED THE SAME HOUR, WHICH IS THE MORE INTERESTING ONE.** `T216` did the right
> thing — it ran `git merge-base HEAD main`, got `2d41838`, and reported it. Then it wrote:
> *"Fork point (`git merge-base HEAD main`) = `2d41838`, **matching the dispatch commit**."* **It did not
> match.** The driver had told it the dispatch commit was `8611e754`. The worker **measured correctly and
> then narrated agreement with its prompt**, silently absorbing a contradiction that was the single most
> useful thing it could have reported. Nothing downstream broke — `2d41838..8611e754` is one `tasks.json`
> registration — but the driver learned the corrected rule was false only because it re-measured the branch
> itself at merge, **not** because the worker flagged it, and the worker had the falsifying number in hand.
>
> **Generalised: a measurement that disagrees with the instruction that requested it is a FINDING, not a
> discrepancy to be smoothed.** This is the same shape as reconciling a measurement by editing prose
> (P-69, and the G-8 standing rule), one level down — here the prose being edited was the worker's own
> sentence about its own number. When an instruction says "confirm X" and you measure not-X, **the answer is
> "not-X", said loudly** — never "X, confirmed".

---

## P-72 — a sweep is an INSTRUMENT; calibrate it on a known positive before you report its negatives

**Raised by `T227`, local fire `20260822-140002`, which could not write it — `patterns.md` was outside its
`files_hint` (`FU-T227-1`). Written by `T232` in the same fire, which re-measured every figure below at
`90c21d6` rather than transcribing T227's, and found one mechanism T227 did not name.**

### The incident

`T224` was dispatched to do two things: fix one live restatement of DEC-2's retracted *"They are not
checked. No guard for either exists"* claim — handed to it **by line number**, at
`.softhouse/conformance.sh:1115-1116` — and then sweep the repository for the rest. It fixed the named
site, ran nine terms, and closed with:

> *"no fourth or fifth surviving live assertion of the claim exists in this repository outside the two
> fixed here [VERIFIED by the sweep above; scope and method stated so the claim is checkable rather than
> taken on trust]"*
> [VERIFIED: `T224.md:164-167`.]

A survivor was sitting on **line 1 of the guard's own source**, and had been since `A2-18` wrote it:

```go
// Command ledgerguard is the source-level guard that DEC-2 §4.4.1 records as NOT EXISTING.
```

[VERIFIED: `git show 90c21d6:.softhouse/guards/ledgerguard/main.go | sed -n 1p` — i.e. present in T224's
**own** tree, at T224's **own** fork point. This is not a P-71 worktree artefact.]

### The measurement — recall on a known positive, both directions

T232 re-ran T224's nine stated terms at `90c21d6` against two targets. For the two `\b` terms it used
**PCRE (`git grep -P`)**, the reading most generous to T224.

| target | of T224's 9 terms, how many hit |
|---|---|
| `ledgerguard/main.go:1` — the survivor it missed | **0 of 9** |
| `conformance.sh:1115-1116` — **the site T224 had just fixed** | **0 of 9** |

The second row is the finding. **T224's sweep had zero recall on the one positive it already held.** The
hit it fixed was handed to it by the brief; the instrument could never have found it. It then reported the
population closed. A search whose measured recall on the instance in your hand is zero licenses nothing
about the instances that are not.

The terms were not *silent* — they were **loud about the wrong lines**. T1 (`not checked`) returned two
hits inside `main.go` itself, at `:476` and `:816`, both about an unrelated parse failure; T3 and T8
returned four lines of `conformance.sh`, at `:731`, `:1348`, `:1778`, `:1780`. So `main.go` **entered
T224's population and was triaged out whole**. Controls that do hit: bare `not existing` finds `main.go:1`
and `conformance.sh:1116`; an unanchored forward-proximity net finds `main.go:1` and `:8`.
[All VERIFIED by T232 at `90c21d6`.]

### Two mechanisms, both one character wide

**Mechanism 1 — a word-boundary anchor on an INFLECTED STEM.** T224's widest net was `\bnot exist\b` and
its proximity net anchored `\bexist\b`. A trailing `\b` demands a non-word character after `exist`; in
`NOT EXISTING` the next character is `I`. So `existing`, `exists`, `existed`, `existence` were outside the
net **by construction** — and the claim's most natural nominalised spelling is exactly *"records as not
exist**ing**"*. Dropping the single trailing `\b` converts both misses into hits. Repo-wide cost at
`90c21d6` under PCRE: `\bnot exist\b` → **172 files**, `\bnot exist` → **178**. English states absence
with a gerund at least as often as with a finite verb. **Anchor the LEFT of a stem if you must; never the
right.**

**Mechanism 2 — `git grep -E` does not implement `\b` at all, and says nothing.** T227 did not name this;
T232 measured it. On this platform `git grep -E` treats `\b` as the **literal character `b`**:

```
git grep -c -E  'balance column'  90c21d6 -- …/main.go   ->  14
git grep -c -E '\balance column'  90c21d6 -- …/main.go   ->  14      <- IDENTICAL: \b == literal b
git grep -c -P '\balance column'  90c21d6 -- …/main.go   ->   0      <- real word boundary, correctly misses
git grep -c -E  'Command'         90c21d6 -- …/main.go   ->   1
git grep -c -E '\bCommand'        90c21d6 -- …/main.go   ->   0      <- 'bCommand' matches nothing
```

So under `git grep -E`, T224's **widest net** `\bnot exist\b` compiles to a search for the literal string
`bnot existb`, and at `90c21d6` it matches **0 files in the entire repository** — against **172** for the
same pattern under `-P` and **178** for the unanchored form. **Exit 1, no error, no warning.** The term
that reads as the broadest in the list is the only one that could never match anything.
[VERIFIED: T232, `git version 2.50.1 (Apple Git-155)`, darwin/arm64. **`[UNVERIFIED]` on GNU/Linux**, where
glibc's `regcomp` supports `\b` as an extension and `git grep -E` may well behave differently — which is
itself the point: **a regex metacharacter is a claim about an ENGINE (P-33)**, and this one changes meaning
between `git grep -E`, `git grep -P`, and the `grep` on `PATH` — which on this machine is not GNU grep at
all but **`ugrep 7.5.0`**, and *does* honour `\b` in ERE.]

### Why it is worse than a typo

A typo produces a hit list that looks wrong. This produces a hit list that looks **thorough**. T224 did
everything the process asks for: it widened its terms (it added five, citing **P-26** — sweep the concept,
not the sentence), it stated its population (~150 files), it declared what it had not opened (**P-40**),
and it scoped its conclusion in writing. Every visible signal of rigour was present. The one unperformed
step was the only one that measures anything: **point the instrument at something you already know is
there.** Widening a list of surface strings does not convert it into a search for a claim — and a handoff
that presents the widening as if it had is how a zero-recall sweep acquires the authority to close a
population.

### The rule

> **Before a sweep may support the sentence "the population is closed", it must be run against at least
> one instance of the target that is already KNOWN to exist — normally the very hit the task was
> dispatched to fix — and that run must be SHOWN to hit. A sweep that cannot find the defect already in
> your hand has unknown, possibly zero, recall, and its silence about the rest of the tree is not
> evidence.**

Three corollaries, each independently load-bearing in this incident:

1. **Calibrate on a known positive, and publish the calibration.** This is the procedure **P-66/P-70** were
   missing. P-66 says *state your scope*; **P-72 says test whether your scope is real.** A stated scope and
   a working instrument are different claims, and T224 supplied the first while failing the second.
2. **Commit the COMMANDS, not a description of them.** T224's handoff records its nine terms as **prose**
   (`T224.md:78-90`: *"8. Added: `\bnot exist\b` without `does`/`did` … 9. Added: a combined-proximity
   search for `guard`/`invariant`/`ledger`/`I-3`/`I-4` near `exist`/`checked`…"*) and **not one executable
   command** — no engine, no flags, no direction for the proximity net. So the sweep is **unreproducible**:
   T227 could only transcribe what the prose describes and had to mark T224's literal commands
   `[UNVERIFIED]`, and T232 had to *choose* an engine to re-measure under — the choice that turned out to
   decide whether the widest term matched 172 files or zero. **A sweep whose commands were not committed
   cannot be audited, only believed.** `A2-31` did this right: its `probe-sweep.sh` and its captured
   `sweep-output.txt` are both in the tree, which is why its nets are checkable and its unanchored
   `records as not existing` demonstrably hit.
3. **Never right-anchor an inflected stem, and triage per LINE, not per FILE.** `main.go` was *inside*
   T224's population — surfaced by an unrelated `not checked` at `:816` — and was dismissed as a file. The
   per-file question ("is this file about the claim?") answered *no*; the per-line question at `:1`, never
   asked, answers *yes*.

### The floor no regex reaches

T227 found a **second** live copy of the same claim **one paragraph over**, at `ledgerguard/main.go:13`:

> *"and §4.4.1 lists, item by item, what nothing in the repository looks for:"*

That is the identical retracted claim, in the present tense, ten lines below line 1. It was named by
nobody, flagged by no term in any sweep in this chain, and found **only because T227 was reading the whole
file it had been sent to fix one line of**. It contains **no inflection of "exist" whatsoever**
[VERIFIED: T232 — `sed -n 13p` at `90c21d6` piped to `grep -c -i exist` → **0**]. Widening the pattern by
one character rescues line 1 and does nothing for line 13. **A concept has a floor that pattern-widening
cannot reach**, and below that floor the only instrument is reading. Corollary for triage: when a file is
already open because one line in it is wrong, read the file.

### The open tail — do not read this pattern as closed

**`FU-T227-2` is open.** Every sweep in this chain — T224's, A2-31's, T227's own, and T232's
re-measurement above — is **line-oriented**. T224's own site is the proof that this matters: the claim
straddles a line break (`§4.4.1 records` on `:1115` / `# as not existing` on `:1116`), and T232 measured
that `:1115` contains no inflection of `exist` and `:1116` contains no `guard`
[VERIFIED at `90c21d6`], so **even the corrected, unanchored forward-proximity net misses it** — only the
mirror direction happens to hit. A multi-line matcher (`perl -0777`, or `git grep` with context joined
before matching) **has never been run against this claim.** The single-character fix in Mechanism 1
narrows the gap; it does not close it. Anyone citing P-72 as evidence that the retracted-claim population
is now clean is committing **P-70** with a better instrument.

### Related

**P-66 / P-70** — "not found" is a statement about the search; P-72 supplies the missing procedure.
**P-40** — count and state what you skipped; T224 did this and it was still not enough, because a declared
skip is honest about *coverage* and silent about *recall*. **P-67 / P-69** — measure both terms, in the
live artefact, at the moment of use; here the unmeasured term was the instrument itself. **P-26** — sweep
the concept, not the sentence; P-72 is what stops "I widened my terms" from being self-certifying.
**P-22 / P-36** — a control that cannot fire is worse than none, because it is believed; a right-anchored
`\b` on an inflected stem, and a `\b` the engine does not implement, are both exactly that.
**P-33** — a tool claim names the binary, the version and the invocation: `-E` and `-P` are different
languages, and `grep` on `PATH` may be neither.


## P-73 — a fact this program HAS measured, filed where the reader who needs it will not look

**Diagnosed by `T234` and given its number here by the driver, local fire `20260822-060013`.** The number
`P-73` was a **hole**: `T234`'s handoff cited *"P-72/P-73 should cross-reference P-53"* at
`.softhouse/capture/t234-sweep-instrument-audit/HANDOFF.md:411`, and `P-73` **existed nowhere in the repo** —
verified by `git grep -n "P-73" -- .` over the whole tree, which returned exactly that one reference and no
heading. `P-72` and `P-74` both exist. So the file carried a live pointer into empty space, which is itself a
small instance of what this pattern is about.

**The shape.** The program measures something, writes it down correctly, and then **re-discovers it later at
full cost** — because the place it was written is not the place the next reader looks. The knowledge was never
missing. Only the **route to it** was.

**Instance 1 — `T234`, on `P-53`.** The `\b`-under-ERE defect was **measured and written down twice before
`T232` re-discovered it**: `patterns.md` `P-53` states it **verbatim**, and `P-12` records a second
measurement. `T232` spent a task rediscovering a defect that had been in force, and documented, for two runs.
`T234`'s verdict, which is the one that matters: **a filing failure, not a knowledge gap.**

**Instance 2 — the driver, on `.softhouse/reference-oracle.md` (D-3, this fire).** The pin file that says of
itself *"every vector capture must cite this file's pin"* named `fineract_tenants` and `fineract_default` as
the databases and **omitted `fineract_gerege`**, the tenant database the six ledger parity vectors were
captured from. Meanwhile the tenant distinction that makes the omission dangerous — tenant 1 `default` is
**`Asia/Kolkata` (+05:30)**, tenant 2 `gerege` is **`Asia/Ulaanbaatar` (+08)**, and CLAUDE.md permits neither
Kolkata nor a hard-coded offset — is recorded across **66 tracked files** of capture evidence. The program
knew. The pin file did not say. Evidence: `.softhouse/capture/driver-20260822-060013/`.

**Why it is worth its own number rather than being folded into P-26 or P-70.** `P-70` is about stating a
*search result* as a *world fact*; `P-26` is about sweeping the concept rather than the sentence. Both are
about the **search**. This one is about the **destination**: the search was never run because the reader had
no reason to think there was anything to find. The tell is retrospective and reliable — *someone spent a task
establishing something this repo already stated, and both statements are correct.* When that happens, the
remedy is **never** to write it down a third time. It is to make the place the reader **will** look point at
the place it is already written.

**Duty.** When you record a fact that a future task would be harmed by not knowing, ask **where that task
will be standing when it needs this**, and put a pointer there — not only where the fact was discovered. And
when you find a stale or incomplete entry in a file *whose stated purpose is to be cited*, treat it as this
pattern and not as a typo: the citation makes the omission load-bearing.

**Related.** `P-53`, `P-12` (the measurements that were filed and lost). `P-69` — a measured claim has a
shelf life; this is what happens when the claim does not even reach its reader. `P-66`/`P-70` — where you
looked. `P-72` — calibrate the instrument.


## P-74 — an unescaped backtick in a `git commit -m "..."` message EXECUTES; it has now silently deleted a word and silently amended a commit

**Caught by `A2-34` (F-A2-34-1, HIGH) and independently by `T228`, local fire `20260822-060013`, both against the driver.**

This project's commit messages are full of prose like ``a `user` gate`` and ``the driver ran `git commit --amend` ``. Written inside a **double-quoted** shell string, a backtick pair is **command substitution**. The shell runs it. Twice in one fire:

1. `git commit -m "... a `user` gate."` -> the shell tried to run `user`, printed `command not found: user`, substituted **empty string**, and committed the sentence as *"a  gate."* The word vanished from the permanent record. Noticed only because the driver happened to grep its own message afterwards.
2. `git commit -m "... the driver ran `git commit --amend` on the merge commit ..."` -> **the shell EXECUTED `git commit --amend`.** That amended the just-created merge commit, minting a new sha and folding in whatever was staged, and the driver's actual `git commit` then reported *"nothing to commit, working tree clean"*. The registrations landed inside a merge commit whose message does not mention them.

**And the second one happened inside the sentence describing the first.** The message being written was an explanation of how amending a commit orphans a circulated sha — and writing it orphaned a circulated sha.

**The damage is the orphaned sha, not the message.** `git commit --amend` **mints a new commit object**. In this fire that produced two pairs of commits with **byte-identical trees and identical parents**, 15 seconds apart, one of each pair unreachable from `main`:

```
d1f74ae  merge A2-15   tree 90514b2f...   NOT on main   <- circulated in 2 worker prompts,
d76594a  merge A2-15   tree 90514b2f...   on main          tasks.json, program.json, a commit msg
32c80d6  merge A2-34   tree ...           NOT on main
7fdcc9e  merge A2-34   tree ...           on main
```

No measurement was invalidated — the trees are identical — but **every recorded reference pointed at an object no ref reaches**, and the driver had already handed one of them to two live workers as a BAR anchor. `A2-34` caught it by running `git merge-base --is-ancestor d1f74ae main` instead of trusting the number it was given.

**The duties:**
1. **Never use `git commit -m` for a message containing a backtick.** Write the message to a file with a quoted heredoc (`<<'EOF'`, quoted so the shell expands nothing) and use `git commit -F`. This applies to `git merge -m` too.
2. **Do not amend a commit whose sha you have already circulated.** Add a follow-up commit instead. A sha in a worker prompt, a task note or `program.json` is a published reference.
3. **Verify a sha is reachable before recording it**: `git merge-base --is-ancestor <sha> main`. Existing and being on the branch are different questions — `git cat-file -e` answers the wrong one.
4. **`main` is not quiescent during a wave** (`T228`): it moved under a worker between its `git log main` and its `git merge main`. **Report the sha you MERGED, never the one you LOOKED AT.**

Related: **P-71** (fork points, measured not asserted), **P-69** (a measured claim has a short shelf life), **P-66/P-70** (state where you looked).


## P-75 — `grep` and `rg` IN AN AGENT SHELL ARE NOT THE PROGRAMS YOU THINK, AND THEY DO NOT SURVIVE INTO A SCRIPT

**Found by `T242` (its finding 1) and sharpened by `T244`, local fire `20260822-060013`; every measurement
below re-derived by the driver, which had circulated the wrong version to four workers earlier in the same
fire.** This is the root cause sitting *under* `P-53`, `P-72` and the fail-open class, and it went unnamed
for the whole program.

### The mechanism

`~/.claude/shell-snapshots/snapshot-*.sh` defines `grep` and `rg` as **shell functions** that shadow the
binaries. The `grep` function execs a bundled **ugrep 7.5.0** with these flags **silently prepended**:

```
-G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg
   --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl
```

Read directly out of the snapshot file by the driver. `T242` reported the first four flags; **there are six
more.**

### Consequence 1 — `--ignore-files` is a SILENT RECALL HOLE in every bare-`grep` sweep

Measured on a purpose-built fixture (`git init`; three files each containing the needle; two of them named
in `.gitignore`, one of those also dot-prefixed):

| invocation | found | of |
|---|---|---|
| bare `grep -rn NEEDLE .` (= the shadowing function) | **1** | 3 |
| `/usr/bin/grep -rn NEEDLE .` (the real BSD grep) | **3** | 3 |
| `rg -n NEEDLE .` | 1 | 3 |
| `rg -n --no-ignore NEEDLE .` | 2 | 3 — *still* misses the dot-prefixed file |

**33 % recall, exit 0, hits printed.** Nothing in the transcript says anything was skipped. This is the
fail-open shape *at the engine level*: the instrument reports success while silently narrowing its own
population. Every "I swept the repo and found N" in this program that used bare `grep` has an **unstated
population** — and `P-67` says count both terms and say where you counted.

### Consequence 2 — `rg` DOES NOT EXIST IN A SCRIPT, and the failure is fail-OPEN

`rg` is a shell function, not a binary: **no `rg` in any of the 13 `PATH` directories.** So it works at an
agent prompt and vanishes the moment a sweep is committed as a `.sh` file. Driver-measured:

```
#!/bin/sh
rg NEEDLE file            ->  rg: command not found   ; exit 127   (fail-closed, catchable)
rg NEEDLE file | head -1  ->  rg: command not found   ; exit 0     <-- FAIL-OPEN
#!/bin/bash + set -euo pipefail
rg NEEDLE file | head -1  ->  rg: command not found   ; exit 127   (fail-closed)
```

**The pipeline swallows the 127.** And `pattern | head`, `pattern | wc -l`, `pattern | sort` *is* the shape
of nearly every sweep script. Without `pipefail` a committed `rg` sweep prints nothing, exits 0, and reads
exactly like *"I searched and the concept is absent"* — the same reading as the dead-`cd` class (`T238`),
reached by a different route. **`T244`'s own sweep was killed by this and saved only by its fail-closed
calibration**, which is `P-72` paying for itself inside the fire that reinforced it.

### Consequence 3 — it reconciles two contradictory "measurements" that were both right

`T239` measured *"ugrep is not installed"* — **true**, no binary of that name. `RESUME.md` claimed *"ugrep
honours `\b`"* — **also true**, because ugrep is what `grep` runs. The driver merged the first as a
correction against the second. **Both were right and neither was complete**, and the thing that dissolves
the contradiction is that the NAME and the PROGRAM had come apart. `P-33` already demanded that a tool claim
name the binary and the version; this is why.

### The duty

1. **In any committed instrument, invoke an ABSOLUTE PATH** — `/usr/bin/grep`, or `git grep` (a real
   subcommand, always present), or `python3 -c` with `re`. **Never bare `grep`, never `rg`.**
2. **State the binary AND how you resolved it.** `type grep` before you trust `grep`. *"BSD grep"* is a
   claim about a path, not about a word — the driver made exactly this mislabel in its own `FINDINGS.md`
   this fire and had to correct it.
3. **`set -euo pipefail` in every sweep script.** It is what converts this class from fail-open to
   fail-closed, and it is free.
4. **Calibrate on a known positive AND a known negative** (`P-72`, as amended under `P-53`), and — because
   `--ignore-files` narrows silently — **put one of your known positives inside an ignored or hidden file.**

**Related.** `P-53` (engine divergence; amended this fire for fabrication). `P-33` (name the binary).
`P-72` (calibrate). `P-73` (this was knowable from the snapshot file the whole time). `T238`'s dead-`cd`
class — same fail-open shape, different cause. `P-57`/`T192` — the pipefail sites that already exist are
what would have caught consequence 2.



## P-76 — A GUARD DRIVEN RED ONLY ON THE SHAPE IT WAS BUILT FROM PROVES THE WIRING, NOT THE COVERAGE

**Caught by the driver, local fire `20260822-060013`, against `T243` — by driving `T243`'s freshly wired
guard rather than reading its transcripts.** Evidence:
`.softhouse/capture/driver-20260822-060013/T243-REDDRIVE-GAP.md`.

**This is a NEW shape, and it is not P-45.** Every prior P-45 instance in this program is a guard that
**ran nowhere** — built, never invoked, failing only when called by hand. This one **runs, is reached on
the automatic path, and passes its own red drive** — and still cannot see the case that motivated it.

### What happened

`T243` wired `T238`'s fail-open linter into `conformance.sh` and reported **RED 13/0**. True. The driver
planted a fail-open instrument anyway (P-22) and **the harness stayed green**. Calibrating the probe
(P-72; and T239's *"not found is a statement about the search"*) got the linter to **name the file** — and
`conformance.sh` **still exited 0**, because the plant classified below the pinned frontier.

Two shapes, both fail-open, only one covered:

```sh
# COVERED — the reassuring echo is an ARM of the failing construct
( cd "$WT" && git grep ... ) || echo "   (no hits)"

# NOT COVERED — the echo is UNCONDITIONAL, on the next line
cd /tmp/T138-merge 2>/dev/null && git grep ... 
echo "   (searched the MERGED tree)"
```

Both exit 0 having searched nothing. **The uncovered one is `r11-hygiene.sh:77-79` — the site `T239`
measured live in that same fire, and the site the driver relayed to `T238` mid-flight as the second
confirmed instance of the class.** It is flagged **zero** times. Of two known live sites, the classifier's
boundary splits them one and one.

### Why the author could not have caught it

`T243` planted the covered shape — **because that is the shape the rule was written from.** A red drive
built from the same example as the rule is a **tautology with a transcript**: it exercises the path the
author already had in mind, and its passing tells you the wiring is connected and nothing about what the
rule can see. The transcript is honest; the inference from it is too strong.

### The duty

1. **Drive every guard red on at least one shape you did NOT design the rule around**, and say which one.
2. **State what you would accept as a falsification** before you run it.
3. **When a task was widened because of a specific site, that site is a MANDATORY red-drive case.** Here
   the whole reason `T238`'s brief was widened was `r11-hygiene.sh`, and it is the case the delivered
   guard misses.
4. **Distinguish the two claims in writing**: *"the guard is wired and reached"* and *"the guard covers
   the class"*. `T243` proved the first. Only the second closes anything, and only a census of the class
   against the rule can establish it.

**Related.** `P-45` (a guard invoked nowhere) — this is its harder sibling: invoked everywhere, blind in
part. `P-22` (drive it red) — satisfied in letter, not in substance. `P-35` (a check that inspected zero
items is not a pass) — here it inspected 892 files and still saw nothing. `P-72` (calibrate the
instrument) — the driver's first probe failed and calibrating it was what turned a wrong conclusion into
a finding.

## P-77 — A GATE'S SCOPE IS A PROPERTY OF THAT GATE. A TOOL THAT HARDCODES ONE SCOPE FOR A WHOLE GATE **CLASS** IS ASSERTING, NOT READING

**Found and fixed by the driver against its own instrument, local fire `20260822-140002`. Independent
re-derivation filed as `T249` — this entry is NOT yet reviewed.**

`.softhouse/bin/ready-tasks.py` printed, under every open **CONTRACT** gate:

> `=> no task may write Go under nexus/ or store a CONTRACT-SHAPED vector for this context until it closes.`

That sentence was **hardcoded at `:125` as of commit `9b6c596^`** — stamped, because the driver has since rewritten this file and a reader at HEAD will find different code on that line [VERIFIED at `9b6c596^` by the driver and independently by `T249`] — and emitted in a loop over `contract_open`. It read **no per-gate
field**, so it could not have distinguished one CONTRACT gate from another — and it printed with exactly the
authority of a measurement.

It encodes **`G-11`**: DEC-2 **UNRATIFIED**, its *shape* the thing under negotiation, so anything consuming
or shaping the contract genuinely had to wait. Correct there. Then `G-14` opened — a **stale-evidence
correction to an already-RATIFIED document**, moving no obligation, no field, no rounding rule, no graded
cell — and the same sentence printed, now claiming that all Tier-A Go was forbidden.

**Two authorities disagreed and the machine-readable one was wrong.** `gates.md`'s GATE REGISTER — the file
this program calls authoritative — recorded `blocks: NOTHING` for `G-14` from the moment it was raised. The
tool the driver runs first at every STEP 1 said the opposite. **The previous fire noticed the smell and
refused to act on it**, leaving a boxed note asking the next fire to settle it explicitly rather than let a
default quietly park a tier. That refusal is the reason this was caught rather than obeyed.

### Why this is not P-45, and not P-73

- **`P-45`** is a guard invoked **nowhere**. This one is invoked every fire, prints every fire, and is read.
- **`P-73`** is a measured fact filed where its reader will not look. Here the fact was filed *exactly* where
  the reader looks — in the authoritative register — and a **second, louder, wrong copy** shouted over it.
- The nearest relative is **`P-76`**: a rule generalised from the one example it was written against, and
  then applied to a population it was never measured on.

### The rule

1. **Scope belongs to the instance, not the class.** A gate records what it blocks; a tool **reads** that
   field. `CUTOVER`, `CONTRACT`, `ENGINEERING` are classes of *decision*, not of *consequence* — this program
   already has open gates in the same class that block a whole tier and gates that block nothing at all.
2. **When a tool must fall back to a default, it must SAY it is falling back**, name the field it wanted, and
   tell the reader the default is an assumption and not a measurement. The patched resolver prints the
   recorded scope when present, and otherwise prints the conservative text **labelled as an assumption**
   together with an instruction to decide and record the real scope. A silent conservative default is
   indistinguishable from a measured one, and gets obeyed the same way.
3. **Free text that a tool prints as authoritative is an unenforced permission surface.** Nothing checks who
   wrote a gate's `blocks`, whether it was reviewed, or whether it is true — a future worker could widen it
   into a self-issued permission slip. `T249` is asked to propose an enforcement; **it is not enforced today,
   and this entry must not be read as saying it is.**
4. **Drive both arms before you commit an instrument.** Positive (scope present → printed) and a **negative
   control** (scope stripped from a throwaway copy → fallback printed). Per `P-76`, note honestly that **both
   of those arms are shapes the author designed**; `T249` is instructed to drive the ones the author did not
   — empty string, whitespace, non-string types, a scope that does not actually grant permission, and two
   open CONTRACT gates at once, a case that never existed when the code was written.

### The generalisation, which is the part worth carrying

**A tool that answers a question the underlying record already answers is a SECOND SOURCE OF TRUTH.** The
same shape as `G-12`'s stored running balance: a value that looks derived, is actually written, and is
believed because it is convenient. **When a tool and the authoritative record disagree, the tool is the
suspect** — and when a tool never consults the record at all, it is not disagreeing, it is guessing out loud.

> **⚠ P-77 WAS ITSELF FAIL-OPEN WHEN FIRST FILED, AND `T249` CAUGHT IT IN THE SAME FIRE.** The driver's
> patch — the one this entry holds up as the fix — read `str(g.get("blocks", "")).strip()`. The **five most
> likely encodings of "no value"** (`None`, `False`, `0`, `[]`, `{}`) all stringify **truthy** (`"None"`,
> `"False"`, `"0"`, `"[]"`, `"{}"`), suppressed the conservative fallback, and printed under
> **`=> SCOPE RECORDED ON THIS GATE`**. A gate carrying `blocks: null` rendered as *"SCOPE RECORDED … None"*,
> **which reads as "nothing is blocked."** The **pre-patch code was fail-CLOSED; the patch made it
> fail-OPEN** — a fresh `P-45` instance, created **in the very commit that filed this pattern about
> unenforced permission surfaces.** Fixed at `925fdfc`: only a genuine non-empty **string** counts, anything
> else falls back **and is reported as MALFORMED**, because a malformed scope is a defect to surface, not a
> value to silently treat as absent.
>
> `T249` also found the **selector** failed open independently: `g.get("class") == "CONTRACT"` **silently
> drops any gate with no `class` key**, and `G-13` is exactly that shape [VERIFIED at HEAD: `class=None`].
> An unclassified gate that was OPEN would have been invisible to the section that exists to catch it.
>
> **The lesson is sharper than the fix.** Point 4 of this entry told the reader to drive both arms, and the
> driver *did* — and both arms it drove were **strings**. `""` and `"…"` are the two shapes you reach for
> when you are thinking in strings, and neither can reveal a type error. **P-76 says drive a shape you did
> not design the rule around; this adds: drive a shape of a TYPE you did not design the rule around.** The
> author's imagination is the boundary of the author's red drive, which is the whole argument for
> independent review — `T249` existed only because the driver filed it against itself.
>
> **Two of the driver's own verification probes were broken here and each produced a false reading it nearly
> acted on** (`P-72`): grepping `SCOPE RECORDED` also matched the fallback text **`NO SCOPE RECORDED`** as a
> substring, reporting every arm as permissive; and grepping lowercase `` no `class` KEY `` against output
> reading uppercase **`` NO `class` KEY ``** reported a working guard as vacuous. **Both were the probe, not
> the code.** A probe must be calibrated to *discriminate*, not merely to match.

> **P-76 ADDENDUM, proposed by `T248` and adopted by the driver, local fire `20260822-140002`
> (merge `fb9c18b`). `T248` left it as text in its handoff because `patterns.md` was outside its scope —
> correctly; this is the driver landing it.**
>
> **A rule's blind spots live in its POPULATION SELECTOR as much as in its conditions.**
>
> `T248` was sent to widen a guard's *conditions*. Measuring first — as instructed — it found the real
> defect one level up: **`RE_REPOWIDE`, the corpus selector, was itself blind.** Its shape R4,
> `git -C DIR grep … || echo "(no hits)"`, **satisfied BOTH of the linter's conditions and was still never
> inspected**, because the selector never put it in front of them. A condition cannot fire on a file the
> selector never selects, and every red drive aimed at the conditions will pass while the hole stays open.
>
> **So: before you trust your conditions, check your selector.** Ask what the instrument *could not have
> seen*, not only what it decided. This is `P-35` ("a check that inspected zero items is not a pass")
> generalised from *zero* to *the wrong population* — the count is non-zero and reassuring, and the item you
> needed was never a candidate.
>
> Two further measured lessons from the same task, both worth carrying:
>
> - **Characterise before you widen.** `T248` was told to establish C1's real matching rule before touching
>   C2, and it paid: C1 was a **four-root allow-list** (`/Users`, `/home`, `/opt`, `/var`), so `/tmp`,
>   `/nonexistent`, `/srv`, `/data`, `/mnt`, `/private` and `/scratch` were all invisible. **Widening C2
>   alone would have placed `r11-hygiene.sh` on the frontier at TIER 2, whose printed meaning is "corpus
>   reachable today" — a false statement about a directory gone for days.** The fix would have *created* a
>   new false claim while closing a true one. Both halves had to move.
> - **A widening must be proved STRICTLY ADDITIVE**, by running the shipped and the widened instrument over
>   the same tree and showing detections gained with **LOST = none** (here 20 → 22). A widening that
>   silently drops a prior detection is a regression wearing the word "improvement". And a pin that moves
>   must be justified as **NEWLY VISIBLE, not NEWLY INTRODUCED** — `T248` moved the frontier 9 → 10 rows and
>   said which it was.
> - **Negative controls are not optional even for vocabulary.** `T248`'s own reassurance word-list, bare
>   `zero` / `above` / `empty`, matched a **section header** and would have promoted a file to TIER 1 **on
>   non-evidence**. The instrument that catches false reassurance can itself be falsely reassured.

---

## P-78 — A revision whose CONTENT is line citations into a MOVING file must be PREPARED AND LANDED IN ONE FIRE

**Found by:** `T251` (C-1, HIGH), cloud catch-up fire 2026-08-22T12:00Z, re-derived by the driver at `66b7453`.

`T247` prepared **DEC-2 revision 7** to fix `G-14` — a gate raised precisely because DEC-2's banner carried
**stale evidence**. `T247` re-measured all 46 line assertions, shipped a `verify-line-numbers.py`, and
correctly landed nothing. Then `main` moved **four merges** under it, and `T248`'s `c13e9d8` added **+30
lines above `run_guards`**. By the commit where revision 7 would have landed, its freshly *"RE-MEASURED"*
citations were **already stale**: `run_guards` drafted at `1474-1500`, actually `1504-1530`.

**The fix for a stale-evidence gate had itself gone stale before it could land.** That is `G-14` re-enacted
inside the repair of `G-14`.

**The rule.** *Prepare-then-review-then-land* is sound for a **normative** change, whose truth does not
depend on where any line sits. It is **unsound for an EVIDENTIAL one whose propositions ARE coordinates into
a file other tasks are editing.** For those:

- **Re-measure LAST**, immediately before the commit that lands, never at drafting time.
- **Re-run the line verifier on the commit you are about to land** and require **exit 0** — not on your fork
  point, and not on the commit you drafted against.
- **Prepare and land in the SAME fire.** Handing a prepared revision to a later fire hands it a *different
  file*.
- Where the citation can be a **NAME instead of an ordinal or a line number, use the name.** `T251`'s C-2 and
  C-4 are both ordinal defects: `guard_ledger_invariants` is the **seventh invoked** and the **sixth
  tallied**, and rev 7 replaced one silently-wrong ordinal with another. **An ordinal used as an identifier
  goes wrong silently; a name goes wrong loudly.**

**Corollary, and it is the expensive half.** A **two-fire program** — one host that can run the BAR and one
that cannot — cannot split *prepare* from *land* across the two for this class of change. The cloud fire may
**review** such a revision (a review is a claim about a commit, and it stamps that commit); it may not
**prepare** one for a local fire to land.

> **MERGE NOTE — these six patterns were renumbered on landing.** They were written as `P-78`…`P-83` by
> the local fire `20260822-140002`, which did not know a cloud catch-up fire was running over the same repo
> and had already published a different **`P-78`** (above). Renumbered to **`P-79`…`P-84`**; the cloud's
> `P-78` keeps its number. **The collision is itself the subject of `P-85`.**
### Run 2026-08-21-run2-tierA-gl-accounting-A2 — local fire `20260822-140002`, SECOND SESSION (five workers, all five merged)

- **What worked**: five workers dispatched in one batch after proving their `files_hint` **pairwise
  disjoint** — `T252` held `conformance.sh`, `T241` held `gates.md`, `T236` held `capture/tierA-a2/`,
  `A2-23` held the Go conformance package, `T251` held only its own reviews dir. Six other READY tasks
  (`T250`, `T226`, `T235`, `T160`, `T192`, `T195`, `T164`, `T174`, `T145`) were **held back for contention
  and the reason recorded**, not silently skipped. Zero merge conflicts across five merges.

- **What the independent reviewer caught**: `T251` **REJECTED DEC-2 revision 7**, the artefact not the work.
  Two HIGH findings, both re-derived by the driver before acceptance: rev 7 **corrects three stale line
  numbers with three that are already stale** (`run_guards` is `:1504` not `:1474`; `guard_ledger_invariants`
  `:1524` not `:1494` — `T248`'s merge grew `conformance.sh` by 30 lines *after* `T247` measured), and a
  **35th site**, §4.4's own lead paragraph *"none of them can be graded today"*, sitting **nine lines above**
  the bullet rev 7 corrects to *"YES, SINCE A2-15"*. It **confirmed no obligation moved** (H-10's BEFORE
  byte-identical to the live ADR) and **the caution survives with both terms counted** (14 declared, 6
  graded, 8 out by name). **G-14 stays OPEN; nothing was ratified.**

- **Vectors added / contexts at parity**: **none, and none claimed.** The vector-store digest
  `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` was **UNMOVED across all five merges** — verified live at each
  BAR (P-61). No task this fire touched the money corpus.

- **Claims marked UNVERIFIED / carried forward**: `T252`'s C6 **inherits `RE_REPOWIDE` unchanged**, so a
  non-fatal dead `cd` in a file with no `git grep` is still invisible — **recorded as a limit, not
  discovered later as a defect**. `T236` did not re-verify numeric-signal trap coverage (`trap … 2 15 1 3`);
  still zero **by inheritance, not by its own sweep**. `A2-23`'s case-only variant (`LEDGER` vs `ledger`)
  **could not be driven live** on this host's case-insensitive APFS — said so rather than papering over it.

- **Verifier**: driver-run on the **merge result** after every merge, never quoted from a worker —
  probe line PRESENT and `up` · **VERDICT PASS (exit 0)** · loanschedule **46 parity / 7884 graded cells** ·
  LEDGER **4 parity + 2 oracle-refusal / 21 money cells** · refused 0 · inadmissible 0 · harness errors 0 ·
  invariant violations 0 · **0 NOT RUN** · all 9 census pins == pinned · fail-open frontier **11 == pinned
  11** · `go build`/`vet`/`test` green · `gofmt -l` **exactly** `contract.go`.

- **Backlog carried forward**: `T253` (DEC-2 rev 7b + the citation-rot mechanism), `T254` (wire
  `manifest.py verify`), `T255` (the restated frontier cardinal + the unrepaired TIER1B pin), `T256` (the
  verdict field that never consults its own predicate).

#### New knowledge

**P-79 — EVIDENCE NOT MISSING, UNREAD. A recorded predicate that no summary consults.**
`T241` found, and the driver verified directly at `capture/t229-g8-site3/out/classify-t229.json`, that
`T229`'s own capture records `P2_totalInterestEqualsNEplusB: false` on **five** rows — and **three of them
(`B201`, `B251`, `B299`) carry `verdict: "AS PREDICTED"`.** Two others carry `REFUTED`, so the field is not
constant: it computes something, and that something **never consults P2**. The refutation of a *registered
prediction* was **measured, printed and committed on the same day**, and appears in no handoff, gate text or
review. This is not the familiar defect of evidence never gathered. It is **P-45 moved one layer out**: the
guard did not fail to run — it ran, wrote its answer down, and the summary line above it said the opposite.
**When you register a prediction, grep for who READS it, not just who WRITES it.** Carried by `T256`.

**P-80 — A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED. The count is the same defect as the line number.**
`T248` moved the fail-open frontier 9 → 10 and corrected it **where it is NAMED** (`conformance.sh`) but not
**where it is RESTATED**. `T252` found `capture/t243-wiring/instruments/20-failopen-red-drive.sh` still
asserting `frontier == pinned (all 9 rows, by path)` in **two live `want_line` checks** — an instrument that
would now fail on its own control arm. Meanwhile `T251` found `T247`'s revision 7 **replacing three stale
line numbers with three already stale**, whose worst property is that the dead ones **resolve to
plausible-looking `warn` strings**, so a reader following one is **MISLED RATHER THAN STOPPED**. Same defect,
two currencies. **The fix is never the new number — it is to make the second site READ the first** (derive
the count from the pin; bind citations by CONTENT with the line number a non-normative hint). A task that
changes the 9 to an 11 and leaves the copy has bought one cycle. `T253` and `T255` carry the two halves.

**P-81 — THE FAIL-OPEN GUARD CAUGHT THREE WORKERS' OWN INSTRUMENTS IN ONE FIRE, INCLUDING TWO WRITTEN TO ENFORCE THE VERY RULE THEY BROKE.**
`T251`'s `p5-probe.sh` — written to enforce **P-66, "state where you looked"** — wrapped every search in
`|| echo "  (none under nexus/)"` and `|| true`. **`git grep` exits 1 on NO MATCH and >1 on ERROR**, so a bad
pathspec printed the same reassuring absence as a genuine no-match. `T241`'s census script collapsed
`grep -c || echo 0`, putting "zero matches" and "I broke" onto one printed zero. `T252`'s own linter caught
**three of its own instruments**, including five `|| echo "(not printed)"` arms **in the instrument written
to expose that class**. **All repaired, none suppressed** — the linter's `# lint-failopen: ok --` escape
hatch would have silenced the detector while leaving the script able to lie. **Writing the rule does not
immunise you against it; only the guard does.**

**P-82 — A PROPOSED FIX CAN BE MEASURED INERT, AND THAT IS A RESULT WORTH THE TOKENS.**
The driver briefed `T252` that "a count is a claim too" and to consider a numeric-claim detector. `T252`
**built it and measured it**: 14 count shapes into `RE_REASSURE`, **frontier 10 → 10, GAINED 0, LOST 0, the
target site still invisible.** It was **not rejected for noise — it produces none.** It failed for two
*independent* reasons: the print predicate is shell-only while the claim is a python `print(`, and the
association window is 3 code lines while the claim is **110 lines downstream**. **A vocabulary was the wrong
AXIS, not the wrong wordlist** — the close came from `C6`, which reads **control flow** and never words.
**Build the driver's suggestion, measure it, and report the zero.** A worker that had simply implemented the
brief would have shipped a detector that detects nothing and called it a widening.

**P-83 — TWO INDEPENDENT MOVEMENTS OF ONE PINNED NUMBER RECONCILE BY RUNNING, NEVER BY ARITHMETIC.**
`T252` forked at `2871f17` and its `C6` **added** a frontier row; the driver, separately and later,
**repaired `p5-probe.sh` on main and removed one**. Neither could see the other. The merged pin agreed at
**11** — but that was **established by running the BAR on the merge result**, not by computing 10 + 1. The
same run also proved the repaired probe is **not detected even under the new, stricter C6 rule**, which no
arithmetic could have told anyone.

**P-84 — "EXIT 2 WITH NO PROBE LINE" IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE.**
The first BAR after merging `A2-23` exited 2 with **no probe line printed at all**. Under the rule as it
stands that is emphatically **not** an oracle outage — four exit-2 paths precede the probe, and a failed
HARD guard is one of them. The cause was `p5-probe.sh`, merged minutes earlier, moving the frontier 10 → 11.
**This fire is the first time that rule was exercised in anger, and it held**: nothing was parked, the
violation was repaired, and the run went green. Had the driver read `probe != up` as trivially true because
nothing printed, it would have parked live vector work as somebody else's server being down.


**P-85 — TWO ORCHESTRATORS HELD THE LOCK AT ONCE, AND THE CAUSE WAS AN UNPUSHED IN-FLIGHT STATE.**
On 2026-08-22 the local fire `20260822-140002` ran a second session from 06:00:13Z with five live workers,
while the cloud catch-up fire **took the same lock at 12:10:00Z** and dispatched its own. The cloud's
reasoning was **documented and locally sound**: the lock's `started_at` was 6 h 07 m old (over the 6 h
threshold) and **`HEAD` `2871f17` attested that fire `20260822-140002` "closed clean with zero live
workers."** Both facts were true of the repo **as published**. Neither was true of the world.

**The defect was the local driver's, and it is a `STEP 5.5` violation in spirit:** it committed its lock
refresh, its dispatch record and its in-flight `RESUME.md` **and never pushed them**. `5f27983`, `ba2d8ed`
and `d6dd8d0` sat local for the whole fire, so **the only evidence a second orchestrator could read said the
opposite of the truth** — and the staleness rule then fired on a *live* session. Worse, `HEAD` still carried
the previous session's "closed clean" checkpoint, which the cloud correctly read as an attestation.

**What it cost:** the cloud's `T253` and `T241` workers were killed with their sandbox and **their branches
never reached the remote — that WIP is gone, not merely unpushed** [VERIFIED: `git ls-remote --heads origin`
and `git branch --list`, both empty]. Three task IDs (`T253`, `T254`, `T255`) and one pattern number (`P-78`)
were **allocated twice with different content**.

**What it was worth:** the duplicated `T251` produced **two independent reviews of one artefact**, which
**agreed on every load-bearing fact** — no obligation moved, the caution survives with the same denominator,
`run_guards` is `:1504` — and whose site lists were **complementary**: the local pass found §4.4's lead
paragraph and two §5.2 sites; the cloud pass found `L821`'s ordinal and the fenced enumeration at `L854-861`
that lists seven guards and omits `guard_no_fail_open_instruments`. **Neither found the other's.** Accidental
redundancy on a document that had already survived two passes was **not** wasted effort — but that is a
reason to duplicate reviews **deliberately**, never a reason to tolerate a broken lock.

**THE RULE: push the lock, the dispatch record and the in-flight manifest IMMEDIATELY, before the first
worker is spawned.** An orchestrator's in-flight state is worthless to the other fire until it is pushed, and
a `HEAD` that says "closed clean" while a session is live is an **active lie to the next orchestrator**.

---

**P-86 — THE PATTERN IDS THEMSELVES ROTTED, IN THE FILE THAT NAMES THE ROT.**
*Local fire `20260822-060013`. This is `P-80` applied to `P-80`.*

`RESUME.md`'s STANDING INSTRUCTIONS block cited **`P-78`…`P-83`** with the meanings that belong to
**`P-79`…`P-84`** — off by one across six patterns. The cause is recorded fifteen lines above them in this
very file: the merge note at `patterns.md:2691` says those six *"were renumbered on landing"* because a cloud
fire had already published a different `P-78`. **The renumbering was applied to `patterns.md` and never to
`RESUME.md`'s restatement of it** — the corrected cardinal rotted in the place it was restated, which is
`P-80` verbatim, committed inside the manifest that teaches `P-80`.

**The driver then propagated it into all ten worker prompts of the next fire**, so this fire's handoffs and
commit messages cite shifted ids: what they call `P-83` (*read the probe line's presence, not its value*) is
**`P-84`**; what they call `P-80` (*`git grep` exits 1 on no-match but >1 on error*) is part of **`P-81`**;
`P-79` → **`P-80`**, `P-78` → **`P-79`**, `P-81` → **`P-82`**, `P-82` → **`P-83`**.

**Materiality is LOW, and the reason is the useful half.** **Not one worker was misdirected**, because every
prompt wrote out the **full rule text** beside the id rather than the id alone. The number was decoration; the
sentence carried the instruction. Had the prompts said *"apply P-83"* and stopped, ten agents would have
applied the wrong rule and the fire's evidence would be unsound.

**THE RULE, and it is `P-80`'s own corollary turned on this file: an ID IS A CARDINAL. Never restate a
pattern id in a second document — make the second site NAME THE RULE, or cite the id AND its sentence
together so a shifted number is self-correcting.** An id used as an identifier goes wrong silently, exactly
as `C-4` established for ordinals in `DEC-2`. **Prefer the name over the number** — the same conclusion,
reached independently, one layer out.

---

**P-87 — A DELIBERATE COLLISION IS A TEST INSTRUMENT. SCHEDULE THE THING THAT WILL BREAK YOUR FIX, IN THE SAME FIRE.**
*Local fire `20260822-060013`.*

The driver dispatched `T253` (which edits `conformance.sh`) and `T255` (whose DEC-2 citations are **line
numbers into `conformance.sh`**) into the **same fire, on purpose**, and told `T255` so in its brief. Three
consecutive passes had shipped stale line numbers, each claiming to have re-measured; the failure mode was
invisible because nothing moved the file between measuring and landing.

**The collision converted an assertion into a measurement.** `T255` did not merely reason that anchors resist
rot — it ran `conformance.sh` **straight out of the rival `T253` branch** and measured: **anchors exit 0,
line numbers 4 of 4 MOVED, including `:1300`, the definition row that had survived every prior pass.**
`T260` then reproduced it under **both** `T253` implementations and found something neither author had: at
the **untouched merge-base**, the line-number checker is already **3 of 4 MOVED** — *a wired line-number gate
would have been RED on `main` before `T253` touched anything.*

**THE RULE: when a fix claims robustness against change, schedule the change that would break it INTO THE
SAME FIRE, and tell the worker it is coming.** Robustness proved against a hypothetical is a claim;
robustness proved against a live concurrent diff is a measurement. The corollary is a merge-order fact:
`T254b` quantified that landing the rival diff first would have rotted **10 citations / 5 ranges / 17 line
numbers — 100%** — so the collision also *decided the merge order*, which no amount of reading could have.

---

**P-88 — THE GREEN BAR DEPENDED ON A 24-BYTE FILE IN `/tmp`, AND FOUR INDEPENDENT PARTIES FOUND IT BEFORE THE DRIVER RAN IT.**
*Local fire `20260822-060013`.*

`rm -f /tmp/t234_matrix2.txt` → `bash .softhouse/conformance.sh` → **EXIT 2, probe-line count 0, "a HARD guard
failed."** Restore the file → **PASS, `probe = up`, frontier 11 == pinned 11.** The file is created by
**line 7 of the very instrument whose fail-open TIER depends on it**, so the harness is green **if and only
if that instrument has already been run on this host**.

Three consequences, in rising order of seriousness. **macOS clears `/tmp` on reboot**, so the first fire after
a restart gets the program's most dangerous signal. **Every green bar recorded on this Mac was contingent on
that residue** — the bar was not reproducible from a clean checkout on a clean host, and the bar is the
instrument that grades everything else. And **the classification was decided by state no reviewer can see and
no commit records**: a fail-open TIER that reads host filesystem residue is itself a fail-open.

**`P-84` earned its keep the same hour.** The driver read the **ABSENCE** of the probe line rather than its
value, and parked nothing. Under the rule as it stood two fires ago, this would have parked every live vector
task as *somebody else's server being down*.

**It also settled an author dispute in the loser's favour.** The Mac author called the effect *"a
classification defect, not a frontier defect"* because the frontier COUNT and PATH-SET are identical and the
harness pins **by path**. `T254b` measured that **the pin also carries the TIER token**, so a TIER2→TIER1 flip
fails it anyway. **The cloud author's refusal to move the pin to make its own bar green is vindicated: it had
an invisible route to green and did not take it.**

**THE RULE: an instrument's verdict must depend on nothing outside the repo.** `/tmp`, `$HOME`, an env var, a
previously-run sibling — each makes the verdict unreproducible and uninspectable. And **when a guard's tier
can be flipped by host state, the guard is not measuring the property; it is measuring the host.**

---

**P-89 — THREE ARTEFACTS SHIPPED WIRED TO NOTHING IN ONE FIRE, AND ALL THREE SAID SO UNPROMPTED. THE FIX IS A FILED TASK, NOT A SENTENCE.**
*Local fire `20260822-060013`.*

`T164`'s AST float guard, `T259`'s R-VPA rule and `T250`'s derived attestation were each **wired to nothing**
on landing — the sixth, seventh and eighth recorded instances of `P-45` in this program, each inside an
artefact **written to remove `P-45`**. The cause was the scope guard working correctly: `conformance.sh` was
held by `T253` and none of the three would cross it.

**All three declared it themselves, without being asked**, and labelled it backlog rather than completion.
That is the behaviour to keep. But **three independent reviewers converged on the same condition**, and
`T262` phrased it best by turning `T259`'s own argument back on it: **"PROSE DOES NOT FIRE ON THE NEXT
FIRE."** A limit written into a handoff, a review, or a `## Backlog` heading is invisible to the scheduler.

**THE RULE: an unwired guard MAY merge — holding it is often worse, since `T164`'s alternative was leaving
the BLIND grep as the only guard on disk — but ONLY against a FILED, DISPATCHABLE TASK with an owner, a
dependency edge, and a red-drive requirement.** The driver filed `T268`…`T274` **before** merging the
branches, not after. **A declared orphan is acceptable; a silent one is not** — and `T261` sharpened it
further: an orphan **may not acquire a caller** until the fail-opens in it are repaired, because wiring a
liar is strictly worse than leaving it unwired.

---

**P-90 — THE REVIEWER MEASURED THE AUTHOR'S DENOMINATOR AND FOUND THE PROOF COVERED ONE FIFTH OF THE DOCUMENT.**
*Local fire `20260822-060013`, `T260` over `T255`.*

`T255` proved *no obligation moved* by byte-identity over a list of sections it **chose**. `T260` did not
re-run that proof — it **measured the proof's own coverage**: **18.2% of lines / 20.1% of characters.** Four
fifths of a ratified contract rested on a modal-sentence diff **structurally blind to obligations phrased
without a modal verb**, and `T255` had itself flagged that blindness without measuring its extent.

`T260` then closed the gap by a route the author had not used: an **exhaustive table-cell census** — **140
rows before, 140 after, 0 removed, 0 added, exactly 4 changed, last cell only** — plus a section-identity map
**derived from headings rather than chosen**, a 219-sentence non-modal predicate against the author's 87
modal lines with **all 14 losses adjudicated by hand**, and an applier re-derivation reproducing the landed
blob **byte-for-byte**. The verdict survived. **The proof did not.**

**THE RULE: when an author proves a negative over a population, the reviewer's first question is not "is the
proof sound?" but "WHAT FRACTION OF THE WORLD DOES THIS POPULATION COVER?"** A sound proof over a chosen
fifth is a sound proof about a fifth. This is `P-67` (count both terms) raised to apply to **the evidence
itself**, not just to the claim — and it is how a `RATIFY` verdict is earned rather than granted.

---

**P-91 — FIVE FIXES FOR A FAIL-OPEN, AND EVERY ONE LOST TO THE SAME EVASION RE-NESTED ONE LEVEL OUT.**
*Local fire `20260823-080004`, the R-VPA lineage: `T259` → `T268` → `T281` → `T286` → `T291`.*

`T259` shipped a rule that printed `REFUSED NIL COVERAGE` in its body and **exited GREEN**. `T268` repaired
it and introduced a **second** fail-open. `T281` rejected that. `T286` repaired *that*, and found a **third
inside the repair in flight for the second** plus a **fourth** nobody had looked for (`--help` raises
`SystemExit(0)` → exit **0 with no probe line**, the one code a caller reads as *"measured, green"*).

**`T286` did the sophisticated thing and it was still not enough.** It rejected the obvious phrasing — *"the
root doesn't count"* — **precisely because** it had measured that phrasing losing to a one-line evasion, and
chose a structural one instead: **"a record is a row reached through a list."** `T291` then defeated the
replacement with **two characters**, by wrapping the fixture header in `[ ]`:

```
H1  {"meta": {"verdict":"AS PREDICTED"},                "cells":[]}   PRE=1  NEW=1
X2  {"meta": {"summary": [{"verdict":"AS PREDICTED"}]}, "cells":[]}   PRE=1  NEW=0
```

Exit **0 GREEN**, `predicates=0`, where the **pre-`T268`** rule exits **1 REFUSED** — a **lost refusal**, the
exact criterion `T281` had used to reject `T268`. Also at depth 2 and 4, as a list-of-lists, and as a
**top-level JSON array** — the shape this program's own `t286-legs.json` and `red-green-legs.json` use.
`T291` reproduced it **inside `T286`'s own sweep, unmodified**: *42 fixtures, 4 lost refusals, FAIL.*

**THE RULE: a guard phrased as a STRUCTURAL PATTERN over the shape of its input can always be re-nested one
level out, so enumerating shapes that COUNT and refusing the unmatched is a losing method no matter how
carefully each shape is chosen.** Five competent, RED/GREEN-driven repairs by five different workers all lost
the same way. The escape is not a better pattern: it is **inverting the burden** — require the document to
POSITIVELY DEMONSTRATE coverage in a form the rule *constructs* rather than *recognises*, so that anything
the rule does not understand **refuses** instead of passing. Fail-closed **by construction**, not by
enumeration. Filed as `T292`, which is told in terms that a sixth shape-patch is the predicted output and
will be rejected, and that **a measured impossibility argument is a better result than a sixth patch.**

**Corollary, and it bit here:** `T286` offered *"battery 32 passed, 0 failed, **0 SKIPPED**"* as proof.
`T291` measured that **the battery returns exit 0 with legs SKIPPED** (23/0/9 → 0). The rig could skip and
still pass, so the `0 SKIPPED` was an observation, never a guarantee. **A test rig is inside the trust
boundary of the thing it grades; check that it cannot pass vacuously before quoting its counts.**

---

**P-92 — THE PROBE THAT WOULD HAVE FIRED WAS ARMED, AND ITS AUTHOR'S OWN COMMENT SAID IT WAS SAFE.**
*Local fire `20260823-080004`, `T289` over `T287`.*

`T287` captured two oracle refusals honestly and well: it re-derived its citation before sending anything,
**refuted the driver's premise** that a `GLClosure` is irreversible (`GLClosure.java:50` carries `is_deleted`
but **no `@SQLDelete`**, so `repository.delete()` is a genuine hard delete), placed its closure before the
earliest existing entry so the plan was safe **even if the delete had failed**, reversed the mutation, and
disclosed the residue it could not reverse. The driver verified all four load-bearing numbers first-hand and
they were all true.

**`T289` checked the claims `T287` did not make.** Every probe body was a **valid, balanced, postable manual
journal entry**. The only thing refusing them was **a precondition in the oracle** — and when a precondition
lapses, the request does not go quiet, **it becomes a write**, and a posted journal entry cannot be deleted.
`T287` had **deleted the closure** that refused two of them; a third armed **the next day**. All four carried
the comment **`"Expected REFUSED, writes nothing"`** — an assertion its own author had made false — and
`T287` §7.5 told the promotion task that **"re-taking arm 2 is cheap now, the recipe is committed and
re-runnable."**

**THE RULE: a probe whose safety comes from an EXTERNAL PRECONDITION rather than from its own content is a
loaded weapon, and the danger is highest immediately after the capture SUCCEEDS — because taking the
observation is often what removes the precondition.** A refusal capture must carry a **fail-closed fence that
re-checks the precondition at fire time**, never a comment asserting the refusal, because **the comment is
written when the precondition holds and is not re-read when it stops holding.** This is `P-89` ("prose does
not fire on the next fire") applied to a *safety* claim rather than a coverage claim, and the consequence is
worse: prose that does not fire leaves a gap, but prose that says *"writes nothing"* invites the write.

---

**P-93 — THE GUARD LANDED AND THE VERY SAME FIRE'S OTHER BRANCH TRIPPED IT.**
*Local fire `20260823-080004`, `T273`'s `guard_no_host_state_in_lint_corpus` over `T271`'s probe.*

`T273` removed the program's most dangerous signal: the bar's green had depended on a 24-byte file in `/tmp`,
so a clean checkout got **exit 2 with no probe line**. Verified both directions — after the fix, the residue
**deleted**, the bar is `PASS exit 0, 46 vectors / 7884 cells`, and the file **is not recreated**.

At fire close the bar went **exit 2, zero probe lines**. It was not an oracle outage (`P-84` — read the
**absence** of the line; the oracle answered SQL seconds earlier) and not a corpus defect. **`T273`'s new
guard had caught `T271`'s new probe, both merged in the same fire**: census 18 against a pin of 17.

The resolution is the part worth keeping. The guard's own text prefers **repair** (`mktemp -d`) over
**pinning** — but that probe exists to measure whether the bar depends on **one specific absolute path
another instrument hard-codes**, so *naming the path IS the measurement* and a fresh `mktemp` path would
measure nothing. It reads the path, records whether it was present, and **restores the state it found**.
Pinned, therefore — **with the reasoning written into `conformance.sh` beside the pin rather than into a
commit message**, because that file is what a future reviewer reads, and filed as `T293` for independent
adjudication with the instruction that a reviewer who disagrees should revert the row and repair the probe.

**THE RULE: when a guard you just merged rejects work you just merged, that is the guard EARNING ITS KEEP on
its first day — do not treat it as a merge accident.** Decide repair-vs-pin on whether the flagged site is a
**dependency** or a **measurement**, write the reasoning where the guard lives, and **file the decision for
review rather than letting an unreviewed judgement stand as precedent.** Distinguish this from the move
`P-88` rejects: `T271` refused to create the file or move `FAILOPEN_PIN_FILE_LIST`, because those manufacture
a green out of host state. A **census** whose stated purpose is that no new site enters unseen is a different
instrument — adding a genuine site **with its justification** is what it asks for.

---

**P-94 — A SEVERITY DOWNGRADE THAT CITES A MITIGATION MUST DRIVE THAT MITIGATION RED IN THE SAME PASS.**

*Local fire `20260827-230001`. `T308` reviewing `T292`; `T314` closing what `T308` opened.*

`T292`'s Theorem 2 has two clauses: (1) raising coverage requires **asserting a fact**, which no rule reading
only *(document, register)* can distinguish from a true one, and (2) **every witness path is printed, so a
forgery is NAMED**. A review pass used **clause 2 twice to downgrade its own severities** — and never tested
it. `T308` tested it and it was false: the witness path is `path + "." + k`, an unescaped concatenation of
**attacker-chosen key strings**, printed unquoted and uncapped. A top-level key literally named `cells[0]`
prints a witness line **byte-identical** to a legitimately nested document's.

**The mitigation was load-bearing for two findings and had never been driven at all.** That is the pattern:
a downgrade converts a finding into a non-finding, so the evidence bar for the *mitigation* is the same bar
as for the *finding* — and it is routinely waived, because a mitigation feels like a reason rather than a
claim.

**The corollary `T314` added, which is where this stops being about one file.** `T308` also reported *"no
scratch leaked"* while its own merged diff carried a scratch file into another task's committed capture
directory. Cause: the `.gitignore` fence in that directory names **one prefix**, and `T308`'s scratch used a
different one. **A scratch fence is scoped to the directory and prefix it names, so "no scratch leaked" is
never an inference from having written a fence — it is a claim about `git status` over the WHOLE TREE**, and
it must be measured that way.

**And the reversal that makes this worth writing down.** `T314` set out to fix what `T308` named, and found
`T308` **right that the digest was the worse half and wrong about why**: `coverage_digest` *discards* the
path, so the digest collision is container-blindness **working as designed**, and restoring the path would
destroy the property the digest exists to have. `T308`'s own §6 says this and its §5c contradicts it. The
real defect was elsewhere and nobody had named it — the canon `";".join(sorted("%s=%s" % …))` is *itself* an
unescaped concatenation, and `;` and `=` are legal in a JSON member name, so a document that graded **one**
proposition produces the fingerprint of one that graded **two**.

**THE RULE: a mitigation cited to lower a severity is a CLAIM, not a reason. Drive it red in the same pass or
do not lower the severity.** Two further obligations follow. **When a fix lands, RE-SCORE every severity
whose justification the fix withdrew** — `T314` had to do this retroactively for two findings and one moved.
And **when you are handed a diagnosis, verify the mechanism before you repair it**: the repair the brief
implied (escape the printer) was measured to leave the attack **fully alive** at 47 collisions, identical to
no fix at all, because the path was not only displayed — it was an **identity**, a member of a set of path
strings that a `rsplit` steers.

---

**P-95 — A FALLBACK AND A FAIL-OPEN ARE INDISTINGUISHABLE BY READING, AND THEY HAVE OPPOSITE SEVERITIES.**

*Local fire `20260827-230001`. `T299` observed it incidentally, the driver filed it as fact, `T316` refuted it.*

`T299`, doing something else, noticed that `guard_rvpa_floor_t290.py` and `red/drive-red-t290.py` both name
`t256-verdict-predicate/run_rvpa_over_targets.py` — **which does not exist** — and **both exit 0 anyway**. It
declared this out of its grant rather than fixing it quietly, which was right. **The driver then filed the
follow-up with the inference baked into the title**, as *"A GUARD RESOLVES A DEAD PATH AND EXITS 0"*, and
called it a fail-open in the very guard that protects the `T114`/`T176` retro-edit ruling.

**Half of that is true and the important half is false.** `T316` verified the dead reference — and sharpened
it: the file exists at exactly one path, confirmed six ways including *every path it has ever occupied
across all refs*. **It was never moved; it was never there.** The reference was born dead in `T290`'s own
commit, the same day the real file landed. So `T299`'s `[UNVERIFIED]` about *when* it broke has no answer.

But `:81-94` is a **two-candidate ordered fallback, with a docstring saying so** — *"the runner moves in
`T269`; look in BOTH"*. Candidate #1 is an **anticipated future location** for a task that never landed. The
guard exits 0 because it **resolved a live runner and ran it** (22 rows, 51 predicates, 7 disagreements) and
it **prints which candidate it used**. Remove *both* candidates in a scratch clone and it exits **2 with the
probe line absent**. The fail direction was already correct.

**THE RULE: a dead literal is equally consistent with a fail-open and with an announced fallback, so it can
never be classified by reading — only by removing every candidate and observing the exit.** The two-line
experiment costs nothing and went unrun across three fires, because the obvious inference sat ten lines above
the disconfirming docstring. When you meet one, run it.

**Three corollaries `T316` paid for.**

**(a) The right fix was to fix NOTHING.** Repointing a stale forward-reference inside another task's
committed evidence is precisely the in-place edit `T114`/`T176` exist to forbid — and these are the guards
enforcing it. *Refusing the assigned work, with the measurement, was the correct deliverable.*

**(b) A brief's assertion is not evidence, even when the driver wrote it.** `T316` was told the conclusion
and checked it anyway. Had it built on the premise it would have "fixed" a working guard and reported
success. **Titles and briefs in this program state findings as fact; a worker owes them the same
adversarial reading it owes the code.** The title was corrected in `tasks.json` at merge, with the original
text kept beside the refutation so the correction is auditable rather than a quiet rewrite.

**(c) An incidental count is a shortlist, not a population.** `T299`'s "two" became **70 instruments naming a
non-resolving path, 31 of them exiting 0** — 35× and 15×. `T316` refused to call the 31 a defect count,
because the top entry is a *deliberately built announced fallback*: the same shape again. And it **broke its
own census first** — v1 reported 154 dead rows of which **56 (36%) were trailing-punctuation artefacts**, one
of which would have accused `T299`'s own guard, landed two commits earlier, of the defect it was being used
to investigate.

---

<!-- T282-CITATION-ERRATA -->

**P-96 — THE ERRATUM SHIELDED THE CITATIONS IT WAS WRITTEN TO CORRECT, AND A GUARD THAT CHECKED
THE NUMBER WOULD HAVE PASSED EVERY INSTANCE.**
*`T282`, measured at `c086ecb2a01b`.*

`P-86` recorded the pattern ids rotting. `T282` was sent to settle the four ids it named and found the
population had never been measured. It is **~8,500 `P-n` citation sites across the tracked tree**, of which
**14 are genuinely drifted** — including one nobody had seen, `tasks.json:2374`, which cites `P-69` for
`P-79`'s rule and is *not* part of the `P-86` off-by-one at all.

**The exact figures are DELIBERATELY NOT RESTATED HERE.** They moved four times while this task ran — twice
from merging `main`, once from adding this very entry (which changed the rare-token frequencies the scorer
derives *from this register*), and once from the handoff's own citations entering the corpus. **A count
copied into a second document is `P-80`**, so the second site READS the first: run
`.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py`, or read the sha-stamped table in
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T282.md` §2. **The 14 is stable and is the
number that matters**; the corpus size is a property of the day it was swept.

**THE RULE, and it is the half `P-86` left implicit.** `P-86` says cite the id **and its sentence**.
The mechanical consequence is that **the checkable property is the SENTENCE, never the id**: a guard
asking *"is `P-n` defined?"* returns **PASS on every recorded instance of this defect**, because every
drifted citation names an id that exists. Demonstrated, not asserted — the existence-only predicate is
run against the same bytes in
`.softhouse/capture/t282-pnumber-drift/red/20-existence-only-on-RED.txt` and reports `VERDICT PASS`
while the sentence-matching predicate reports three findings and exits 1.

**THREE THINGS THIS COST, all found by driving the checker at real bytes rather than reading it:**

1. **The erratum was a shield.** `P-86`'s body names `P-78`…`P-84` *in order to say those citations are
   wrong*. Cross-reference suppression — *"if the better-matching rule names the cited id, they are
   already bound"* — therefore exempted the drifted citations **because `P-86` mentions them**. The
   correction absorbed the defect it documented. A suppressed winner may now be skipped but may never
   **end** the search.
2. **Use is not mention.** Removing the shield then flagged `patterns.md` itself, where the wrong ids are
   *quoted* with the correction on the same line. Resolved by `P-86`'s own remedy: if the right id is
   already beside the citation, the text is **self-correcting** and no reader can be misdirected.
3. **A markdown table cell is a citation boundary.** A correct `(P-33)` at the end of a row scored
   against `P-25` because the extractor walked backwards into a neighbouring cell about floating point.

**And the repair for `P-80` nearly committed `P-80`:** inserting this file's new banner shifted every
definition line beneath it (`P-12` `:284`→`:315`), including the line numbers the new banner cites. They
are now derived by `bin/restamp.py` from the live file, never typed.

**COLLISION HAZARD, declared rather than discovered.** This entry claims **`P-96`** while four other
workers were live in the same fire. If a rival `P-96` lands, **renumber this one** — and note that the
instrument below is exactly what was missing when `P-78` collided: it detects a renumbering that failed
to reach the places restating it. **Renumbering is now safe in a way it has never been in this program.**

**INSTRUMENT:** `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py`.
`--selftest` = 11/11. **NOT YET WIRED into `conformance.sh`** — `T326` held that file for the batch;
the exact un-applied wiring diff is in `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T282.md`.
**Until it is applied this enforces nothing**, which is the sixth occurrence of this program's
most-repeated lesson and is recorded here so it is not the seventh.

### `T282` CITATION ERRATA — corrected FORWARD, never edited in place

These citations are in **committed evidence, ratified ADRs and orchestrator-owned files**, which the
program corrects forward rather than rewriting (`T316`). The id in *cited* is wrong; the rule the
sentence actually states is under *actually*. Derived from the checker's adjudicated output — a table
of corrected cardinals that someone retyped would be the next instance of this defect.

| # | site | cited | actually | why |
|---|---|---|---|---|
| 1 | `.softhouse/capture/t234-sweep-instrument-audit/instruments/31-sound-sweep.py:14` | `P-131` | **`-- NOT DEFINED --`** | cited id exists in neither register |
| 2 | `.softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py:36` | `P-79` | **`P-80`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 3 | `.softhouse/capture/t255-dec2-rev8/instruments/30-apply-revision-8.py:72` | `P-79` | **`P-80`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 4 | `.softhouse/capture/t256-verdict-predicate/RULES-failopen.md:17` | `P-80` | **`P-81`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 5 | `.softhouse/capture/t290-review-t271/guard_rvpa_floor_t290.py:24` | `P-261` | **`-- NOT DEFINED --`** | cited id exists in neither register |
| 6 | `.softhouse/capture/t304-evidence-destruction/evidence/10-raw-sites.tsv:1718` | `P-79` | **`P-80`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 7 | `.softhouse/reviews/t260-dec2-rev8/evidence/20-normative-set-diff.txt:65` | `P-79` | **`P-80`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 8 | `.softhouse/reviews/t260-dec2-rev8/evidence/90-per-section-line-delta.txt:271` | `P-79` | **`P-80`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 9 | `.softhouse/reviews/t260-dec2-rev8/instruments/50-collision-and-red-drive.sh:5` | `P-80` | **`P-81`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 10 | `.softhouse/tasks.json:2374` | `P-69` | **`P-79`** | NOT the P-86 off-by-one -- an INDEPENDENT drift, and the strongest signal in the entire population (score 21). Gloss: 'the guard did not merely fail t |
| 11 | `.softhouse/tasks.json:2427` | `P-80` | **`P-81`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 12 | `.softhouse/tasks.json:2427` | `P-83` | **`P-81`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |
| 13 | `.softhouse/tasks.json:3149` | `P-79` | **`P-80`** | Gloss 'make the second site READ the first, do not restate the cardinal' is P-80. This IS the P-86 off-by-one; the keyword adjudicator missed it only  |
| 14 | `docs/adr/DEC-2-gl-accounting-adapter.md:294` | `P-79` | **`P-80`** | the `P-86` off-by-one: the sentence is the rule defined one number higher |

**Total: 14.** Full population, including the 21 adjudicated FALSE POSITIVES and the 2 ambiguous
rule-pairs, in `.softhouse/capture/t282-pnumber-drift/out/population.md`.

**Rows 1 and 5 are cited ids that resolve to NOTHING** — `P-131` and `P-261`, almost certainly typos for
`P-13`/`P-31` and `P-26`, though only their authors can say. Naming them in this table made the checker go
**fatal on the very table recording them**, because `patterns.md` is a directive file. That was the guard
working, and the fix is a declaration rather than an exemption — symmetric with the collision declaration in
the banner, and fatal if it ever goes stale (a declared id that turns out to be defined, or to be cited
nowhere, stops the run):

`PNUMBER-DANGLING-CITED-IDS: 131, 261`

**`P-99` is NOT in that list and must never be.** It is a deliberate absence used as a negative control by
three instruments; the checker carries it separately, with the instrument that depends on it named.


---

<!-- T334-WRITER-SAFETY -->

**P-97 — NEVER WRITE IN PLACE TO A FILE THAT MAY BE EXECUTING. THE WRITERS THIS PIPELINE'S OWN
GUIDANCE PREFERS ARE THE IN-PLACE ONES.**

*Local fire `20260828-080001`. `T309` asked the question, `T301` censused 17 writers, `T334` re-measured
it on three userlands and found the rule cannot be keyed to the writer at all.*

**The mechanism.** zsh does not slurp a script — it returns to the open fd for more input. So a write that
goes **through the original inode** of a script that is *currently running* can be executed as a spliced
tail. `T301` reproduced the splice **at the read-buffer boundary with no length change at all**: four
characters swapped for four, and the row straddling the boundary executed as `ROW 0291 ORIK` — three bytes
from the old file, the rest from the new. Inside a quoted string that prints harmlessly; inside a command
name, an `if`/`fi` or a heredoc delimiter it is a syntax error or **a different command**.

**The census, re-measured by `T334` on three userlands.** Two instruments per writer, because the inode is
only a proxy: (1) `st_ino` before/after, and (2) **a read fd held open across the write**, then `lseek(0)`
and re-read — which is the hazard's own shape. Every leg asserts the bytes actually changed, so a writer
that no-ops scores `NOOP` and is never counted as evidence. Instrument: `probe-writer-census.py` under
`.softhouse/capture/t334-writer-guidance/` with its three outputs. The two instruments agreed on every
scored leg on all three hosts.

| writer | BSD / macOS | GNU / Linux | busybox / Alpine |
|---|---|---|---|
| `cat > file` | **in place** | **in place** | **in place** |
| `printf > file (truncate)` | **in place** | **in place** | **in place** |
| `>> append` | **in place** | **in place** | **in place** |
| `tee file` | **in place** | **in place** | **in place** |
| `tee -a file` | **in place** | **in place** | **in place** |
| `dd conv=notrunc` | **in place** | **in place** | **in place** |
| `cp src dst` | **in place** | **in place** | isolated |
| `cp -p src dst` | **in place** | **in place** | isolated |
| `cat src > dst` | **in place** | **in place** | **in place** |
| `python open(w)` | **in place** | **in place** | **in place** |
| `python open(r+)` | **in place** | **in place** | **in place** |
| `sed > tmp; cat tmp > f` | **in place** | **in place** | **in place** |
| `noclobber-defeating >\|` | **in place** | **in place** | **in place** |
| `ex -s` | **in place** | — | — |
| `ed -s` | **in place** | — | — |
| `mv src dst` | isolated | isolated | isolated |
| `install -m 755` | isolated | isolated | isolated |
| `python write+os.replace` | isolated | isolated | isolated |
| `sed -i (in-place flag)` | isolated | isolated | isolated |
| `sed -i.bak` | isolated | isolated | isolated |
| `perl -i -pe` | isolated | isolated | — |
| `awk > tmp; mv tmp f` | isolated | isolated | isolated |
| `patch` | isolated | — | isolated |
| `git merge --ff-only` | isolated | — | isolated |
| `git checkout other -- <p>` | isolated | — | isolated |
| `git restore -s other <p>` | isolated | — | isolated |
| `git reset --hard other` | isolated | — | isolated |
| `git apply <patch>` | isolated | — | isolated |
| `git checkout-index -f -a` | isolated | — | isolated |
| `git stash pop` | isolated | — | isolated |
| `git pull --ff-only` | isolated | — | isolated |

* **macOS 25.5.0 arm64, BSD userland** — `legs=31 in_place=15 isolated=16 unscored=0`
* **Linux 6.12 aarch64, GNU sed 4.9 + GNU coreutils (docker odoo:18)** — `legs=31 in_place=13 isolated=7 unscored=11`
* **Linux 6.12 aarch64, busybox 1.37 userland (docker alpine:3)** — `legs=31 in_place=11 isolated=17 unscored=3`

**THE RULE IS CONDITIONAL ON THE TARGET, NOT ON THE WRITER — and that is a measured conclusion, not a
stylistic one.** `cp` is **in place** on BSD and on GNU and **isolated** on busybox. A rule of the form
"prefer `cp`" or "`cp` is dangerous" is therefore true on one host and false on another, which is exactly
the class of defect `T256`/`T298` spent themselves establishing may never enter a graded path, and that
`T326` closed again in this same fire. The target-conditional rule holds on all three:

> **Never write IN PLACE to a file that may be executing.** Concretely, in this repo: the fire wrapper
> `.softhouse/bin/fire-program.sh`, anything else under `.softhouse/bin/` while a fire is running,
> `.softhouse/conformance.sh` mid-run, and any guard under `.softhouse/guards/` mid-run. For every other
> target — handoffs, captures, `RESUME.md`, observations, source files, vectors — the shell writers are
> **fine**, and the guidance preferring them is right: they are cheap and composable, and **most targets
> are not running scripts**.

**Safe alternatives, in order of preference.** (1) Edit in a **worktree and land it through git** — all
eight measured git write paths rename, on all three hosts, so a merge can never reach a running fire.
(2) Use a writer that **renames**: `sed -i`, `perl -i`, `mv`, `install`, `patch`, `write-to-temp` **then**
`mv`, or the harness's own `Write`/`Edit` tools, which `T301` measured by hand as renaming.
(3) If it must be a shell writer against a live path, write a temp file and `mv` it — never `cp` it.
**`cp` is the one that bites**: "copy the fixed wrapper over the live one" is what a human types, and it is
the dangerous half of the `cp`/`mv` pair on the two userlands that matter here.

**`sed -i` IS SAFE ON ALL THREE, WHICH SETTLES THE OPEN QUESTION `T301` LEFT.** Measured on all three, `sed -i ''` (BSD spelling) and `sed -i` (GNU and busybox spelling): **ISOLATED — rename — on every one**. The spelling differs
— BSD demands the empty-suffix argument — but the *behaviour* is identical: build a temp file, rename it
over the target. **This matters because this program is driven by two fires on two hosts**, a launchd fire
on the Mac and a cloud fire that never runs here, and a writer-safety rule true only on macOS would be the
same defect `T326` closed in this fire. So the one writer the wrapper's old comment block named as
**dangerous** is in fact the one writer that is **portable-safe**. Naming a safe writer as dangerous is the
cheap direction of the error; it was still an unmeasured claim sitting in a file as if it had been measured.

**HOW NARROW THIS ACTUALLY IS — stated plainly, because overstating it is how a real rule gets ignored.**
The exposure needs *all* of: an agent writing **in place**, to a script that is **running**, **past the
point the shell has already read**. Against the wrapper as shipped it **does not reproduce** — `T301` drove
it and the marker never reached the running fire, because the driver call is nested inside the final
`while` loop, so reaching it forces a read through the loop's `done` and the remaining bytes sit inside the
read-ahead. **That immunity is layout, not design**: appending 15 KB of top-level content after the chain
loop brings the hazard straight back, which `T301` also drove. This is a **default-choice defect**, not a
live bug: nothing is broken today, and the wrong writer is the one an agent reaches for first.

**WHERE THE DEFECTIVE GUIDANCE LIVES: NOT IN THIS REPO.** The instruction to prefer shell writers over the
harness's file tools is injected by the **harness** when bypass-permissions mode is active, and its text
occurs **nowhere in the tracked tree** — `CLAUDE.md`, every `SKILL.md`, and `settings.json` are all clean
[VERIFIED: `git grep` for the phrase returns no tracked hit; the text is in this run's own system prompt].
**So it cannot be edited out, and no `SKILL.md` change removes it.** The repo can only *override* it for
executing targets, which is what this rule is for. Any restatement of it must **name the rule or carry its
sentence, never just the id** (`P-86` — *"an id is a cardinal … make the second site NAME THE RULE, or cite
the id AND its sentence together so a shifted number is self-correcting"*).

**COLLISION HAZARD, declared rather than discovered**, following `T282`'s precedent: this entry claims
**`P-97`** against a register whose high-water mark was measured as `P-96` at the moment of writing,
while other workers were live in the same fire. If a rival `P-97` lands, **renumber this one** — and the
`T282` checker is what detects a renumbering that failed to reach the places restating it.

### `T334` CITATION ERRATUM — corrected FORWARD, never edited in place

Same treatment as the `T282` errata table above, and **deliberately a separate table**: that one is `T282`'s
record and is not to be tidied or renumbered.

**The paraphrase _"a guard that only works when someone remembers to run it enforces nothing"_ is NOT
`P-45`'s recorded text, and it is not any other pattern's text either.** `P-45` is at `patterns.md:1503`
and reads: *"A test-only guard is not a guard … when hardening a check, verify the path that actually
executes in CI/conformance calls it, not merely that a test does."* Related, but a different rule: `P-45` is
about **which path invokes the guard**; the paraphrase is about **a guard invoked only by memory**.

| # | what | measured |
|---|---|---|
| 1 | sites citing the paraphrase as `P-45` | **a moving number, deliberately not pinned here** — see below |
| 2 | recorded rule that states the paraphrase | **none** — the checker scores every one `BARE`, *"matches no registered rule"*, best trigram 1 < 6, fatal **0** |
| 3 | so the correction is | the paraphrase is an **unrecorded gloss**, not a mis-numbered citation. This is **not** the `T282` off-by-one shape (cited `P-x`, actually `P-y`): there is no `P-y` |

**Row 1 is deliberately not a cardinal, and the reason is `P-80` catching this entry mid-write.** The count
was **25** across **18** files when `T334` first measured it and **35**
across **20** files an hour later — because `T334`'s own capture files quote the paraphrase and
**entered the checker's corpus**. That is the same trap `T282` recorded (*"a count copied into a second
document is `P-80`"*), sprung again in the table written to record it. **The second site READS the first:**
run `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py` and filter on the sentence. The
number below that does NOT move is the one that matters, because it counts directive-zone files no evidence
task writes.

**AND PROMOTING THE GLOSS TO A RULE IS A TRAP, MEASURED RATHER THAN ASSUMED.** Recording that sentence as
its own `P-n` immediately turns those harmless `BARE` citations into `MISDIRECTING` ones, **7 of them in the
DIRECTIVE zone, which is FATAL and turns the bar red** — in `.softhouse/bin/branch_sweep.py`,
`.softhouse/bin/fire-program.sh`, `.softhouse/bin/ready-tasks.py` and `.softhouse/conformance.sh`, four
files `T334` was forbidden to edit. Driven in a throwaway clone at `probe-p45-promotion.sh` with output at
`p45-promotion-experiment.txt`, both under `.softhouse/capture/t334-writer-guidance/` — the tree goes from
`VERDICT PASS -- 0 fatal` to `VERDICT FAIL -- 7 fatal (register 0, directive-file 7)`.

**So the sequence matters and is recorded here for whoever owns those files:** repair the citing sites
FIRST, then record the rule. Doing it in the other order reds the bar. Until then the erratum is the
correction, and the gloss stays unrecorded on purpose.

---

**P-98 — A CONTROL THAT CANNOT FAIL AND A CONTROL THAT REFUSES EVERYTHING ARE THE SAME DEFECT WEARING
OPPOSITE SIGNS, AND BOTH READ GREEN FROM OUTSIDE.**

*Local fire `20260828-140005`. Four independent sites across three tasks and one review, collected from
the record rather than taken on `T383`'s count — `T362`'s review of `T357`
(`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T362.md:159-166`, F-2), `T377`'s handoff
(`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T377.md:23-38,300-317`, F-T368-2 and its own
recommendation), `T383`'s handoff (`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T383.md:1-96`,
F-T380-1), and `T385`'s independent review of `T383`
(`.softhouse/reviews/t385-review-t383/REVIEW.md:20-60,170-215`), merged at `e6cd307f`.*

**The four sites, in the order they were laid down.**

1. **`conformance.sh:guard_guards_dir_registration`** (`T323`, extended since). An empty population of
   guard files is refused by name — *"the population is EMPTY. That is a SELECTOR"* failure, never a
   clean tree (`.softhouse/conformance.sh:3271`). This is the founding instance of the *vacuous-pass*
   half: a check that inspects nothing still prints PASS unless the census itself is guarded.
2. **`T362` F-2, reviewing `T357`.** `adjudicate-section1.py` §4 built `vector_files` by `rglob` and
   printed the population size without ever asserting it was non-zero. With `.softhouse/vectors/` moved
   aside it reported `"population searched: 0"`, `"0 distinct capture_ref values inspected"` — and
   **passed, rc 0**. `T357` had marketed the guard as *"executable and permanent, not a paragraph"*; it
   was also permanently green over nothing. `T362` named it the same defect class `P-22` and `P-45` were
   already carrying — evidence this rule was recognisable before it had its own number.
3. **`T377` F-T368-2, `fire-program.sh`'s pre-fire self-test.** `T368` had measured the mechanism directly:
   delete all 45 `_row`/`_arow` invocations from the self-test and it still prints
   `ROWS=0 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0`, exits 0, **and the fire starts** — the fatal control that
   gates every fire in this program, vacuously green on nothing. `T377` closed it with a derived floor
   (population read from the executing bytes, not typed), an empty-population refusal borrowing
   `guard_guards_dir_registration`'s own wording, and a reconciliation (`ROWS + SKIPPED` must equal the
   census, so a silently-skipped row cannot hide). `T377`'s own follow-up (handoff §"Follow-ups" item 1)
   named sites 1–3 as *"three independent instances… in one fire is the bar `patterns.md` normally uses"*
   and recommended filing the rule — but declined to write it, because `patterns.md` was not that task's
   grant.
4. **`T383` F-T380-1, the SAME file, a DIFFERENT control in it.** `T380` had measured the mirror-image
   fail-open in the summary-line reader: `tail -1` of the self-test's printed tally means a SECOND,
   clean-looking summary line silences a real failing one, and the fire starts on a run that just failed
   its own self-test. `T383` fixed it by refusing on multiplicity — zero summary lines refuses (`P-84`,
   presence before value), exactly one behaves as before, two or more refuses regardless of order. That
   closes the fail-open. **And in closing it, `T383`'s own first implementation became the mirror-image
   defect inside the same task**, which is why this site is the one that generalises the rule rather than
   just adding a fourth count to it.

**The mirror-image, caught inside `T383` by its own control.** The first cut counted summary lines with
`_ST_NSUM=${#${(f)_ST_SUMS}}`. In an assignment context that nested form is scalar, and `${#…}` on a
scalar is a **string length**, not an array count: it read **41** — the character count of
`ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0` — and refused the healthy control case `m00` with *"printed 41
TALLY LINES"*. **The multiplicity fix had briefly become a control that refuses every fire.** It was caught
only because `m00` — one well-formed, healthy summary, asserted GREEN — sat beside the thirteen RED
mutation cases in the same driver run, rather than the suite consisting only of cases that are *supposed*
to refuse. A suite built entirely from refusal cases cannot see this bug: it is wrong on exactly the one
input every other case in it deliberately is not.

**`T385`'s independent review answered the mirror-image question FIRST, and named the rule explicitly
before checking anything else** (`REVIEW.md:42-46`): *"a control that refuses everything and a control
that cannot fail are the same defect wearing opposite signs"* — and re-drove *"does a healthy fire still
start"* three independent ways, none of them reusing `T383`'s own driver, before touching any of the
three named fixes. All three came back `rc 0`, healthy fire starts.

**A stated reason can be wrong even when the conclusion it defends is right — fold this in, it is not a
footnote.** `T383` also deliberately kept substring containment green (a line that merely *contains*
`ROWS=` must not join the summary population), and gave a reason: the wiring's own
`lockselftest| ROWS=…` echo is itself a substring line, so a naive unanchored count would refuse every
healthy fire. `T385` (F-T385-1) measured that reason **false**: the `lockselftest| ` prefix is added
*downstream* of the capture, inside `log()`, so that echo is never in `$_ST_OUT` and cannot join the
population whether the selector is anchored or not — and building the exact naive wrapper `T383`
described, against the exact healthy input, returns `rc 0`, fire starts. **The anchoring design was right
and independently reproducible; the example `T383` cited to justify it was not.** `T385` re-derived the
real justification — a future narration line emitted by the self-test itself, not this one — and it holds.
Verifying a conclusion is not the same act as verifying the reason given for it, and both were owed
independent re-derivation here, not just the one that happened to be checkable by rerunning a script.

**THE RULE.** A vacuous-pass control (exits 0 having checked nothing — an empty population, a dead
reference, a floor with no population behind it) and a vacuous-refuse control (exits non-zero on
everything, including the healthy case — a miscounted population, an unanchored selector, a threshold with
no ceiling) are **the same defect**: a control that no longer distinguishes the case it exists to catch
from the case it exists to pass. Both are invisible from the same vantage point, because both a check that
always passes and a check that always fails **look identical to a suite built only from the polarity being
tested** — a vacuous-pass guard looks fine to a suite of clean inputs, and a vacuous-refuse guard looks fine
to a suite of bad inputs. Neither vantage point alone can see its own defect.

**THE DUTY.** Hardening a fail-open control is incomplete without a driven, asserted **healthy CONTROL
case** — not merely a clean-input case that happens to be included, but one whose expected grade is
explicitly GREEN and that is run in the *same* pass as the refusal cases, on the *same* bytes. `m00` is
what caught `T383`'s own regression before it left the worktree; without it the file would have shipped
refusing every fire and passing every "does it refuse?" test written for it. And measure with a real
population (an array, a count of matched rows, a reconciled census), never a proxy that degenerates
silently — a string length standing in for a line count is exactly how a correct-looking predicate becomes
wrong on precisely the one input it must get right.

**Why this is not a restatement of `P-22` or `P-45`.** `P-22` says a control that cannot fail is worse than
none, and prescribes driving every guard red. `P-45` says a test-only guard enforces nothing if the
executing path never calls it. Both are about the vacuous-pass half alone, and neither says what to do
about a *fix* for a vacuous-pass control, which is exactly the shape that produces the mirror image: the
fix pulls the control from "always passes" toward "always refuses," and unless a healthy case rides along
for the whole trip, the fix can overshoot without anyone noticing, because overshoot reads green to a
red-only suite the same way undershoot read green to the original.

**COLLISION HAZARD, declared rather than discovered**, following `T282`'s precedent: this entry
claims **`P-98`** against a register whose high-water mark was measured as `P-97` at the moment of writing
(`.softhouse/patterns.md:3261`), with `P-99` confirmed permanently reserved as a deliberate negative
control and never a real id (`.softhouse/patterns.md:3253`, `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py:61`).
`T398`, filed after this task and depending on it for exactly this reason, takes the next free cardinal
above this one — never `P-98` itself, and never `P-99`. If a rival `P-98` lands anyway, renumber this one
and run `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py` to find every restatement.


---

<!-- T398-MEASURED-BUT-BACKWARDS -->

**P-100 — A REMEDY CAN BE CORRECTLY MEASURED AND STILL GRADE BACKWARDS. ONE IMPLEMENTATION CANNOT
DETECT AN INVERSION, BECAUSE THE SIGNAL IS IDENTICAL FROM THAT SIDE.**

*Local fire `20260828-140005`. `T352` banked the candidate vector, `T359` reviewed it and measured a
one-line remedy, `T360` declined the remedy on reasoning, and `T387`'s independent review of `T360`
(`.softhouse/reviews/t387-review-t360/REVIEW.md`, §1.1–§1.7) ran the same patch against **two**
implementations and found the grading inverted. Merged at `cc45c5af`.*

**WHAT WAS MEASURED, AND IT WAS MEASURED CORRECTLY.** `T359`'s finding F-T359-1 proposed a one-line
change at `impl.go:276-279`: make the port's sub-minor-unit residue refusal return `(*Refusal, nil)`
with an HTTP `422` instead of a Go `error`. `T359` built it, ran it, and reported that `T352`'s stuck
candidate vector then grades `FAIL` with exit 1 and no schema change. **That measurement reproduces
exactly** — `T387` rebuilt the patch from source in a scratch worktree at `main`
(`instruments/patch_t359.py`) and got the reported result line for line. `T359` was also right that
the polarity exists, right that the routing is the cause, and right that `T352`'s "the schema cannot
represent it" premise was false. Nothing about the *diagnosis* is wrong, and nothing about the
*measurement* is wrong.

**WHAT ONE IMPLEMENTATION COULD NOT SEE.** `T387` ran the identical patched tree against the identical
store with exactly one flag changed — `-ledger-impl=ledger-wrong-residue-rounding`, the deliberately
wrong port that rounds the residue HALF_UP and posts. Re-verified for this entry against the committed
transcripts themselves rather than the review prose
(`out/DRIVE-A2-t359-remedy-ledgergo-FULL.log:273,276,281` and its tail `RC_ledger_go=1`;
`out/DRIVE-B2-t359-remedy-wrongimpl-FULL.log:246,276,277,279,284,479` and its tail `RC_wrongimpl=0`):

| implementation | the candidate vector | ledger parity | ledger cells graded / MONEY cells | run verdict |
|---|---|---|---|---|
| `ledger-go` — **the CORRECT port** | `FAIL` — 1 cell, **0 money** | `PASS 7` **`FAIL 1`** | `143` graded, `39` MONEY | **`FAIL (exit 1)`** |
| `ledger-wrong-residue-rounding` — **DELIBERATELY WRONG** | `PASS` — 11 cells, **4 MONEY** | **`PASS 8`** `FAIL 0` | `153` graded, `43` MONEY | **`PASS (exit 0)`** |

**Under a remedy that was correctly measured, the deliberately wrong implementation is the one that
passes and greens the bar, and the correct port is the one that reds it.** The wrong port passes by
matching an `amount_minor` of `10013` across four money cells — a minor-unit quantity that `T352` wrote
knowing **neither the reference oracle (Fineract) nor the port ever produced it**. Note what that
inflation is and is not: the corpus never treats `10013` as a *number* to be recomputed, only as bytes
to be compared, and the port's residue detection scans fraction bytes against `'0'` with no `strconv`,
no division and no exponent. **No float is involved anywhere in this defect**, and money stays integer
minor units throughout. The failure is that a fabricated integer minor-unit value entered the graded
money census at all, moving a pinned figure (`LEDGER money cells compared`) by four.

**THE RULE.** *Verifying that a fix makes the failing case fail is not verifying that it grades
correctly.* A change to a **grading** path — a comparator, a routing decision, an outcome polarity, a
gate criterion — must be driven against **at least one correct implementation and at least one
deliberately wrong one, in the same pass, on the same bytes**, and the correct one must come back green
while the wrong one dies. One implementation cannot detect an inversion: from a single side, "my patch
made the stuck vector red" and "my patch made every conforming port red and every wrong port green"
emit **the same observation**.

**THE TWO COROLLARIES, both found by `T387` and named by neither `T359` nor `T360`.**

1. **A permanent baseline FAIL makes a `kills >= 1` criterion vacuous.**
   `.softhouse/conformance.sh:gate_wrong_ledger_impls_die` decides that a wrong port DIED from
   `rc == 1 && banner && (parityFAIL + refusalFAIL) >= 1`, read off the *printed* figures. Under the
   remedy the **correct** port prints `ledger parity FAIL 1` permanently, so every implementation
   inherits the floor and satisfies `>= 1` without the corpus discriminating anything. That is the
   shape of `P-35` — every vacuous guard in this repo is a NEGATIVE assertion, and that is the whole
   diagnosis — arriving through the back door of a *fix*.
2. **A diff appended UNCONDITIONALLY means no vector shape can ever be green.** In `grade.go` the
   refusal-on-a-parity-vector branch appends its diff before `cmpInt("leg_count", …)`, and `gradeOne`
   sets `OutcomeFail` whenever `Detail` is non-empty. There is no vector shape — not even
   `expect.legs: []` — that reaches that branch and passes. So the remedy could only ever express an
   open, gated disagreement as **a permanently red bar**, which is the state a later engineer deletes
   to get a green run.

**THE DUTY.** Before a grading change lands: name the correct implementation and the wrong one you drove
it against, commit both transcripts, and state the exit code of each. If the corpus has no wrong
implementation for the behaviour under change, **that is the finding** — build one first, per `P-3`: a
green conformance run says nothing about behaviours no vector exercises, so mutate the port. And when a
grading change moves a pinned money figure, reconcile it by running, never by arithmetic (`P-83`).

**`T359`'S REMEDY IS `DO-NOT-APPLY`.** This is the durable marking the record was missing, and it is
recorded here because `T359`'s review is committed evidence that may not be rewritten in place. A later
reader who finds `T359`'s review alone finds a measured, confident, reproducible recommendation with
nothing beside it saying **do not apply this patch**. Applying `T359`'s `impl.go:276-279` change will:
(a) fabricate a wire status and a Fineract globalisation code that no observed refusal carries — every
one of the port's nine existing `&Refusal{…}` sites carries an *observed* `403` and a real code;
(b) invert the grading, so a wrong port greens the bar and the correct port reds it; (c) admit an
invented `amount_minor` into the money-cell census; and (d) make the wrong-implementation kill criterion
vacuous per corollary 1. **`T360` was right to refuse it.** `T359`'s *diagnosis* stands and `T360` built
on it correctly; only the patch is condemned. Compare `P-82` — a proposed fix can be measured inert, and
that is a result worth the tokens — and note the sharper case this is: a fix measured **active**, in the
direction its author intended, and still wrong.

**Why this is not `P-98`.** `P-98` is the rule that a control that cannot fail and a control that refuses
everything are the same defect wearing opposite signs, and both read green from outside; its duty is to
ride a healthy GREEN control case alongside the refusal cases. This rule is about a control that
*discriminates perfectly and points the wrong way*. A healthy-case control of the kind `P-98` prescribes
would not have caught `T359`'s remedy, because under it the healthy implementation is exactly the one
that goes red — the control fires, correctly, and reports the wrong verdict. The defect is **polarity**,
not **vacuity**, and it needs a wrong implementation rather than a clean input to expose it.

**COLLISION HAZARD, declared rather than discovered**, following `T282`'s and `T392`'s precedent: this
entry claims **`P-100`**. `P-98` was the register's high-water mark at the moment of writing, taken by
`T392` and merged to `main` at `2f4c3378`; `P-99` is permanently reserved as a deliberate negative
control and is never a usable id (`.softhouse/patterns.md:3253`,
`.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py:61`). `100` was verified free by
enumerating every `P-n` token in this file and across the whole tree before writing: the only
pre-existing occurrences of the literal `P-100` anywhere were three *instructions to take it*
(`.softhouse/RESUME.md`, `.softhouse/tasks.json`, and `T392`'s handoff), and no definition. A worker who
must write a not-yet-defined id in prose inside a directive file should know that the citation checker
reads any `P-<n>` token as a citation regardless of the surrounding words — `T392` scored an UNDEFINED
citation that way while drafting this very forward reference — so define the id in the same commit that
first names it.

---

<!-- T398-SELF-REFERENTIAL-CENSUS -->

**P-101 — WRITING A FINDING DOWN DESTROYS THE MEASUREMENT THAT REPRODUCES IT. THE CORPUS STARTS
MATCHING ITS OWN DOCUMENTATION, AND THE CONTROLS GO FIRST.**

*Local fire `20260828-140005`. `T238` recorded the finding, `T379` inherited its framing, `T381`
re-measured and corrected it, and `T386`'s review of `T381`
(`.softhouse/reviews/t386-review-t381/REVIEW.md`) found that `T234` had already run the decisive control
many fires earlier and that the number it produced had since rotted. Re-measured for this entry by
`T398` on head `4cf77a42` with `T386`'s own instrument, unmodified; transcript at
`.softhouse/capture/t398-measured-but-backwards/out/T398-r3-remeasure.txt`.*

**THE UNDERLYING HAZARD IS REAL AND UNCHANGED.** `git grep -E` compiles POSIX ERE, which has no word
boundary, so the escape in `-E '\bmain\b'` degrades to the literal letters and the pattern is exactly
`-F 'bmainb'`. Not a similar count — **the same bytes**: all three forms return one output whose sha256
is `f4f1f727bd97a7ecb72fefc0e66a2d02cfbc62c8972016da00236f15b40f2445` on today's tree. A sweep written
with `\bmain\b` under `-E` silently searches for a word nobody writes. This is the same family as
`P-75`. The engine that actually has word boundaries is `-P`.

**WHAT WENT WRONG WAS THE FRAMING, AND IT SURVIVED THREE TASKS.** `T238` read "the two patterns return
the same count" as the engine **fabricating** matches. It is not fabricating anything: `T386`'s control
— which nobody before it ran — shows the engine interprets ERE alternation perfectly well, because
`-E 'ma(in|ni)'` and `-F 'ma(in|ni)'` disagree by four orders of magnitude. POSIX ERE simply has no
`\b`. Worse, `T234`'s handoff (`.softhouse/capture/t234-sweep-instrument-audit/HANDOFF.md:266-276`) had
**already run the `-P` control and already quantified the damage** — *"a 95.3 % recall loss (61/64)"* —
so the program spent three more tasks rediscovering a result it already had in writing, filed where the
reader who needed it did not look (`P-73`).

**AND THEN THE MEASUREMENT DIED OF BEING RECORDED.** Every number below is a count of matching lines,
`git grep -c` summed, scope `-- .softhouse`, same instrument each time:

| term | `T234` (`HANDOFF.md:272`) | `T386` (`out/T386-r3-measure.txt`, head `9eedfe4d`) | `T398` re-measure (head `4cf77a42`) |
|---|---|---|---|
| `-E '\bmain\b'` | **0** | 114 | **138** |
| `-E 'bmainb'` | **0** | 114 | **138** |
| `-F 'bmainb'` | not run | 114 | **138** |
| `-E 'ma(in\|ni)'` — ERE-interpretation control | not run | 33,751 | **35,633** |
| `-F 'ma(in\|ni)'` — the literal half of that control | not run | **0** | **7** |
| `-P '\bmain\b'` — the real answer | 17,646 *(repo-wide)* | 22,524 | **23,111** *(23,324 repo-wide)* |
| `-E 'bzzqabsenttermb'` — `T386`'s ABSENT-TERM negative control | not run | **0** | **3** |

**The `-E` figure went from 0 to 138 for one reason: the program kept writing the finding down.** Every
one of the 138 is a document *this program authored about this hazard* — `T234`'s handoff and its
instrument, `T381`'s and `T386`'s material, and now this entry. A term that was absent from the corpus
is now abundant in it, purely as an artefact of documenting its absence, and the measurement that proved
the point can no longer prove it.

**THE CONTROLS DEGRADED FASTEST, AND INSIDE ONE FIRE.** `T386` built two controls and both were clean
when built. Re-run one day later, unmodified: the ERE-interpretation control's literal half has gone
`0 → 7`, and **`T386`'s deliberately-absent negative control has gone `0 → 3`**. All ten of those new
hits are `T386`'s own review, `T386`'s own instrument source, `T386`'s own transcript, and the task
description written to dispatch this entry. `T386`'s instrument still prints its hardcoded narration
*"both 0, they AGREE"* over a measurement that now reads 3 and 3 — a stale sentence standing over a
moved number, which is `P-80`: a corrected cardinal rots in every place it was restated, and the count
is the same defect as the line number. The reserved-id discipline that protects `P-99` is this same
discipline applied to a name rather than a search term, and it is the only reason `P-99` has not
suffered the same fate.

**THE RULE.** Any census that greps *this repo* for evidence *about this repo* is self-referential, and
its population grows every time a task records the finding. Such a count is **a fact about today's
corpus, not a property** (`P-7`), and it decays in a specific direction: toward the program's own
documentation, which means toward false positives that all look like confirmations. A negative control
built from a literal search term is the most fragile part of the instrument, because the act of
publishing the control publishes the term.

**THE DUTY, four parts.**

1. **Never state a self-referential count as a standing fact.** State it with its head sha, its scope,
   its exact invocation, and the date — `P-33`: a tool claim is a claim about a binary, a version, a
   locale, an invocation AND an input shape, so name all five.
2. **Re-measure before citing, never inherit.** `T379` inherited `T238`'s framing and carried it a
   further task; `T381` re-measured and corrected it in one pass.
3. **Exclude the program's own record from a census about the program**, or partition the hits into
   "code and instruments under test" and "documents about the hazard" and report both. A census whose
   population is dominated by its own commentary has measured its own commentary.
4. **Build negative controls that cannot be contaminated by publication** — derive them (a term
   generated at run time, a population read from the executing bytes) rather than typing a literal
   nonce into a file that will be committed. If a literal nonce is unavoidable, assert its count against
   an expected value that is *computed*, so the instrument goes red when it rots instead of printing a
   stale gloss. `P-72`: a sweep is an INSTRUMENT, so calibrate it on a known positive before you report
   its negatives — and note that a *known negative* needs the same care and gets far less.

**THIS ENTRY IS ITSELF AN INSTANCE, AND IT WAS MEASURED RATHER THAN PREDICTED.** The same instrument was
re-run immediately after this entry was committed, and every figure in the table above had already moved
again: `-E 'bmainb'` **138 → 147**, `-F 'ma(in|ni)'` **7 → 11**, `-E 'ma(in|ni)'` 35,633 → 35,653
(`out/T398-r3-remeasure.txt` vs `out/T398-r3-remeasure-AFTER-COMMIT.txt`, same instrument, same scope,
one commit apart). **The act of recording the rule invalidated the numbers the rule cites**, inside one
commit, exactly as the rule says it will. That is not a reason to leave the rule unwritten; it is the
reason it must be written **with its invocation and its head sha attached**, so the next reader re-runs
it instead of quoting it. `P-84` applies to reading these numbers as much as to a probe line: read the
absence, not the value.

**COLLISION HAZARD, declared rather than discovered:** this entry claims **`P-101`**, verified free the
same way `P-100` was — no `P-101` token existed anywhere in the tree before this commit, defined or
cited, and `P-100` is defined immediately above by the same task in the same commit.

**One pattern or two, and why two.** `P-100` and `P-101` were dispatched together and both are about a
measurement that is sound from the only vantage point its author occupied. They are filed separately
because their **populations** differ (implementations under grade, versus documents in a corpus), their
**remedies** differ (add a deliberately wrong implementation to the same pass, versus exclude the
program's own record and derive the control), and a single merged entry would be cited for one half and
read for the other — which is the exact hazard `P-86` records: the pattern ids themselves rotted, in the
file that names the rot.

---

<!-- T438-SELF-CONVICTING-CARDINAL -->

**P-102 — WHEN TWO TASKS DISAGREE ABOUT A MEASURED VALUE, CHECK WHETHER THE DISPUTING TASK'S *OTHER*
NUMBERS COULD HAVE BEEN COMPUTED FROM ITS OWN. OFTEN THEY COULD NOT, AND THE DISPUTE SETTLES ITSELF
FROM THE RECORD BEFORE ANYONE RE-RUNS ANYTHING.**

*Local fire `20260829-080002`. `T409` published a value; `T417` published a different one, declared the
discrepancy, declined to chase it, and told later readers not to trust `T409`'s. `T438`'s independent
review of `T417` found `T417` wrong and `T409` right. The driver then settled it with its own `SELECT`s
against `fineract_gerege` rather than by weighing two accounts, and found the disagreement was already
decidable from `T417`'s own published figures. Transcripts: the correction block in
`.softhouse/handoff/T417-scheduler-attribution.md`, and `.softhouse/reviews/t438-review-t417/REVIEW.md`.*

**THE MEASUREMENT.** Four queries, all on one unmoved table:

```
min(entry_date)                                             -> 2026-01-15   <- what T417 published
min(entry_date) WHERE is_running_balance_calculated = false -> 2026-05-15   <- what T409 published
count(*)        WHERE entry_date >= DATE '2026-01-15'       ->        109
count(*)        WHERE entry_date >= DATE '2026-05-15'       ->         55
```

`T417` published the **global** minimum under the alias `min_uncalculated_entry_date`, because its own
committed SQL put the `FILTER` on the `count(*)` and **not** on the `min()`. Its stated reason for not
chasing the discrepancy was *"the count is 55 either way."*

**THE COUNT IS NOT 55 EITHER WAY, AND THAT IS THE WHOLE PATTERN.** `55` follows **only** from
`2026-05-15`. From the `2026-01-15` that same task published, the count is `109`. So the `55` it
reported as *confirmed pre-state* **could only have been computed from the value its prose told the next
reader to distrust.** The task's own arithmetic was using `T409`'s number while its sentence disputed it.

**WHY THIS IS A METHOD AND NOT AN ANECDOTE.** A disagreement between two tasks about a measured value
normally costs a re-run — and on an oracle that edits itself, a re-run can return a *third* answer and
settle nothing, because the state may have moved between the readings. But a published record usually
contains **more than one number derived from the disputed one**, and those derived numbers are a free,
retrospective check that needs no access to the oracle at all. Ask: *given the value this task claims,
does its own next figure follow?* When it does not, the disagreement is resolved out of the record, at
zero cost, and **without the possibility of drift confusing the answer** — which is precisely what made
this one a **measurement defect rather than drift**, the distinction `T417` was built to draw and got
wrong about itself.

**THE GENERATIVE CAUSE, worth its own line because it is invisible on reading.** An aggregate carrying a
`FILTER` sitting in the same `SELECT` list as an aggregate without one, under a column alias that
implies **both** are filtered. It reads correctly. It runs wrong. `git diff` shows nothing unusual, a
reviewer scanning the query sees the `FILTER` and moves on, and the alias — the only thing a later
reader will actually quote — is a lie about the value beneath it. Census for this shape directly; do not
expect to notice it while reading for something else.

**THE PROCEDURE, in order, cheapest first:**
1. **Re-derive the disputed value's *dependents* from the record.** Does the disputing task's own next
   number follow from its own claim? This costs one arithmetic check and no oracle access.
2. **Read the query, not the result.** Look for an alias that claims more than its expression does.
3. **Only then re-run** — and when you do, state the instant, because on a self-editing oracle a third
   answer is a possible outcome and you must be able to tell drift from defect.

**AND THE HARM THIS PARTICULAR SHAPE DOES IS ASYMMETRIC.** A wrong number is corrected by the next
person who measures it. A wrong number **accompanied by an instruction to distrust the correct one**
survives that correction: it converts the next reader's agreement with reality into a reason to look
again. `T417` wrote *"a later reader should not take `2026-05-15` from `T409` without re-deriving
it"* — advice that is unimpeachable in general and, here, pointed the reader away from the right answer.
**Never pair an unchased discrepancy with a verdict about who is wrong.** Record the discrepancy, name
both values, and say plainly that you did not settle it. A follow-up (`FU-T417-2`) had already inherited
the verdict and would have sent its worker into the unfiltered `min`.

**COLLISION HAZARD, declared rather than discovered:** this entry claims **`P-102`**, verified free the
way `P-100` and `P-101` were — `git grep -c 'P-102'` over the whole repository and a working-tree
`grep -rn` both returned **no hits** before this commit, defined or cited.

> **AND THE FIRST DRAFT OF THIS VERY PARAGRAPH REDDENED THE BAR, which is worth more than the pattern
> above it.** It ended with a sentence reporting that the *next* cardinal had also been checked and was
> free. That sentence put a bare, undefined `P-<n>` token into `.softhouse/patterns.md` — a **DIRECTIVE**
> file to `check-pnumber-citations.py` — so `guard_pnumber_citations`, which is **HARD**, refused:
>
> ```
> PNUMBER-CITATIONS: FATAL UNDEFINED .softhouse/patterns.md:<line> <token> -- defined in neither register
> PNUMBER-CITATIONS: VERDICT FAIL -- 1 fatal (register 0, directive-file 1)
> EXIT=2        # and the `probe = ` line was NEVER PRINTED
> ```
>
> This is the same defect that reddened `main` for **three pushed commits** during local fire
> `20260828-140005`, committed here by the driver that had just finished reading the account of it. The
> only thing that differed is that the bar was run on the working tree **before** the push, so `main`
> never went red — which is the whole of the remedy, and it is `T412`'s standing complaint that the
> driver is the one identity that pushes to `main` and the one that does not grade itself.
>
> **The rule this yields is narrow and absolute: a freshness check on an unclaimed cardinal must never be
> written down using the cardinal.** Say that the next id was checked and found free; do not spell it. An
> id is a citation the moment it is typed, and a citation to something you deliberately did not define is
> by construction undefined. Note also the failure shape: **exit 2 with NO probe line at all.** Read the
> line's *absence*, never its value — four exit-2 paths precede it and a failed HARD guard is one of
> them, so "probe != up" is trivially true when nothing printed.

**Relation to neighbours.** `P-83` says two independent movements of one pinned number reconcile by
running, never by arithmetic — this is not its converse. `P-83` governs a **pin that has legitimately
moved twice**, where only a run can order the movements. `P-102` governs a **single unmoved value two
tasks read differently**, where a run is the *expensive* step and the record decides it for free. The
two are compatible: check the record first, and when the record cannot decide, run.

---

<!-- T458-FIXTURE-LITERAL-REFLEX -->

**P-103 — A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE, NOT A STRING. SIX WORKERS
IN ONE FIRE SPELLED ONE AS A LITERAL, THE BAR REFUSED ALL SIX ON THEIR FIRST COMMITTED RUN, AND ALL
SIX REPAIRED THE INSTRUMENT RATHER THAN GROWING THE PIN — WHICH IS WORTH RECORDING AS MUCH AS THE
DEFECT IS.**

*Local fire `20260829-080002`, iterations 3–5. Filed by `T458`, which re-derived every row below from
the branches and transcripts on `main` rather than inheriting them from its own dispatch brief.*

**THE MEASUREMENT.** Six workers, one fire, one reflex. Every row was read from the cited committed
artefact, not from the task description that dispatched this entry:

| # | Task | Guard that refused | Measured probe line / figures | Verified in |
|---|------|--------------------|-------------------------------|-------------|
| 1 | `T440` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2` | `.softhouse/reviews/t440-review-t424/out/T440-BAR-own-RED.txt:191`; narrated in that review's §10a |
| 2 | `T446` | `guard_no_fail_open_instruments` (the **sibling** guard) | fail-open frontier `15`, `pinned at 11`, **4** new `TIER2` rows, bar `EXIT 2`, `grep -c 'probe = ' = 0` | `.softhouse/reviews/t446-review-t445/REVIEW.md` §11.1; `.softhouse/reviews/t446-review-t445/evidence/80-my-first-bar-REFUSED-failopen.log:100,122` |
| 3 | `T447` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2` | `.softhouse/reviews/t447-review-t442/REVIEW.md` §11 |
| 4 | `T448` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2`, `grep -c 'probe = ' -> 0` | `.softhouse/reviews/t448-review-t433/out/79-BAR-FIRST-RUN-REFUSED-BY-MY-OWN-INSTRUMENT.txt:193`; `.softhouse/reviews/t448-review-t433/REVIEW.md:531` |
| 5 | `T451` | `guard_dead_path_frontier` | `rows=120 pinned=108 added=12` — **all twelve from one file** | `.softhouse/handoff/T451-t449-conditions.md:374-382` |
| 6 | `T452` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2`, on a clean tree (0 dirty) | `.softhouse/handoff/T452-t447-conditions.md:404-410` |

**ALL SIX ROW COUNTS REPRODUCE.** `T458` re-read each artefact; nothing in the table was inherited.
Two refinements the dispatch brief did not carry, recorded because they change what a reader should
generalise:

* The brief gives `T452` as `rows=109 pinned=108`. The committed line also carries `added=1
  removed=0`; the abbreviation was lossy, not wrong.
* The brief calls all six *fixture* literals. **Measured, they are three sub-classes, and only two
  are fixtures.** See below. The *reflex* is one; the *object* is not.

**THE THREE SUB-CLASSES, because the remedy differs slightly and the misdiagnosis is expensive.**

1. **CROSS-BRANCH ARTEFACT REFERENCE (`T440`, `T447`, `T448` — three of six).** The instrument names
   a real file that exists **only on the branch under review**. On the author's own tree the path is
   *genuinely* dead, so the census is not merely defensible here — it is **right**, and it caught a
   claim that stops reproducing the moment the instrument leaves that one branch. `T448`'s own words:
   its instrument "spelled the path of the guard it tests as a literal. That guard is on
   `softhouse/T433-t423-c1` and **not on `main`**."
2. **FIXTURE LITERAL PROPER (`T451`, `T452` — two of six).** The string is not a reference to this
   tree at all. `T451`'s `bin/10-fixture.sh` built a *synthetic* repository whose paths had to
   **mimic** this program's conventions (that mimicry is the point of its cases K and R2), and twelve
   of them were spelled out. `T452`'s arm C named a relocation destination it *creates at run time*.
3. **THE SIBLING REFLEX (`T446` — one of six).** Not a dead path: four drives whose failure arms
   *printed* instead of exiting, so each could print a negative it had not measured. Different guard,
   same generative cause — **an instrument that states something about the world it never established.**

**EVERY ONE OF THE SIX REPAIRED AT THE INSTRUMENT AND NONE GREW THE PIN.** That is the finding, and
it is a *good* one:

* `T440` — the graded path became **a required argument with no default**, and the script refuses when
  it does not resolve. It explicitly refused the tempting alternative: *"spell the literal in pieces
  so the census would not see it. That is gaming a guard this program has paid for twice."*
* `T447` — same repair, on the erratum it grades: required argument, `NO-ARG EXIT=2` verified.
* `T448` — location became the required caller parameter `T448_GUARD`, and a value that does not
  resolve is **`exit 3` in `prepare()` — never a skipped case and never a pass**.
* `T451` — the fixture's paths are now assembled from `S=".softhouse"` [`10-fixture.sh:16`], with the
  reason written in the file. The pin was not touched.
* `T452` — the destination is assembled at run time from the real directory and sanity-checked before
  use. The pin was not touched; the frontier went back to 108.
* `T446` — the four drives were rewritten so a failure arm exits instead of printing.

**THE REMEDY, and it is always small. One of these three, never a fourth:**

1. **ASSEMBLE the path at run time from a variable** — `S=".softhouse"` and build downward. The census
   reads **quoted literals only**, and a path that is not spelled in one is not a row. This is not
   evasion: an assembled path is a *different claim*, one about a directory the script computes, and
   that is exactly what a fixture means.
2. **MAKE THE LOCATION A REQUIRED PARAMETER** — `${VAR:?…}` with no default, and a **hard exit** (not
   a skip, not a warning, not a default) when it does not resolve. This is what the frontier guard
   asks for in exchange for the row, in the refusal text itself.
3. **ADOPT `T238`'s `sweeplib.sh` SHAPE** so an instrument cannot print a negative it did not measure
   — the `T446` half of the class. A `|| echo "(none)"` arm cannot tell *"the line is absent"* from
   *"the log is absent"*, and it reports the second as the first.

**AND THE FORBIDDEN FOURTH, stated because it is the one that will occur to the next worker:** do
**not** split, concatenate or otherwise disguise the literal to slip past the selector, and do **not**
add the row to the pin. The pin is a frontier, not an amnesty. Splitting the string leaves the false
claim in place and removes the only instrument that would have found it.

**CAN THE GUARD TELL A FIXTURE LITERAL FROM A GENUINE DEAD PATH? NO — AND IT SHOULD NOT TRY.** This
was asked directly and the honest answer is the useful one. The two are **textually identical**: the
same quoted string inside a fixture builder and inside a real reference is the same bytes, in the same
position, in the same kind of file. The difference lives entirely in **what the surrounding program
does with the value at run time**, which a string-literal census by construction cannot see, and which
no heuristic over the text can recover without guessing. A detector that guessed would be strictly
worse than none: its false negatives would be silent, and *silently excusing a real dead reference* is
the failure this guard exists to prevent — a guard that cannot fail is worse than none, because it is
believed.

So the census's inability is **not a defect to be closed; it is the guard's fail-closed direction
working.** The remedy is to make the distinction visible in the text — which is precisely what all
three repairs above do. Assembling from a variable, or taking a required parameter, does not *hide*
the fixture from the census; it *states* that the path is computed rather than referenced. **The
author encodes the intent because only the author has it.**

**Corollary, and it is the reason this entry exists at all.** The knowledge was in the tree the whole
time — `T440` wrote the remedy down, then `T447`, `T448`, `T451` and `T452` each rediscovered it from
scratch. Four rediscoveries at reviewer cost. A refusal that names **what is wrong** but not **what to
do** buys exactly one of these lessons per worker, and buys it again every time.

**WHAT `T458` CHANGED IN CONSEQUENCE.** The refusal now names the remedy. Both sites that print the
"a `+` row is a NEW site" verdict — the guard's own message in
`.softhouse/guards/check-dead-path-frontier.sh`, which is where the six workers actually read it, and
the wrapper arm in `.softhouse/conformance.sh` — now print the three repairs, the forbidden fourth,
and a **grep anchor into this entry** rather than a line number. Driven RED (a planted dead literal in
a scratch clone: the remedy block prints) and GREEN (clean tree: frontier == pin, the block does not
print); transcripts in `.softhouse/capture/t458-fixture-literal-reflex/`.

**WHY THE ANCHOR IS A SENTENCE AND NOT AN ID.** The refusal message quotes this entry's opening
sentence — `A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE` — and tells the reader to
grep for it. `P-86`: *"an ID IS A CARDINAL. Never restate a pattern id in a second document — make the
second site NAME THE RULE, or cite the id AND its sentence together so a shifted number is
self-correcting."* A number in a shell string is a citation nobody re-checks; a sentence relocates
with its text.

**READ THE REFUSAL'S SHAPE BEFORE ITS CONTENT.** Five of these six bars were `EXIT 2` with the oracle
probe line printed **zero** times. `P-84`: *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ
THE ABSENCE, NOT THE VALUE."* Every one of the six tested the probe line's PRESENCE before its value,
and so none of them misread a failed HARD guard as an oracle outage. That habit held under six
independent hits in one fire, which is the strongest evidence this program has that it has taken.

**COLLISION HAZARD, declared rather than discovered:** this entry claims **`P-103`**, verified free
the way `P-100`, `P-101` and `P-102` were — a whole-repository search for the token returned exactly
**one** hit before this commit, and it is not a definition: it is the recorded *transcript of a
refusal*,
`.softhouse/capture/fire-20260829-080002/60-BAR-RED-p102-first-draft-FATAL-undefined-citation.txt:125`,
in which `guard_pnumber_citations` went fatal on a draft that spelled the then-unclaimed cardinal.
Defining `P-103` here retires that dangling citation rather than creating one. Four workers were live
in the same wave; **if a rival `P-103` lands, renumber this one.**

---

### `T470` ERRATUM TO `P-103` — corrected FORWARD, never edited in place

*Filed by `T470` from `T468`'s independent adversarial review of `T458` (finding `C-T468-1`, MAJOR),
local fire `20260829-080002` iteration 6. `T470` re-derived the finding from the shipped bytes rather
than inheriting `T468`'s reading, and it holds. The entry above is **not edited**: this register is
append-only and corrected forward — the same treatment the `T334` CITATION ERRATUM above records, and
for the reason `P-96` gives. **Read the entry above together with this erratum.***

**WHAT IS WRONG, in one clause.** The entry above closes its remedy list with a paragraph beginning
*"AND THE FORBIDDEN FOURTH, stated because it is the one that will occur to the next worker"*
(`.softhouse/patterns.md:3908-3911` as `T458` committed it at `6612d7da`), and that paragraph is a
**conjunction of two prohibitions**:

> "do **not** split, concatenate or otherwise disguise the literal to slip past the selector, **and do
> not add the row to the pin**."

**The first half is right. The second half is wrong**, and so is the heading four lines above it,
*"THE REMEDY, and it is always small. One of these three, never a fourth"* (`:3895`), and so is
`:3903`'s gloss that remedy 2 is *"what the frontier guard asks for in exchange for the row."*

**WHY IT IS WRONG — five sanctioning sites in this tree, each opened rather than cited.**

| # | Site | The bytes |
|---|------|-----------|
| 1 | `.softhouse/guards/check-dead-path-frontier.sh:59-61`, the block headed `WHAT A ROW DOES **NOT** MEAN` | *"A dead literal is a SMELL that must be inspected once, by a human, and then **either repaired or pinned with its reason**. This guard counts; it does not judge."* |
| 2 | The **same refusal message**, in the very `added_n > 0` branch the remedy block lives in, unchanged since `T316` — before `T458`'s block, not after it | *"Either make the path resolve, or — if the reference is a deliberate fallback candidate — make the instrument REFUSE when no candidate resolves, **and record why in the pin**."* |
| 3 | `.softhouse/guards/dead-path-frontier.pin:170-171` (the reason) and `:215-216` (the rows) | The two `FU-T299-2` ordered-fallback instruments — `guard_rvpa_floor_t290.py`, `red/drive-red-t290.py` — are **on the pin, with the reason written above them**, and were never repaired. |
| 4 | `.softhouse/guards/dead-path-frontier.pin:81-87` (the reason) and `:222-225` (the rows) | `T305`'s four red-drive literals — an `attest` dir under the deliberately fictional task id `t999-rig`, and two ledger vectors the drive writes — are **dead BY DESIGN**: *"A red drive plants files that MUST NOT exist in a clean tree; that is what makes it a red drive."* Pinned, with the reason. (`.softhouse/conformance.sh:2694-2698` carried these four for `T323` and says *"They are pinned here, with the reason"*; `T326` folded them into the pin and emptied that list, so the pin is now the live site.) |
| 5 | `.softhouse/guards/dead-path-frontier.pin:121-125` — **the decisive one** | `T326` took a **NEW** row (`T306`'s injected acceptance vector), inspected it, and **pinned it**: *"SAME CLASS, byte for byte, as the four `T305` rows above. **Pinning it is the disposition `T316`'s own header prescribes**: 'a SMELL that must be inspected once, by a human, and then either repaired or pinned WITH ITS REASON.'"* — immediately followed by *"**REPAIR WAS CONSIDERED AND IS NOT AVAILABLE.**"* A NEW row, pinned with its reason, by a later worker, in the very file this guard grades against. That is exactly the case the entry above declared forbidden. |

So the register was telling every future worker not to do a thing that the guard's header sanctions in
terms, that the same refusal message offers on the same screen, and that **the pin this guard grades
against has already done at least three times — once on a NEW row, after explicitly considering repair
and rejecting it**. That is the species of defect already recorded inside the `removed_n` arm of
`.softhouse/conformance.sh` — *"[T358: this line used to say 'the pin is outside T323's edit grant',
which stopped being true when T326 regenerated the pin — a false statement inside a refusal
message.]"* — and it is worse in one respect, because it also reached the register.

**THE CORRECTED RULE. Read this in place of the two clauses above.**

A `+` row is a NEW site and the **PRESUMPTION IS REPAIR** — unchanged, and deliberately so: six of six
workers in fire `20260829-080002` repaired, and none of them needed the pin. Three repairs, and they
are still the three listed above. **But there is a FOURTH DISPOSITION, and it is sanctioned, not
forbidden:**

> **PIN THE ROW WITH ITS REASON.** Permitted only where the reference is a deliberate
> **ORDERED-FALLBACK** candidate or is **DEAD BY DESIGN** (a red drive plants what must not exist in a
> clean tree), and **only together with remedy 2's arm**: the instrument must REFUSE when no candidate
> resolves. The reason goes in the pin, in the same commit, where a reviewer reads it. It is the
> **exception**, never the default, and widening it to "pin anything awkward" is the amnesty the
> frontier exists to prevent — which is what `THE PIN IS A FRONTIER, NOT AN AMNESTY` already says.

**WHAT `THE FORBIDDEN FOURTH` STILL MEANS, because the name is load-bearing and was kept.** It names
**splitting, concatenating or otherwise disguising the literal to slip past the selector, and nothing
else.** It is "the fourth" because it is the fourth *idea that occurs to a refused worker*, not a
fourth entry in a list. **Pinning with a reason is not it.** The string is unchanged in the guard, in
the `conformance.sh` wrapper arm and here, because `T458`'s drive asserts on it verbatim and renaming
it would have silently broken that assertion.

**WHAT `T470` CHANGED IN CONSEQUENCE, driven RED and GREEN.** Both refusal sites now carry the pin
route as a named, sanctioned, gated disposition instead of forbidding it, and remedy 2's arm is stated
as required on *either* route — because site 2 above requires it for the pin route too:

* `.softhouse/guards/check-dead-path-frontier.sh` — the foreclosing clause is gone, and a block headed
  `THE ROUTE THAT IS NOT A REPAIR, AND IS STILL SANCTIONED` prints between the three remedies and
  `THE FORBIDDEN FOURTH`.
* `.softhouse/conformance.sh` — one contiguous hunk of four `warn` lines replacing three, in
  `guard_dead_path_frontier`'s `elif ! LC_ALL=C diff` arm, whose `T458` line likewise read *"do not
  grow the pin"*.
* Driven RED (planted dead literal in a throwaway clone: the refusal prints the pin route **and** the
  pre-existing `record why in the pin` offer **and** `THE FORBIDDEN FOURTH`, and the foreclosing
  strings are gone) and GREEN (clean tree: frontier == pin, none of it prints), with the *absence*
  assertions calibrated against the pre-repair bytes so they are falsifiable. Instruments and
  transcripts in `.softhouse/capture/t470-refusal-forecloses/`.

**NO NEW CARDINAL IS CLAIMED, on purpose.** This is an erratum to `P-103`, not a rule of its own, so it
takes no `P-n`: a correction that needs its own number is a second thing to keep in sync, and four
workers were live in the same wave. `P-86` is why it names the rule and quotes its sentence rather than
leaning on the number. **`P-99` remains the permanently reserved negative control and was not
disturbed.**

**ALSO CORRECTED HERE, since it is a claim about the same commit** (`C-T468-2`, LOW): `T458`'s handoff
reports its `.softhouse/conformance.sh` hunk as **`+9` lines**, twice
(`.softhouse/handoff/T458-handoff.md:114` and the table at `:348`). Measured with `git diff --numstat
3f4e236a 0db7538b`: **`+13`** — **7 `warn` lines + 6 comment lines**, `13` added and `0` removed. The
handoff's own §6 re-specification at `:362` says *"insert those seven `warn` lines"* and **is correct**;
only the two summary figures were wrong, so the specification was never defective. `T458`'s committed
bytes are left as written — a handoff is a dated record of what its author measured, and correcting it
forward preserves the audit trail that editing it would erase.

---

**P-104 — A COUNTED CLAIM RESTING ON ONE PATTERN MATCH MEASURES THAT PATTERN'S VOCABULARY, NEVER THE CODE. THREE INDEPENDENT REVIEWERS IN ONE FIRE EACH BROKE ONE, AND TWO OF THE THREE BROKE IT THE SAME WAY.**

> **THIS HEADING WAS REWRITTEN BEFORE IT EVER LANDED, AND THE GUARD IS WHY.** Its first wording ended
> *"…IS A CLAIM ABOUT THE PATTERN'S VOCABULARY, NOT ABOUT THE WORLD"*, which is P-66/P-70's own
> distinctive sentence — *"'Not found' is a statement about the search, never about the world"* — with
> two words changed. `PNUMBER-CITATIONS` went **FATAL, 3 directive-file misdirections**: the glosses at
> `.softhouse/bin/branch_sweep.py:33`, `.softhouse/bin/fire-program.sh:2934` and
> `.softhouse/conformance.sh:2009` cite P-66 and P-70, and the new heading scored **10** against those
> glosses where the ids they actually cite scored **0** and **1**. Three files that instruct future
> workers were, for one commit, pointing at the wrong rule — and **nobody had edited them.**
>
> **A new rule that borrows an existing rule's sentence silently steals its citations.** The register is
> matched on *text*, so the cost of an evocative heading is paid by every file that already quoted the
> rule you echoed. Say the new thing in new words. This is `P-86`'s converse: `P-86` says cite a rule by
> quoting its sentence rather than leaning on its number; P-104 adds that **the sentence is therefore an
> identifier, and identifiers must not collide.**

**Recorded by:** the `/softhouse-program` driver, cloud fire `cloud-20260902-2000`, 2026-09-02, from the three paired reviews of that fire — the first fire in this program whose entire output was source analysis rather than instrument work, which is very likely why the class became visible at all.

This program already has the rule *"'Not found' is a statement about the search, never about the world."* **P-104 is the sharper, more dangerous special case: not the negative claim, but the COUNTED one.** *"There is exactly one X."* *"There are exactly four Y."* *"Z appears nowhere in these 63 files."* A reader takes those as facts about the code. They are facts about a regular expression.

**Three reviewers, three authors, one class:**

| Review | The author's counted claim | What the reviewer found | Why the search missed it |
|---|---|---|---|
| `T490` vs `T487` | *"exactly ONE rounding site on the posting path"*, and `setScale` appears **nowhere** in 63 files | A **fifth** binary-float money decision — `SavingsTransactionDTO.java:51`, `overdraftAmount.doubleValue() > 0`, reached from 8 call sites — and a **second** rounding site, the INSERT itself | Both of the author's sweeps (`"double \|float \|Double\|Float"` and the §6.2 pattern) contain **no token matching `doubleValue`**. The four `floatValue` sites it *did* find were caught **incidentally**, because they happen to contain `.multiply(` |
| `T491` vs `T488` | *"exactly ONE `POST /journalentries` call site in the whole integration corpus"* | **Five** sites, and the shape-changing conclusion built on the count — *"Fineract's tests never post a manual JE for its own sake"* — **refuted** by a test that does exactly that | The cited grep was structurally blind to those sites, **and the universal was asserted over files the document's own §1.3 declares NOT OPENED** |
| `T492` vs `T489` | `organisation.teller` → NOT-APPLICABLE | A **false NOT-APPLICABLE deleting a live Tier B subsystem**: teller is split across two Gradle modules and the 1,225-LOC service half was classified away while `tierB-branch` sits `pending` | Not a grep, but the same shape — a conclusion drawn over **one** search domain (a module) and stated over **the subsystem**. The author documents this exact split trap in its own §5.6 and applies it correctly to four other cases |

**THE TELL, and it is cheap to check:** the claim contains a **cardinal or a quantifier** — *exactly one*, *all four*, *nowhere*, *never*, *the only* — and its evidence is a **single pattern match**. One search cannot establish a universal over a domain it does not cover, and **the vocabulary of the pattern IS the domain it covers.** `floatValue` and `doubleValue` are the same idea and share no substring; a sweep naming one and not the other is not a sweep for binary floats, it is a sweep for the word the author happened to think of.

**Worse, the failure is silently self-confirming.** A grep that finds four sites *looks like it worked*. Nothing about a result set announces the members it could not match, so the author gets positive evidence for a number that is wrong, and the more sites the pattern does find, the more confident the wrong count becomes.

**THE REMEDY IS NOT A BETTER PATTERN — that is the same move again, one word wider.** Do one of these instead, and say in the document which one you did:

1. **Enumerate the domain, then classify it.** Read all 63 files, or list every method on the type. Bounded and finite beats clever.
2. **Search for the SHAPE, not the word.** *"Any method whose return type is a Java primitive, called on a `BigDecimal`"* covers `doubleValue`, `floatValue`, `intValue` and `longValue` at once. A conversion is not a spelling.
3. **Search for the COMPLEMENT and check it is empty**, which is a different query that fails differently.
4. **Downgrade the claim to what the evidence actually supports.** *"The following four sites, found by this pattern"* is TRUE, useful, and costs the author nothing. **`[UNVERIFIED]` has no penalty in this program; a confident wrong cardinal does.**

**AND THE GENERAL LESSON THE THREE CASES SHARE:** every one of these documents was **good** — three reviewers rated them ACCEPT WITH CONDITIONS and the citation support rates were 96.2 %, 98.5 % and 97.0 %. **The counted claims were the defects, and they were the BOLDED HEADLINES.** The most confident sentence in each document was the wrong one, because a cardinal is what an author bolds. So: **when reviewing, go to the bolded number first.** When authoring, treat your own bolded cardinal as the claim most likely to be wrong, and say which of the four remedies above earned it.
