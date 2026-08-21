# T136 — independent review of T125 (`softhouse/T125-attest-canary-gates` @ `7a7acea`)

Reviewer branch `softhouse/T136-review-t125`, forked from `main` @ `e35ea7b`.
Reference oracle UP (`probe = up`), PostgreSQL `localhost:5432`, container
`fineract-fineract-1` **not restarted, rebuilt, re-seeded or reconfigured** — read-only
plus `POST /loans?command=calculateLoanSchedule`, which persists nothing. No
`docker compose` of any kind was run.

---

## VERDICT: **MICRO-FIX**

**Every load-bearing claim T125 makes, I reproduced independently, and none of them is
false.** The gate is real: I drove it red on the live `HALF_EVEN` tenant, green on the
ratified one, red under an absent-tool attack, and I separated the two gate layers by
experiment rather than by reading. The blast-radius ruling holds and is not a tautology —
I mutated each of its seven load-bearing operands and it went red on all seven.

The MICRO-FIX findings are **six residuals of the very class this task exists to close,
living in T125's own new tooling and in the file it modified**, plus two count/scope
corrections. None of them is exploitable in the shipped gate today; three of them are the
"value computed and never compared" shape, and one of them (F-5) I demonstrated **live** by
destroying and restoring a committed evidence file.

---

## 1. The `HALF_EVEN` JVM — re-measured, and one confound T125 did not close

### 1.1 One process, two tenants

```
$ docker inspect fineract-fineract-1 --format '{{.State.StartedAt}}'
2026-08-18T09:51:53.088984338Z
$ docker image inspect fineract:latest --format '{{.Id}}'
sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a

$ docker logs fineract-fineract-1 2>&1 | grep -F 'Initialized rounding mode'
2026-08-18 09:53:01.504 ... Initialized rounding mode for tenant `default`: HALF_EVEN
2026-08-18 09:53:01.711 ... Initialized rounding mode for tenant `gerege`: HALF_UP
```

Confirmed. Same `StartedAt` and same image id as every one of the five committed
attestations records.

### 1.2 My own measurement on the pinned exact tie — both tenants, both HTTP 200

```
$ shasum -a 256 .softhouse/capture/pathb/t22-audit/req/calc-pmode2-{gerege,default}.json
2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154  calc-pmode2-gerege.json
1461810087c56ba11ae3f37c705f8235fed35020e083c7e5a5beb1a9ac3bf902  calc-pmode2-default.json
```
Both match `attest_gate.PINNED_CANARY_BY_TENANT` exactly.

```
POST /loans?command=calculateLoanSchedule   (2026-08-21)
  Fineract-Platform-TenantId: gerege   -d @calc-pmode2-gerege.json   HTTP=200
  Fineract-Platform-TenantId: default  -d @calc-pmode2-default.json  HTTP=200

  gerege  period1 interestOriginalDue = '20925.05'   totalInterestCharged = '140457.89'
  default period1 interestOriginalDue = '20925.04'   totalInterestCharged = '140457.88'
```

Re-derived from the constants with `decimal` at the ratified `MathContext(19, …)` — no
float anywhere (P-25):

```
monthly rate  = 21.6/100/12 = 0.018
1162502.50 x 0.018 = 20925.04500      (exact, prec 19)
  HALF_UP   -> 20925.05
  HALF_EVEN -> 20925.04
```

**T125's discriminating observation is confirmed digit for digit.**

### 1.3 The confound T125 asserted but did not measure — I closed it

The two requests differ **only** in `productId` (11 on `gerege`, 10 on `default`). T125
asserts they are "the tenant's own twin of the same tie" without showing it. If the two
products were not identical, `20925.05` vs `20925.04` could be a *product* difference, not
a *mode* difference — and the entire task rests on that one observation.

```
to_jsonb(m_product_loan) — fineract_default id=10  vs  fineract_gerege id=11
   columns compared: 89   differing: 1
     id   default10=10   gerege11=11
```

**89 columns, the only difference is the primary key.** The divergence is attributable to
the tenant rounding mode and to nothing else. T125's claim is not merely reproduced, it is
now *established*.

---

## 2. THE FINDING THAT MATTERS MOST — confirmed, and extended from 4 shapes to 52

T125 reports that in its red run **all four** Path B captures came back
`matches committed corpus: True` on a `HALF_EVEN` JVM. Verified two independent ways.

### 2.1 T125's own committed red evidence, re-graded by me

```
.softhouse/capture/pathb/t125/red-pre-fix-default/attestation.json
  tenant default | ordinal 6 | JVM in force HALF_EVEN
  MathContext(19, HALF_EVEN) | matches_ratified: False
  canary HTTP 200 | answered '20925.04' | verdict 'MODE NOT CONFIRMED — see observed value'
  B-01 sha 713a35601b8909f4  matches_committed_corpus_bytes=True
  B-02 sha 9de8757deeb02476  matches_committed_corpus_bytes=True
  B-03 sha 892dd6f537ef34f5  matches_committed_corpus_bytes=True
  B-04 sha c80f62b01721ab15  matches_committed_corpus_bytes=True
```
I re-hashed those four body files myself against `pathb/out/*` — **4/4 byte-identical to
the committed HALF_UP corpus.**

