# T85 — independent adversarial review of `softhouse/T80-pathb-recipe-hardening`

Reviewer: T85, independent. I did not plan T80. Every material claim is tagged
`[VERIFIED: <how>]` or `[UNVERIFIED]`. Attacks I describe are attacks I ran; where I tried and
failed to break something I say so, because a failed attack is evidence too.

Branch reviewed: `softhouse/T80-pathb-recipe-hardening` (`352f623`, `813acb1`, `e45f2bf`), forked
from T76's head `9dbccf4`. Handoff read from the branch, diff read with three dots.
[VERIFIED: `git show <branch>:.softhouse/handoff/…/T80.md`, `git diff main...<branch>`]

**Method.** I did not run the attacks in the shared checkout. I exported the branch's `.softhouse`
tree to `/tmp/t85` (`git archive <branch> .softhouse | tar -x -C /tmp/t85`) and attacked that copy,
so every destructive result below is reproducible without any repository being modified. My own
worktree is clean after all work [VERIFIED: `git status --porcelain` empty].

---

## VERDICT: **MICRO-FIX**

**T80's two assigned P0s are genuinely closed.** I could not make the recipe pass on the wrong
tenant, at the wrong rounding mode, with a mutated canary, with a swapped canary, with a forced
output directory, with a caller-set pin constant, or with a path-traversing tenant id — under
either interpreter. The acceptance test stated in my brief is met in full, and the happy path is
intact and byte-identical to five earlier independently produced sets plus three of my own.

The MICRO-FIX is **two mechanical edits, 8 lines total, no number changed and no guard predicate
changed**, both listed as F-1 and F-2 below with the exact patch. F-1 is a defect **T80 introduced
this fire**: a wrong-tenant run of `attest.py` brands a *committed* capture directory with the wrong
tenant and destroys its transcript, before the gate, while printing "no capture attempted, no
attestation written". F-2 is **pre-existing on main**, not a T80 regression, but it is a guard in
the reviewed script that **dies instead of firing**, which is the exact failure class this task
exists to eliminate, and it is a two-character fix.

I did not apply either patch. My branch forks from `main`, which does not contain T80's versions of
`attest.py`/`preconditions.sh`; committing an edit to those files here would collide with T80's
branch at merge. Apply them on `softhouse/T80-pathb-recipe-hardening` (F-1) and to `main`'s copy
too (F-2, which is on both).

---

## PART 1 — the six required attacks. None of them broke it.

Every attack below was run against `/tmp/t85/.softhouse/capture/pathb/`, exported from the branch.
`sh` on this machine is GNU bash 3.2.57 in POSIX mode; `bash` is the same binary out of POSIX mode.

| # | attack | interpreter | exit | FAIL lines | captures written | forbidden sentence |
|---|---|---|---|---|---|---|
| 1 | `TENANT=default sh t36/recapture.sh` | `sh` | **1** | **5** | **none** | absent |
| 1 | same | `bash` | **1** | **5** | **none** | absent |
| 2a | mutated canary (`1162502.5`→`1162502.55`), gerege | `sh`/`bash` | **1** | **1** | n/a | absent |
| 2b | the same mutation on HALF_EVEN `default` | `sh`/`bash` | **1** | **5** | n/a | absent |
| 3 | swapped canary (`calc-pmode-gerege.json`, a committed valid non-tie) | `sh`/`bash` | **1** | **1** | n/a | absent |
| 4 | `TENANT=default RECAPTURE_OUT=…/t36/out/recapture-gerege` | `sh`/`bash` | **1** | 0 (refused before preconditions) | **none** | absent |

[VERIFIED: `/tmp/t85/a1-wrong-tenant.sh`, `/tmp/t85/a2-canary.sh`, both run twice with the recipe
interpreter as the argument; transcripts `/tmp/t85/o2a.txt o2b.txt o3a.txt o4.txt`]

Details that matter:

