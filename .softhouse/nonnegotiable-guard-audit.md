# Non-negotiable guard audit — T134

**Task:** audit **every** CLAUDE.md non-negotiable's guard and prove which ones can actually fail.
**Branch:** `softhouse/T134-nonnegotiable-guard-audit` · **Date:** 2026-08-21 · fire `20260821-080001`
**Reference oracle (Fineract):** UP throughout (`probe = up`, `https://localhost:8443/…/actuator/health`).
Nothing was restarted, rebuilt or re-seeded; every destructive experiment ran in `/tmp/T134`, a
`git archive HEAD` export. **This audit fixes nothing.** Every recommendation below is text for the
driver to route, because `conformance.sh`, `capture/charges/`, `capture/pathb/`, `capture/t91/`,
`capture/t74-multiplesof/`, `gates.md`, `nexus/…/emi.go` and `nexus/…/conformance/` are held by other
workers and three fixes (T125, T132, T133) are in flight.

---

## 0. Why this task existed, and what the set-as-a-set says

The fire found the same defect against three separate non-negotiables — money (T108 F-T108-1), the
ratified rounding mode (T109), and PostgreSQL-only (T99b F-5) — each by accident. The inference was
that it is systematic. **It is, but not in the shape the brief predicted.**

The defect is not "guards are broken". It is that **this program has two populations of guard and
only one of them was ever engineered**:

- **Population A — the graded path.** `conformance.sh` → the Go conformance binary → `admit.go` /
  `vector.go` / `generator.go`, plus the pass-3 capture scripts that produced the corpus. These are
  positive-equality assertions with explicit anti-vacuity clauses. Every one I attacked fired.
- **Population B — the shell/Python capture rigs and their "cross-check" mirrors.** These are
  *negative* assertions ("count of bad things == 0", "this variable is empty", "grep found nothing").
  **A negative assertion is vacuous on zero input by construction**, and every one of the three
  reported defects is an instance. So is every new one I found.

The single sentence that predicts a vacuous guard in this repo: **it tests that something is
ABSENT.** Population A tests that something is PRESENT AND EQUAL, and cannot be starved into passing.

The second systematic finding is worse than any individual row and is **not** about scripts at all:
`.claude/skills/softhouse-uat/SKILL.md:35-43` publishes a table headed **"HARD checks — must be
zero"** listing five checks. **Four of the five have no executable existence anywhere in the repo.**
A `/softhouse-uat` PASS is therefore read as certifying the ledger, holds and `Idempotency-Key` rules
when nothing has looked at them.

---

## 1. The register

Classification: **FIRES** = driven red here, discriminating · **VACUOUS** = can pass without checking
· **ABSENT** = no guard exists · **UNGATED** = verdict computed and reported but does not fail the run.
Paths are worktree-relative unless absolute. All line numbers are as of `8faee44`.

### 1.1 Money is integer minor units — no floating point

> *"No floating-point in any monetary code path, struct field, schema column, API field, or test
> fixture — including intermediate calculation."*

| # | Guard | file:line | Class | Command that drove it red / why not | Recommended fix |
|---|---|---|---|---|---|
| M-1 | `guard_no_float_in_vectors` | `.softhouse/conformance.sh:180-190` | **FIRES**, then **VACUOUS ×3** | RED: `printf '{"amount":1234.56}' > $STORE/x.json; bash .softhouse/conformance.sh` → `conformance: FLOAT-SHAPED NUMBER in …` exit 2. **Attack 1 (invalid byte, T108 F-T108-1 reproduced):** `printf '{"case_id":"T134-EVADE","x":\xff,"amount":1234.56}' > $STORE/T134-evade.json` → **exit 0, full PASS**, guard silent. Mechanism isolated: BSD grep, ambient `C.UTF-8` → rc 1; `LC_ALL=C` → rc 0; `-a` alone under `en_US.UTF-8` → rc 1; `LC_ALL=C` + `-a` → rc 0. **Attack 2 (zero files):** `STORE_ROOT` nonexistent → `find` errors, loop never runs, `return 0`. **Attack 3 (absent tool):** `PATH` without `perl` → `perl: command not found`, `pipefail` returns grep's 1, guard passes. | `LC_ALL=C perl … \| LC_ALL=C grep -aEq …`, **both tokens** (P-33: they defeat different programs). Add before the loop: `n=$(find "$STORE_ROOT" -name '*.json' -type f \| wc -l); [ "$n" -gt 0 ] \|\| { warn "…guard inspected 0 files"; return 1; }`. Add `command -v perl >/dev/null \|\| { warn "…perl absent"; return 1; }`. |
| M-2 | `guard_no_float_in_harness` | `.softhouse/conformance.sh:197-208` | **FIRES**, then **VACUOUS ×3** | RED: append `var rate float64 = 0.036` to a file under `nexus/internal/apps/loanschedule/` → `conformance: FLOATING-POINT IDENTIFIER in …`, exit 2. Same zero-file and absent-`perl` vacuity as M-1 (proved in `/tmp/T134/probe-entrypoints.sh`). **Third, worse hole below (M-3).** | Same three hardenings as M-1. |
| M-3 | **float LITERALS are invisible to BOTH no-float guards** | `.softhouse/conformance.sh:203` and `nexus/…/conformance/conformance_test.go:770-818` | **VACUOUS — new finding, the most serious money row** | Added to `nexus/internal/apps/loanschedule/`: `func t134InterestProbe(p int64) int64 { rate := 0.036 / 12.0; amt := rate * 1.0; return p + int64(amt) }`. Binary floating-point arithmetic on a money path, naming **none** of the forbidden identifiers. Result: `go build` **exit 0**; `go test -run TestNoFloatInTheLoanScheduleTree` **ok**; `bash .softhouse/conformance.sh` **exit 0**, zero `FLOATING-POINT IDENTIFIER` lines. Control with an explicit `float64` fired correctly (exit 2). | In `conformance_test.go:797-806`, reject the token as well as the identifier: `if tok == token.FLOAT \|\| tok == token.IMAG { t.Errorf("%s: floating-point literal %q: …", fset.Position(pos), lit); continue }`. **Verified free:** a token-stream scan of the current tree reports **0 float/imaginary literal tokens across 21 files**, so the fix is a no-op on today's code and closes the hole permanently. |
| M-4 | `RejectFloatTokens` — the guard that actually works | `nexus/…/conformance/vector.go:792`, called at `vector.go:767`, `admit.go:58`, `capability.go:110` | **FIRES** | RED: injected `"probe_float_t134":1234.56` into `loanschedule/P-00-baseline-6x7pct.json` → exit 2. **Immune to the M-1 evasion:** same float with a leading `\xff` on the line → shell guard silent, but Go reported `scanning for float tokens: invalid character 'ÿ'` and exit 2. It is JSON-aware, not byte-aware, so poison either makes the document invalid (caught) or lives inside a string (where it is not a number). | None. This should be described as *the* float guard; M-1 should be described as a redundant pre-check, not as coverage. |
| M-5 | Coverage limit of M-4 | `nexus/…/conformance/vector.go:822-838` (`LoadStore`) | **VACUOUS (scope)** | `LoadStore` reads only `*.json` **one level down, inside a context directory**. A `.json` at the store root that is neither `PIN.json` nor `capabilities.json` is never read by Go. Proved: `T134-evade.json` sat at the store root, was in the graded store (`store /tmp/T134/.softhouse/vectors`), and the run reported `inadmissible 0` and **`VERDICT: PASS (exit 0)`**. So for store-root files M-1 is the **only** float check, and M-1 is defeatable. | Have `LoadStore` return a `LoadError` for any unexpected `*.json` at the store root, or make M-1 non-vacuous (above). The former is stronger. |
| M-6 | No-float in **analysis scripts** (P-25) | `.softhouse/capture/charges/bin/selfcheck.sh:20-31` (S2/S3) | **ABSENT in practice** | The only such guard exists, checks the right thing (`float(`, `double`, `numpy`, `math.fsum`; and `parse_float=Decimal` on three named files), and **fails the run** (`bad()` → `exit 1` at `:49`). But (a) `$CH` is hard-wired at `:5` to `.softhouse/capture/charges` only, and (b) **nothing invokes it** — `grep -rn selfcheck` over the repo returns the file itself and one mention in `.softhouse/handoff/T40-charges-capture.md:648`. Live violation it does not cover: `.softhouse/capture/actualactual/analysis/discriminate.py:160` compares monetary values as `[float(g) for g in got] != [float(w) for w in want]` and then prints **"ALL n PERIODS REPRODUCED DIGIT FOR DIGIT"** — a money claim decided by binary-float equality, the exact P-25 shape that put 18-instead-of-22 into `gates.md`. Sweep: **74 of 240** `.py` files under `.softhouse/` call `json.load` with no `parse_float=`. | Promote S1-S6 out of `capture/charges/bin/selfcheck.sh` into a repo-wide `.softhouse/bin/guard-nonnegotiables.sh` invoked from `run_guards`, with `$CH` = `$REPO_ROOT`, an explicit file-count assertion, and `LC_ALL=C grep -a`. Separately fix `discriminate.py:160` to compare `Decimal(str(...))`. |
| M-7 | Floats in the **capture** tree | — | **ABSENT (correctly)** | **647 of 980** capture `*.json` carry a float-shaped number. That is *right*: a capture is a verbatim oracle body and Fineract returns `20925.05` as a JSON number. The defect is never the capture; it is the **read** side, i.e. M-6. Recorded so that a later sweep does not mistake this count for 647 violations. | None. Record the reasoning in `vectors/README.md` so the number is not re-litigated. |