### 2.2 My own live cross-mode sweep of the whole Path B request corpus

I posted **every** committed `calc-*.json` under `.softhouse/capture/**/req*/` (197 files)
to **both** tenants of the one running process and compared raw response bytes. Then I
discarded every comparison where the `productId` names a *different* product on the two
tenant schemas — because such a comparison measures the product, not the mode. (This
matters: 8 files did come back with differing bytes, and **all 8 are confounded** — e.g.
`calc-p06.json` addresses "T22 repro mult100" on `default` and "T22 probe p06-diycs-sarp-feb29"
on `gerege`.)

Products 1–4 were verified column-identical across `fineract_default` and `fineract_gerege`
(89 columns, 0 differing, for each of the four).

```
SOUND cross-mode comparisons (product row column-identical on both tenants):
  both HTTP 200, response bytes IDENTICAL : 52
  both HTTP 200, response bytes DIFFER    :  0
  not gradeable (non-200 on one tenant)   : 60

CONFOUNDED (productId names a different product per tenant) — no ruling possible:
  identical anyway 20 | differ 8 | non-200 57

The 52 sound, byte-identical shapes, by corpus:
   leapboundary/req            22
   pathb/t36/req-emiloop        9
   charges/req                  9   (the charge-free shapes)
   actualactual/pathb/req       8
   pathb/req                    4   (calc-B-01 … calc-B-04 — T125's four)
```

### RULING — is any Path B digest mode-sensitive at all?

**No. Not one.** Across 52 sound cross-mode comparisons on four different capture corpora,
**zero** response bodies differ between a `HALF_UP` and a `HALF_EVEN` JVM. T125's claim was
about four shapes; it holds over thirteen times that many, on shapes it never examined.

**The only mode-discriminating observation in the entire Path B apparatus is the pinned
`calc-pmode2-*` tie**, and it discriminates only because each tenant owns a column-identical
twin product. So the canary really was the sole alarm, and it really was the one thing
unchecked. **The fix is necessary, and it is sufficient as a gate.**

Three things this ruling adds that T125 did not state:

1. **Which shapes are mode-blind and why.** The four `B-0x` shapes use principal
   `1,200,000` at `1.8 %`/period — `21,600.00` exactly, never a tie. The tie has to be
   engineered (`1,162,502.50`); it does not occur by accident anywhere in the standing set.
2. **The T40 charge corpus is not merely mode-blind, it is structurally untestable by this
   method.** `m_charge` has **0 rows on `default`** and 18 on `gerege`, so 44 charge-bearing
   shapes return HTTP 404 on the `HALF_EVEN` tenant. `attest-t40.py`'s 22 committed captures
   are therefore neither shown mode-blind nor shown mode-sensitive by anybody — and
   correspondingly **`attest-t40.py` has no RED proof**: `drive-canary-red.sh` drives
   `t36/attest.py`, `drive-stale-fork.sh` drives `charges/bin/attest.py`, and nothing drives
   `attest-t40.py` against a wrong-mode tenant. Its gate is the same shared call and the
   self-test covers the logic, so this is a documentation gap, not a defect — but P-22 says
   name it.
3. **The graded parity corpus is not blind to the parameter, contrary to what "no digest
   carries one bit about the mode" invites you to conclude.** I scanned all 46 vector files:
   **0** contain `20925.05` or `20925.04`, so no *parity* vector discriminates the mode —
   but `vectors/loanschedule/REFUSE-02-half-even-ungraded.json` is a **contract-refusal**
   vector that requires an implementation asked to run at `HALF_EVEN` to refuse with
   `ErrNoDiscriminatingVector`, and cites this exact `20,925.05 / 20,925.04` observation in
   its own title. Conformance grades 4 contract-refusal cases, PASS 4 / FAIL 0. So a Go port
   cannot silently ship `HALF_EVEN` and pass — it must refuse.

   **Recommendation (backlog, not a T125 gap):** promote the pinned tie into the standing
   Path B set as a first-class parity vector at `(19, HALF_UP)`. It is already captured on
   every attested run as `canary-halfcent-raw.json` and is byte-identical across the T36,
   T76, T80 and T125 runs — it simply is not graded. That retires the corpus's dependence on
   a single canary, which is the durable answer to P-9.

---

## 3. The float in the guard — confirmed, and it was not merely cosmetic

Against the **pre-fix bytes** (`git show main:`), not the after:

