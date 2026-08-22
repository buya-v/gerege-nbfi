# RESUME manifest — gerege-nbfi Fineract→Go migration

**IN FLIGHT — DO NOT TAKE THE LOCK.** Local fire `20260822-060013` is LIVE with **five independent reviews**
running. Judge this lock by **push recency on `origin/main`**, never by `started_at` — see STEP 0, rewritten
this fire.

## Fire facts

- Host: Buyan's Mac. **Reference oracle (Fineract): REACHABLE** throughout at `https://localhost:8443`.
  PostgreSQL up. Pinned Fineract checkout `426a23544`. No prohibited engine port open.
- **Baseline BAR, driver-run at `c0e88c6` on the live oracle, before dispatch:** probe line **PRESENT**,
  reads `up`; **PASS (exit 0)**; 46 parity / 7884 cells; LEDGER 4 parity + 2 oracle-refusal / 21 money cells;
  all 9 census pins `== pinned`; fail-open frontier **11 == pinned 11**; 6/6 deliberately-wrong ledger
  implementations killed **through the harness**. Store `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`.
  Log at `.softhouse/capture/bar-baseline-20260822-060013.log`.
  **IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a `user` gate.**

## Five workers dispatched, five complete, ZERO merged — all in independent review

| Task | Branch @ tip | Shape |
|---|---|---|
| **T255** DEC-2 revision 8 | `softhouse/T255-dec2-rev8` @ `b334786` | +688/−185, 43 hunks |
| **T253b** harness portability | `softhouse/T253b-harness-portability-mac` @ `0208477` | **net ZERO lines** in `conformance.sh` |
| **T250** tenant attestation | `softhouse/T250-tenant-attestation` @ `d2b5772` | 130 files, purely additive |
| **T259** verdict predicate | `softhouse/T259-verdict-predicate` @ `8d72844` | 22 A / 0 M / 0 D |
| **T164** analyze7 float guard | `softhouse/T164-analyze7-float-guard` @ `f084819` | 2113 ins / 0 del |

Every branch scope-checked by the driver on the **three-dot** diff. **Every one is purely additive** — no
committed evidence file was modified anywhere in this fire. Store digest re-read live at every finish:
**unmoved all fire**.

Reviews live: **T260**←T255, **T254b**←T253, **T261**←T250, **T262**←T259, **T263**←T164.

---

# HEADLINE 1: THE CITATION-ROT MECHANISM IS FIXED, AND IT WAS PROVED ON A REAL COLLISION

`T255` was told to fix the mechanism, not the hunks — three passes in a row had shipped stale line numbers,
including revision 7's own *"re-measured"* ones. **It defied part of its brief and was right to.**

The brief suggested wiring a line-number checker into the automatic path. `T255` **measured that suggestion
and rejected it** (P-81): `verify-line-numbers.py`'s row list is **4 rows**, while DEC-2 carried **115**
`path:NNNN` citations, **90** into this repo — so wiring it *"would have enforced 4 of 90 while reading as
though it enforced all."* It would also have gone red on `T253`'s unrelated `mktemp` edits, and a gate with
that false-positive rate **is amnestied within two fires** — a life-cycle this harness already documents in
`FAILOPEN_PIN_FILE_LIST`.

It chose **ANCHOR** (citations bind to an exact unique substring, resolved by `git grep -n -F`) + **DERIVED**
(source properties written once in a fence, re-parsed and compared). **Elimination beats detection: an
anchored document is correct with nothing running.**

**Then it ran the collision for real rather than modelling it.** It took `conformance.sh` straight out of the
cloud `T253` branch (67 ins / 59 del) and re-ran both checkers: **revision 8's anchors all hold, exit 0**,
while `verify-line-numbers.py` goes **4 of 4 MOVED — including `:1300`, the definition row that had survived
every prior pass.** Under `T253`, revision 7 would have been wrong in **every** position.

**The document had already prescribed this exact remedy at revision 4 (`FU-A2-25-3`) and left it undone.
Revision 8 performs it.**

**Its own declared HIGH weakness, unprompted:** the checker is **HAND-RUN** — `conformance.sh` was `T253`'s
this fire — so it filed pre-written wiring instead of installing it. **T260 must rule on whether that is
mergeable.** Do not let "wiring written but not installed" read as installed.

# HEADLINE 2: THE DELIBERATE COLLISION PAID, AND IT DECIDES A MERGE ORDER

The driver put `T253` (edits `conformance.sh`) and `T255` (cites `conformance.sh` by line) in the **same
fire on purpose**, and told `T255` so. That is why the mechanism was tested instead of asserted.

**The consequence for merging is concrete.** Two `T253` implementations exist:
- **Mac** `T253b` — **net ZERO** line delta [driver-VERIFIED: 2617 lines before **and** after, every hunk
  in-place].
- **Cloud** `d7a7ea3` — **+72/−21, shifts every line below ~570.**

Merging the cloud diff would have rotted revision 8's citations **ON THE MERGE** — re-enacting `G-14` inside
the fix for `G-14`, in one fire. **Revision 8 is now indifferent to either**, but the finding stands and
`T254b` must quantify it.

# HEADLINE 3: THE LOCK RULE WAS REWRITTEN AND PASSED ITS FIRST LIVE TEST FOUR HOURS LATER

`started_at` is **not** a freshness signal: stamped once, it cannot tell *"the holder died five hours ago"*
from *"the holder has been working for five hours."* Raising the 6 h threshold trades one failure for the
other.