### 1.2 PostgreSQL is the only database — Oracle Database / MySQL / MariaDB prohibited

| # | Guard | file:line | Class | Command that drove it red / why not | Recommended fix |
|---|---|---|---|---|---|
| D-1 | P5 prohibited-engine count in container env | `.softhouse/capture/pathb/t36/preconditions.sh:97-100` (identically `capture/charges/bin/preconditions.sh`, `capture/audit-t44/charges/bin/preconditions-COPY.sh`) | **FIRES**, but **VACUOUS on zero input** | RED, with a stub `docker` that reports an Oracle/MySQL container: `FAIL 2 prohibited-engine hits in container env`. **VACUOUS:** stub `docker` = `#!/bin/sh\nexit 0` → `grep -icE … ` over an empty stream is `0` → **`PASS  0 prohibited-engine hits in container env`**, having scanned nothing. Identical with `docker` absent (exit 127). T99b F-5 reproduced exactly. | Assert the input, not only the verdict: `env=$(docker inspect …); [ -n "$env" ] \|\| bad "docker returned no container env — P5 scanned nothing"` before counting. |
| D-2 | P6 prohibited driver jars in the jar | same file `:103-105` | **FIRES**, **VACUOUS on zero input** | RED with the stub: `FAIL 2 prohibited driver jars inside fineract-provider.jar`. VACUOUS with the silent/absent `docker`: **`PASS  0 prohibited driver jars in fineract-provider.jar`**. | Same: require a non-empty `unzip -l` listing (`[ "$(… \| wc -l)" -gt 50 ]`) before believing a zero count. |
| D-3 | P11 `schema_connection_parameters` must be EMPTY | same file `:154-158` | **VACUOUS — the only one with no compensating assertion** | A dead/absent `psql` returns `""`, and the assertion is `[ -z "$scp" ]` → **`PASS  schema_connection_parameters is empty`**. Unlike D-1/D-2 there is no positive twin anywhere in the script that would fail on the same starved input. It is a pure false PASS. | Two operands: `[ -n "$scp_raw" ] \|\| bad "psql returned nothing for schema_connection_parameters — P11 checked nothing"`, using a sentinel query (`select coalesce(x,'<empty>')`) so "absent" and "empty" are distinguishable. |
| D-4 | P5 Postgres-driver / P6 pg-jar / P12 port 5432 | same file `:92-95`, `:106-108`, `:158-161` | **FIRES** | These are **positive** assertions and they fail closed on every starved input: with `docker` silent or absent the block reports `fails=4`. This is why the *script* never produced a false overall verdict — only three false PASS **lines**. | None; hold them up as the pattern D-1/D-2/D-3 should follow. |
| D-5 | Repo-source scan for `ojdbc\|oracle\.jdbc\|:1521\|com\.mysql\.cj\|mariadb\|go-sql-driver` | `.softhouse/capture/charges/bin/selfcheck.sh:14-17` | **ABSENT in practice** | Correct pattern, real `exit 1` — but scoped to `.softhouse/capture/charges` and **invoked by nothing** (see M-6). | Fold into the repo-wide guard proposed in M-6. |
| D-6 | "A diff introducing a MySQL/MariaDB/Oracle driver or dialect is a rejection" | — | **ABSENT** | No CI, no git hook, no pre-commit config anywhere: `.github/`, `.gitlab-ci.yml`, `Makefile`, `justfile`, `.pre-commit-config.yaml` all absent; `/Users/buv/gerege-nbfi/.git/hooks` holds only `*.sample`. The rule is enforced by reviewer attention alone. | Add the D-5 pattern to the repo-wide guard, and run that guard from `run_guards` so `conformance.sh` — the one thing that is actually executed — carries it. |
| D-7 | DB engine on the path that produced the **graded corpus** | `.softhouse/capture/src/run-pass3*.sh` | **ABSENT (and immaterial)** | The 42 promoted parity vectors come from `capture/out/capture-prod3{b..i}-raw.json`, produced by `run-pass3*.sh`, which runs the seam class in a container **with no database in the loop at all**. There is therefore no DB assertion in that path and none is needed. | None. State it in the write-up so nobody adds a vacuous one for symmetry. |

### 1.3 Ratified tenant parameters — `HALF_UP` (ordinal 4), precision 19

