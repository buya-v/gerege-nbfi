# What the T352+T359 oracle movement actually invalidated — found by T363, not inherited

**Neither T352's list nor T359's list was reused.** T352 declared one casualty and it is misdescribed;
T359 declared four, of which one is overstated and one is incomplete. This file is a fresh search.

## Where I looked — this is a statement about the SEARCH, never about the world

Re-runnable: `bash instruments/casualty-sweep.sh`. Output committed at `out/CASUALTY-SWEEP.txt`.

- **Population:** `git ls-files .softhouse` = **7,996 tracked files** at repo commit `f6c83157`.
  Untracked files under `.softhouse/` when this task started: **0** (the 11 the sweep now reports are
  this task's own new files).
- **Engine and flags:** `git grep` with `-F` or `-E`, stated per selector. **No `\b` anywhere** —
  `git grep -E` reads `\b` as a literal `b` on this host and returns zero silently (T232).
- **Eleven selectors**, S1–S11, each printed with its own hit count split three ways: total, archived,
  live. The archive predicate is one regex, printed in the script, so a reader can disagree with it by
  reading it.
- **What I did NOT search:** anything outside `.softhouse/`; the `nexus/` Go tree (checked separately —
  the Go port opens no live database); binary artefacts. A selector not in `casualty-sweep.sh` was not
  searched, and that script is the record of that.

**Most hits are archived and are NOT casualties.** A conformance transcript, a psql dump, an `out/`
file — these are snapshots of a state the oracle has left, and going stale is what they are for.
Editing one to agree with today would forge a witness. The live set is small.

## A. Executable — the only sites where a program changes behaviour

**`t305` and `t327`, 5 sites; and T359's characterisation needs one correction.**

| site | what it does |
|---|---|
| `capture/t305-openingbalance-accepting-side/throwaway/capture.sh:77` | `[ "$now" = "$want" ] \|\| refuse "… STANDING ORACLE MOVED"` |
| `…/t305/throwaway/capture2.sh:59` | same |
| `…/t305/throwaway/down.sh:52` | same, sets `rc=1` |
| `capture/t327-closure-accepting-side/throwaway/capture.sh:82` | same |
| `…/t327/throwaway/down.sh:54` | same, sets `rc=1` |

`$want` is grepped out of `throwaway/out/STANDING-baseline.txt`, which pins
`acc_gl_journal_entry = 60/64`, `distinct_transaction_id = 26`, `m_portfolio_command_source = 352/352`
(t327 adds `m_loan = 7`, `m_office = 1`).

**THREE of those pins have moved, not two.** T359 named the first two.
**`m_portfolio_command_source` moved `352 → 359` as well**, and neither probing task's record names it
[VERIFIED: T363, live]. `acc_gl_closure 0/null`, `m_loan 7`, `m_office 1` are unmoved.

**CORRECTION to T359's blast-radius entry: "both rigs fail closed on their next run" holds only for a
STANDALONE invocation.** The supported entry point is `run-all.sh`, and step 0 of both `run-all.sh`
scripts does `rm -rf "$OUT"` and then **regenerates** `out/STANDING-baseline.txt` from the live oracle
before `capture.sh` or `down.sh` ever reads it
[VERIFIED: `t305/throwaway/run-all.sh:29,33` then `:53`; `t327/throwaway/run-all.sh:45,50` then `:70`].
So through `run-all.sh` the rigs are **unaffected**. Through `bash capture.sh` typed by hand against the
committed file, they refuse. The distinction matters because it changes what the right repair is.

### DECISION: retype nothing, delete nothing, do not convert the pin — fix the AGE

Three options were on the table.

- **Delete the rigs.** Rejected. `run-all.sh` is the *admissibility argument* for vectors captured on an
  instance that no longer exists ("the recipe being deterministic and committed",
  `t305/throwaway/run-all.sh:6-12`). LDG-05 and LDG-06/07 rest on it. Deleting the rigs destroys the
  evidence that makes promoted vectors admissible — a worse defect than the one being fixed.
- **Re-baseline: retype `60/64 → 71/75`, `26 → 31`, `352 → 359`.** Rejected, and this is the option the
  task warned about. `out/STANDING-baseline.txt` is not a pin a human maintains — it is a **capture
  output**, timestamped `2026-08-27T15:38:48Z`, produced by `guard-throwaway-isolation.sh` and committed
  as the transcript of that run. Retyping its numbers makes the file disagree with the run that produced
  it: a forged witness, and one that rots again on the very next probe.
- **Convert the pins to derived queries.** Rejected as stated, because it misidentifies the bug. The
  comparison is *already* derived on one side — `$now` is a live `SELECT`. The invariant these scripts
  actually want is **"the standing oracle did not move BECAUSE OF ME"**, which is a **delta across my own
  run**, not equality with a file of unknown age.

**RECOMMENDED REPAIR — a condition, not a new number.** `capture.sh` / `capture2.sh` / `down.sh` should
refuse a baseline that does not belong to the current run, instead of refusing a baseline whose numbers
have moved:

```sh
# after: [ -f "$BASE" ] || refuse "F5 no standing baseline at $BASE."
[ "$BASE" -nt "$RUNMARK" ] || refuse "F5 baseline at $BASE predates this run ($(head -1 "$BASE")).
  It is a transcript of an earlier run, not a fact about now. Re-run run-all.sh, which regenerates it."
```

where `$RUNMARK` is a file stamped at the start of the run. Fail-closed; never rots; no cardinal typed
anywhere; converts a *silent wrong answer* into a named refusal. **NOT APPLIED HERE** — `t305/` and
`t327/` are outside this task's write grant, which the driver narrowed to
`.softhouse/capture/t363-oracle-baseline/` and `.softhouse/reference-oracle.md`. Raised as a follow-up.

## B. Doctrine and generated report text — read as current, and WRONG

| site | claim | status |
|---|---|---|
| `.softhouse/vectors/capabilities-ledger.json:22` | *"gl 16 carries **SIXTEEN** journal entries, more than any other account"* | **STALE.** Live: **21**. T242 measured 16; T352 restated 16→20 at `:52` but **left `:22` untouched**; T359 then moved it to 21. |
| `.softhouse/vectors/capabilities-ledger.json:52` | *"the live count is now **TWENTY**, gl 17 is **FIVE** and gl 21 is **TWELVE**"* | **STALE.** Live: **21 / 5 / 13**. It went stale within the hour, by T359, inside the same fire. |
| `.softhouse/vectors/capabilities-ledger.json:90` | *"Every journal entry in the corpus is MNT"* | **Corrected in place by T352** with a long bracketed note; the headline sentence still reads MNT-only and the correction is ~1,400 characters downstream of it. |
| `.softhouse/reference-oracle.md:907, 917, 1001` | `acc_gl_journal_entry` at `60 rows / max id 64` | **Correct as history, stale as a statement about today.** Fixed by T363 with a superseding marker at each table plus a new derived-baseline section — *not* by retyping the historical figures. |
| `.softhouse/observations/20260827-chain2-standing-oracle-baseline.md:21-26` | six counters, three of which have moved | **Correct as a dated observation.** But its stated purpose is to make a *later* task's "I did not write to the standing oracle" claim checkable, so readers will treat it as a live reference. Needs a superseding pointer, not an edit. Outside this task's grant. |
| `.softhouse/capture/t327-closure-accepting-side/README.md:147` | `acc_gl_journal_entry = 60/64` in prose | **Stale**; historical prose in a completed capture's README. Low value, listed for completeness. |
| `.softhouse/reference-oracle.md:930` | *"the split **is** `156 PROCESSED / 194 ERROR`"* — **PRESENT TENSE, whole-table, live doctrine** | **MISSED BY T363's ELEVEN SELECTORS. Found by T367 as F3. Repaired by T371.** Live at 2026-08-28 was **162 / 197** [re-derived by T371, `.softhouse/capture/t371-t367-conditions/sql/q2-status-split.sql`]. The repair does **not** substitute today's pair — it deletes the cardinal, keeps the qualitative claim (*refusals are the majority*), and points at the derivation, because the replacement pair would be wrong by the next probe. |

**How eleven selectors missed it, stated plainly, because it is the more useful finding.** Every one of
S1–S11 hunts a **ledger** count — `acc_gl_journal_entry`, per-GL-account legs, currency. The missed site
was an **audit-table** count, three lines above the sentence this document quotes for correction #2. The
class is wider than either: *any cardinal about a live table, written in the present tense, in a file a
reader treats as doctrine.* T371 added **S12–S16** to `casualty-sweep.sh` to look for that **shape**
rather than for known strings, and drove that they now match the site
[`.softhouse/capture/t371-t367-conditions/out/DRIVE-SWEEP-FAILCLOSED.txt` § H: 3 hits after, **0** with
S1–S11 only]. T363's `[UNVERIFIED] that the 11 selectors are exhaustive` was the honest thing to write,
and it bit.

**And the sweep could not have told anyone.** T367's **F2**: `casualty-sweep.sh:39` discarded
`git grep`'s exit status, so a selector that **never ran** (rc 128) and a selector that **ran and matched
nothing** (rc 1) printed the identical `total=0 archived=0 LIVE=0`. A negative the instrument never
measured, inside the instrument whose own header cites T232. **Repaired by T371** in T238 `sweeplib.sh`'s
shape — status read, positive calibration, anti-calibration, and an exit contract
(`0` ran / `2` no corpus / `3` calibration failed / `4` a selector did not run). Driven in both directions:
BEFORE the two shapes are indistinguishable at exit 0; AFTER they are exit 0 vs exit 4
[same transcript, § A/B/C/D].

**All three `capabilities-ledger.json` rows are PRINTED BY THE HARNESS on every conformance run**, pass
or fail, as measured fact [VERIFIED: `out/BAR-conformance.txt:459-508`]. That is what makes them worse
than a stale comment — the report restates them with the authority of a run.

## C. T352's ONE declared casualty — misdescribed in three ways, and it is not a casualty

T352 wrote: *"Any query that previously asserted 'every row `currency_code = MNT`' (A2-15's
`sql/q4-a2-26-ledger-state.sql` did) is now false."*