1. **Wrong tenant aborts and captures nothing.** `t36/out/recapture-default/` after the run holds
   exactly two files, `CAPTURED-FROM-TENANT` (contents `default`) and `preconditions.txt`. No
   `B-0*-raw.json` [VERIFIED: `ls` in the transcript]. Every file under `t36/out/recapture-gerege/`,
   `t76/out/recapture-gerege/` and the three `t80/out/` sets is byte-identical before and after all
   my attacks [VERIFIED: full-tree `shasum` snapshot `/tmp/t85/BEFORE.txt` vs `AFTER.txt`; the only
   differences are the three directories I name in F-1/F-3].
2. **The mutated-canary digest is `13ce2f4f21a1ad568b080b859682b9e995aac97712e00fcf44c6fc177d6b9ca5`**
   — the same `13ce2f4f…` T77 and T80 report, so my mutation is byte-for-byte theirs
   [VERIFIED: `shasum -a 256` of my own `sed`-produced file]. The breach message names **both**
   digests and states `THE CANARY WAS NOT SENT` [VERIFIED: transcript text].
3. **The canary really is not sent on a mismatch.** On `default` with the mutated canary the FAIL
   count is 5 — the same 5 environment breaches as the untouched run — i.e. the canary contributes
   no *result* line at all, not a failing one [VERIFIED: FAIL=5 both with and without the mutation
   on `default`].
4. **The `2>&1` is on the file actually grepped.** `recapture.sh` writes
   `> "$O/preconditions.txt" 2>&1` and greps `"$O/preconditions.txt"` — same variable, one file
   [VERIFIED: read of the script]. And the two operands are independently load-bearing: see I4.

## PART 2 — eight attacks T80 did not run. Two of them landed.

### I1 — the caller sets `PIN_CANARY_SHA256` to the mutated digest. **Refused.**
`PIN_CANARY_SHA256=13ce2f4f… CANARY_REQ=<mutated> sh t36/preconditions.sh gerege` → exit **1**,
1 FAIL, `DIGEST MISMATCH`, no HALF_UP sentence. The pin is a plain assignment that overwrites any
inherited value, so it is not an operand the caller reaches [VERIFIED: `/tmp/t85/a5-invented.sh`,
`/tmp/t85/i1.txt`].

### I2 — `PATH`-poisoned `shasum`. **Landed, but only with privileges that defeat everything.** (F-4)
A 2-line `shasum` stub earlier on `PATH` that always prints the pinned digest drives the mutated
canary to **exit 0, 0 FAIL, and the sentence `PASS effective rounding mode canary … (= HALF_UP)`**
on `gerege` [VERIFIED: `/tmp/t85/i2.txt`]. The recipe trusts `PATH` for `shasum`, `curl`, `docker`,
`grep` and `sed`; poisoning any of them defeats any precondition. I rank this **P3**, not a
rejection: it is the same class as T80's own disclosed limitation ("the pin is defeated by editing
the recipe"), and an operator who can do it can equally hand-write the transcript. It is worth
recording because unlike editing the recipe it leaves **no trace in a diff** — the resulting
transcript looks perfect and is committable.

### I3 — a wrong-tenant `attest.py` run on the name-check-**exempt** `emiloop` set. **Landed. (F-1)**
See finding F-1.

### I4 — neuter the grep operand: pre-create `preconditions.txt` as a symlink to `/dev/null`. **Refused.**
`TENANT=default RECAPTURE_OUT=/tmp/t85/sink-default sh t36/recapture.sh` with
`sink-default/preconditions.txt -> /dev/null` aborts with
`exit status 1, 0 FAIL line(s)` — the transcript operand counted **zero** and the run still died on
the exit-status operand [VERIFIED: `/tmp/t85/i4.txt`]. This is the strongest positive result in the
review: T80's decision to use *two* operands is not decoration, and I demonstrated the second one
carrying the abort alone.

### I5 — is `t80/forbidden-sentence.sh` a guard that can fire? **Yes, twice over.**
* As committed: **27 files scanned, 8 OK, 19 absent, 0 violations, exit 0** — reproduces the
  committed `t80/out/forbidden-sentence.txt` exactly [VERIFIED: `/tmp/t85/fs-asis.txt` vs the
  committed file].