| # | Guard | file:line | Class | Command that drove it red / why not | Recommended fix |
|---|---|---|---|---|---|
| R-1 | Capture-time gate on the graded corpus | `.softhouse/capture/src/run-pass3b.sh:149-152, 158-159, 166-170` (and siblings) | **FIRES** | `sys.exit("RUN FAILED: …")` on `ambientMoneyHelperPrecision != 19`, `ambientMoneyHelperRoundingModeOrdinal != 4`, `mathContextPrecision != 19`, `mathContextRoundingModeOrdinal != 4`, and on `matchesRatifiedProductionSetting is not True`. **This checks the ORDINAL 4 explicitly** and it is the gate every promoted vector passed through. Not driven red here (it would require re-running a capture against the shared containers, which the brief forbids); classified FIRES on the strength of an unconditional `sys.exit` with no starvable operand — every operand is a required key whose absence raises `KeyError`. | None. |
| R-2 | Admission | `nexus/…/conformance/admit.go:527, 545-571` | **FIRES** | Any mismatch → `bad()` → INADMISSIBLE → `Summary.Inadmissible > 0` → exit 2. An **empty** ambient MathContext is explicitly inadmissible, so it is not starvable. Corroborated in passing by the T134-EVADE runs, where an admission `bad()` produced `VERDICT: UNUSABLE (exit 2)`. | None. |
| R-3 | Runtime refusal | `nexus/internal/apps/loanschedule/generator.go:353-359` | **FIRES** | `ungraded(…)` on `SignificantDigits != 19`, `RateFactorScale != 19`, `Mode != HALF_UP`. | None. |
| R-4 | pathb effective-mode canary | `.softhouse/capture/pathb/t36/preconditions.sh:181-215` | **FIRES — the model to copy** | Hardened twice over by T76/T80: `CANARY_EXPECT` is a constant and an inherited value is itself a breach (`:53`, `:181-183`); the request is pinned by **digest comparison** `PIN_CANARY_SHA256` (`:44`, `:196-201`); and the canary is **not sent** unless both pins hold (`canary_pinned`). | None. |
| R-5 | **charges / audit-t44 canary — the same defect T76/T80 fixed, still live in two files** | `.softhouse/capture/charges/bin/preconditions.sh:36` and `.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh:36` | **VACUOUS — new finding** | `CANARY_EXPECT=${CANARY_EXPECT:-20925.05}` — env-overridable, and there is **no `PIN_CANARY_SHA256`** in either copy. Driven both ways against a stubbed `curl` playing a HALF_EVEN JVM (the live containers were never touched): default → `FAIL … returned period-1 interest '20925.04', expected '20925.05'`; then **`CANARY_EXPECT=20925.04 sh …` → `PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)`**. One environment variable turns the strongest assertion in the script into a green line asserting the opposite of the truth. Also open to T77's substring/request swap, since the request is unpinned. | Port `preconditions.sh:44` and `:53` and `:181-215` verbatim from `capture/pathb/t36/` into both copies — constant expectation, `CANARY_EXPECT_ENV_ATTEMPT` tripwire, digest pin, and `canary_pinned` so the PASS sentence is unreachable off the pinned tie. **P-27 applies to `preconditions-COPY.sh`:** it is a second copy of a document being corrected and should be deleted or regenerated, not patched. |
| R-6 | Attestation canary verdict | `.softhouse/capture/charges/bin/attest.py:337`, `attest-t40.py:377`, `.softhouse/capture/pathb/t36/attest.py:437` | **UNGATED** | All three compute `'verdict': 'HALF_UP confirmed behaviourally' if canary_p1 == '20925.05' else 'MODE NOT CONFIRMED — …'`, write it to `attestation.json`, print it, and **never** branch on it. Their only `sys.exit`s are for a breached `preconditions.sh` (`attest.py:96-98`) and a non-200 capture (`:240`). T109 confirmed. The real gate is therefore whichever `preconditions.sh` the script invokes — sound for `pathb/t36`, **defeatable** for the two `charges` scripts (R-5). | Two lines at the foot of each: `if att['effective_mode_canary']['verdict'] != 'HALF_UP confirmed behaviourally': sys.stderr.write(...); sys.exit(1)` — and the same for `matches_ratified_production_setting`. A verdict that is printed and not branched on is P-22's definition of a believed non-guard. |

### 1.4 The remaining non-negotiables

