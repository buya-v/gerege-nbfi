# Reproducing capture pass 3i (Path A) — the executable recipe

**Pass 3i is pass 3h's rig with one structural fix and a new case list**, exactly as pass 3c is
pass 3b's. `README-pass3b.md` still describes the shape of the recipe; everything it says about
preconditions, output paths and attestation applies here unchanged. This file records only what
differs, and it is the **closure of T21 §10 P0-4** for the Path A seam.

> "The oracle" is the Fineract reference implementation this program grades Go output against.
> Oracle Database is a prohibited product here. PostgreSQL is the only permitted database; this
> seam is a library call and opens no database connection at all. The recipe writes nothing to the
> running reference-oracle container, its PostgreSQL database, its `c_configuration` or any tenant.

## Run it

From the repo root:

```sh
sh .softhouse/capture/src/run-pass3i.sh
```

Optional environment: `PINNED_FINERACT`, `CAP_OUT_DIR`, `REF3B_JSON`, `REF3C_JSON`, `REF3E_JSON`,
`REF3G_JSON`.

**It is a script, not a prose instruction.** The seam byte-identity check is a precondition step that
`exit 1`s; the log/JSON split is built in (`grep -n '^{'` → `head`/`tail`, never a manual edit); and
the attestation sidecar is written by the same run that produced the capture.

## What makes it fail

All of pass 3h's fifteen preconditions, **not one weakened**, with the calibration arm widened from
eight references to nine. Three checks are added and one is replaced by a stronger form:

| # | check | added by |
|---|---|---|
| 1–3 | docker present; image id == the pinned digest; pinned checkout present, at the right commit, working tree clean | earlier passes |
| 4 | the repo's seam copy is byte-identical to the pinned original (`cmp`) | earlier passes |
| **4b** | **the seam's sha256 equals a LITERAL pinned in the script — checked on BOTH copies** | **pass 3i** |
| 5–7 | container exit 0; a parseable JSON document on stdout; stderr empty | earlier passes |
| 8–9 | no `observed: null`, no `error` key, exact id list; ambient MoneyHelper `(19, ordinal 4)` and threaded mode ordinal 4 on every case | earlier passes |
| 10–13 | all nine rig calibrations reproduce their committed observation cell for cell, `inputs` and tenant id included; each reference artefact present at its recorded sha256 | earlier passes + `P-CAL-MNT5M` |
| 14–15 | PATH IDENTITY on every case; mechanism columns present and non-empty | pass 3h |
| **16** | **FIELD SEPARATION** — an expected per-id `(decimalPlaces, currencyInMultiplesOf, installmentAmountInMultiplesOf)` table, **plus** a check that the capture contains a currency-only case *and* an installment-only case | **pass 3i** |
| **17** | **MathContext precision from a HAND-WRITTEN per-id table; an id it does not register fails the run, and so does an entry this run does not capture** | **pass 3i**, table corrected by **T82** |
| **18** | **every `-p12` case actually runs below precision 19 and every case below 19 is named `-p12`; the sidecar classifies them as discrimination probes, separately from `parityCandidateCaptureIds`** | **pass 3i**, corrected by **T82** |

### Why 4b exists

Check 4 compares two files and **a caller controls both operands** — the repo copy through the
working tree, the pinned copy through `$PINNED_FINERACT`. Two files mutated the same way compare
**equal**. Checks 3 and 4 together look airtight because git would normally notice, but
`git update-index --assume-unchanged` silences `git status --porcelain` without moving `HEAD`.

A literal digest has no such operand.

### Why 17 replaces rather than extends the pass-3h check

Pass 3h read `CAL_PRECISION.get(id, 19)`: an id nobody had registered silently defaulted to the
production precision and passed. Pass 3i deliberately carries precision-12 companions, so a defaulted
lookup would let a **discrimination probe validate as though it were a parity candidate** — the exact
confusion `CLAUDE.md` warns about for the pass-1 and pass-2 corpus.

**CORRECTED BY T82 (T75 defect N4).** As pass 3i first shipped, this section's claim was NOT TRUE of
the code. The table was **built by looping over `EXPECTED_IDS`** and filling each missing entry from
the id's own suffix (`endswith('-p12') -> 12, else 19`), so `_unregistered` was **empty by
construction** and the "unregistered id fails the run" exit was **unreachable**. That is the same
default pass 3h had, moved one layer down and keyed on a string suffix — a **P-15 violation inside the
check advertised as curing P-15**. T82 wrote the table out by hand, added the stale-entry direction,
and **demonstrated all three halves red**; transcript in
`.softhouse/capture/t74-multiplesof/T82-guard-proofs/TRANSCRIPT.txt`. The same transcript runs the
identical mutation through the OLD self-constructing table and shows it **exit 0**, which is what
makes the correction a fix rather than a restatement.

