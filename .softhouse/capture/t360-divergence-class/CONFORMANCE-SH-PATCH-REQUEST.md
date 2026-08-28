# T360 — `.softhouse/conformance.sh` PATCH REQUEST

`.softhouse/conformance.sh` is held exclusively by **T375** this fire. T360 did **not** write
it. This file is the exact patch T360 would have applied, with line numbers and the reason.

**Sequencing note for the driver: patch 1 is MERGE-BLOCKING.** Without it, `main` with T360
merged is **exit 2**. With it, exit 0. It is one integer on one line.

---

## PATCH 1 — MERGE-BLOCKING. One integer.

**File:** `.softhouse/conformance.sh`
**Line:** `3923` on `main` at `05ce01de` — `EXEMPTION_PIN_LEDGER_WRONGIMPLS=13`
(locate it with `grep -n '^EXEMPTION_PIN_LEDGER_WRONGIMPLS=' .softhouse/conformance.sh`;
the line number moves, the symbol does not)

```diff
-EXEMPTION_PIN_LEDGER_WRONGIMPLS=13
+EXEMPTION_PIN_LEDGER_WRONGIMPLS=14
```

**Why.** T360 registers a fourteenth deliberately-wrong ledger implementation,
`ledger-wrong-residue-rounding`, in `nexus/internal/apps/ledger/conformance/impl.go`.
`gate_wrong_ledger_impls_die` DISCOVERS the population from the binary's own
`-list-implementations` and compares it with this pin for **equality in both directions**,
which is the guard working exactly as designed: a wrong implementation added without being
executed here, or deleted while vectors still cite it, must refuse. T360 moved the population
and cannot move the pin, so as committed the bar prints

```
conformance: CENSUS wrong ledger implementations — discovered 14 registered as DELIBERATELY
conformance:   WRONG from the binary's own -list-implementations; pinned at 13.
conformance: WRONG-IMPLEMENTATION POPULATION 14, PINNED 13.
```

and returns **exit 2**. That is a *pin refusal*, not a corpus defect and not an oracle
outage — the probe line reads `up`.

**What the fourteenth one is, in one sentence, so the pin edit is reviewable rather than
mechanical:** a port that ROUNDS a sub-minor-unit residue HALF_UP and POSTS where this port
REFUSES and the reference oracle ACCEPTS the residue unrounded (G-19). It is
byte-identical to `ledger-go` on all thirteen vectors that existed before T360 — **measured**,
`out/T360-D02-wrongimpl-SURVIVES-without-the-vector.txt`, `VERDICT: PASS (exit 0)` with
`LDG-DIV-01` withheld — and dies on `LDG-DIV-01` alone.

**Measured with the patch applied**, in a scratch copy of this branch that differs from it by
this one character: `out/T360-BAR-with-patch1.log`, exit **0**, and the line the
non-vacuity requirement asks for:

```
conformance:   KILLED  ledger-wrong-residue-rounding — exit 1, ledger parity FAIL 1 + oracle-refusal FAIL 0
```

---

## PATCH 2 — NOT blocking. The divergence census, in the shell.

**File:** `.softhouse/conformance.sh`, `gate_exemption_census`, the ledger figure block
(`main` at `05ce01de`: the `l_declared`/`l_parity`/`l_refusal`/`l_money` reads ending at **3747**
and the four `_cmp` calls ending at **3759**; `local l_declared="" ...` is at **3720**), plus
a new pin beside `EXEMPTION_PIN_LEDGER_MONEYCELLS` at **683**.

```diff
+# THE LEDGER DIVERGENCE PIN  [T360, G-19]
+#
+# A `divergence` vector records the reference oracle ACCEPTING a request this port REFUSES.
+# Its PASS is counted in `ledger divergence PASS` and NOWHERE in `ledger parity PASS`, because
+# on such a vector the port did NOT match the oracle. Both directions of drift are bad in a
+# way no other ledger population is: an ADDED divergence is the cheapest route there is to a
+# green bar over a wrong port, and a REMOVED one deletes the only record that an open, gated
+# port/oracle disagreement exists.
+EXEMPTION_PIN_LEDGER_DIVERGENCE=1
```

