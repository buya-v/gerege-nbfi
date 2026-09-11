# OH-DLPAUSE-BT2 — grade delinquency PAUSE periods. ONE property, concrete inputs. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-dlgrade` (branch `feat/OHDLGRADEbt`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Two earlier attempts at this task spent 586 and 347 events reading without writing a line. Everything you need is
named below. **Do not read findings, maps or other vectors beyond what is listed. Start writing within 30 iterations.**

## The port (read these two functions, nothing else in it)
`nexus/internal/apps/loan/delinquency.go:96` `OverdueDays(overdueSinceDate, businessDate)` and `:109`
`DelinquentDays(overdueDays, pausedDays, graceDays)`.

## The seam you extend — exact lines (from `.softhouse/maps/loan.md` § Seam entry points)
* `nexus/internal/apps/loan/conformance/vector.go:415` — `DelinquencyRequest` (add the pause input here)
* `vector.go:78` — `SeamLoanDelinquentDays`
* `admit.go:394` — its admission rule (admit the new field the way the existing ones are)
* `impl.go:620` — `goDelinquency` (pass paused days into `DelinquentDays`)
* `impl.go:1229-1248` — `delinquencyWrongMode` / `wrongDelinquencyEvaluator` (add ONE mode: pause ignored)
* existing vectors to copy: `.softhouse/vectors/loan/LN-L01-delinquent-days-july-62.json` (shape + provenance) and any
  `LN-TD-*` vector (throwaway-tenant provenance: tenant `tierd`, image `e596339626bf…`, not tenant `gerege`)

## The observations — transcribe exactly these (driver-selected, sha256 from the committed files)
All under `.softhouse/capture/tierd-feasibility/delinquency-mnt/loans/`:
* `loan-14/loan-14-detail-associations-all-5.json` — `delinquent.pastDueDays 61`, `delinquentDays 44`, pause
  2023-11-17 → 2023-12-01 (active). **A pause that changes the count.**
* `loan-1/loan-1-detail-associations-all-5.json` — `pastDueDays 4`, `delinquentDays 0`, pause 2023-10-16 → 2023-10-20.
  **Overdue entirely inside a pause.**
* `loan-14/loan-14-detail-associations-all-4.json` — `pastDueDays 47`, `delinquentDays 44`, pause 2023-11-17 → 2023-12-30.
Read each file yourself; the business date and the exact paused-day count come from the file, not from this brief.
If the observed delinquentDays cannot be reproduced by `DelinquentDays` from the observed inputs, THAT is the finding —
record the numbers and stop; do not bend the port.

## Deliver
Three vectors (one per file above), the extended seam, the one drive. Measure the drive WITHOUT and WITH the vectors.
Coverage of `DelinquentDays` from the committed-store test (`-count=1`). **Commit after the first vector passes.**

## Non-negotiables
No balance-named field written by any seam or drive. Integer days; no float. `capture_ref` a JSON record +
`capture_sha256`. **Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps.
One bounded context: `loan`. PostgreSQL only; **Oracle Database is prohibited.** Bar: exit 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
