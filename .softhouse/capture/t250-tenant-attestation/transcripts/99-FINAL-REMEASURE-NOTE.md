# T250 — re-measurement at finish (P-69), and why the numbers MOVED

The task's own instruments were re-run after the T250 files were committed, so they are now part of
the population they measure. The counts changed. **Every delta is this task's own artefacts, and
none of it is a newly-discovered defect.** Recording the deltas rather than quietly re-baselining,
because a number that moved without explanation is exactly the kind of thing this task exists to
stop.

| measure | at start (`a71c140`) | at finish (`b4d170d`) | why |
|---|---|---|---|
| tracked files | 5215 | 5341 | +126 T250 files committed |
| `.sh`/`.py` | 918 | 933 | +15 T250 instruments and evidence scripts |
| TERM 1 (attestation writers touching the oracle) | 29 | 33 | +4: T250 red-drive scripts, which do talk to the oracle |
| TERM 2 (literal where a variable was in scope) | 4 | **5** | +1: **instrument `10-population.py` matches ITSELF** — see below |
| tenant senders (12-A) | 50 | 56 | +6 T250 scripts that send a tenant on purpose |
| tenant attested as LITERAL (12-C) | 5 | 9 | +4: T250 red-drive scripts that **deliberately reproduce the defective writer** |
| tenant attested DERIVED (12-C) | 0 | **0** | see the limitation below — this is the honest number |
| redaction class (11-C) | 4 | 5 | +1, same self-match |

## The self-match is real and is left in place

`10-population.py:139` is the instrument's **calibration positive-control fixture**:

```python
pos = ("T='Fineract-Platform-TenantId: gerege'\n"
       'curl -H "$T" x\n'
       'echo "Fineract-Platform-TenantId: gerege" > f\n')
```

It is, by construction, a perfect instance of the pattern the instrument detects — which is why it
is the positive control. The detector correctly flags it.

**It was NOT excluded.** Adding a self-exclusion would make the instrument's own count prettier at
the cost of giving it a blind spot aimed at itself, which is the shape T250 removes. The honest
report is "5, of which 1 is this instrument's own test fixture", not "4" with a silent carve-out.

The same applies to the +4 in 12-C: `20-redA-…sh` contains a verbatim reproduction of `cap10.sh`'s
literal writer, because reproducing the defect is how RED-DRIVE A proves the defect exists. A
detector that did not flag it would be failing to detect the thing it was pointed at.

## A stated limitation of instrument 12 — it UNDERSTATES the fix

Instrument 12 detects **attestation by emission**: it looks for a script that itself emits a
`Fineract-Platform-TenantId:` line. `oracle_send.sh` does not emit one — it *derives* the whole
attestation through `wire_attestation.py`. So the fix is invisible to instrument 12 and lands in
bucket D ("sends a tenant, attests no tenant line").

**This is why "attested DERIVED" still reads 0 at finish and that number is correct as printed.** It
is a statement about what instrument 12 can see (P-66: "not found" is a statement about the search),
not a claim that no derived attestation exists. The derived attestations are the sidecars under
`evidence/redA/derived/`, `evidence/redB/out/` and `evidence/redC/out/`, each carrying an
`attestation-derivation:` line and each verifiable with `wire_attestation.py verify`.

A future instrument that wants to count derived attestations should key on the
`attestation-derivation:` marker in the produced `.http` artefacts, not on emission sites in scripts.
Filed as backlog B-6 in the T250 handoff.

## Unchanged, and the one that matters

`git rev-parse HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` at start and at
finish. The four `tierA-a2/cap*.sh` files and every committed `.http` sidecar are byte-identical to
their state at `a71c140`.