| # | Rule (CLAUDE.md) | Guard | Class | Evidence | Recommended fix |
|---|---|---|---|---|---|
| L-1 | *"The ledger is double-entry and append-only. Balances are derived, never written."* (`:14`) | — | **ABSENT** | No check anywhere for `UPDATE`/`DELETE` of a posted entry or assignment to a balance column. The three HARD guards run by `conformance.sh` are exhaustively `run_guards()` at `:239-250` — float, float, gofmt. `.claude/skills/softhouse-uat/SKILL.md:38-39` advertises two ledger checks under **"HARD checks — must be zero"** that have no executable form. | Until a ledger exists in Go there is nothing to grep; the fix now is **honesty**, not code — strike rows 2-5 from the UAT table or mark them `NOT YET IMPLEMENTED — no ledger in the Go module`. |
| L-2 | *"Holds … alter `available` only, never posted `balance`."* (`:14`) | — | **ABSENT** | Same. The word "hold" in `conformance.sh:671-741` is the invariant verb (`HOLD`/`violated`), unrelated to money holds. Named in `program.json:414` as the defect that failed review twice on the sister project — and it has no guard. | As L-1. Add the guard with the context that introduces holds, and drive it red in the same commit. |
| L-3 | *"`Idempotency-Key` is mandatory on every money-movement POST."* (`:15`) | — | **ABSENT** | Only prose, plus `contract.go:144, 2456` explaining why it does not apply to a pure schedule calculator. Advertised at `SKILL.md:41`. | As L-1. |
| O-1 | *"Fineract is the oracle and fallback."* (`:16`) | `.softhouse/conformance.sh:258-266` + the Go grader's `-oracle-probe` | **FIRES** | `CONFORMANCE_ORACLE_HEALTH_URL='https://127.0.0.1:9/nope' bash .softhouse/conformance.sh` → `probe = down`, `the reference oracle is UNREACHABLE`, **exit 2**. Also driven with a *reachable* URL whose body lacks `"status":"UP"` (`…/actuator/info`) → `probe = down`, exit 2 — so it keys on the health assertion, not on reachability. Non-vacuous: `probe_oracle` defaults to `down` on empty output. | None. |
| O-2 | Parity PASS must be earned | `nexus/…/conformance/conformance_test.go:820-860` (`parityPassViolations`) | **FIRES** | Four independent conditions per parity pass (implementation registered, class PARITY, provenance is an oracle capture, capture ref + seam named) plus a `counted != s.ParityPass` reconciliation. Not starvable — it iterates results and cross-checks a count. | None. |
| C-1 | *"Contract-first … the frozen adapter contract is the boundary."* (`:17`) | `nexus/…/conformance/admit.go:79-95` `VerifyContractDigest`, called `grade.go:237` and `conformance_test.go:42` | **FIRES** | RED: appended `\n// T134 probe\n` to `contract.go` → exit 2, *"frozen contract … digest 2c704947… does not match the store pin 0db73d4a…"*. **Attack (make the operand unreachable):** repointed `PIN.json:contract_file` at a nonexistent path → still **exit 2** (`os.ReadFile` error is returned, not swallowed). Not starvable. | None. |
| C-2 | `guard_gofmt` and the G-3 exemption | `.softhouse/conformance.sh:227-238` | **FIRES**, **VACUOUS ×2** | RED: appended `func t134Unformatted( ) {…}` to `conformance/grade.go` → `conformance: not gofmt-clean:` exit 2. **Attack 1 (exemption over-matches):** the filter is `grep -v "/contract/contract.go$"`, a **suffix** test, not the pinned path. Created `conformance/contract/contract.go`, unformatted; `gofmt -l` listed it and the filter dropped it — `conformance.sh` **exit 0** with an unformatted file present. **Attack 2 (absent tool):** `gofmt` off `PATH` → `2>/dev/null` and `\|\| true` swallow both the error and the status; the guard returns 0 with a known-unformatted file present. | Exempt the exact path: `\| grep -vFx "$NEXUS_DIR/internal/apps/loanschedule/contract/contract.go"`. And `command -v gofmt >/dev/null \|\| { warn "gofmt absent"; return 1; }`. Do **not** `gofmt -w` `contract.go` (G-3). |
| I-1 | Interpreter guard (exit 3) | `.softhouse/conformance.sh:70-104` | **FIRES** | `sh` → 3, `zsh` → 3, `bash --posix` → 3, each printing `WRONG INTERPRETER`. It is the first executable statement and feature-tests process substitution rather than the shell's name, so it is not starvable. | None. Best-engineered guard in the repo. |
| S-1 | *"Never describe member savings as insured, protected, or guaranteed."* (`:18`) | `.softhouse/capture/charges/bin/selfcheck.sh:36-38` | **ABSENT in practice** | Correct pattern, genuine `exit 1` — but scoped to `.softhouse/capture/charges` and **called by nothing**. No Cyrillic (`даатгал`) scan exists anywhere. Never scans `nexus/`. | Fold into the repo-wide guard (M-6) with `$CH = $REPO_ROOT`, add `даатгал\|баталгаа`, and exclude only this guard file by exact path. |
| S-2 | *"Names are three fields … never `first_name`/`last_name`."* (`:19`) | `.softhouse/capture/charges/bin/selfcheck.sh:32-34` | **ABSENT in practice** | Same: right pattern, real `exit 1`, orphaned and mis-scoped. Every other repo-wide hit is a reviewer *narrating* a hand-run grep (e.g. `.softhouse/reviews/T5-DEC-1-contract-review.md:261`) — a transcript, not automation. | As S-1. |
| S-3 | *"National ID is 10 characters — 2 Cyrillic letters + 8 digits."* (`:20`) | — | **ABSENT** | Two hits repo-wide, both the rule text. No regex, no validator, no test; there is no party/client type in the Go module yet. | Ship the validator with the client/party context and drive it red on: 9 chars, 11 chars, Latin letters, `month+20` boundary for a 2000+ birth. Do not invent a check-digit rule — it is unpublished. |
| Z-1 | *"Two time zones, no DST … never hard-code an offset."* (`:21`) | `nexus/…/conformance/admit.go:615-621`; `nexus/internal/apps/loanschedule/generator.go:205-250`; `loanschedule_test.go:270-282` | **FIRES** (offset half) | RED at the admission layer, three ways, each `INADMISSIBLE` + exit 2: `"+08:00"`, `"UTC+8"`, and — the interesting one — **`"Etc/GMT-8"`**, a genuine IANA name that *is* a fixed offset, correctly refused. | None for this half. |
| Z-2 | "…**two** time zones — `Asia/Ulaanbaatar` and `Asia/Hovd`" | — | **ABSENT** (the other half) | `"America/New_York"` in a graded vector → **exit 0, VERDICT PASS, 42 parity vectors**. The guard enforces "IANA name, not an offset"; it does not enforce *which* zones. Arguably right for a generic harness and wrong for a tenant assertion — but nobody decided it, so record it. | Add a tenant-scoped assertion where tenancy is expressed (not in the generic harness): `Asia/Ulaanbaatar\|Asia/Hovd` only, with `UTC` permitted for fixtures. |
| P-1 | *"No US payment rails / vendors … threshold from config, never hard-coded."* (`:22`) | — | **ABSENT** | Zero executable checks for `stripe\|plaid\|lithic\|persona` anywhere. `selfcheck.sh:14-17` covers DB engines only. `tasks.json:237` asks a *reviewer* to look for a hard-coded threshold — a brief, not a guard. | Add both patterns to the repo-wide guard: the vendor list, and `5[,_ ]?000[,_ ]?000` outside `.softhouse/capture/**` (where it is a captured principal, not a threshold — verified: every current hit is capture data). |
| G-1 | Deposit-taking activation prohibited; ported deposit code ships disabled (`:49`, `:58`) | — | **ABSENT** | Prose in `CLAUDE.md`, `patterns.md:32`, `gates.md:9`, and `program.json:302` (`activation_gate: "user — …"`, a human gate). No script greps for a deposit endpoint; no test asserts the config flag defaults off. | When `fineract-savings` is ported: a test asserting the feature flag's **zero value** disables every deposit route, plus the S-1 string scan over that package. Drive both red in the porting commit — a disabled-by-default flag that nobody has seen refuse a request is exactly P-22. |

### 1.5 Cross-cutting defects that belong to no single rule

| # | Finding | file:line | Class | Evidence |
|---|---|---|---|---|
| X-1 | **The shell guards and the Go grader can inspect two different vector stores.** `conformance.sh` derives `STORE_ROOT` from `BASH_SOURCE` (`:110`); the Go grader derives it from `FindRepoRoot(".")` (`registry.go:291-306`), i.e. **the process CWD**. | `.softhouse/conformance.sh:110` vs `nexus/…/conformance/registry.go:291` | **VACUOUS (silent scope divergence)** | Ran `/tmp/T134/.softhouse/conformance.sh` from the worktree's CWD: the guard reported `/tmp/T134/.softhouse/vectors/…` while the report header printed `store /Users/buv/…/agent-afe57438d3a7cf76c/.softhouse/vectors`. Re-run with `cd /tmp/T134` first: `store /tmp/T134/.softhouse/vectors`. **The HARD guards can certify one corpus while the grader grades another, with no warning.** Fix: pass `-store="$STORE_ROOT"` from the shell explicitly, or have the Go side reject a store root that differs from `$CONFORMANCE_STORE_ROOT` when set. |
| X-2 | **`--prove` does not run the HARD guards.** `prove()` (`:312`) calls `load_toolchain` but never `run_guards`; only `main_grade` (`:281`) does. | `.softhouse/conformance.sh:312` | **VACUOUS (mode gap)** | Read directly; `run_guards` appears only at `:241-243` inside `main_grade`. `--prove` currently reports **21 passed, 0 failed** and none of those 21 is a guard proof. A reader who runs `--prove` to check "does the rig go red" gets no information about the three HARD guards. Fix: call `run_guards` from `prove()` too, or add three proof cases that drive M-1/M-2/C-2 red. |
| X-3 | **The UAT skill advertises four checks that do not exist.** | `.claude/skills/softhouse-uat/SKILL.md:35-43` | **ABSENT, advertised as HARD** | The table is headed *"HARD checks — must be zero"* and lists five. Only the float row has an implementation. The section closes *"A HARD hit is a failure regardless of context"*, which reads as a statement about machinery. The "Property invariants" section below it likewise claims `go test` checks "double-entry always balances" — there is no ledger in `nexus/`. This is the largest honesty gap found and it is one edit to fix. |
| X-4 | **There is no CI, no git hook, no pre-commit.** | — | context | `.github/`, `.gitlab-ci.yml`, `Makefile`, `justfile`, `.pre-commit-config.yaml` all absent; `/Users/buv/gerege-nbfi/.git/hooks` holds only `*.sample`. **Exactly two things in this repo can mechanically fail:** `bash .softhouse/conformance.sh` and `go test ./...` under `nexus/`. Every rule not enforced by one of those two is enforced by an agent remembering to read `CLAUDE.md`. This is the reason the orphaned `selfcheck.sh` matters: there is no place that would have run it. |
| X-5 | **P-33 confirmed on this host, for this audit.** | — | context | `type -a grep` at the Claude Code Bash-tool top level → *"grep is a shell function from …/shell-snapshots/snapshot-zsh-…"*, then `/usr/bin/grep`. Inside a script → `/usr/bin/grep` alone, **BSD grep 2.6.0-FreeBSD**. Ambient locale in this session is `LANG=C.UTF-8`, `LC_ALL` unset — and BSD grep treats `C.UTF-8` as multibyte, so the M-1 blindness reproduces at the *default* locale, not only under `en_US.UTF-8`. Every guard sweep in this register was run from a script under `LC_ALL=C` with `-a`. |

