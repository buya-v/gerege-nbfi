# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260827-230001` — CLOSED CLEAN. 15 dispatched, 14 merged, 1 merge ABORTED, **0 live at exit**.

`main` is **GREEN** and every worker was awaited. Verified at exit, not asserted:

```
git status --porcelain   → empty
bash .softhouse/conformance.sh → EXIT 0
  probe line count = 1   ← presence read BEFORE value (P-84)
  probe = up
  parity vectors PASS 46 / FAIL 0, 7884 cells
  all 11 wrong ledger implementations DIED through this harness
tasks.json in_progress   → []   (zero — no dispatch is left claiming to be alive)
```

---

## THE HEADLINE: the corpus moved, for the first time in several fires

**`T305` captured `LDG-05-openingbalance-accepted-empty-ledger`** — the accepting side of
`defineOpeningBalance`, HTTP 200, six journal entries — and it **kills `T296` arm A**, the port that
refused *every* opening balance while staying green on the whole corpus. `posted_non_contra_transaction_ids`
is no longer inert for grading.

| | before | after |
|---|---|---|
| ledger parity vectors | 4 | **5** |
| LEDGER money cells compared | 21 | **29** |
| registered wrong implementations | 9 | **11**, all killed |

**The standing oracle was never written to.** Driver-verified independently, before and after:
`acc_gl_journal_entry` **60 / maxid 64**, `acc_gl_closure` **0**, 26 distinct transaction ids,
`m_portfolio_command_source` **352**, `m_loan` 7, `m_office` 1 — identical to the fire-start baseline. No
container remains on 8444. The capture was taken on a **throwaway instance** built from the same image, and
the unlock was that tenant identifier, timezone and rounding mode are bound into Fineract's tenant liquibase
seed — so a fresh instance boots at `Asia/Ulaanbaatar` with **rounding mode 4 (HALF_UP)** and an empty ledger.

**It also corrected this store in three places.** An arm predicted 403 and got **200**:
`findNonContraTransactionIds` **excludes** contra-touching transactions, and every opening-balance entry
touches contra — so **opening balances do not block each other**; the oracle reverses the previous one and
posts a new one. Byte-identical bytes, one tenant, three answers in sequence: ACCEPT → ACCEPT-with-reversal →
REFUSE. `T320` found a **fourth** unannotated site, filed as `T322`.

---

## WHAT THE ORACLE DID, AND WHY NOTHING WAS PARKED

The fire opened with the oracle **UNREACHABLE** and Docker running — which the fire contract makes **T1's
job, not a park reason**. The fault was narrow: `fineract-db-1` had been healthy for five hours; only the app
container was missing. Brought up with `docker-compose-postgresql.yml` **alone**; the mariadb/mysql files were
never invoked. Asserted *before* starting: `org.postgresql.Driver`,
`jdbc:postgresql://db:5432/fineract_tenants`, and a prohibited-engine grep over all three env files and all
three compose files → **0 hits**. Healthy in **80 s**. Recorded in `reference-oracle.md`, with two facts that
will bite a script author: tenant id `gerege` maps to database **`fineract_gerege`**, and
`fineract_tenants.tenants` has **no `schema_name` column** in this build.

---

## FIVE WORKERS REFUTED THE DRIVER OR A PREDECESSOR. ALL FIVE WERE RIGHT.

1. **`T308` caught the driver's pre-flight.** It declared eight previously-dispatched branches *"gone or
   empty"* in a **pushed** commit. **All eight had commits** — 32, 11, 10, 7, 5, 4, and T297's "empty" branch
   had 4 including one named *"first commit before analysis (SIGTERM insurance)"*. Cause: a **lowercase glob
   against an uppercase convention**. Worse, dispatching lowercase names **created** case-shadowing refs —
   `packed-refs` is case-sensitive, the filesystem is not — and two lines had genuinely **diverged**. Closed
   by **`T312`**, which reproduced the numbers from a different instrument and made the refusal a git
   **`reference-transaction` hook** that aborts the ref creation itself.