| file (on `main`) | line | canary body parsed as |
|---|---|---|
| `.softhouse/capture/pathb/t36/attest.py` | `:273` | `json.loads(fh.read().decode())` — **binary float** |
| `.softhouse/capture/charges/bin/attest.py` | `:188` | `json.loads(fh.read().decode())` — **binary float** |
| `.softhouse/capture/charges/bin/attest-t40.py` | `:187` | already `parse_float=str` |

Two of three, exactly as reported — a float on a monetary path, inside the rounding-mode
check itself (P-25). The replacement is exact in all three: `parse_float=str`, and the
value is compared as exact text against a module string constant.

**It was not a purely stylistic defect.** Python's shortest-repr round-trips `20925.05` and
`20925.04`, so those two values survived — but the same code path loses trailing zeros:
a JSON `20925.00` becomes `20925.0`, which would not equal `'20925.00'`. The float was one
tie-value away from turning the gate into a false refusal.

`attest_gate.py` itself contains **no float, no division, no `float()`, no `round()`** — I
swept it; every decimal numeral in the file is inside a comment or docstring, and both
expectations (`EXPECTED_UNDER_HALF_UP`, `EXPECTED_UNDER_HALF_EVEN`) are string constants.

---

## 4. The fix — ordering and write-refusal proved by **experiment**, not by reading

Both properties are the ones worth the most, so I did not read them; I separated the two
gate layers and measured which one fires.

### 4.1 The unmutated RED run (live `default`, one labelled substitution)

```
$ bash .softhouse/capture/pathb/t125/drive-canary-red.sh t136-red-default
181c181
< if pre.returncode != 0:
---
> if False:  # T125 RED DEMO: OUTER precondition gate DISABLED
changed lines: 2

ATTESTATION REFUSED — the effective rounding mode is NOT the ratified MathContext(19, HALF_UP)
  * EFFECTIVE ROUNDING MODE IS NOT HALF_UP: ... answered period-1 interest '20925.04' ...
    That is exactly the HALF_EVEN answer. The process is running Fineract's STOCK DEFAULT ...
  * c_configuration.rounding-mode for tenant 'default' is 6, ratified ordinal is 4 (HALF_UP).
  * the running JVM initialized tenant 'default' at 'HALF_EVEN', not HALF_UP.
--- EXIT CODE: 4 ---
--- attestation.json was NOT written ---

output directory: CAPTURED-FROM-TENANT, canary-halfcent-raw.json, preconditions.txt,
                  scratch.diff, stderr.txt, stdout.txt   -> ZERO B-0x capture bodies
```

Exit 4 is uniquely the gate's — `grep -n sys.exit` in `t36/attest.py` gives only `1`s
(`:64 :73 :185 :351`), and `EXIT_MODE_UNVERIFIED = 4` exists only in `attest_gate.py:75`.
So the observation cannot have been produced by the gate never running.

Precise statement of "no captures spent": **no corpus capture body is written**; the
canary response, the provenance stamp and the precondition transcript *are* (they are the
observation and its provenance). T125's wording is accurate; this is the exact form.

### 4.2 The differential that proves the ordering claim (my own probe, not T125's)

I neutered **only** `assert_effective_rounding_mode` — leaving the document grader live —
and ran against the live `HALF_EVEN` tenant:

```
297c297,298
< attest_gate.assert_effective_rounding_mode(
---
> (lambda **kw: None)(  # T136 probe: FIRST gate neutered

ATTESTATION REFUSED — the attestation about to be written carries an unverified claim
  * effective_mode_canary.verdict is 'MODE NOT CONFIRMED — see observed value', not
    'HALF_UP confirmed behaviourally'.
  * effective_mode_canary.observed_period1_interest is '20925.04', not '20925.05'.
  * effective_math_context.matches_ratified_production_setting is False, not True.
--- EXIT: 4 ---
--- capture bodies present: 4 ---
--- attestation.json present: NO ---
```

**Four capture bodies appear** when the first gate is removed and **zero** when it is
present. That is the ordering claim measured, not read. And the second gate refuses
independently on live data: **no `attestation.json` claiming an unverified verdict can be
written even with the first gate gone.** The two layers are genuinely independent.

### 4.3 Attacking the gate — the four entry points and the P-33 trap