---

## 2. The count

**19 non-negotiable rules** enumerated from `CLAUDE.md` (the 11 bullets at `:13-23`, the 3 ratified
tenant parameters at `:58-60`, the deposit-activation gate at `:49`, and the 4 derived obligations the
harness actually implements: oracle-fallback, earned-parity, contract digest, interpreter). Counting
by **rule**, taking the strongest guard each rule has:

| | count | rules |
|---|---|---|
| **Has a guard that FIRES** | **8** | money-in-vectors (via M-4), rounding `HALF_UP`/19/ordinal-4 (R-1/R-2/R-3/R-4), no-hard-coded-offset (Z-1), Fineract-is-the-oracle (O-1), earned parity (O-2), frozen contract (C-1), gofmt/G-3 (C-2, partially), interpreter (I-1) |
| **Has a guard, but it is VACUOUS or UNGATED** | **3** | PostgreSQL-only (D-1/D-2/D-3 vacuous on zero input; D-6 absent for diffs) · money-in-Go-source (M-2/M-3 — **blind to every float literal**) · the charges/audit-t44 rounding canary (R-5 vacuous, R-6 ungated) |
| **ABSENT — no guard exists in any executable form** | **8** | ledger append-only (L-1) · holds→available (L-2) · `Idempotency-Key` (L-3) · never-insured/protected/guaranteed (S-1) · three-part names (S-2) · national ID (S-3) · no-US-rails / RTGS threshold (P-1) · deposit-activation disabled (G-1) |

Counting by **guard site** rather than by rule — **38 sites** examined (the 40 rows above less X-4 and
X-5, which are context rather than guards):

**FIRES 16 · VACUOUS 6 · UNGATED 1 · ABSENT 15.**

- **FIRES 16** — M-1, M-2, M-4, D-1, D-2, D-4, R-1, R-2, R-3, R-4, O-1, O-2, C-1, C-2, I-1, Z-1.
  **Five of those sixteen are simultaneously vacuous at an entry point** (M-1, M-2, D-1, D-2, C-2):
  they discriminate on real input and pass silently on starved input. Counting them as green is
  precisely the P-22 error, which is why they are listed in both columns rather than in one.
- **VACUOUS 6** — M-3, M-5, D-3, R-5, X-1, X-2.
- **UNGATED 1** — R-6.
- **ABSENT 15** — M-6, M-7, D-5, D-6, D-7, L-1, L-2, L-3, S-1, S-2, S-3, Z-2, P-1, G-1, X-3.
  **Two of the fifteen are correctly absent** (M-7 floats in verbatim capture bodies, D-7 a DB
  assertion on a DB-free capture path) and should not be "fixed"; adding a guard there would create
  a vacuous one for symmetry's sake.

Two of the eight ABSENT rules (S-1, S-2) have correct, run-failing code sitting in
`capture/charges/bin/selfcheck.sh` that is **scoped to one capture directory and invoked by nothing**.
Wiring that one file into `run_guards` with `$CH = $REPO_ROOT` converts **five** rows at once
(S-1, S-2, D-5, M-6, and the offset scan) and is the single highest-leverage fix in this register.

**Every guard classified FIRES was driven red here except R-1**, which would require re-running a
capture against the shared containers; its class is argued from an unconditional `sys.exit` over
non-starvable operands and is marked as such.

---

## 3. Blast radius — has anything been certified through a vacuous guard?

### 3.1 Money — **no. Measured, not assumed.**

- **The vector store is clean.** Every `*.json` under `.softhouse/vectors` re-scanned with the
  mitigations the guard is missing (`LC_ALL=C`, `-a`, string literals stripped): **0 float-shaped
  vector files**. So although M-1 *can* be starved, nothing has in fact passed through it.
- **The Go money tree is clean.** 0 forbidden float identifiers, and — the check nobody had run —
  **0 `token.FLOAT`/`token.IMAG` literals across all 21 files**. The M-3 hole is real and is
  currently unexercised. This is the one finding where "nothing has slipped through yet" is a
  measurement rather than an inference, and it is why M-3's fix is free.
- **What *has* been certified through a vacuous guard is the analysis layer.** 74 of 240 `.py` files
  under `.softhouse/` load JSON without `parse_float=`, and at least one
  (`capture/actualactual/analysis/discriminate.py:160`) decides a money claim by binary-float
  equality and prints *"ALL n PERIODS REPRODUCED DIGIT FOR DIGIT"*. P-25 records that this exact
  class already put a wrong refutation count (18, not 22) into the gate document Buyan reads. **The
  money rule's live blast radius is entirely in the analysis scripts, not in the port or the corpus.**

### 3.2 Database engine — **no, and for a structural reason worth stating.**

- **Nothing prohibited exists to have been certified.** Repo-wide, `LC_ALL=C grep -aiE
  'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|go-sql-driver|mariadb|lib/pq'` over `nexus/` returns
  **zero hits**. The Go module imports **no** database driver at all — no `database/sql`, no `pgx`,
  no `sqlx` — because it has no persistence layer yet. There is currently nothing for D-6 to catch.
- **The graded corpus never passed through a DB assertion in the first place.** All 42 promoted
  parity vectors trace to `capture/out/capture-prod3{b,c,d,e,f,g,i}-raw.json`, produced by
  `run-pass3*.sh`, which executes the seam class in a container **with no database in the loop**.
  So the vacuous P5/P6/P11 never certified any promoted vector — they were not on that path.
