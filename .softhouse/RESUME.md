# RESUME manifest — gerege-nbfi Fineract→Go migration

## ⚠ IN FLIGHT — local fire `20260822-060013b` HAS SIX LIVE WORKERS AS OF THIS COMMIT

**Do not read this HEAD as a closed fire.** Written and pushed BEFORE the first worker was spawned, which is
the P-85 obligation: a HEAD saying "closed clean, zero live" while workers run is an active lie to the next
orchestrator, and no lock-freshness rule can read through it.

| task | role | branch | what |
|---|---|---|---|
| T273 | coder | softhouse/t273-* | the BAR's green depends on a 24-byte file in /tmp (HIGH, 4 confirmations) |
| T268 | coder | softhouse/t268-* | R-VPA rule fails open — REFUSED in the body, GREEN in the exit code |
| T274 | coder | softhouse/t274-* | T250's attestation verifier fails open four ways |
| T264 | reviewer | softhouse/t264-* | independent review of the cloud fire's T241 branch (df0aed2) |
| T265 | reviewer | softhouse/t265-* | independent re-derivation of the driver's own lock fix |
| T275 | test_writer | softhouse/t275-* | **ORACLE-ONLY** — the A2 captures §5 called "cheap next fire" and never took |

**Lock**: taken by push-recency. Prior lock `released_at` non-null → free (STEP 0 rule 1).
**Oracle**: REACHABLE, `https://localhost:8443`. Bar re-run by the driver at fire open: **PASS exit 0, probe
line PRESENT and reads `up`, 46 parity vectors / 7884 cells**. That green was contingent on `/tmp` residue
still being present on this un-rebooted host — which is exactly what T273 is dispatched to fix.

**Why a capture task exists this fire.** The pending queue was 21 tasks and every one was harness self-repair;
two consecutive fires added zero vectors; the ledger corpus is 6 vectors / 21 money cells against
loanschedule's 46. An oracle-reaching fire is the only fire that can capture, so this one spends it on that.
T275 captures RAW ONLY — promotion into `.softhouse/vectors/ledger/` and the population pins at
`conformance.sh:551-553` follow in a separate task, because T273 holds `conformance.sh` this fire.

---

# ⚠ READ THIS BEFORE QUOTING ANY PATTERN NUMBER (P-86)

**The STANDING INSTRUCTIONS block in the previous manifest was OFF BY ONE for `P-78`…`P-83`, and this fire
propagated the error into all ten worker prompts.** `patterns.md:2691` records that those six were
**renumbered on landing**; the renumbering reached `patterns.md` and never reached `RESUME.md`'s restatement
of it. **The corrected cardinal rotted in the place it was restated — which is `P-80` itself, committed
inside the manifest that teaches `P-80`.**

**Correct ids (verified against `patterns.md` at this commit):**

| Rule | Correct id |
|---|---|
| Evidence not missing, **UNREAD** — grep for who READS a prediction | **`P-79`** |
| A corrected cardinal rots wherever it was restated; make the second site READ the first | **`P-80`** |
| The fail-open guard caught three workers' own instruments — `git grep` exits 1 on NO MATCH, **>1 on ERROR** | **`P-81`** |
| Build the driver's suggestion, MEASURE it, report the zero | **`P-82`** |
| Reconcile two movements of a pinned number by RUNNING, never arithmetic | **`P-83`** |
| **"Exit 2 with no probe line" is the guard working — read the ABSENCE, not the value** | **`P-84`** |
| Two orchestrators held the lock; the cause was unpushed in-flight state | **`P-85`** |

**Materiality was LOW and the reason is the lesson: not one worker was misdirected, because every prompt
wrote the FULL RULE TEXT beside the id.** The number was decoration; the sentence carried the instruction.
**Cite the rule, or the id AND its sentence — never the id alone.**

---

# HEADLINE 1: G-14 IS CLOSED. DEC-2 REVISION 8 IS RATIFIED AND LANDED

Ratified by the driver under CLAUDE.md § Answering gates (DEC-n ratification is agent-decidable once the
contract passes an independent review clean; **Buyan may reverse it**). **Cutover, regulatory sign-off and
licence facts are untouched and remain hard `user` gates. This closure authorises NOTHING about the port.**

**`T260` earned the verdict by refusing to accept `T255`'s proof.** It measured that `T255`'s byte-identity
population was **chosen**, covering **18.2% of lines / 20.1% of characters** — four fifths of a ratified
contract rested on a modal-sentence diff **blind to obligations phrased without a modal verb**. It closed the
gap itself: an **exhaustive table-cell census — 140 rows before, 140 after, 0 removed, 0 added, exactly 4
changed, last cell only** (`I-7`'s `Idempotency-Key` cells byte-identical; all ten §5.3 precondition rows
byte-identical); a section map **derived from headings rather than chosen**; a 219-sentence non-modal
predicate against the author's 87 modal lines, **all 14 losses adjudicated by hand**; and an applier
re-derivation reproducing the landed blob **byte-for-byte**. **(P-90.)**