| attack | result |
|---|---|
| **absent tool** — `PATH=/usr/bin:/bin:/usr/sbin:/sbin` (no `docker`), ratified tenant | **REFUSED exit 4**, `PRECISION is None`, `ordinal is None`, `mode_in_force None`; **0 captures**, no attestation. The canary POST *succeeded* (curl present, answered `20925.05`) — the configuration clauses caught it. Defence in depth works in both directions. |
| **environment supplying the answer** | `CANARY_EXPECT`, `ATTEST_SKIP_MODE_GATE` both refuse (self-test cases 11–12, re-run by me) |
| **non-tie request (T77's tautology)** | refused by pinned-digest comparison |
| **zero input / empty file set** | **FOUND — F-1**, in `compare-bytes.py`. See §7. |
| **value printed but never compared** | **FOUND — F-2**, in `drive-canary-red.sh`. See §7. |
| **P-33 `grep`** | two bare `grep` in T125 shell scripts; both run under `/usr/bin/grep` (BSD) because they are inside scripts. `drive-stale-fork.sh:52` is verdict-bearing. Low risk (ASCII needle, and it precedes the em-dash on its line) but see F-9. |
| **mutation test of the self-test itself** | I neutered `attest_gate.refuse()` to a `return`: the self-test went from **22 cases, 0 failed** to **22 cases, 18 failed**. The self-test is a real discriminator, not a rubber stamp. |

---

## 5. Red and green, re-run in full

```
$ python3 .softhouse/capture/pathb/t125/gate-selftest.py        EXIT 0   22 cases, 0 failed
$ bash    .softhouse/capture/pathb/t125/drive-canary-red.sh …   EXIT 4   attestation NOT written, 0 captures
$ bash    .softhouse/capture/pathb/t125/drive-stale-fork.sh     EXIT 0   default->exit 4 refused; gerege-> not refused, dies at
                                                                         FileNotFoundError: charges/req/calc-B-01-baseline.json
$ bash    .softhouse/capture/pathb/t125/drive-canary-green.sh   EXIT 0
    t36/attest.py    EXIT 0, 4 captures, all matches-committed-corpus True
    attest-t40.py    EXIT 0, 22 captures + 1 observed refusal (XR-01 HTTP 403)
    byte-identical: 29   CHANGED: 0   no committed counterpart: 0
$ bash .softhouse/conformance.sh                                EXIT 0
    probe = up | parity vectors PASS 42 FAIL 0 | 5576 graded cells
    invariant violations 0 | invariant assertions 0 NOT RUN
```

Every number matches the standing constraint and T125's report exactly.

**Reproduction of T125's committed green evidence.** I stashed the two committed evidence
directories, re-ran the green driver, and diffed field by field:

```
green-t36-gerege/attestation.json : 185 fields, 5 differing — all *_at_utc timestamps
green-t40-gerege/attestation.json : 600 fields, 24 differing — all *_at_utc timestamps
every raw response body            : byte-identical
```

T125's green evidence reproduces on every non-timestamp field. I restored both directories
from the branch afterwards; `git status` is clean.

---

## 6. Blast radius — re-run and ruled independently

```
$ python3 .softhouse/capture/pathb/t125/blast-radius.py      EXIT 0
 charges/out/attested/            T40  2a6621be… HTTP 200  ANSWERED '20925.05'  HALF_UP  4
 pathb/t36/out/emiloop/           T36  2a6621be… HTTP 200  ANSWERED '20925.05'  HALF_UP  4
 pathb/t36/out/recapture-gerege/  T36  2a6621be… HTTP 200  ANSWERED '20925.05'  HALF_UP  4
 pathb/t76/out/recapture-gerege/  T76  2a6621be… HTTP 200  ANSWERED '20925.05'  HALF_UP  4
 pathb/t80/out/attest-gerege/     T80  2a6621be… HTTP 200  ANSWERED '20925.05'  HALF_UP  4
 5 committed attestations graded, 0 not clean
 distinct container StartedAt: 2026-08-18T09:51:53.088984338Z
```

I confirmed `2a6621be…` is `calc-pmode2-gerege.json` by `shasum` (§1.2), confirmed
`StartedAt` and image id by `docker inspect` **today**, and measured that same process at
`HALF_UP` **today** (§1.2). The attestations were taken from the process I just measured.

**Is the grader itself a tautology?** No — I mutated each of its seven load-bearing operands
in a mirrored copy (no committed byte touched) and required a NOT-CLEAN verdict:

```
  PASS tamper: the HALF_EVEN answer            -> exit 1
  PASS tamper: a non-tie canary request digest -> exit 1
  PASS tamper: canary never answered           -> exit 1
  PASS tamper: DB ordinal 6 (HALF_EVEN)        -> exit 1
  PASS tamper: PRECISION 12                    -> exit 1
  PASS tamper: JVM init line says HALF_EVEN    -> exit 1
  PASS tamper: a different oracle image        -> exit 1
  7 mutations, 0 not detected
```

**No attestation byte was edited by T125** — confirmed:
`git diff --stat main...softhouse/T125-attest-canary-gates -- charges/out pathb/t36/out
pathb/t76/out pathb/t80/out capture/out` is **empty**. And the branch's whole footprint
outside its own new directories is exactly the three files it claims:

```
.softhouse/capture/charges/bin/attest-t40.py
.softhouse/capture/charges/bin/attest.py
.softhouse/capture/pathb/t36/attest.py
```
No vector JSON, no `PIN.json`, no `capabilities.json`, no `gates.md`, no `conformance.sh`,
no `preconditions.sh`, nothing under `nexus/`.

### RULING

**Concur: no committed sidecar attestation was taken on a non-`HALF_UP` JVM.** The
erratum T125 asks for is owed and correctly worded — the numbers stand, the process that
produced them did not. All four downstream citations verified at the exact file:line
(`reviews/t41-probe/edit.py:46,52-53`, `capture/charges/bin/t46-defvsreq.py:21`,
`reviews/t45-probe/t45_extra.py:314`, `reviews/t47-probe/t47_extra.py:314`); note they cite
the attestations for **PRECISION = 19**, which is independently sound (javap over the
deployed bytecode), so the erratum is about provenance and not about any number.

---

## 7. Findings

### F-1 — MICRO-FIX (P2). `compare-bytes.py` exits **0** having compared **zero files**

`.softhouse/capture/pathb/t125/compare-bytes.py:41-72`

```
$ python3 compare-bytes.py
  --
  byte-identical: 0   CHANGED: 0   no committed counterpart: 0
EXIT=0
$ python3 compare-bytes.py /tmp/t136/does-not-exist
  byte-identical: 0   CHANGED: 0   no committed counterpart: 0
EXIT=0
```

`main(dirs)` returns `1 if diff else 0`, so an empty argv, a typo'd path or a directory that
was never created all produce a clean exit and a reassuring "0 CHANGED" line having verified
nothing. This is `patterns.md`'s own rule verbatim — *"a guard that inspects zero files must
be an error, not a pass"* — inside the task whose subject is that class.

Mitigated, not excused: `drive-canary-green.sh` always passes two directories it has just
created, so **the green proof itself is sound**, and `README.md:22` documents the script as
"called by `drive-canary-green.sh`". But it is a committed, named, reviewer-facing checker.

**Fix:** `if not dirs: sys.exit(2)` and `if same == 0 and nocounterpart == 0: sys.exit(2)`.

### F-2 — MICRO-FIX (P2). A value printed against a hard-coded expectation and never compared — in the red driver

`.softhouse/capture/pathb/t125/drive-canary-red.sh:42-43`

```sh
nchanged=$(diff "$T36/attest.py" "$SCRATCH" | grep -c '^[<>]')
echo "changed lines: $nchanged (expect 4 = 2 substitutions x <old + >new)"
```

Nothing compares `$nchanged` to `4`, and on the post-fix script it prints
**`changed lines: 2 (expect 4 …)`** — the script emits its own contradiction and continues.
T125's handoff §3 explains why the number is 2 (the fixed script picks the canary by tenant,
so the second `sed` is a no-op), so the *claim* is sound. The *shape* is precisely the one
being closed: computed, printed, gated nothing. If a future edit added a third substitution,
`nchanged` would silently become 6.