- **Where they *were* on the path — `capture/charges/**` and `capture/pathb/**` — nothing was
  promoted.** No vector in the store carries a `capture_ref` pointing into either tree; the only
  non-pass-3 `capture_ref` values are the four `REFUSE-*` vectors, which carry `""` and are refusals
  rather than parity vectors.
- **What would settle the residual question, which I cannot settle read-only.** The three vacuous
  lines print PASS on a starved input, so any *archived* `preconditions.txt` transcript containing
  `PASS 0 prohibited-engine hits` is ambiguous between "checked and clean" and "checked nothing".
  Distinguishing them requires re-running the assertions against the live containers with the
  input-presence checks in place — a capture-side action this task is forbidden from taking. Until
  then, **treat every archived P5/P6/P11 PASS line as unproven**, and do not cite one as evidence
  that a capture ran on PostgreSQL. The *positive* assertions in the same transcripts (P5 lines 1-2,
  P6 pg-driver, P7 version, P12 port 5432) are sound and do carry that evidence.

### 3.3 Rounding mode — **no, and this one is a near miss.**

- The corpus's rounding provenance rests on **R-1** (`run-pass3*.sh`, which checks precision 19 *and*
  ordinal 4 *and* `matchesRatifiedProductionSetting` and `sys.exit`s on each), not on the defeatable
  charges canary. R-2 and R-3 then re-assert it at admission and at runtime.
- The defeatable canary (R-5) gated `capture/charges/**` and `capture/audit-t44/**` — **and nothing
  from either tree has been promoted**. So the two live copies of the T76/T80 defect have certified
  attestations, not vectors.
- **The near miss:** the fix landed in `capture/pathb/t36/preconditions.sh` and not in the two files
  that restate it. That is P-21/P-26 verbatim, at a distance of one directory. The next task that
  captures from `capture/charges/` inherits the pre-T76 rig.

---

## 4. What this audit could NOT cover (P-26)

State these before citing anything above as exhaustive.

1. **I did not run any capture rig against the live oracle.** The brief forbids touching the shared
   containers, so R-1 was classified by reading, and R-5's proof used a **stubbed `curl`** playing a
   HALF_EVEN JVM rather than a real HALF_EVEN tenant. The evasion is proven against the *script*; it
   is not proven that a HALF_EVEN JVM is currently reachable.
2. **I did not test post-merge behaviour (P-24).** Every result here is on this branch. Any claim
   about how these guards behave once merged — particularly X-1, where `FindRepoRoot(".")` resolves
   differently depending on the caller's CWD — must be re-verified on a scratch merge into current
   `main`.
3. **A guard that does not exist cannot be driven red, so the eight ABSENT rows are argued from a
   negative sweep** (`grep -rn` over `*.sh`, `*.py`, `*.go`, `*.md`, `*.json`, plus a hand check for
   CI/hooks). A negative sweep is exactly the shape this register criticises. It could miss: a guard
   expressed as prose an LLM is expected to execute (I found three such — `SKILL.md:35-43`,
   `tasks.json:237`, and reviewer narrations of hand-run greps — and there are likely more); a guard
   inside a `.md` fenced block; a guard in `/Users/buv/fineract`, which I did not sweep.
4. **I enumerated 19 rules. The number is a reading of `CLAUDE.md`, not a fact.** Several bullets
   bundle two obligations (the timezone bullet is really "IANA name" **and** "one of two zones" —
   Z-1 fires, Z-2 does not; the money bullet is really "no float" **and** "display 0 / store 2" —
   I did not audit the display/storage half at all). A different split gives a different count.
5. **Coverage ≠ correctness.** Every FIRES row proves a guard rejects the violation I constructed.
   None proves it rejects the violation someone else will construct. M-3 is the standing proof:
   `TestNoFloatInTheLoanScheduleTree` has an anti-vacuity clause, a considered rationale, and a
   token-stream implementation — and it is blind to `0.036`.
6. **I did not audit the invariants** (`invariants.go`, 807 lines) for vacuity. `--prove` reports
   21/21 and case 20 explicitly guards against `principal_amortizes_to_zero` becoming a no-op, which
   is the right instinct, but I did not attack the other invariants and cannot say they discriminate.
7. **I did not check whether the 42 currently-passing vectors would still pass with the recommended
   fixes applied**, beyond M-3 (verified: 0 float literals, so no-op) and Z-2/P-1 (not applied).
   Anyone landing M-1's `LC_ALL=C grep -a` hardening must re-run `conformance.sh` first: a guard
   that was blind may have been hiding a hit.
8. **`docs/` was not swept for restatements of the rules** (P-21). A correction to `CLAUDE.md` or to
   `SKILL.md` will not reach `docs/softhouse-migration-pipeline.md` or
   `docs/agent-squad-delivery-and-scheduler.md`, and I do not know what they claim.

---

## 5. Reproduction

All scripts are in `/tmp/T134/` (a `git archive HEAD` export plus probes; not committed):

| script | proves |
|---|---|
| `probe-float-guard.sh` | M-1's locale/`-a` matrix; `type -a grep` inside a script |
| `probe-entrypoints.sh` | M-1/M-2 zero-file vacuity |
| `probe-absent-tool.sh` | M-1 absent-`perl` vacuity |
| `probe-go-float.sh` | M-4 fires; M-4 survives the byte poison that defeats M-1 |
| `probe-float-literal.sh` + `floatlit/main.go` | M-3: float literals invisible to both guards; 0 in the current tree |
| `probe-db-preconditions.sh` (+ `fake-silent/`, `fake-absent/`, `fake-oracle/`) | D-1/D-2/D-3 vacuous on zero input; fire on a real violation |
| `probe-canary.sh` | R-5: `CANARY_EXPECT=20925.04` flips FAIL to PASS on a HALF_EVEN oracle |
| `probe-misc.sh`, `probe-gofmt-exempt.sh`, `probe-gofmt-absent.sh` | C-1 fires twice; C-2 fires, over-matches, and is absent-tool vacuous |
| `probe-tz.sh` | Z-1 fires on `+08:00`, `UTC+8`, `Etc/GMT-8`; Z-2 absent |
| `probe-oracle-interp.sh` | O-1 and I-1 fire |
| `probe-cwd.sh` | X-1 store divergence |
| `probe-blast.sh` | §3 sweeps |