**Carried forward, NOT closed** — folded into **`T269`** as conditions on wiring:
- **`F-2`** — a **NON-UNIQUE** anchor yields 2 matches and `git grep` **exits 0**, and nothing flags it. So
  *"an anchored document is correct with nothing running"* is **overstated**; non-uniqueness is the new rot.
  A **deleted** anchor gives 0 matches and **exit 1** — loud, and strictly better than a rotted line number.
  Anchors are **worse** than line numbers under reformatting (one inserted space → ROT).
- **`F-1`** — the checker parses **22 of the document's 25** `[ANCHOR` tokens; two **live** anchors with a
  trailing `; MEASURED by …` are **silently unchecked**. Both resolve today.
- **`FU-T255-1`** — the checker is **HAND-RUN**. "Wrote the wiring" ≠ installed.
- **`C-8`'s class is not closed** — 38 bare citations survive, **disclosed rather than hidden**.

# HEADLINE 2: THE BAR'S GREEN DEPENDS ON A 24-BYTE FILE IN `/tmp` — `T273`, HIGH

**Driver-verified first-hand on merged `main`, both directions:**

```
rm -f /tmp/t234_matrix2.txt   ->  EXIT 2, probe-line count 0, "a HARD guard failed"
restore the file              ->  PASS exit 0, probe = up, frontier 11 == pinned 11
```

The file is created by **line 7 of the very instrument whose fail-open TIER depends on it**, so the harness is
green **iff that instrument has already been run on this host**. **macOS clears `/tmp` on reboot**, so the
first fire after a restart gets exit 2 with no probe line — this program's most dangerous signal.
**Every green bar recorded on this Mac was contingent on that residue**; the bar is not reproducible from a
clean checkout, and the bar grades everything else.

**`P-84` earned its keep the same hour:** the driver read the **ABSENCE** of the probe line, not its value,
and **parked nothing**. Under the older rule this would have parked every live vector task as somebody else's
server being down.

**Four independent confirmations** (cloud `T253`, `T254b`, `T261`'s F-11, and the driver). **It also settled
an author dispute in the loser's favour:** the Mac author called it *"a classification defect, not a frontier
defect"* since count and path-set match and the harness pins **by path**; `T254b` measured that **the pin also
carries the TIER token**. **The cloud author's refusal to move the pin to go green is vindicated — it had an
invisible route to green and did not take it. (P-88.)**

# HEADLINE 3: THE DELIBERATE COLLISION WAS A TEST INSTRUMENT, AND IT DECIDED THE MERGE ORDER (P-87)

The driver put `T253` (edits `conformance.sh`) and `T255` (cites it **by line number**) in **one fire on
purpose** and told `T255` so. `T255` then ran `conformance.sh` **straight out of the rival branch**: **anchors
exit 0, line numbers 4 of 4 MOVED, including `:1300`** — the definition row that survived every prior pass.
`T260` reproduced it under **both** implementations and found what neither author had: **at the untouched
merge-base the line-number checker is ALREADY 3 of 4 MOVED.**

**`T254b` put a number on the merge order: the cloud diff would have rotted 10 citations / 5 ranges / 17 live
line numbers — 100%.** Merged-cloud is **2669** lines; merged-mac is **2617**. Landing the wrong one first
would have re-enacted `G-14` **inside the fix for `G-14`**, in one fire.

# HEADLINE 4: FOUR CORRECTIONS AGAINST THE DRIVER

1. **Acted on a stale measurement.** `RESUME.md` said `T253`'s branch was destroyed; **true when measured,
   stale when acted on** (`P-69`). The driver dispatched a duplicate before fetching. Salvaged by redirecting
   the live worker to a peer branch rather than killing it — **never kill a live worker to tidy a mistake.**
2. **Mislabelled every dispatch** as *"`T251`'s C-1…C-8"*. **`T251` issued C-1…C-6**; C-7/C-8 were the
   driver's own labels, invented in the prompt and attributed to the reviewer. Caught by `T260`.
3. **Propagated an off-by-one pattern-id block** into all ten prompts (**`P-86`**, above).
4. **Expected only a Mac could settle the BSD `mktemp` arm.** The cloud settled it **from Linux** by fetching
   Apple's `shell_cmds/mktemp/mktemp.c`, **compiling it**, and driving the fix against the real program —
   **12 OK / 0 FAIL**, ten-X template byte-for-byte the one BSD `mktemp` builds for itself.
   **Source you can compile beats a host you happen to be sitting on.**

# HEADLINE 5: THREE ARTEFACTS SHIPPED WIRED TO NOTHING — ALL THREE SAID SO UNPROMPTED (P-89)

`T164`'s AST float guard, `T259`'s R-VPA rule, `T250`'s derived attestation: the **sixth, seventh and eighth**
`P-45` instances, each inside an artefact **written to remove `P-45`**. Cause: the scope guard **working** —
`conformance.sh` was `T253`'s.

**`T262` phrased the condition best, turning `T259`'s own argument back on it: "PROSE DOES NOT FIRE ON THE
NEXT FIRE."** So **`T268`…`T274` were filed BEFORE the branches merged, not promised after.**

## Reviewer findings that became blocking tasks

| id | finding |
|---|---|
| **`T268`** | `T259`'s R-VPA prints `REFUSED NIL COVERAGE` in its body while **exiting GREEN** — coverage measured per-file, gated globally. **BLOCKS wiring.** |
| **`T274`** | `T250`'s verifier checks **only the assertions that are PRESENT** — delete `body-sha256:` and a same-length body swap returns `VERIFIED rc=0`. Plus header-set-not-sequence, an exemption-list `known_keys`, and an **entirely unattested response leg**. **BLOCKS wiring.** |
| **`T270`** | `T164`'s superseded blind guard is **still invoked** at `reviews/A2-11/run-all.sh:36`. And `reproduces:` **accepts an absolute path OUTSIDE the repo** — a money guard licensed by a file nobody can review. |
| **`T271`** | B-1 in `t219-g8-residual`: agreement is **6 of 7, not 7 of 7**, and the failing row is the one `T259` did **not** flag. |
| **`T273`** | The `/tmp` residue defect, above. **HIGH.** |
| **`T272`** | Graft the cloud's `GEREGE_GO_STRICT` arm onto the merged Mac `go-env.sh` — `T254b`'s exact recipe. |
| **`T269`** | Wire all four unwired artefacts. Depends on `T268` + `T274`. |

## Other reviewer results worth carrying

- **`T263`** got **11 of 17 adversarial shapes past `T164`'s new guard**, including two it **named in its own
  output and graded `ok`** (`pf = float`; `parse_float=lambda s: float(s)`) — because
  `resolves_to_builtin_float()` compares against three literal source strings: **a source grep inside the
  file written to replace a source grep.** Bounded honestly to MEDIUM: none of those shapes exists in
  `tierA-a2` today.
- **`T262`** re-derived `T259`'s money claim **from the raw gz capture in integer minor units** and
  reproduced **3-of-6 / 6-of-6 to the unit**, then sharpened it: `interest = totalRepayment − principalRepaid`
  is **exact and unconditional**, while `n·E + B` is **conditional and holds only 4/6** — which is what makes
  6-of-6 non-vacuous rather than tautological.
- **`T261`** reproduced `T250`'s counts with a **wider** instrument (45 and 52/6/0/46 against 29/4 and
  50/5/0/45) and confirmed the **long-header wrap fix** across the whole boundary (1 → 4000 bytes). It states
  plainly that **the literal class was the smaller half by an order of magnitude**: 50 scripts send a tenant,
  **45 attest nothing at all**.
