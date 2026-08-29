# REQUEST to the holder of `.softhouse/conformance.sh` (T404 this wave) — T416, closing T405's F-T405-4

`.softhouse/conformance.sh` is **not edited by T416**. This is the patch, with the drive that
makes it a finding rather than a proposal.

## THE HOLE, RE-DERIVED (not inherited from T405)

Instrument: `t416-e4drive.sh`; transcripts `out/e4-*.log`; the pin arithmetic driven separately by
`t416-pinreq-drive.sh`, transcript `out/PINREQ-drive.txt`.

| store state | declared | parity | refusal | money cells | inadmissible | divergence PASS | the FOUR pins the bar holds |
|---|---|---|---|---|---|---|---|
| baseline | 0 | 10 | 6 | 63 | 0 | 1 | **GREEN** (correctly) |
| ONE DIVERGENCE VECTOR REFUSED ADMISSION | 0 | 10 | 6 | 63 | **1** | **0** | **GREEN — and it should not be** |
| one PARITY vector refused admission | 0 | **9** | 6 | **58** | 1 | 1 | **RED** (caught, twice over) |

**RE-BASELINED BY RUNNING (P-83), not assumed.** T391 merged into `main` mid-task and moved
`EXEMPTION_PIN_LEDGER_PARITY` 7 -> 10, `_MONEYCELLS` 39 -> 63 and `_WRONGIMPLS` 14 -> 15. Every
figure in this table is from the post-merge tree. **The finding survives the re-baseline
unchanged**, which is itself the point: the divergence hole is structural, not a function of how
many parity vectors happen to be in the store.

The mutation that makes the divergence vector inadmissible is a single character removed from
`oracle_accepted.observed_amount_texts` (`100.125000` → `100.12500`) — a transcription slip in the
one field in this program whose entire purpose is to hold the reference oracle's own characters
for a value no numeric type can represent.

**T405's narrowing is confirmed against its own first statement.** `inadmissible` is *not*
unpinned in general: an inadmissible PARITY vector moves `ledger parity` 10 → 9 and
`ledger cells compared … MONEY` 63 → 58, and `EXEMPTION_PIN_LEDGER_PARITY` /
`EXEMPTION_PIN_LEDGER_MONEYCELLS` both catch it. The hole is **specific to the DIVERGENCE class**,
which contributes to none of the four pinned figures — and it is the class T397 routes a NEW
refusal into, which is what makes this the moment to pin it.

`grep -c 'ledger inadmissible' .softhouse/conformance.sh` → **0**.
`grep -c 'INADMISSIBLE' .softhouse/conformance.sh` → **0**.
`grep -c 'divergence vectors' .softhouse/conformance.sh` → **0**.
The bar reads neither figure anywhere.

## WHY IT SHOULD BE PINNED (the decision, ENGINEERING, chosen_by: agent)

The counter-argument is that `Summary.ExitCode()` already returns 2 on `Ledger.Inadmissible > 0`,
so nothing green is called green. That is true and it is exactly the shape this program keeps
paying for: **one boolean, in one Go function, with no second layer** — one level above the P-45
shape T397 just removed *inside* the ledger package, and reached through a `case` arm no test
exercised until T416 wrote one (F-T405-5, same file, same fire). The pins exist because a census
figure that nothing compares is prose.

The pin also carries information the exit code cannot: `divergence vectors PASS 0 (pinned 1)`
names *which* recorded port/oracle disagreement stopped being graded. Exit 2 alone does not.

## THE PATCH

Three hunks. `_cmp` and `_census_one` are unchanged; this only adds two constants, two
extractions in the existing `ledger_cmp` block, and two comparisons in the existing `_cmp` block.