Baselines for the pristine tree, recorded before and after every experiment:
`bash .softhouse/conformance.sh` → **exit 0**, *"VERDICT: PASS (exit 0) — 42 parity vectors match the
pinned reference oracle, 5576 cells compared"*; `bash .softhouse/conformance.sh --prove` → **exit 0**,
*"PROOFS: 21 passed, 0 failed"*. No file outside this register and
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T134.md` was modified.

---

## APPENDED BY T154 — closure record for the money rows. T134's measurements above are NOT edited.

**This section is additive on purpose (P-27).** The table above is T134's *measurement*, taken on
21 Aug 2026 on the bytes of that day. Rewriting its cells to say "fixed" would destroy the evidence
that the holes existed and would make the register unable to answer P-34's real question — *what was
certified through this guard while it was blind?* The rows stand; this section records what closed
them, the command that drives each guard **red**, and the date it was last seen red.

| row | closed by | the command that drives it RED | last seen RED |
|---|---|---|---|
| **M-1** `guard_no_float_in_vectors` — bare `grep -Eq`, no `LC_ALL=C`, no `-a` | T154 leg 1 | `bash .softhouse/capture/t154-nofloat/regen-leg1-red.sh` (runs the guard's own pre-fix bytes from a pinned sha against a poisoned corpus) | 2026-08-21 |
| **M-1/M-2** zero files inspected returns 0 | T154 leg 1 — both guards now count what they inspected and treat 0 as an ERROR | same script, section [3] | 2026-08-21 |
| **M-2** `guard_no_float_in_harness` — same bare grep | T154 leg 1 | same script, `harness` rows | 2026-08-21 |
| **M-3** float LITERALS invisible to both guards | T154 leg 2 — `ScanGoTreeForFloatingPoint` censuses `token.FLOAT` / `token.IMAG`, and it is called by `Run`, so it gates the conformance VERDICT and not only `go test` | `bash .softhouse/capture/t154-nofloat/regen-leg2-red.sh`; in process, `go test -run TestNoFloatInTheLoanScheduleTree/the_guard_fires` | 2026-08-21 |
| **M-5** a store-root `.json` is never decoded by Go | T154 leg 3 — `StoreFileCensus` refuses any `.json` under the store root the harness did not load | `bash .softhouse/capture/t154-nofloat/regen-leg3-red.sh`; in process, `go test -run TestStoreFileCensus` | 2026-08-21 |

**Two corrections to the rows above, both measured rather than argued:**

1. **M-3's "21 files" is 22.** A token-stream scan of `nexus/internal/apps/loanschedule` on the same
   pinned tree reports **22** `.go` files, not 21 — and **0** `token.FLOAT` / `token.IMAG` literals,
   which is the part that mattered and which reproduces exactly. The fix was free, as stated.
   [VERIFIED: T154, `go run` over `go/scanner`; and `find … -name '*.go' | wc -l` = 22.]
2. **M-5's "for store-root files M-1 is the ONLY float check" is true only for a store-root file that
   is neither `PIN.json` nor `capabilities.json`.** `LoadPin` (`admit.go:58`) and
   `LoadCapabilityRegistry` (`capability.go:110`) each call `RejectFloatTokens` on their own bytes,
   so a float in `PIN.json` was already refused before T154 — measured with the **pre-fix binary**,
   which reports `FLOAT TOKEN "19.0"`. T154's own first draft repeated M-5's sentence unqualified and
   its `wanted PRE 0` expectation was refuted by its own probe; the expectation and the source comment
   were corrected to the measurement rather than the code adjusted to fit the guess.
   [VERIFIED: `.softhouse/capture/t154-nofloat/out/leg3-GREEN-after-fix.txt`, section 3b.]

**And what T154 measured that this register did not have.** T120's structural finding is six modes,
not one, and four of them are silent on the committed corpus. Every figure below is the **pre-fix**
harness with the corpus otherwise intact [VERIFIED:
`.softhouse/capture/t154-nofloat/out/leg3-RED-before-fix.txt`, the PRE column]:

| mode | pre-fix result |
|---|---|
| a symlinked EXTRA context directory holding a float | exit 0 · 42 parity · 5576 cells |
| a vector one directory too deep | exit 0 · 42 parity · 5576 cells |
| `T154-UPPER.JSON` holding a float | exit 0 · 42 parity · 5576 cells |
| a store-root `.json` with a float behind one invalid byte | exit 0 · 42 parity · 5576 cells |
| `P-00` and `p-00` — case-only `case_id` variants | exit 0 · **43** parity · **5623** cells |
| NFC and NFD spellings of one `case_id` | exit 0 · **44** parity · **5670** cells |

The last two are the dangerous pair: they do not hide a defect, they **inflate the two numbers this
program quotes as its evidence of coverage**, and every other check stays green while they do it.

**Baselines re-taken after all three legs**, unchanged from T134's: `bash .softhouse/conformance.sh`
→ **exit 0**, *"VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576
cells compared"*; `--prove` → **exit 0**, *"PROOFS: 21 passed, 0 failed"*.

**Still open in this register after T154:** D-1/D-2/D-3 (PostgreSQL-only preconditions vacuous on
zero input), R-5/R-6 (the rounding canary), X-1, X-2, Z-2, and the eight non-negotiables with no
executable guard at all. T154 touched none of them.

---

## APPENDED BY T171 — correction: T154's "fail-closed" characterization of `fire-program.sh:224`
is wrong; the true direction is fail-open. This section corrects the RECORD; it edits no code and
no committed handoff (T114 precedent — superseded, never rewritten).

**The wrong claim, precisely.** T154's handoff, Blockers §1, describes the pre-fix line
`DIRTY=$(git status --porcelain | grep -v '^?? \.softhouse/LOCK' || true)` (`fire-program.sh:224`) as
**"fail-closed"**: *"a blind `grep -v` fails to match, so the line is kept, `DIRTY` is non-empty, and
the rescue path runs rather than being skipped."* That is backwards.

**The correct characterization** [VERIFIED:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T157.md`, "The red probe" section, and my
own independent reproduction below]: fed a **seekable** input (a regular file, by argument or `<`
redirection) containing **one invalid byte anywhere**, BSD grep does not "keep the poisoned line" — it
prints **nothing at all for the whole input** and exits 1. `DIRTY` comes back **empty**, and
`run_exit_guard` concludes there is nothing to rescue. That is **fail-open**, the dangerous direction
for an exit-protocol guard, and the opposite of what T154 recorded.

### My own reproduction (independent of T157's and the driver's)

**Apparatus** [VERIFIED, this session]: `/usr/bin/grep` reports itself as `grep (BSD grep, GNU
compatible) 2.6.0-FreeBSD` — the **same version string** T108/T154/T157 used. Host: `sw_vers` →
`ProductName: macOS`, `ProductVersion: 26.5.1`, `BuildVersion: 25F80`, `arch: arm64`. Locale as
inherited by this shell: `LANG=C.UTF-8`, `LC_ALL` unset — matching T157's reported production locale.
`/usr/bin/grep` is a genuine Mach-O binary at that path (`file` confirms x86_64 + arm64e slices, not a
shell alias); a `grep` **shell function** exists in this environment that shadows the name for
interactive use, but I called `/usr/bin/grep` by full path throughout, and re-ran the same tests inside
a clean `env -i LANG=C.UTF-8 /bin/bash script.sh` to rule out the function entirely — same results.

**Result — this build does NOT reproduce the blindness.** I drove six invalid-byte spellings
(`\xe2`, `\xff`, `\x80`, `\xc0`, `\xfe`, `\x81\x82`) across three input shapes (file argument, `<`
redirection, anonymous pipe), including the poison placed directly on the LOCK-matching line itself.
**Every single case** returned the correct filtered output (the non-`.softhouse/LOCK` lines, poison
notwithstanding) with **rc=0** — none went silent, none returned rc=1-with-no-output. This is the
opposite of what T157 measured on its own machine and the opposite of the ugrep 7.5.0 result the
driver independently derived.

