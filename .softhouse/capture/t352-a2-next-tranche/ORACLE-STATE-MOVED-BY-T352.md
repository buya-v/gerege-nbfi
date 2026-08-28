# T352 MOVED THE REFERENCE ORACLE'S STATE — what changed, and what it does not affect

Same discipline as `.softhouse/capture/tierA-a2/ORACLE-STATE-MOVED-BY-T276.md`. A journal
entry cannot be deleted, so every probe this task fired is permanent, and the next task to
re-derive a count against the live PostgreSQL will see these rows. Recording them here is
the difference between a moved baseline and an unexplained discrepancy.

Fire `20260828-140005`, tenant `gerege`, oracle pinned at `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

## Four transactions, nine legs, all MANUAL, all office 1, all dated 2026-06-01

| txn | legs | what it probes | capture |
|---|---|---|---|
| `a29bca0816a7` | gl 16 DEBIT 100.125000, gl 21 CREDIT 100.125000 | G-08 residue: a non-zero digit at the THIRD decimal in a 2-minor-unit currency | `out/T352-A01-residue-3dp.*`, `out/T352-A09-residue-3dp-readback-cited.json` |
| `a29bca9bf813` | gl 16 DEBIT 0.125000, gl 17 DEBIT 0.125000, gl 21 CREDIT 0.250000 | whether the debits==credits check runs BEFORE or AFTER minor-unit rounding | `out/T352-A03-residue-balance-scale.*` |
| `a29bcaa6a41b` | gl 16 DEBIT 100.123457, gl 21 CREDIT 100.123457 | posted at SEVEN decimals (100.1234565); stored at the column's scale 6 | `out/T352-A04-overscale-7dp.*`, `out/T352-A05-overscale-readback.json` |
| `a29bcb5d6fcf` | gl 16 DEBIT 12.340000 **USD**, gl 21 CREDIT 12.340000 **USD** | whether the ledger accepts a non-MNT entry at all | `out/T352-A07-usd-entry.*`, `out/T352-A08-usd-readback.json` |

`a29bcb5d6fcf` is **the first non-MNT journal entry in this tenant.** Any query that
previously asserted "every row `currency_code = MNT`" (A2-15's
`sql/q4-a2-26-ledger-state.sql` did) is now false, and that is a real change to the
baseline rather than a defect in the query.

## Per-account counts this moves

Re-derived in `out/T352-A10-accrual-reachability.txt` AFTER the probes:

| account | before (T242's measurement) | after |
|---|---|---|
| gl 16 | 16 | **20** |
| gl 17 | 4 | **5** |
| gl 21 | 7 | **12** |
| gl 18 | 0 | **0** — unchanged |
| gl 22 | 0 | **0** — unchanged |

`gl 18 -> 0` and `gl 22 -> 0` are the pair the `ledger.accrual.entry` argument actually
rests on, and neither moved. The stale `gl 16 -> SIXTEEN` sentence in
`capabilities-ledger.json` is restated in the same diff that created these rows.

## What this does NOT affect, checked rather than hoped

* **No promoted vector reads these transactions.** Every ledger vector grades legs
  selected by a specific `transaction_id`; none of the seven parity vectors or six
  refusal vectors names any of the four ids above.
* **No promoted vector grades an account BALANCE.** LDG-01's `_note` states it outright
  ("NO BALANCE IS GRADED"), and gate G-12 is open on the running-balance columns, so the
  vector schema has no field that could move when an account gains rows.
* **The harness does not read the oracle's database when it renders a report**, so no
  printed figure changes as a consequence of these rows. The counts that DO go stale are
  the ones written as PROSE into `capabilities-ledger.json`, which is why they are
  restated by hand in the same commit — the identical failure mode T242 had to correct
  once already (A2-34 F-4).
* **No product, GL account, mapping, closure or business date was created, edited or
  deleted.** The only writes are the four journal entries above. In particular no
  existing product was retyped, which is the A2-26 hazard (GL account 2 flipped
  ASSET -> INCOME underneath five live mappings).
* **No deposit or savings behaviour was touched.** The tenant is an NBFI (ББСБ) and
  accepting deposits is prohibited (Law on Non-Banking Financial Activities Art. 12.1.3
  / 12.1.4); this task captured manual GL journal entries only.

## Re-derivation

Every probe is re-runnable from this directory:

```
./cap11.sh <NAME> POST /journalentries req/<FILE>.json <KEY>
./capsql.sh <NAME> sql/q1-t352-residue-rows.sql
```

The transaction ids will differ on a re-post — the oracle assigns them — so a re-run is a
claim about the LEGS, never about the id.