**Fix:** compute the expectation from the number of `-e` clauses that actually matched, or
assert `[ "$nchanged" -eq 2 ] || exit 1` with the reason on the line above.

### F-3 — MICRO-FIX (P2). `assert_attestation_is_verified` is type-strict on one field and type-loose on the other

`.softhouse/capture/lib/attest_gate.py:224-231`

Measured (module imported directly, live):

| document | result |
|---|---|
| `captures: []` (zero captures) | **ACCEPTED** |
| `captures` key absent entirely | **ACCEPTED** |
| `matches_committed_corpus_bytes: 'False'` (the **string**) | **ACCEPTED** |
| `matches_committed_corpus_bytes` key missing from the capture | ACCEPTED, reported as "no counterpart" |
| `matches_ratified_production_setting: 'True'` (the string) | REFUSED exit 4 |

The mode field is graded `is not True` — correctly strict. The per-capture identity field is
graded `is False`, so **any non-`False` value passes, including the string `'False'`**, and a
document with no captures at all passes. Not exploitable today: all three sidecars assign a
real `bool`/`None`
(`t36/attest.py:365`, `charges/bin/attest.py:286`, `charges/bin/attest-t40.py:302`), and
`CAPTURES` is never empty (`t36/attest.py:90`). Latent, and the asymmetry is exactly how a
guard drifts.

**Fix:** grade the identity key with the same strictness — anything that is neither `True`
nor `None` refuses — and refuse a document whose `captures` list is empty.

### F-4 — note (P3). `json.load` without `parse_float=str` in two analysis scripts (P-25)

`blast-radius.py:50`, `gate-selftest.py:84`. **Measured, not asserted:** loading all five
committed attestations without `parse_float` materialises **0 Python floats** — the sidecars
serialise every money value as a string — and none of the seven fields the grader compares is
numeric-money. So this is latent, not live. It becomes live the day any attestation field is
written as a JSON number. One token closes it.

### F-5 — MICRO-FIX (P2). T85's F-1 is still live in `attest-t40.py`, and T125's "what else is unfixed" list omits it