This is a **material finding, stated plainly**: two invocations of a grep binary reporting the
identical version string (`2.6.0-FreeBSD`) behave differently on invalid-byte input. I did not
determine why — I only measured that they differ [UNVERIFIED beyond the observation itself]. The
plausible explanation is that Apple ships `/usr/bin/grep` as a periodically-patched BSD-derived binary
that keeps a static self-reported version banner across OS updates, so "same grep --version string"
is not sufficient provenance for a cross-machine reproduction claim — the OS build (`sw_vers`) should
be recorded alongside it. **This does not change the correction above**: T157 and the driver each drove
the bug red on their own machines with the bytes shown in T157's handoff, and I have no reason to doubt
either of those two independent, differently-implemented reproductions. It does mean a *third* attempt
(mine) is a documented **negative**, not a third confirmation, and the guard's behavior should be
treated as build-dependent rather than universal across everything that calls itself BSD grep 2.6.0.

### Reachability, stated exactly (not overstated)

The corrected direction (fail-open) is **not reachable through the live code as written today**:

1. `fire-program.sh:224` feeds grep via an **anonymous pipe**
   (`git status --porcelain | grep -v ...`), never a file argument or `<` redirection. T157 drove every
   poison placement through an actual pipe and every one produced the **correct** output — pipe-fed
   `grep -v` was not observed to go blind on either machine tested. [VERIFIED:
   T157's handoff, "ANONYMOUS PIPE" row; matches my own pipe results, rc=0 with correct output on the
   build I tested, which reproduced no failure mode at all.]
2. **APFS refuses to create a filename containing an invalid UTF-8 byte outright** — `EILSEQ`
   [VERIFIED: T157's handoff, `python3 -c "open(b'...\xe2...', 'wb')"` → `OSError(92, 'Illegal byte
   sequence')`]. So on this filesystem the poisoned byte cannot even originate from a locally-created
   file in the first place.

So: this is a **latent mischaracterization sitting in merged evidence**, not a live hole. It would only
matter if a future edit changed the line from a pipe to a seekable read (e.g. capturing
`git status --porcelain` to a temp file before grepping it) — a plausible refactor, and one that would
then fail silently in the fail-open direction rather than the fail-closed direction T154 recorded.
Saying more than this — e.g. that the guard is currently unsafe — would be overstating the risk to make
the correction sound urgent, which the task brief specifically warned against.

### Merged artefacts left unedited under the T114 precedent (named, not rewritten)

Four committed files still carry the wrong claim or a repetition of it. Per T114, committed evidence is
named and superseded, never rewritten in place:

1. `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T154.md`, Blockers §1 — the original
   claim ("It is also **fail-closed** under BSD grep...").
2. `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T155.md`, lines 49–52 — T155's own review
   handoff repeats it as confirmed fact: *"I confirmed it is **fail-closed** — a blind `grep -v` keeps
   the line, `DIRTY` is non-empty, the rescue runs."*
3. `.softhouse/reviews/T155-review-of-T154.md`, lines 76–82 — the same repetition, this time marked
   `[VERIFIED]`: *"I confirmed its direction is **fail-closed**... The blind grep can only cause a
   spurious DIRTY, never a skipped rescue [VERIFIED]."*
4. `.softhouse/reviews/T155-probe/prove-x-removal-and-failclosed.sh` and its recorded output
   `.softhouse/reviews/T155-probe/out/probe-ix.txt` — the probe script T155 wrote to test this
   (named, literally, `...-and-failclosed.sh`) drives the poison through `cat file | grep -v ...`
   (line 41 of the script) — **a pipe**. Per T157's finding (and mine, on the build that reproduces
   nothing at all) a pipe is exactly the shape that does **not** exhibit the blindness. So T155's
   "confirmation" tested a shape that structurally cannot fail the way the claim describes; it
   demonstrated the pipe is safe (true, and consistent with §Reachability above) while believing it had
   confirmed something about the general `grep -v` behavior (false). This is the specific mechanism worth
   naming in `patterns.md` — see P-55 below.

**Already correct, no fix needed:** `.softhouse/RESUME.md:85` and `.softhouse/tasks.json` (lines 415,
651, 663) already state the corrected fail-open direction accurately — these were written after T157's
finding and do not need correction.

---

## DRIVER ADDENDUM to the fail-open correction — local fire `20260821-054355`

**Scope warning on the section above.** T171's correction states that the true direction is
**fail-open**. The driver merged that correction, because P-55 and the finding about T155's probe
shape are independently valuable and correct. **But the fail-open direction itself now has two
positives and two negatives, and the reader must not inherit it as settled.**

| attempt | implementation | result on invalid UTF-8, seekable input |
|---|---|---|
| T157 | BSD grep 2.6.0-FreeBSD | reported: prints nothing, exit 1 → `DIRTY` empty (**fail-open**) |
| a previous fire's driver | recorded as ugrep 7.5.0 | reported: reproduced |
| T171 (this fire) | /usr/bin/grep 2.6.0-FreeBSD, macOS 26.5.1 build 25F80 | **did NOT reproduce**, 6 spellings × 18+ shapes |
| **this driver** (this fire) | /usr/bin/grep 2.6.0-FreeBSD, same host | **did NOT reproduce** |

**What the driver measured, at the merge of T171** — commands and outputs, not recollection:

- `printf 'keep-me\n\xff\xfe invalid bytes here\nalso-keep\n' > f.txt`, then
  `/usr/bin/grep -v 'nomatch' f.txt` → **all three lines printed, exit 0**. Identical under
  `LC_ALL=C`, `LC_ALL=en_US.UTF-8` and `LC_ALL=POSIX`, and identical again through a pipe
  (`cat f.txt | ...`). So on this host, **invalid UTF-8 does not suppress anything**, and the
  seekable-vs-pipe distinction the correction leans on was not observable at all.
- A **real NUL byte** *does* change behaviour: `printf 'keep-me\n\x00binary\nalso-keep\n' > g.txt`,
  `LC_ALL=C /usr/bin/grep -v 'nomatch' g.txt` → **`Binary file g.txt matches`, exit 0**, with the
  lines suppressed. **This is a THIRD failure mode and nobody has characterised it.** It is neither
  cleanly fail-open nor fail-closed: `DIRTY` comes back **non-empty**, so the exit guard would treat
  the tree as dirty, but its contents are a **message instead of paths**, so anything downstream that
  reads those lines as filenames gets one that does not exist.
- Provenance caveat the driver hit on its own machine: `which -a grep` resolves `grep` to a **shell
  function wrapper** here, and **`ugrep` is not on `PATH`** — so the earlier ugrep corroboration could
  not be re-checked, and the binary actually invoked may differ between any two of the four attempts
  above. **A version string is not provenance** (T171's P-55 rule 4, confirmed a second time).

**Standing instruction until `T189` settles it:** cite this dispute as *unresolved*. Do not write
"fail-open" or "fail-closed" as an established property of `fire-program.sh:224` — **neither
direction currently has more support than the other**, and the NUL shape suggests the question may
have been framed around the wrong byte class from the start. The **anchoring** defect at the same
line is a separate matter and **is** settled: T172 fixed and red/green-proved it.
