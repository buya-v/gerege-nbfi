# T359 MOVED THE REFERENCE ORACLE'S STATE — what changed, and what it breaks

Same discipline as `.softhouse/capture/tierA-a2/ORACLE-STATE-MOVED-BY-T276.md` and
`ORACLE-STATE-MOVED-BY-T352.md`. A journal entry cannot be deleted. Every row below is
permanent.

Fire `20260828-140005`, tenant `gerege`, database `fineract_gerege`, oracle pinned at
`426a23544e8426a38ae43ae404670a0a7e85b9eb` (re-verified by `git log -1` in
`/Users/buv/fineract`).

## ONE transaction, TWO legs, manual, office 1, dated 2026-06-01

| txn | legs | what it probes | capture |
|---|---|---|---|
| `a29bd5eaeb1b` | id 74 gl 16 DEBIT `300.625555`, id 75 gl 21 CREDIT `300.625555` | independent re-derivation of T352's central claim: posted `300.6255545`, i.e. a NON-ZERO digit at the THIRD decimal (residue in a 2-minor-digit currency) AND a seventh decimal against `numeric(19,6)`, cut after an EVEN digit at exactly half so HALF_UP separates from both HALF_EVEN and truncation | `out/T359-P03-residue-post.*`, `out/T359-P04-residue-readback.*`, `out/T359-Q5-my-probe-and-attribution.txt` |

Two POSTs before it were **refused with HTTP 400 and moved nothing** — `comments` exceeds
its max length of 500 (`validation.msg.GLJournalEntry.comments.exceeds.max.length`).
Recorded because a refusal is an observation: `out/T359-P01-residue-post.json`,
`out/T359-P02-residue-post.json`.

## Counters, measured by me AFTER the probe — this is the baseline the next task inherits

`out/T359-Q5-my-probe-and-attribution.txt`:

| counter | before T352 (re-derived, see below) | after T352 | **after T359** |
|---|---|---|---|
| `acc_gl_journal_entry` count / max id | 60 / 64 | 69 / 73 | **71 / 75** |
| distinct `transaction_id` | 26 | 30 | **31** |
| gl 16 legs | 16 | 20 | **21** |
| gl 17 legs | 4 | 5 | **5** — unmoved by T359 |
| gl 18 legs | 0 | 0 | **0** — never moved by anyone |
| gl 21 legs | **8, not 7** | 12 | **13** |
| gl 22 legs | 0 | 0 | **0** — never moved by anyone |
| distinct `currency_code` | `MNT` | `MNT, USD` | `MNT, USD` |

The pre-T352 column is **re-derived, not inherited**: the ledger is append-only, so
counting rows whose `transaction_id` is not one of T352's four gives the count before
T352 ran (`out/T359-Q3-account-counts.txt`). It disagrees with T352's own table at gl 21
— see F-T359-4.

`gl 18 -> 0` and `gl 22 -> 0` are the pair the `ledger.accrual.entry` argument rests on.
**Neither has ever moved, and T359 did not move them** — verified, not assumed:
`out/T359-Q3-account-counts.txt`'s `GROUP BY` returns no row for either account.

## What this breaks — stated, because T352's equivalent record understated it

These were already broken by T352; T359 moves them one row further and does not repair
them. They are listed here because the T352 record did not list them and nothing on
`main` records the movement at all.

* `.softhouse/capture/t305-openingbalance-accepting-side/throwaway/out/STANDING-baseline.txt:20,22`
  and `.softhouse/capture/t327-closure-accepting-side/throwaway/out/STANDING-baseline.txt:20,22`
  pin `gerege acc_gl_journal_entry = 60/64` and `gerege distinct_transaction_id = 26`, and
  five sites compare them by **string equality** and refuse:
  `t305/throwaway/capture.sh:77`, `t305/throwaway/capture2.sh:59`, `t305/throwaway/down.sh:52`,
  `t327/throwaway/capture.sh:82`, `t327/throwaway/down.sh:54`. Both rigs now **fail closed**
  on their next run.
* `.softhouse/observations/20260827-chain2-standing-oracle-baseline.md:21-26` — the driver's
  own independent baseline, whose stated purpose is to make "I did not write to the standing
  oracle" checkable against a figure the task did not supply.
* `.softhouse/reference-oracle.md:907,917,1001` — `acc_gl_journal_entry` recorded at 60 rows /
  max id 64.
* `.softhouse/capture/tierA-a2/out/A2-390-db-ledger-state-a2-15.json:109` —
  `"distinct_currency_codes" : ["MNT"]`, digest-pinned at
  `.softhouse/capture/tierA-a2/MANIFEST.sha256:447`.

## What this does NOT affect, checked rather than hoped

* **The bar is unaffected.** `bash .softhouse/conformance.sh` was run AFTER the probe:
  **PASS, exit 0**, 46 parity / 0 FAIL, ledger parity 7 == 7, refusal 6 == 6, money cells
  39 == 39, 13/13 wrong implementations dead, 9 `exemption census READ` lines printed
  (`out/T359-BAR.log`). This is the positive test of T352's claim that the harness does
  not read the oracle's database when it renders a report.
* **No promoted vector reads `a29bd5eaeb1b`.** Every ledger vector selects legs by an
  explicit `transaction_id`; grep over `.softhouse/vectors/ledger/*.json` for the id
  returns nothing.
* **No product, GL account, mapping, closure, job or business date was created, edited or
  deleted.** The only write is the one journal entry above.
* **No deposit or savings behaviour was touched.** The tenant is an NBFI (ББСБ) and
  accepting deposits is prohibited — Law on Non-Banking Financial Activities Art. 12.1.3 /
  12.1.4. This task posted a manual GL journal entry only.
* **No floating-point value existed anywhere in this transport.** The request bodies are
  hand-typed heredoc/literal JSON; `cap10.sh` sends them with `--data-binary` and commits
  the exact wire bytes plus a sha256; `capsql.sh` writes psql's output verbatim. Both are
  **byte-identical** to the audited `.softhouse/capture/tierA-a2/` originals — verified by
  digest, see `REVIEW.md` F-T359-9.

## Was firing it the right call?

One transaction, for a claim on which a `user` gate to Buyan already rests. The read-only
half of this review (`out/T359-Q1..Q4`) established that T352's rows exist and say what
T352 said they say; that alone is not an independent re-derivation, because it grades
T352's evidence with T352's own probe. The single POST used a value **T352 did not
choose**, with the half-way digit on the opposite parity, and it settled a question T352
left open by inference — see F-T359-3. Two rows, three claims. I judge that proportionate
and I would not have fired a second.

## Re-derivation

```
./cap10.sh   T359-P03-residue-post  POST /journalentries \
             req/T359-R03-residue-halfeven-discriminator.json  T359-P03-residue-post
./cap10.sh   T359-P04-residue-readback GET \
             '/journalentries?transactionId=<ID>&transactionDetails=true' '' T359-P04-residue-readback
./capsql.sh  T359-Q5-my-probe-and-attribution sql/t359-q5-my-probe-and-attribution.sql
```

The oracle assigns the transaction id, so a re-run is a claim about the LEGS, never the id.