`.softhouse/capture/charges/bin/attest-t40.py:115-121` — `os.makedirs(OUT)` and the
`preconditions.txt` write happen **before** the `pre.returncode` check. T80 fixed exactly this
in `pathb/t36/attest.py` (commit `8d6be94`, "attest.py's gate now runs before any write"); the
charges fork never received it, and T125 modified this file without noticing.

**Demonstrated live, then restored:**

```
$ shasum -a 256 charges/out/attested/preconditions.txt
4c3ff7f8c07e89d5a7e16b0d8e386b74a4b2c21e089052b546d336b9c51d1768
$ python3 charges/bin/attest-t40.py default
  ... ABORT: preconditions breached — no capture attempted, no attestation written.
EXIT=1
$ shasum -a 256 charges/out/attested/preconditions.txt
b74409be1cce491a984f8cd2fb5bf0f0d557b0c534f693fc0b161aabfccf8add     <-- OVERWRITTEN
$ git status --short charges/out/
 M .softhouse/capture/charges/out/attested/preconditions.txt
```

The run printed *"no capture attempted, no attestation written"* while having already
replaced the committed evidence transcript of a `gerege` capture set with a `default`-tenant
transcript. That is T85's F-1 verbatim — *"the message was true about captures and false about
writes"* — and `attest-t40.py` also has no `CAPTURED-FROM-TENANT` stamp, so nothing else
would have caught the cross-tenant filing. I restored the file from the branch
(`4c3ff7f8…`, `git status` clean).

T125's §5 lists three things the charges copies never received (no `ATTEST_OUT` — which T125
itself then added, no provenance stamp, and the `CANARY_EXPECT` hole). **T85's F-1 is a
fourth, and it is the one that can destroy committed evidence.** Route it with F-6 of the
`preconditions.sh` work.

### F-6 — note (P3). The `CP_DIGEST` backlog: the count of 11 is right, the **symbol** reaches only 6

T125 §7 heads the item *"`CP_DIGEST` — 11 rigs"* and lists 11 file paths. The paths are
correct and the phenomenon count is 11. But scanning bytes directly (no `grep`, per P-33):

```
shell rig                                                     CP_DIGEST   inline
capture/actualactual/src/run-actualactual.sh                          2        1
capture/audit-t44/mathcontext/src/run-mathcontext.sh                  2        1
capture/audit-t44/mathcontext/src/run-mathcontext2.sh                 0        1
capture/audit-t44/rerun-periodratio/src/run-periodratio.sh            2        1
capture/mathcontext/src/run-mathcontext.sh                            2        1
capture/mathcontext/src/run-mathcontext2.sh                           0        1
capture/mathcontext/src/run-mathcontext3.sh                           0        1
capture/mathcontext/src/run-t50-tier1.sh                              0        1
capture/mathcontext/src/run-t50-tier2.sh                              0        1
capture/periodratio/src/run-periodratio.sh                            2        1
capture/periodratio/src/run-t46-periodratio.sh                        2        1

 named variable CP_DIGEST : 6      inline, UNNAMED form : 5      total : 11
```

Five of the eleven compute the same classpath digest **with no variable at all** —
e.g. `run-mathcontext2.sh:87`, `ok "classpath: … digest $(shasum -a 256 "$CPLIST" | awk …)"`.
This is T125's own declared blind spot #1 ("a guard that computes an ordinary local and
never compares it is invisible to both nets") landing inside the backlog entry that declares
it. **Whoever fixes this must not grep for `CP_DIGEST`: it finds 6 of 11.**

Confirmed clean: `EXPECTED_CP|PIN_CP|CP_DIGEST_EXPECT` → **0 occurrences repo-wide**.

`capturesCanonicalSha256`: **8 rigs confirmed** (`capture/src/run-pass3{b,c,d,e,f,g,h,i}.sh`),
computed and written into 8 attestations, **compared by no code** — the only comparators are
four README instructions. `PASS3B-REPORT.md:194` does say the digests make a re-run *"verified
rather than eyeballed"* while `README-pass3b.md:51` says *"Do not eyeball it. Compare
`capturesCanonicalSha256` …"*. The eyeball is the entire mechanism. T125's finding stands at
the exact cited lines.

### F-7 — nit (P3). "29 re-captured bodies" is 29 comparisons over 28 distinct bodies

`canary-halfcent-raw.json` is compared once from each of the two green directories, both
times against the same committed counterpart
(`t36/out/recapture-gerege/canary-halfcent-raw.json`). Visible in the driver's own output,
which prints that line twice. The claim "0 CHANGED" is unaffected.

### F-8 — nit (P3). Unconditional `rm -rf` on a repo path in a committed script

`drive-stale-fork.sh:63`: `rm -rf "$CHBIN/out"`. Safe **today** — I verified
`git ls-files .softhouse/capture/charges/bin/out` is empty and the directory does not exist.
It deletes whatever a future worker puts there.