```diff
@@ around line 524, after EXEMPTION_PIN_LEDGER_DECLARED=0
 EXEMPTION_PIN_LEDGER_DECLARED=0
+
+# EXEMPTION_PIN_LEDGER_INADMISSIBLE / _DIVERGENCE_PASS [T416, closing T405's F-T405-4].
+#
+# The four LEDGER figures pinned here and below guard the PARITY and
+# ORACLE-REFUSAL classes: refusing a parity vector admission moves
+# `ledger parity` 10 -> 9 and the money-cell count 63 -> 58, and both _cmp lines
+# go red. A DIVERGENCE vector contributes to NONE of the four, so refusing THAT
+# one admission left every pinned figure identical -- measured, in
+# .softhouse/capture/t416-t405-conditions/out/PINREQ-drive.txt.
+#
+# It matters because the divergence class is the one whose whole content is a
+# RECORDED DISAGREEMENT WITH THE REFERENCE ORACLE, held open at a named gate,
+# and because T397 routed a new refusal (a truncated `observed_amount_texts`)
+# straight into it. Until these two lines exist the only thing standing between
+# a mistyped digit and a vanished divergence record is one boolean in
+# loanschedule/conformance/grade.go's ExitCode().
+EXEMPTION_PIN_LEDGER_INADMISSIBLE=0
+EXEMPTION_PIN_LEDGER_DIVERGENCE_PASS=1
```

```diff
@@ in the ledger_cmp=1 block, after l_money=
     l_money="$(_census_one "$report" \
       's/^ *ledger cells compared  *[0-9][0-9]* graded, of which \([0-9][0-9]*\) are MONEY cells.*$/\1/p' \
       'LEDGER-money-cells')" || rc=1
+    l_inadm="$(_census_one "$report" \
+      's/^ *ledger inadmissible  *\([0-9][0-9]*\).*$/\1/p' \
+      'LEDGER-inadmissible')" || rc=1
+    l_divpass="$(_census_one "$report" \
+      's/^ *divergence vectors  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*.*$/\1/p' \
+      'LEDGER-divergence-PASS')" || rc=1
   fi
```

```diff
@@ in the _cmp block
     _cmp "LEDGER money cells compared " "$l_money"      "$EXEMPTION_PIN_LEDGER_MONEYCELLS"
+    _cmp "LEDGER inadmissible         " "$l_inadm"      "$EXEMPTION_PIN_LEDGER_INADMISSIBLE"
+    _cmp "LEDGER divergence vectors   " "$l_divpass"    "$EXEMPTION_PIN_LEDGER_DIVERGENCE_PASS"
```

## THE EXTRACTIONS ARE DRIVEN, NOT PROPOSED

Both `sed` expressions were run against the three real transcripts. Every one of the six figures
was extractable on every row — an empty extraction would itself be a `_census_one` refusal, which
is the failure mode a new census line is most likely to have:

```
baseline                 declared=0  parity=10 refusal=6  money=63 | inadm=0  divPASS=1  || FOUR EXISTING PINS: GREEN  TWO PROPOSED PINS: GREEN
divergence-inadmissible  declared=0  parity=10 refusal=6  money=63 | inadm=1  divPASS=0  || FOUR EXISTING PINS: GREEN  TWO PROPOSED PINS: RED
parity-inadmissible      declared=0  parity=9  refusal=6  money=58 | inadm=1  divPASS=1  || FOUR EXISTING PINS: RED    TWO PROPOSED PINS: RED
```

RED-before is row 2, column "FOUR EXISTING PINS" = GREEN. GREEN-after is row 2, column "TWO
PROPOSED PINS" = RED. Row 1 is the healthy control: both pin sets green on the unmutated store,
so neither is a comparison that fails everything. Row 3 is the specificity control.

## PIN VALUES AT THE TIME OF WRITING

`EXEMPTION_PIN_LEDGER_INADMISSIBLE=0` and `EXEMPTION_PIN_LEDGER_DIVERGENCE_PASS=1`, both
**measured by RUNNING** the graded binary on the committed store (P-83), transcript
`out/e4-baseline.log`. `DivergencePinCount()` in `ledger/conformance/grade.go` is also 1, and the
two are deliberately independent numbers: that Go pin counts LOADED vectors and this one counts
GRADED ones, which is precisely the distinction F-T405-6 turns on.

**T391 HAS LANDED and moved `EXEMPTION_PIN_LEDGER_PARITY` to 10, `_MONEYCELLS` to 63 and
`_WRONGIMPLS` to 15. It moved neither of these two** — it adds no divergence vector and no
inadmissible one, and the drive above was re-run against the merged tree to establish that rather
than to assume it.