1. **The path as written does not resolve from T352's own directory.**
   `.softhouse/capture/t352-a2-next-tranche/sql/` holds exactly two files,
   `q1-t352-residue-rows.sql` and `q2-t352-accrual-reachability.sql`. The file exists at
   `.softhouse/capture/tierA-a2/sql/q4-a2-26-ledger-state.sql` — a *different* capture directory, for
   which T352 gives no base path.
2. **It is A2-26's query, not A2-15's.** A2-15's is `q7-a2-15-ledger-state-json.sql`, same directory.
3. **NEITHER FILE ASSERTS ANYTHING ABOUT CURRENCY.** `q4` selects `j.currency_code` as one projected
   column among twenty; it has no `WHERE`, no filter and no aggregate over it [VERIFIED: read in full,
   T363]. `q7` emits `'distinct_currency_codes', (SELECT json_agg(DISTINCT currency_code) …)` at `:74` —
   **a projection, which re-run today correctly returns `["MNT","USD"]`.**

**So the MNT-only claim was never in SQL at all.** It lives in exactly two places: the **prose** at
`capabilities-ledger.json:90`, and the **captured output**
`.softhouse/capture/tierA-a2/out/A2-390-db-ledger-state-a2-15.json:109`
(`"distinct_currency_codes" : ["MNT"]`), digest-pinned in `MANIFEST.sha256`. The output is an archived
snapshot and **must not be edited** — it is a true record of 2026-08-22.