### F-9 — nit (P3, P-33). Two bare `grep` in T125's shell scripts

`drive-stale-fork.sh:52` (`grep -q "ATTESTATION REFUSED"`) is **verdict-bearing** — it decides
"GREEN FAILED". `drive-canary-red.sh:42` (`grep -c '^[<>]'`) feeds F-2. Inside a script the
token `grep` is `/usr/bin/grep` (BSD), which goes blind to the remainder of a line at an
invalid multibyte sequence; `LC_ALL=C grep -aq` is the form this repo has settled on. Risk is
low here (the needle is ASCII and precedes the em-dash on its line, and `rc -eq 4` is checked
first), but a verdict-bearing grep should not be the one exception.

### F-10 — informational, and **in T125's favour**. The blast-radius scope of 5 is right, but the sentence invites a wrong reading

There are **14** committed files carrying a `HALF_UP` verdict, not 5:

```
5  produced by the three attest*.py sidecars               <- T125's scope, ungated until T125
8  capture/out/capture-prod3{b..i}-attestation.json        <- produced by run-pass3{b..i}.sh
1  capture/out/t35-rc6-rounddown-attestation.json
```

I checked whether the other nine are of the same defect class. **They are not.** All eight
pass3 rigs *do* gate the mode and abort:

```
run-pass3b.sh:167-169
  if not (mh['effectiveMathContextPrecision'] == 19 and mh['effectiveRoundingModeOrdinal'] == 4
          and mh['effectiveRoundingMode'] == 'HALF_UP' and mh['matchesRatifiedProductionSetting'] is True):
      sys.exit("RUN FAILED: effective MathContext is %r, not the ratified production …")
```
— `RUN FAILED: effective MathContext` present in all 8 of `run-pass3{b,c,d,e,f,g,h,i}.sh`.

So T125's scope is **correct**, and this note only asks that §4 say "five committed
attestations *produced by these three scripts*", because "five committed `attestation.json`
files" reads as "all of them" and a future P-34 register needs the distinction.
`t35-rc6-rounddown-attestation.json`'s generator: **[UNVERIFIED]** — not traced.

---

## 8. The three open questions, ruled

### 8.1 `charges/bin/attest.py` — **delete it**, in a separate task, not silently

The premise is verified independently:

* it is a **byte-identical** copy of `pathb/t36/attest.py@aafc8b3`
  (`diff` of `git show aafc8b3:` against `git show main:` → identical);
* it is **unrunnable** where it sits — I ran it: `FileNotFoundError: …/capture/charges/req/calc-B-01-baseline.json`;
* it has **produced nothing** — its `OUT` resolves to `charges/bin/out/…`, and
  `git ls-files .softhouse/capture/charges/bin/out` is empty;
* **nothing references it** except T125's own `drive-stale-fork.sh`/`README.md`, the
  `attest_gate.py` docstring, `t36/attest.py:38`, and the `tasks.json` backlog entry.

**Recommendation: DELETE, and delete `drive-stale-fork.sh` with it**, replacing both with two
sentences in the charges rig's README recording that the fork existed, that it was never
runnable, that it produced no artefact, and the sha `aafc8b3` from which it is recoverable.

**Reasoning.** Re-pointing is the worse option and it is worse for the reason this task
exists. Re-pointing means *maintaining a third copy* of a sidecar whose job `attest-t40.py`
already does for the same corpus — which is to deliberately recreate the P-21 fork hazard
that produced this defect in the first place. Every future hardening would then have three
files to reach instead of two, and the third is the one that cannot be driven end-to-end
(§2, limitation 2), so it is the one that will silently drift. "A file a future worker may
copy" is not hypothetical here: copying `t36/attest.py` is literally how this file came to
exist. Git keeps the history; a dead file in the tree buys nothing that `git show aafc8b3:`
does not.

**Why a separate task, not a MICRO-FIX to T125:** `charges/bin/` is held by T115 this fire,
and removing a committed script deserves the one line of review T125 correctly asked for
rather than a silent `git rm`. T125 was right not to do it.

### 8.2 `charges/bin/preconditions.sh:36` — the hole is REAL, demonstrated, and I did not fix it

```
$ sed -n '36p' .softhouse/capture/charges/bin/preconditions.sh
CANARY_EXPECT=${CANARY_EXPECT:-20925.05}

$ CANARY_REQ=…/calc-pmode2-default.json CANARY_EXPECT=20925.04 \
      sh .softhouse/capture/charges/bin/preconditions.sh default
  FAIL  c_configuration.rounding-mode = '6' in fineract_default — ratified value is 4 (HALF_UP) …
  FAIL  running JVM initialized tenant 'default' at a mode other than HALF_UP: … HALF_EVEN
  PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)
```