- **`T254b`**: the true `mktemp -t` population is **34 sites / 19 files, not 10**. The ten fixed are the only
  **BAR-executed** ones, so the scope was right — **21 stay latent on GNU**.

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** Zero tasks `in_progress`; zero live workers.

1. **`T273`** — the `/tmp` residue. HIGH, four confirmations, and it makes every bar on this host
   non-reproducible. Do this before trusting another green.
2. **`T268`** and **`T274`** — fail-opens **inside** two guards landed this fire. Both **block `T269`**;
   wiring a liar is worse than leaving it unwired.
3. **`T269`** — wire all four unwired artefacts once `conformance.sh` is free, fixing `T260`'s `F-1`/`F-2`
   in the same pass.
4. **`T270`**, **`T271`**, **`T272`**, **`T256`**, **`T264`** (the cloud's `T241` branch is money-adjacent and
   has had **no reviewer at all**), **`T265`** (attack the driver's own lock fix).
5. Then `T257`, `T258`, `T226`, `T235`, `T145` (denominator **438**), `T160`, `T164`-followups, `T174`,
   `T192`, `T195`, `T266`, `T267`.

**CONTENTION MAP** — `conformance.sh` → `T253`-followups, `T257`, `T258`, `T226`, `T235`, `T160`, `T192`,
`T195`, `T266`, `T267`, `T269`, `T273`. `capture/lib/` → `T274`, `T195`. `capture/tierA-a2/` → `T270`, `T174`.
`.softhouse/capture/` (whole) → `T145`. `gates.md` → `T241`(cloud), `T264`.

## What is NOT true, and must not be inferred from the green bar

**The ledger is graded on six captured cases and no more.** Accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances, `GLClosure` and **slot resolution** are all **ungraded**; the harness prints
all eight not-graded rows from the registry. **Two of the 46 loanschedule vectors have
`principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **`G-4`, `G-5`, `G-8`, `G-10`, `G-12`
remain OPEN; `G-4` and `G-5` are hard `user` gates.** **`G-8`'s region is a conservative superset only**,
resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan — unconditionally,
with no expiry.** **No vector was added this fire. Nothing was cut over, and nothing here authorises it.**
The gate register at the top of `gates.md` is authoritative.
