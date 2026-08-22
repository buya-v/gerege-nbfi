# Driver findings — local fire `20260822-060013`

Measured by the **driver**, on the live PostgreSQL reference oracle, at repo commit `c0be92b`.
Evidence: `.softhouse/capture/driver-20260822-060013/oracle-rederivation.txt`.
**These are snapshots (P-69).** Any later restatement must re-measure and re-stamp.

## D-1 (confirms T242 F-4) — gl 16 has SIXTEEN journal entries, and it is the most-posted account of all

The ledger report prints, as a measured fact on every run, *"gl 18, 22, 16 have ZERO journal entries."*
Re-derived independently by the driver against `fineract_gerege`:

| gl id | code | name | journal entries |
|---|---|---|---|
| **16** | 10300 | Fund Source Alternate | **16 — the highest of any account** |
| 18 | 10500 | No Manual Entries Asset | 0 ✅ |
| 22 | 99010 | Unknown Param | 0 ✅ |

Two of the three are right and the third is not merely wrong, it is the **maximum**. The sentence's
*intent* holds — accounts with no entries exist — but there are **eight** of them (gl 3, 5, 7, 12, 15,
18, 22, 24), not three, so the hand-written list is both wrong and incomplete. **T242 is dispatched to
DERIVE this rather than re-hand-write it**, which is the only fix that survives the next capture.

## D-2 (confirms A2-34, for T244) — the corpus DOES contain reversals: exactly 8, by two independent predicates

`select count(*) filter (where reversed), count(*) filter (where reversal_id is not null), count(*)
from acc_gl_journal_entry` → **8, 8, 60**. Both predicates agree. DEC-2 §4.4's stated evidential
reason for `I-5` being ungraded — *"the corpus contains no reversal"* — is **false at this commit**.
T244 prepares revision 6 and raises the gate; it does **not** land it, because DEC-2 rev 5 is ratified.

## D-3 (NEW, driver-found) — `reference-oracle.md` does not name the database every ledger vector came from

`.softhouse/reference-oracle.md` is the file that, in its own words, **"every vector capture must cite"**.
Its `Databases` row reads `fineract_tenants`, `fineract_default`. Measured on the live instance there
are **three** Fineract databases, and the missing one is the one that matters:

| database | public tables | tenant | tenant timezone |
|---|---|---|---|
| `fineract_default` | 281 | 1 `default` — *Default Demo Tenant* | **`Asia/Kolkata`** |
| `fineract_gerege` | 281 | 2 `gerege` — *Gerege T22 Audit Tenant* | **`Asia/Ulaanbaatar`** |
| `fineract_tenants` | 6 | — (registry) | — |

`fineract_gerege` is named in **74** tracked files under `.softhouse/`; `fineract_default` in **71**.
It is the tenant the six ledger vectors were captured from. It appears **nowhere** in the pin file —
verified by a literal-string grep over the whole of `.softhouse/reference-oracle.md` (BSD grep, no
regex, no anchoring), which is the scope of that negative and the whole of it (P-66/P-70).

**Why this is more than a typo.** The two tenants sit in **different time zones**, and one of them is
`Asia/Kolkata` — an offset that CLAUDE.md's two-timezone non-negotiable does not permit anywhere in
this program's own stack. A fire that read the pin file and captured against the database the pin file
names would be capturing at `+05:30`. The program has in fact been careful about this — the
distinction is recorded in **66** tracked files of capture evidence — so the defect is **filing, not
knowledge**, which is precisely the diagnosis `T234` reached about `P-53`. That makes this the second
measured instance of the same failure shape and it belongs in `patterns.md`, not just in a task.

Corrected in place this fire, with the measurement stamped. **Not independently reviewed yet** — filed
as **T245** so that a second pair of eyes re-derives it rather than reading this paragraph.