**A `PASS` line asserting `(= HALF_UP)` next to the `HALF_EVEN` answer, on a `HALF_EVEN`
JVM.** T76's hole verbatim, in the charges rig, today. Contrast `pathb/t36/preconditions.sh:35-54`,
which captures the inherited value one line *before* overwriting it
(`CANARY_EXPECT_ENV_ATTEMPT`) and pins the request by `PIN_CANARY_SHA256`.

**Blast radius, stated precisely.** The exploit turns the script's *strongest* clause — the
only behavioural one — into a tautology. It does **not**, on its own, produce a green
preconditions run on today's `default` tenant, because the DB-ordinal and JVM-init clauses
still FAIL; overall `fails` remains non-zero. The clause matters where those two cannot
help: a tenant whose configuration says 4 and whose log says HALF_UP but whose *effective*
arithmetic is something else — precisely the ambient/threaded distinction T42 and T51
established is real. There the canary is the sole discriminator, and `CANARY_EXPECT` disarms
it. **And since T125 landed, this no longer buys a green attestation**: the inner gate
forbids `CANARY_EXPECT` in the environment outright (`attest_gate.py:76-78`, self-test case
11), so defence in depth already contains it. **Not fixed here — T115 holds the file and
T137 is registered.** T125's routing note is correct and its worked reference
(`pathb/t36/preconditions.sh:35-54,185-217`, plus `PINNED_CANARY_BY_TENANT` for a per-tenant
pin table) is the right instruction.

### 8.3 Backlog counts — confirmed with one correction

* `capturesCanonicalSha256`: **8 rigs — CONFIRMED**, read by no code, comparator is a README
  instruction, and `PASS3B-REPORT.md:194` states the backwards claim at the cited line.
* `CP_DIGEST`: **11 rigs — CONFIRMED as a count of the phenomenon**, with the correction in
  F-6: the token itself appears in only **6** of the 11.
* `EXPECTED_CP|PIN_CP|CP_DIGEST_EXPECT` → **0 hits — CONFIRMED**.

---

## 9. `[UNVERIFIED]` — what I did **not** establish

1. **Whether any charge-bearing Path B shape is mode-sensitive.** Structurally untestable by
   tenant-crossing: `m_charge` has 0 rows on `default`, so all 44 charge shapes 404 there. My
   "0 mode-sensitive" ruling covers the 52 sound comparisons only; the 44 charge shapes are
   *not* in it. Closing this needs charges provisioned on a second tenant — a write to the
   shared oracle, which this task may not make.
2. **`attest-t40.py` has no live RED proof.** Its gate is the same shared call and the
   self-test covers the logic, but no run of that file against a wrong-mode tenant exists.
   Not attempted here (see 1).
3. **The generator of `capture/out/t35-rc6-rounddown-attestation.json`** and whether it gates
   its own `HALF_UP` claim. The eight pass3 rigs do; this ninth file I did not trace.
4. **T125's claim that pre-fix only `attest-t40.py` *printed* the verdict.** I verified the
   float defect against pre-fix bytes and the gate wiring post-fix, but did not separately
   diff the pre-fix print statements of all three.
5. **Post-merge behaviour (P-24).** I verified on the branch. Nothing in T125 asserts a
   post-merge property and nothing in it is baselined on a moving ref (its digests are
   literals and `blast-radius.py`'s file list is a literal), so I judged a scratch merge
   unnecessary — but I did not perform one.
6. **`nexus/` and the Go side.** Out of scope and untouched; T125 states the same limitation.

---

## 10. Standing-constraint compliance for this review

* Money handled as integer minor units / exact text throughout; every re-derivation used
  `decimal` at precision 19 (P-25). No float in any script I wrote.
* No `gofmt -w` anywhere; `contract.go` untouched (G-3).
* No vector JSON, `PIN.json`, `capabilities.json`, `gates.md`, `conformance.sh`,
  `preconditions.sh` or `nexus/` modified. Nothing promoted. **T125's fix not modified.**
* Files I temporarily wrote and then restored, each verified back to its committed digest:
  `charges/out/attested/preconditions.txt` (`4c3ff7f8…`, F-5), and the two
  `t125/green-*-gerege/` directories (green re-run). My three scratch output directories
  (`t136-red-default`, `t136-ordering-default`, `t136-nodocker-gerege`) were removed;
  `git status` on the review branch shows only this file and the T136 handoff.
* Oracle: read-only plus `POST /loans?command=calculateLoanSchedule` (pure calculation, no
  persistence). No container restarted, rebuilt, re-seeded or reconfigured; no
  `docker compose`. `container_started_at` is unchanged at
  `2026-08-18T09:51:53.088984338Z`, so the blast-radius evidence remains intact.
* `bash .softhouse/conformance.sh` → **PASS exit 0, 42 parity vectors, 5576 graded cells,
  0 invariant violations, 0 assertions NOT RUN, probe = up.**