```diff
     l_money="$(_census_one "$report" \
       's/^ *ledger cells compared  *[0-9][0-9]* graded, of which \([0-9][0-9]*\) are MONEY cells.*$/\1/p' \
       'LEDGER-money-cells')" || rc=1
+    l_divergence="$(_census_one "$report" \
+      's/^ *divergence vectors  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*.*$/\1/p' \
+      'LEDGER-divergence-PASS')" || rc=1
   fi
```

```diff
     _cmp "LEDGER money cells compared " "$l_money"      "$EXEMPTION_PIN_LEDGER_MONEYCELLS"
+    _cmp "LEDGER divergence vectors   " "$l_divergence" "$EXEMPTION_PIN_LEDGER_DIVERGENCE"
```

(`local l_declared="" l_parity="" l_refusal="" l_money=""` gains `l_divergence=""`.)

**Why it is NOT blocking, and why T360 did not simply wait for it.** The population is
**already pinned, in both directions, in Go** — `DivergencePinCount()` in
`nexus/internal/apps/ledger/conformance/grade.go`, checked in `Run` **above every early
return** so that a corpus which lost every ledger vector refuses instead of satisfying the
census by being empty, and reported through `Summary.Fatal`, which
`loanschedule/conformance/grade.go`'s `ExitCode()` maps to **exit 2**. Driven red in both
directions by `TestDivergencePopulationIsPinnedInBothDirections`. Patch 2 adds a **second,
independent** reader of the same figure — derived by a different program from the printed
report, which is this repository's own habit — but the figure is not unpinned today.

---

## PATCH 3 — NOT blocking. Where the `ledger divergence` line is printed.

T360's divergence census is rendered by `Summary.NotGradedLines()` in
`nexus/internal/apps/ledger/conformance/notgraded.go`, which the loanschedule reporter prints
verbatim. That is deliberate — the ledger context renders its own prose (DEC-2 §5.2, and the
correction A2-34 forced) — **and** it was forced: `nexus/internal/apps/loanschedule/
conformance/report.go`, where `ledger parity` and `ledger oracle-refusal` are printed, is
outside T360's grant. If a later task with that grant would rather the two figures sat beside
the other ledger counts, the lines to add after `report.go:818` are:

```go
p("    ledger divergence       PASS %-4d FAIL %d   (the ORACLE ACCEPTED and this port REFUSES:",
    l.DivergencePass, l.DivergenceFail)
p("                                              a RECORDED, GATED divergence. NOT a parity pass.)")
```

and `divergenceCensusLines()`'s first four lines would then be dropped from `notgraded.go`.
The claim-limit prose below them stays where it is: it belongs with
`WHAT A GREEN LEDGER SECTION DOES NOT MEAN`, which is the block it qualifies.

---

## WHAT DOES **NOT** MOVE, and it is the load-bearing half of this request

Verified by running, not by arithmetic (P-83):

| pin | before | after | why it does not move |
|---|---|---|---|
| `EXEMPTION_PIN_LEDGER_PARITY` | 7 | **7** | a divergence PASS is not a parity PASS, by construction in `Run` |
| `EXEMPTION_PIN_LEDGER_REFUSAL` | 6 | **6** | the oracle ACCEPTED; this is not an oracle refusal |
| `EXEMPTION_PIN_LEDGER_MONEYCELLS` | 39 | **39** | a divergence vector compares ZERO money cells — there is no port-side amount and the oracle-side amount has no int64 form. Asserted by `TestADivergenceVectorGradesNoMoneyCell` |
| `EXEMPTION_PIN_LEDGER_DECLARED` | 0 | **0** | this schema admits no exemption and T360 declares none |
| loanschedule parity 46 / cells 7884 | 46 / 7884 | **46 / 7884** | T360 touches no loanschedule vector and no loanschedule code |
| dead-path frontier pin | 109 | **109** | the census corpus is tracked `.softhouse/*.py` and `.softhouse/*.sh`; T360 commits neither |

`EXEMPTION_PIN_LEDGER_WRONGIMPLS` is the **only** figure in `.softhouse/conformance.sh` that
T360 moves, and that is a deliberate property of the design rather than a coincidence: a
divergence is neither a parity result nor a money comparison, so it touches neither tally.
