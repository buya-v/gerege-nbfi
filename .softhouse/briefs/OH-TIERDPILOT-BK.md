# OH-TIERDPILOT-BK — Tier D pilot: promote a few replayed read-backs onto the existing LOAN seams. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-tdpilot` (branch `feat/OHTIERDPILOTbk`)
Work ONLY in that directory. **Take no captures. Start no container.** **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/findings/F-2026-09-11-tierd-feasibility.md` — all three passes; the THIRD PASS's Q4 table says
   which cells of the replayed read-backs map onto which `loan` seams, and with what transform.
2. `.softhouse/capture/tierd-feasibility/uc6/OWNER.md` — the extracted loan-1 / loan-10 read-backs and request
   bodies, byte-verified against `feign-uc6.log`, with sha256 per file.
3. `.softhouse/maps/loan.md` — the seams and their existing vectors.

## The driver's provenance decision (2026-09-11) — apply it exactly
A vector MAY cite a capture taken on the Tier D THROWAWAY tenant (`tierd`), on the T305 precedent (LDG-05 was
promoted from throwaway tenant `t305`), because and only because: the instance ran the SAME image
(`sha256:e596339626bf…`) as the standing oracle; the tenant was seeded at `Asia/Ulaanbaatar` with rounding mode
4 (HALF_UP); and the instance was destroyed. Every such vector's provenance must NAME the tenant `tierd`, the
image id, and the replayed scenario (feature file + scenario name), and say it is NOT tenant `gerege`.

## The task
Promote **two or three** vectors onto EXISTING `loan` seams — the cells the Q4 table marks "maps directly" or
"maps with a transform" (e.g. the multi-disbursement schedule of UC6 loan 10 onto
`loan-schedule-amortization`, or a summary onto `loan-summary-outstanding`). Transcribe only observed values;
apply only the transforms the finding names.
* **The admission rules are strict and correct. If a vector is refused** (for example the replay loans are in
  **EUR**, and a seam may admit MNT only), **the refusal is a finding: record which rule, do NOT relax it**, and
  try a seam that admits the case. If none does, promote nothing and say so plainly — that is a valid pilot result.
* Measure every loan drive WITHOUT and WITH the new vectors; report which (if any) newly die. A pilot vector
  that no drive notices is still useful as cross-validation — say which it is.

## Non-negotiables
- Integer minor units; no float. `capture_ref` a JSON record; `capture_sha256`; re-verify after writing.
- **Do not touch `.softhouse/guards/`** (baseline **8** pairs), `.softhouse/conformance.sh` (census 17),
  the capture files, or `.softhouse/maps/`. **One bounded context: `loan`.** PostgreSQL only;
  **Oracle Database is prohibited.** Controls: `loanschedule-wrong-days-in-year-365` → **48**.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~250 iterations. **Commit by iteration 80.**
**`git commit -F <file>`. Never commit TASK.md.**
