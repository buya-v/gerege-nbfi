# OH-ACCCTL-CG — EUR CONTROL for the one LoanAccrualActivity-Part2 MNT failure (scenario 11, C3697). CAPTURE ONLY.

Worktree: `/Users/buv/oh-gerege-accctl` (branch `feat/OHACCCTLCG`)
Work ONLY in that directory (plus the disposable copy `/Users/buv/fineract-tierd`). The driver pushes; never exercise
the push gate. Commit after each step, and tear down even if a step fails.

## The one question
`.softhouse/capture/tierd-feasibility/accrual-activity-mnt/replay-result-table.md` records scenario 11 (`@TestRailId:C3697`,
feature line 1231, "Verify accrual activity of overpaid loan in case of reversed MIR made before MIR and CBR for
progressive loan - UC6") FAILED in MNT at feature line 1274 by ONE minor unit on schedule period 1 (principal due 120.21
vs 120.20 expected; balance 222.25 vs 222.26). **Does it fail identically in EUR?** If yes, the pinned build disagrees
with its own `.feature` and the MNT output is gradeable; if not, the MNT re-seed changed the arithmetic — a finding.

## Copy the precedent exactly — do not re-derive
`.softhouse/capture/tierd-feasibility/charges-eur-control/` (read its OWNER.md and `run-charges-eur.sh` first): revert
ONLY the five currency constants to EUR in the disposable copy, rebuild at the pinned image the way it did, replay ONLY
the named scenario (anchored Cucumber `name` regex — make sure no other scenario matches; say which regex), capture on,
then RESTORE MNT and record `mnt-currency-restore.diff` + a post-restore diff proving the copy is back to its MNT seed.

## Deliver in `.softhouse/capture/tierd-feasibility/accrual-activity-eur-control/`
`OWNER.md` with the ANSWER first (same failure / different), a table: step line, period, cell, expected, actual EUR,
actual MNT (from the MNT result table), delta — money in integer minor units; `run-*.sh`, the replay log, `scenario-results.json`,
`preflight.txt`, `up.txt`, `teardown-isolation.txt` (12/12 == baseline), the Feign log's sha256 (not the log).

## Run every command in the FOREGROUND with a bound
Two earlier capture runs wedged (a background job; a command that never returned). **Never `&`, never `jobs`, never
`wait`, never `sleep` > 60.** If a command does not return, note it in OWNER.md and go on to teardown.

## Non-negotiables
Standing tenants `gerege` and `default` untouched — proven by the rig. Never write into `/Users/buv/fineract`. The
disposable copy MUST end on its MNT seed (the next capture depends on it). Tear down every `tierd-*` container. **Do
not touch `nexus/`, `.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, `.softhouse/maps/`.**
PostgreSQL only; **Oracle Database is prohibited.** Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`.
`git commit -F <file>`; never TASK.md. ~200 iterations.