The cloud fire's proposal was a **heartbeat field**. **The driver implemented the heartbeat but refused it as
the primary signal**, on this program's own most-repeated evidence: a heartbeat is a thing somebody must
remember to refresh (**P-45**, five recorded instances — `manifest.py verify`, `t44_float_roundtrip_v3`,
T173's float guard, `guard_ledger_invariants`), and **decisively, it would have sat in the same UNPUSHED
commits that caused the incident** (`5f27983`, `ba2d8ed`, `d6dd8d0`) and changed nothing.

**STEP 0 now reads PUSH RECENCY on `origin/main` as authoritative** — derived from doing the work, not
maintained beside it. Four cases written out; wrapper patched; `zsh -n` clean.

**It was tested in anger the same day.** A second cloud fire read `origin/main`, saw this fire alive, **left
the lock alone and worked alongside**. Filed **`T265`** to attack the fix, including the obvious counter: a
fire that thinks for 6 h **without pushing** gets declared dead by the sign-flipped version of the same bug.

# HEADLINE 4: FOUR WORKERS CORRECTED A PUBLISHED FIGURE, AND ONE OF THEM CORRECTED THE DRIVER

- **`T259` corrected the driver's denominator: it is 6, not 9.** The `P2` key is **absent by design** on the
  three `RESCUED_BY_SITE3` rows. *"Five of nine"* would have been the wrong sentence and **the driver was
  about to publish it.**
- **`T250` corrected the population 3 → 4.** `cap10.sh` carries the identical defect and is the **NEWEST**
  link in the chain — minted by `T236` **after** `T163` and `T216` each audited it. Its larger finding
  dwarfs the one it was sent for: **50 scripts send a tenant, 5 attest it, 0 attest it derived, and 45
  attest NOTHING AT ALL** — worse than a literal, because there is no line to be wrong.
- **`T164` measured 742 sweep sites as UNMEASURED, NOT CLEAN**, and labels them that way everywhere.
- **The cloud's `T254` corrected the driver on method.** The driver briefed BSD as *"the arm only this Mac
  can execute."* The cloud settled it **from Linux**: it fetched Apple's `shell_cmds/mktemp/mktemp.c` — the
  actual source of `/usr/bin/mktemp` on this Mac — **compiled it**, and drove the fix against the real
  program, **12 OK / 0 FAIL**, confirming the ten-X template is **byte-for-byte the one BSD `mktemp` builds
  for itself** (`mktemp.c:166,168`). **Source you can compile beats a host you happen to be sitting on.**

# HEADLINE 5: TWO WORKERS REPORTED THEIR OWN WORK IS WIRED TO NOTHING, UNPROMPTED

`T164`'s AST guard and `T259`'s R-VPA rule are both **wired to no harness**, because `conformance.sh` was
held by `T253` this fire. **That is the P-45 shape both were written to remove** — for the sixth and seventh
recorded time. `T250`'s derived-attestation successor has **no caller** for the same reason. All three
labelled it **backlog, not completion**. Every reviewer is asked to rule explicitly on whether an unwired
guard may merge.

**`T253` had an invisible route to a green bar and did not take it** — `touch /tmp/t234_matrix2.txt` alone
makes the probe line appear. It refused to move the pin or weaken the guard. **That refusal is a credit and
must survive review.**

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.**

1. **Collect the five reviews and merge on their verdicts.** Merge order matters: **`T253b` (Mac, net zero)
   before `T255`**, then re-run the BAR on the **merge result** — never quote a worker's bar.
2. **`G-14` closes on `T260`'s verdict**, if it is RATIFY/MICRO-FIX. `T255` prepares, `T260` reviews, the
   **driver** ratifies. `T255` says the gate is closeable on this artefact but not by its own act.
3. **`T266`** — the linter patch must be re-proved against the **722-line** linter; `T253`'s 5/5 is a result
   about a file that no longer exists on `main`. **`T267`** — the toolchain-substitution notice is 32 lines
   on **stderr, 0 on stdout**, so the verdict block never says which Go compiled the money guard.
4. **`T265`** — attack the driver's own lock fix. **`T264`** — the cloud's `T241` branch is money-adjacent
   and **has had no reviewer at all**. **`T256`** — 30 instruments hardcode the Mac toolchain, and
   **`reference-oracle.md:616` PRESCRIBES it as the activation line** (T245's shape: inventory corrected,
   instruction left behind).
5. **Wire the three unwired guards** (T164's, T259's, T250's) once `conformance.sh` is free.
6. New backlog raised this fire: **B-1** — the same verdict/predicate defect on 3 rows / 4 pairs in
   `t219-g8-residual`, in no handoff, nobody having looked. **`FU-T255-2`** — ~70 bare `admit.go`/`vector.go`/
   `grade.go` basenames under `nexus/`, ambiguous between two packages as well as perishable.

**CONTENTION MAP** — `conformance.sh` → `T253`, `T257`, `T258`, `T226`, `T235`, `T160`, `T192`, `T195`,
`T266`, `T267`, plus the three wiring jobs. `capture/lib/` → `T250`, `T195`. `capture/tierA-a2/` → `T164`,
`T174`. `.softhouse/capture/` (whole) → `T145`. `gates.md` → `T241`(cloud), `T264`.

## What is NOT true, and must not be inferred from the green bar

**Nothing merged this fire at the time of writing. No vector was added — none is claimed. The store digest
did not move.** The ledger is graded on **six captured cases and no more**; accrual, account transfers
(gl 17), charge-off, multi-currency, opening balances, `GLClosure` and slot resolution are **ungraded**, and
the harness prints all eight not-graded rows. **Two of the 46 loanschedule vectors have
`principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **G-4, G-5, G-8, G-10, G-12 and G-14
remain OPEN; G-4 and G-5 are hard `user` gates.** **G-8's region is a conservative superset only**, resting
on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan — unconditionally, with
no expiry.** **Nothing was cut over, and nothing here authorises it.** The gate register at the top of
`gates.md` is authoritative.