* I planted a transcript containing the canary PASS on `tenant 'default'` → **VIOLATION, exit 1**.
* I planted the subtler one — the canary PASS on `tenant 'gerege'` but with **no** passing digest-pin
  line → **VIOLATION, exit 1** [VERIFIED: `/tmp/t85/fs-planted.txt`, `fs-planted2.txt`].
* **But it passes vacuously.** Pointed at a directory with zero transcripts it prints
  `violations: 0` and `RESULT: the HALF_UP claim is never made except on tenant gerege…`, exit 0
  [VERIFIED: `/tmp/t85/fs-empty.txt`]. A guard about guards with no floor on what it scanned. **P3,
  F-5.**

### I6 — file a real `gerege` capture inside a `default`-named tree. **Landed. (F-3)**
The name guard tests `basename` only.
`TENANT=gerege RECAPTURE_OUT=…/t36/out/recapture-default/sub-gerege sh t36/recapture.sh`
→ **exit 0**, four real captures written to
`t36/out/recapture-default/sub-gerege/` [VERIFIED: `/tmp/t85/i6.txt`, `ls` of the directory, and the
B-04 digest `c80f62b0…` matching every other set]. The leaf name and the stamp are truthful; the
*path* is not. A reviewer doing `ls t36/out/recapture-default/` finds capture bytes under a tenant
that did not produce them. **P2** — it needs an operator to supply a deliberately misleading path,
and the inverse direction (a `default` capture under a `gerege` name) is properly refused.