**The good news is buried in this finding.** The two SQL files are exactly the shape the whole problem
calls for: they **derive**, so they did not go stale, so they needed no correction. What went stale is
what was **typed into prose**. That contrast is the entire argument for
`instruments/oracle-state-baseline.sh`.

## D. Checked and NOT affected — verified rather than assumed

- **`bash .softhouse/conformance.sh` — PASS, exit 0**, 46 parity / 0 FAIL / 0 inadmissible, run *after*
  the movement (`out/BAR-conformance.txt`). The harness reaches the oracle at **one** place, an HTTP
  health probe at `conformance.sh:416`; it issues **no** SQL and opens **no** database connection
  [VERIFIED: grep for `psql`, `docker exec`, `fineract-db-1`, `5432` over `conformance.sh` → only the
  health-URL line]. So no graded figure can move because a row was added.
- **No promoted vector reads any of the five transaction ids.** Every ledger vector selects legs by an
  explicit `transaction_id`.
- **`guards/check-ledger-invariants.sh` and `guards/ledgerguard/`** walk the Go tree with
  `filepath.WalkDir` against a `git ls-files` floor. Neither opens the tenant database.
- **`gl 18` and `gl 22` remain at zero legs** — the pair `ledger.accrual.entry`'s argument rests on.
  Derived, not assumed: the instrument's per-account query returns an explicit `0` for each rather than
  relying on a `GROUP BY` that would simply omit the row.
- **0 floating-point columns** on `acc_gl_journal_entry` / `acc_gl_closure`; engine PostgreSQL 18.3.
  Both re-derived on every run of the instrument.

## E. One defect found in this task's OWN instrument, recorded because it is the same class

The first version of `oracle-state-baseline.sh` refused a wrong interpreter with
`[ -z "${BASH_VERSION:-}" ]`. **It admitted `sh`.** On this host `/bin/sh` *is* bash 3.2.57 in POSIX
mode, so it sets `BASH_VERSION` and the test passes. Driven, not reasoned:
`sh -c 'shopt -qo posix; echo rc=$?; echo $BASH_VERSION'` → `rc=0`, `3.2.57(1)-release`; the same under
`bash` → `rc=1`. Transcripts: `out/RED-3-wrong-interpreter.txt` (the version that admitted, exit 0) and
`out/RED-3b-wrong-interpreter-fixed.txt` (refuses, exit 3). The fix reads POSIX mode, with the non-bash
case handled first because `shopt` is a syntax error in dash — a guard whose own probe crashes on the
shell it exists to reject has refused nothing.

**A guard nobody has watched fail enforces nothing**, and this one was written by an agent that had just
read that sentence four times in this repository.
