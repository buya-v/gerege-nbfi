# OH-TIERD4-BM — Tier D replay in MNT: can the e2e scenarios produce observations the loan seams admit?

Worktree: `/Users/buv/oh-gerege-tierd4` (branch `feat/OHTIERD4bm`)
Work ONLY in that directory (plus the disposable copy `/Users/buv/fineract-tierd`). **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate. **You are the only run on the machine** — the
driver left the second slot empty so the build and the throwaway have memory.

## Read first — do not search
1. `.softhouse/findings/F-2026-09-11-tierd-feasibility.md` (all three passes) and
   `.softhouse/findings/F-2026-09-11-tierd-pilot-loan-refusal.md` — the replay works; its read-backs were refused
   by the loan harness's `tenant_params` rule because the replay loans are **EUR** and the loan pin is **MNT**.
2. `.softhouse/capture/tierd-feasibility/throwaway/` — the throwaway rig (compose, preflight, isolation guard,
   teardown). **Reuse it.** Its baseline file must be written by `preflight.sh` in THIS worktree before anything
   starts (the second attempt's teardown compared against a missing baseline and cried wolf).
3. `.softhouse/capture/tierd-feasibility/bin/` — the control-tested, loan-keyed extractor. **Use it** to pull
   read-backs out of the new Feign log.

## The driver's decision (2026-09-11) — why MNT is legitimate
MNT, like EUR, has 2 minor digits (ISO 4217 496), so a scenario's arithmetic does not change with the currency
code. Re-seeding the throwaway's currency to MNT and replaying produces the ORACLE'S OWN responses in MNT —
observations, not synthesis. The edit is made ONLY in the disposable copy `/Users/buv/fineract-tierd` (never in
the pinned `/Users/buv/fineract`), and it is recorded as a diff in the capture's OWNER.md.

## The task
1. Find where the e2e runner fixes the currency — `fineract-e2e-tests-core/src/test/resources/
   fineract-test-application.properties` and whatever initializer reads it; step phrases like "{string} EUR
   transaction amount" are LABELS, not configuration — and change the seeded currency to **MNT**, the smallest
   edit that does it. Record the diff.
2. Rebuild only what that edit touches (the recipe in the finding: JDK container over the disposable copy,
   `--no-daemon`, bounded heap). Bring up the throwaway (tenant `tierd`, image `e596339626bf…`,
   `Asia/Ulaanbaatar`, rounding mode 4), replay the **UC6** scenarios of `LoanUpdateApprovedAmount.feature`
   again with the Feign capture on, tear it down.
3. **Do the scenarios still PASS in MNT?** Report per scenario. A failure is a finding (which step, which value).
4. Extract UC6 loan 1 / loan 10 with `bin/extract.py`, commit them under `.softhouse/capture/tierd-feasibility/
   uc6-mnt/` with an OWNER.md, and check whether each read-back's currency is MNT.
5. Try ONE of the pilot's three candidates again (the pilot's finding shows them) on its existing loan seam with the
   MNT capture as `capture_ref`. If the loan harness now ADMITS it and `loan-go` passes it, commit that one vector.
   If it is refused for another reason, record the rule and stop — never relax a rule.

## Isolation — non-negotiable
The standing oracle's tenants `gerege` and `default` must be untouched: the rig's preflight baseline and its
teardown comparison must both read CLEAN, and name the file they compared. Tear down every `tierd-*` container.
Never write into `/Users/buv/fineract`.

## Other non-negotiables
Integer minor units; no float. `capture_ref` a JSON record; `capture_sha256`; re-verify. **Do not touch
`.softhouse/guards/`** (baseline 8 pairs), `.softhouse/conformance.sh`, or `.softhouse/maps/`. PostgreSQL only;
**Oracle Database is prohibited.** Never `find` over `/Users/buv`.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~400 iterations. **Commit the currency diff + a first
finding note by iteration 100**, then each capture as it lands. **`git commit -F <file>`. Never commit TASK.md.**
