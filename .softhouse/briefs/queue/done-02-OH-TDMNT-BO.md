# OH-TDMNT-BO — more Tier D vectors from the committed UC6 MNT capture. NO ORACLE, NO REPLAY.

Worktree: `/Users/buv/oh-gerege-tdmnt` (branch `feat/OHTDMNTbo`)
Work ONLY in that directory. **Start no container.** **A run works ONLY in its own worktree.** The driver pushes;
never exercise the push gate. **OVERNIGHT QUEUE run: nobody is watching — commit early and often.**

## Read first — do not search
1. `.softhouse/findings/F-2026-09-11-tierd-mnt-uc6-promotion.md` — how the first Tier D vector
   (`LN-TD-L10-loan-1-pending-amortizes-to-zero`) was admitted; copy its shape and provenance exactly.
2. `.softhouse/findings/F-2026-09-11-tierd-pilot-loan-refusal.md` — the other two candidates (schedule-interest,
   disbursement-net) and why they were refused in EUR.
3. `.softhouse/capture/tierd-feasibility/uc6-mnt/OWNER.md` and `manifest-uc6-loans-1-10.json`.

## The task
From the committed MNT read-backs (tenant `tierd`, driver provenance decision of 2026-09-11), promote more vectors
onto EXISTING loan seams — at least: loan 1 `loan-schedule-interest` and `loan-disbursement`; loan 10's
multi-disbursement schedule on `loan-schedule-amortization` if its shape admits it. Transcribe only observed values.
**Any refusal is a finding: record the rule, never relax it.** Measure every loan drive WITHOUT and WITH the new
vectors and report which newly die — and say plainly when none does (a cross-validation vector).
**No Go change, no new seam.**

## Non-negotiables
Integer minor units; no float. `capture_ref` a JSON record; `capture_sha256`; re-verify. **Do not touch
`.softhouse/guards/`, `.softhouse/conformance.sh`, captures, or `.softhouse/maps/`.** **One bounded context: `loan`.**
PostgreSQL only; **Oracle Database is prohibited.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~200 iterations. **Commit after each vector.**
**`git commit -F <file>`. Never commit TASK.md.**