### I7 — TOCTOU: pinned file digested, different file POSTed. **Attempted, not achieved.**
`preconditions.sh` opens `$CANARY_REQ` twice — once for `shasum`, once for `curl -d @`. I ran a
background symlink flipper (`ln -sfn` alternating pinned/mutated, 4000 iterations) against 25 serial
runs of the script and **never won the race** [VERIFIED: `/tmp/t85/b5-toctou.sh`, "race attempts: 25
won: 0"]. A symlink pointing at the pinned file is accepted, correctly (exit 0, 0 FAIL). The
structural hazard exists; I could not exploit it and I do not claim it is exploitable.
`[UNVERIFIED: whether a faster flipper wins]`

### I8 — path traversal through `TENANT`. **Refused.**
`../gerege`, `gerege/../gerege`, `.` and `GEREGE` all die on
`TENANT='…' is not a valid tenant identifier (expected [a-z0-9_-]+)` before anything is created
[VERIFIED: `/tmp/t85/a5-invented.sh`].

### I9 / I11 — the second entry point, `attest.py`. **Refused on the pathb set.**
`ATTEST_OUT=…/recapture-gerege python3 t36/attest.py default` → exit 1, `ABORT: output directory …
is not named for tenant 'default'` — the same refusal `recapture.sh` gives, so the two entry points
do agree [VERIFIED: `/tmp/t85/i9.txt`]. `python3 t36/attest.py default` → exit 1,
`ABORT: preconditions breached — no capture attempted` [VERIFIED: `/tmp/t85/i11.txt`].

---

## FINDINGS

### F-1 — **P1, introduced by T80.** `attest.py` writes provenance and destroys a committed transcript *before* the gate, and says it did not.

`t36/attest.py` runs `preconditions.sh`, then — **before** testing `pre.returncode` — does
`os.makedirs(OUT)`, writes `CAPTURED-FROM-TENANT`, and overwrites `OUT/preconditions.txt`. The stamp
write is new code added by T80 (`git diff main...HEAD -- t36/attest.py`). On the `emiloop` capture
set, which T80 deliberately exempted from the directory-name check, `OUT` is the **committed**
`t36/out/emiloop/` holding 11 `gerege` EL-* captures.

Reproduce, two words, no override:

```
$ python3 t36/attest.py default emiloop
ABORT: preconditions breached — no capture attempted, no attestation written.
$ echo $?
1
```

What that run actually did [VERIFIED: `/tmp/t85/a6-attest.sh`, and the whole-tree digest snapshot
`/tmp/t85/BEFORE.txt` vs `AFTER.txt`]:

* created `t36/out/emiloop/CAPTURED-FROM-TENANT` containing **`default`** — the file whose entire
  purpose is to record which tenant a capture set came from, now recording the HALF_EVEN tenant over
  11 captures taken on `gerege`;
* overwrote the committed `t36/out/emiloop/preconditions.txt`
  (`4c3ff7f8c07e89d5a7e16b0d8e386b74a4b2c21e089052b546d336b9c51d1768` →
  `e0cf542d82d931293ac8b856b91c00547240f639556b5ed9d573d240130d3501`), replacing the transcript that
  evidences the captures were taken at `(19, HALF_UP)` with a breached `default` transcript whose
  first line reads `== T36 Path B preconditions, tenant 'default' ==`;
* left `attestation.json` untouched, still claiming `gerege`, so the directory now contradicts
  itself;
* and printed **"no capture attempted, no attestation written"**, which is true about captures and
  false about writes.

This is P0-B's family — an action that outruns the gate, and a capture set labelled with a tenant it
did not come from — surviving in the sibling entry point T80 edited this fire. T80 disclosed the
name-check exemption and wrote `[UNVERIFIED: whether it matters]`. It matters: the exemption is what
lets the pre-gate write reach a directory that already holds evidence. Secondary effect: the next
legitimate `python3 attest.py gerege emiloop` is then **refused** by the stamp check
("already holds a capture set taken from tenant 'default'") until someone hand-deletes the stamp.

**MICRO-FIX (mechanical, 6 lines moved, no number, no predicate).** In `t36/attest.py`, move the
`os.makedirs` / stamp / transcript writes to *below* the existing gate:

```python
# before                                     # after
os.makedirs(OUT, exist_ok=True)              if pre.returncode != 0:
with open(_stamp, 'w') as fh:                    sys.stderr.write(pre.stdout + pre.stderr)
    fh.write(TENANT + '\n')                      sys.stderr.write('\nABORT: preconditions breached …')
with open(os.path.join(OUT,                      sys.exit(1)
        'preconditions.txt'), 'w') as fh:    os.makedirs(OUT, exist_ok=True)
    fh.write(pre.stdout + pre.stderr)        with open(_stamp, 'w') as fh:
if pre.returncode != 0:                          fh.write(TENANT + '\n')
    sys.stderr.write(pre.stdout+pre.stderr)  with open(os.path.join(OUT,
    sys.stderr.write('\nABORT: …')                   'preconditions.txt'), 'w') as fh:
    sys.exit(1)                                  fh.write(pre.stdout + pre.stderr)
```

Nothing is lost: the abort branch already dumps the full breached transcript to stderr, and the
caller already redirects. After the move, a breached run writes **nothing**, which is what its own
message claims. `recapture.sh` has the same pre-gate `mkdir`+stamp, but there it is harmless — the
name guard runs first and no committed directory is reachable — so I do not ask for it to change.

`[UNVERIFIED]` I did not check whether a breached **pathb** run can overwrite the committed
`t36/out/recapture-gerege/preconditions.txt`; my attempt to force one (a stubbed `docker`) hit F-2
and crashed before reaching the writes, so the question is open in that direction. The fix closes it
either way.

### F-2 — **P1, pre-existing on `main`, not a T80 regression.** `preconditions.sh:114` — a guard that dies instead of firing.

```sh
*) bad "PostgreSQL version is '$pgv', pin is '$PIN_PG_MAJOR_MINOR…'" ;; esac
```

The variable reference runs straight into `…` (U+2026, bytes `e2 80 a6`) with no brace. bash parses
the `0xe2` as part of the identifier, and under `set -u` the script **aborts**:

```
t36/preconditions.sh: line 114: PIN_PG_MAJOR_MINOR<e2>: unbound variable
```

Measured, with P7 forced to fail (a stubbed `docker`), identical under `sh` and `bash`
[VERIFIED: `/tmp/t85/a9-p7death.sh`, transcripts `/tmp/t85/p7-sh.err`, `p7-bash.err`]:

| | broken (as shipped) | with the two-character fix |
|---|---|---|
| FAIL lines printed | **7** | **16** |
| P8…P15 executed | **no** | yes |
| canary lines in the transcript | **0** | 2 |
| `PRECONDITIONS BREACHED: n` summary | **never printed** | printed |
| exit status | 1 | 1 |
| `attest.py` behaviour | **`UnicodeDecodeError` traceback** — the truncated multibyte name breaks `subprocess.run(text=True)` | clean ABORT |

It is **fail-closed** — the exit status is still 1, so `recapture.sh` aborts and nothing is captured
— and that is why I rate it P1 and not P0. But the effect is that a single environment drift (the
PostgreSQL version, or the DB container being down) silently deletes the back half of the
precondition suite **including the entire rounding-mode canary**, replaces the breach summary with
one cryptic line, and makes the Python entry point die with a stack trace. On the branch it is
line 114; on `main` it is line 96, textually identical [VERIFIED: `git show
main:….../preconditions.sh | grep -n PIN_PG_MAJOR_MINOR`], so it must be fixed in both places.

**MICRO-FIX (mechanical, 2 characters, no number, no predicate):**
`'$PIN_PG_MAJOR_MINOR…'` → `'${PIN_PG_MAJOR_MINOR}…'`. I ran the patched script and it produces the
table's right-hand column [VERIFIED: `/tmp/t85/precond-fixed.sh`]. It is the only such construct in
the file [VERIFIED: grep for a `$NAME` immediately followed by a non-ASCII byte].

### F-3 — **P2.** The output-directory guard checks the basename, so the *path* can still name the wrong tenant.
`case "$Obase" in "$TENANT" | *-"$TENANT" )` in `recapture.sh` (and the `os.path.basename` twin in
`attest.py`) leaves an ancestor unconstrained. I6 above filed four genuine `gerege` captures at
`t36/out/recapture-default/sub-gerege/` with **exit 0**. The property T80 states in its header
comment — "A CAPTURE IS FILED UNDER THE TENANT IT WAS TAKEN FROM, STRUCTURALLY" — holds for the leaf
and the stamp, not for the path. Not a micro-fix (any repair changes the guard's predicate); a
follow-up.

### F-4 — **P3.** `PATH` is an unpinned operand. See I2. Recording it because it is the one bypass
that produces a *clean, committable* transcript with nothing in a diff to show for it.

### F-5 — **P3.** `t80/forbidden-sentence.sh` passes vacuously on zero files. See I5. Any repair
adds a predicate ("at least N files scanned, at least one OK"), so it is a follow-up, not a
micro-fix.

### F-6 — **P3.** `t36/out/recapture-gerege/` — the canonical committed capture set — carries **no**
`CAPTURED-FROM-TENANT` stamp [VERIFIED: `ls`]. The stamp guard therefore has nothing to compare on
the directory it most needs to protect; only the name guard applies there. T80's three new sets and
`recapture-default` are stamped. Consistent with T80's own "UNVERIFIED: necessity" note about the
stamp.

---

## PART 3 — T80's specific claims, checked rather than accepted

| claim | result |
|---|---|
| Canary pinned by **digest comparison**, two independently-sourced operands | **TRUE.** `shasum` at run time vs a literal the caller cannot set (I1). [VERIFIED] |
| On mismatch **the canary is not sent at all** | **TRUE.** `canary_pinned` gates P14c; on `default` the mutated run yields the same 5 FAILs as the clean run, i.e. no canary line either way. [VERIFIED] |
| Pinned file is genuinely a half-minor-unit tie | **TRUE.** `t22-audit/req/calc-pmode2-gerege.json` digests to `2a6621be…52154` = `PIN_CANARY_SHA256`; principal `1162502.5`, `interestRatePerPeriod 21.6` annual ÷12 = 1.8% → 1,162,502.50 × 0.018 = **20,925.045**, an exact tie. [VERIFIED: `shasum`, file contents] |
| …and it discriminates HALF_UP from HALF_EVEN live | **PARTLY.** I POSTed it myself: `gerege` → HTTP 200, `interestOriginalDue: 20925.05`. `default` → **HTTP 404** (its `productId 11` does not exist on that tenant), so on `default` P14 fails for a *provisioning* reason, not an arithmetic one. The 20925.04-under-HALF_EVEN half rests on T22's earlier observation, not on anything I or T80 measured this fire. [VERIFIED: `/tmp/t85/a0-canary-discriminates.sh`] `[UNVERIFIED: the HALF_EVEN limb, live]` |
| `t80/forbidden-sentence.sh`: 27 files, 0 violations, and not itself tautological | **TRUE**, and it fires on two different planted violations. Vacuous-pass caveat = F-5. [VERIFIED] |
| Gate tests exit status **and** greps a `2>&1` transcript, on the file actually grepped | **TRUE**, and I proved the exit-status operand aborts alone (I4). [VERIFIED] |
| Decoy `CANARY_EXPECT_OVERRIDE` is gone / inert | **TRUE.** With it set: 22 PASS, 0 FAIL, exit 0. [VERIFIED: `/tmp/t85/c4c.txt`] |
| Breach count on `default` with `CANARY_EXPECT=20925.04` is **6**, measured | **TRUE and measured by me independently.** 6 FAIL with the override, 5 without — the delta is exactly the `CANARY_EXPECT was set in the environment ('20925.04')` tripwire. Not adjusted to fit prose. [VERIFIED: `/tmp/t85/c4a.txt`] |
| Sidecar reads "revision **12** and **RATIFIED**", sourced not hard-coded | **TRUE.** `_status` = "…DEC-1 is at revision 12 and RATIFIED (gate G-1 CLOSED)"; `_dec1.revision` = 12 = `PIN.json:dec1_revision`; `_dec1.ratified` = true and `gates.md` carries exactly one `G-1 · **CLOSED — RATIFIED**` heading. `_closes` is gone, `_closed_by` present. `produced_by.task` = `T80` (not a stale `T36`). [VERIFIED: `/tmp/t85/b3-claims.sh`] |
| **Nothing promoted** | **TRUE.** `git diff main...<branch> -- .softhouse/vectors/` is **0 lines**. `contract.go` is not in the diff and still digests to `0db73d4a…f139` = `PIN.json:contract_sha256`. The whole diff is confined to `.softhouse/capture/pathb/` and `.softhouse/handoff/`. [VERIFIED] |
| Happy path: exit 0, 22 PASS / 0 FAIL | **REPRODUCED**, under `sh` and under `bash`, into my own directories. `ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.` [VERIFIED: `/tmp/t85/hp-sh.txt`, `hp-bash.txt`] |
| **1 distinct digest per capture id across six sets** | **REPRODUCED AND EXTENDED to nine.** [VERIFIED] |

Byte identity, computed by me over `out/`, `t36/out/recapture-gerege/`, `t76/out/recapture-gerege/`,
`t80/out/{recapture-gerege,bash-recapture-gerege,attest-gerege}/` and my three fresh sets:

```
B-01-baseline            9 sets, 1 distinct digest  713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009
B-02-multiplesof100      9 sets, 1 distinct digest  9de8757deeb02476d48e4c84a42b297cc99fab9a286adb505c005ab8d99d02f8
B-03-diycs-fullleapyear  9 sets, 1 distinct digest  892dd6f537ef34f50f6c46258d054e620565951e671b414184f0ffb9f7da58bf
B-04-diycs-feb29only     9 sets, 1 distinct digest  c80f62b01721ab15e994dcf7fca5d5f3f60ada39aa210ca45bbb67b65c724a80
```
[VERIFIED: `/tmp/t85/b2-identity.sh`]

I did **not** re-derive the money this fire. T77 re-derived B-01…B-04 from the pinned source at
0 minor units of disagreement; I relied on that plus byte-identity. My claim is about bytes, not
about arithmetic. `[UNVERIFIED by me: the amortisation itself]`

---

## PART 4 — fork-freshness, conformance, environment

**Conformance was run from my own worktree, forked from current `main`, invoked as `bash`:**

```
parity vectors    PASS 42   FAIL 0
contract-refusal  PASS 4    FAIL 0
self-test         PASS 1    FAIL 0
cells compared    5576 graded, 84 ungraded
invariant violations 0     harness errors 0
VERDICT: PASS (exit 0)
```
[VERIFIED: `bash .softhouse/conformance.sh`, exit 0]. This matches the driver's expectation exactly
(42 / 5576 / exit 0). T80's own `t80/out/conformance.txt` reports **36** parity vectors because its
fork point predates the merge that raised the corpus; I did not treat it as evidence about `main`
and neither should anyone else. **T80 added no vector, so the delta is entirely fork age.**

**Merge cleanliness.** `git merge-tree --write-tree main softhouse/T80-pathb-recipe-hardening`
returns a tree with **no conflict** [VERIFIED: exit 0, tree `81e1f5081af800a08d50e881c4514aa7a33f378f`].

**Leftovers.** Exactly what the handoff says, no more: `t36/out/recapture-default/` = 2 files
(stamp + breached transcript, **no** capture bytes), `t80/out/stamp-probe-default/` = 1 hand-seeded
stamp, three `gerege` capture sets under `t80/out/` [VERIFIED: `git ls-tree -r` of the branch].

**The oracle, before and after all my work** [VERIFIED: `docker ps`, `docker inspect`, `psql`,
`curl`]:

| | before | after |
|---|---|---|
| `fineract-fineract-1` | Up 2 days (healthy) | Up 2 days (healthy) |
| `fineract-db-1` | Up 3 days (healthy) | Up 3 days (healthy) |
| fineract `State.StartedAt` | `2026-08-18T09:51:53.088984338Z` | **identical** |
| db `State.StartedAt` | `2026-08-17T11:30:08.172024591Z` | **identical** |
| `actuator/health` | `{"status":"UP",…}` | same |
| `m_loan` gerege / default | — | **0 / 0** |
| `c_configuration.rounding-mode` gerege / default | — | **4/true, 6/true** (unchanged) |
| `m_product_loan` 1–4 (gerege) | — | `1\|NULL\|NULL`, `2\|100.000000\|NULL`, `3\|NULL\|FULL_LEAP_YEAR`, `4\|NULL\|FEB_29_PERIOD_ONLY` |

The `StartedAt` values are byte-identical to the ones T76, T77 and T80 recorded: no restart, no
rebuild, no `compose down`, no re-seed. Every request I sent was
`POST /loans?command=calculateLoanSchedule`, a pure calculation endpoint; the rest was read-only
`docker`/`psql`. Nothing else on the pinned Fineract checkout was touched.

---

## Follow-ups

1. **F-3, F-5, F-6** above — a guard-predicate change each, so a task, not a micro-fix.
2. **T77's F-1 is still open and T80 correctly declined it.**
   `.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh` carries the pre-hardening hole.
   T80's advice — replace the copy with a call to the original — is right, and F-1 above is the
   third instance of the same shape (two entry points that must agree, plus a copy). Converging
   `recapture.sh` and `attest.py` on one implementation (T80's own follow-up 3) would have prevented
   F-1 outright.
3. **F-2 must also be fixed on `main`**, where it sits at `preconditions.sh:96`.
4. A precondition suite that can be truncated by one of its own FAIL messages should assert its own
   completeness — e.g. a final "P15 reached" marker the caller greps for. That is a design task, and
   it is the general lesson behind F-2.

## What would have made me reject

If any of the six required attacks had reached exit 0, or if F-1 had written **capture bytes** —
rather than a provenance stamp and a transcript — into a directory naming a tenant that did not
produce them, this would be a rejection rather than a micro-fix.