2. **`T302` rejected `T309`.** Its *replacement* reconciler predicate reproduces the exact near-miss `T309`
   caught: **7 demotable, every one a live worker**. `T309`'s 8/8 matrix missed it because one cell passes a
   single commit as both lock and state-under-test, **freezing the clock**. Fixed by **`T319`**, whose new
   matrix **fails the whole run if no cell can see a re-dispatch**.
3. **`T316` refuted a task the driver filed with the conclusion in its title.** The "fail-open" is an
   **announced two-candidate fallback with a docstring saying so**. It fixed **nothing** — correctly, since
   repointing a forward-reference inside committed evidence is the in-place edit those guards forbid. Title
   corrected in `tasks.json`, original kept beside the refutation. → **P-95**.
4. **`T314` refuted its own brief.** `coverage_digest` *discards* the path, so the collision is
   container-blindness **by design**; the real defect is the canon's unescaped `;`/`=` join. → **P-94**.
5. **`T320` caught `T306` before it could land.** `T306` is **already written** and its narrowing would make
   LDG-05 **inadmissible and revive the mutant `T305` just killed**.

---

## THE DRIVER'S OWN ERRORS — ALL FILED, NONE BURIED

- The lowercase branch glob, and the case-shadowing it created. → `T312` (closed), observation note.
- **Reproduced the recorded backtick-injection defect** in the `T309` merge message; `` `fire` `` was
  command-substituted away. Corrected **forward**, not by force-pushing published history while workers held
  forks of it.
- Re-stamped the `fire` field; `T302` correctly called it **cosmetic and half-done**, and `T319` **deleted**
  the field.

---

## WHAT WAS ABORTED, AND WHY `main` IS STILL GREEN

**`T323`'s guard wiring was NOT merged.** The driver merged it **locally without committing** and ran the bar
itself: **EXIT 2 with ZERO probe lines** — under P-84 a failed HARD guard, *not* an oracle outage —
`guard_dead_path_frontier REFUSED rows=78 pinned=98 added=4 removed=24`.

Measured cause: **`.softhouse/toolchain` exists in the main checkout, has ZERO tracked files, and was ABSENT
in `T323`'s worktree**; **23 of the 24** vanished rows name it. So `T316`'s pin derives from **untracked host
state**, and wiring it HARD makes the bar's verdict depend on the machine — fatal in a program driven by
**two fires on different hosts**, and it presents as `exit 2, no probe line`, *the costume of a float
violation*.

The guard is **not** wrong to refuse; it caught a defect in its own pin on first contact with a second
machine. **The pin is the defect.** Branch intact and pinned at
`refs/rescue/20260827-230001/t323-wiring-branch`; retry is **`T326`**, told to start from that branch.

---

## NEXT FIRE PICKS UP, in this order

| Task | Why it is first |
|---|---|
| **`T324`** | **HIGH, live in committed code.** A worktree with live content is **destroyed** — three "independent" clean checks share one blind spot (an index skip bit) and fail together. |
| **`T326`** | Restart `T323` from its branch. One defect: make the frontier derive from **tracked content only**, and prove it with the toolchain present **and** absent. |
| **`T306`** | **BLOCKED.** Unblock condition is exact and recorded in its note: drop the refusal-kind precondition, and conformance must still show 11/11 dying with LDG-05 admissible. |
| `T310`, `T311` | Reverse the A2-02 declination (zero oracle contact — the bytes are on disk); wire the expiry guard. |
| `T313`, `T315`, `T317`, `T322`, `T325`, `T321` | Non-wiring content of the guard tasks, `T320`'s medium findings, the attestation adoption. |

**Standing hazard for whoever reads this:** three of `T287`'s four probes are **armed** (a1-02 armed
2026-08-24), and `acc_gl_closure` is **0**, so a2-01/a2-02 would POST two journal entries each. A posted
journal entry **cannot be deleted**. Read `.softhouse/capture/t287-closure-refusals/req/` — never POST it.

## Pause reason

**None — the fire finished its work.** Every dispatched worker was awaited and its output merged or pinned;
no worker was killed. Ended because the batch was complete with `main` green, not because of a token limit,
a quota error, or a gate. **No `user` gate was reached or crossed.**