### Why 16 is written to be falsifiable

The defect this pass exists to fix is one field feeding two JSON keys. If a later edit re-aliases
them, the currency-only and installment-only arms collapse onto one another and check 16 goes red. An
assertion that cannot fail converts "not checked" into "checked and fine" — pattern **P-15**.

## The guards were falsified, not asserted

Each of these was actually run by task T74; transcripts in the T74 handoff.

| attack | result |
|---|---|
| append a comment to the repo's seam copy | **exit 1**, precondition 4 (`seam class DRIFT`) |
| append the same comment to **both** copies, with `git update-index --assume-unchanged` silencing the checkout so preconditions 3 **and** 4 both pass | **exit 1**, precondition **4b** (`sha256 00d08ef6… expected bf397f0b…`) |
| re-alias `CurrencyData.inMultiplesOf` back onto `installmentMultiplesOf`, exactly as passes 3–3h had it | **exit 1**, precondition **16**, naming all eleven affected cases |
| leave a `-p12` case named `-p12` but make it run at precision 19 | **exit 1**, precondition **17** (`must run at precision 12, got 19`) |

**T82 added five more, because T75 found that two of pass 3i's guards could not go red at all**
(`T82-guard-proofs/TRANSCRIPT.txt`, 16 outcomes, all as expected):

| attack | result |
|---|---|
| add a case to `EXPECTED_IDS` **and to the capture** and forget `CASE_PRECISION` | **exit 1**, precondition **17** (`no expected MathContext precision registered for [...]`) |
| the **same** mutation against the pre-T82 self-constructing table | **exit 0** — the counterproof that the old guard was dead |
| leave a stale `CASE_PRECISION` entry for a case this run does not capture | **exit 1**, precondition **17** (`registers [...] which this run does not capture`) |
| register a **non-`-p12`** case at precision 12 and run it there, so 17 is satisfied | **exit 1**, precondition **18** (`the cases named -p12 are [...] but the cases actually running below precision 19 are [...]`) |
| run both counterfactual arms at a **non-ratified** rounding mode | **exit 1**, `build-counterfactuals.py` — which the pre-T82 chained comparison **passed** |

The falsification was performed on a **scratch clone** of the pinned checkout at `/tmp`, never on
`/Users/buv/fineract`, which was verified clean and at `426a23544e…` afterwards.

## Verifying a re-run

Compare **`capturesCanonicalSha256`** in `out/capture-prod3i-attestation.json`:

```
41bcf7306f691b730d17ed7fa08131b16052d737773c80d12f5abacf6b7d581f
```

Stable across runs; the whole-file digest is not, because the attestation carries a UTC timestamp.
The pass was run twice with the identical harness and both runs produced that digit string.

## The prediction, and that it was registered first

`.softhouse/capture/t74-multiplesof/PREDICTION.md` and `predicted.json` were committed **two commits
before** this capture ran. `check-prediction.py` compares them against the artefact: **1,083
predictions over 875 money cells, 1,082 held, 1 refuted** (sharp claim S2, and the refutation is
written up in `PASS3I-REPORT.md` §6 with its source mechanism rather than quietly dropped). The git
history is what makes that checkable rather than narrated.

## What the pass found, in one paragraph

Every cell the multiples-of family moves belongs to `CurrencyData.inMultiplesOf` alone; every
`installmentAmountInMultiplesOf` arm is byte-identical to its baseline, which is the **first
observed** proof of a blindness that until now rested on a source reading. At the production
`MinorUnitDigits = 2` neither input moves a single cell. The channel that does move money is the
`Money` **constructor** leak, so it quantizes the disbursed principal itself — a requested MNT
5,000,000 came back as **5,000,002** at `inMultiplesOf = 7` — and it has **no zero-guard**, so on a
small enough loan every installment quantizes to zero. **Nothing from any of that was promoted**, for
four independent reasons set out in `PASS3I-REPORT.md`. What was promoted is the `36 × 16.8 %`
small-principal family T21 required change P1-11 asked for: six vectors, MNT 4.00 to 6,940.00, inside
the graded domain.
