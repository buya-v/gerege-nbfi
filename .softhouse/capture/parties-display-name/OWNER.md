# parties-display-name — capture owner notes

Run: **OH-NAMECAP-AW** — CAPTURE ONLY. No vector, drive, or `.go` file is written here.
A later run extends the seam and grades it.

- Worktree: `/Users/buv/oh-gerege-namecap`, branch `feat/OHNAMECAPaw`.
- Oracle: Fineract reference API (PostgreSQL only) plus the `gerege-oracle-db`
  container; tenant **`gerege`** only, never `default`. Read-back is read-only.
- Target: `DeriveDisplayName` (nexus `client.go:75`, ported from `Client.java:457-481`),
  the code behind CLAUDE.md's **"Names are three fields"** (line 19).
- Body shape copied from the accepted
  `capture/loan-writeoff-paid-instalment/req/client-OHWOPAID-C01-create.json`
  (`officeId:1`, `legalFormId`, `locale:"en"`, `dateFormat:"dd MMMM yyyy"`), with
  `active:false` so every client stays **PENDING** (no activation path exercised).
- Scripts: `bin/step01-person-three-parts.sh`, `bin/step02-person-blank-middle.sh`,
  `bin/step03-entity-no-joined-name.sh`; read-back helper `bin/db-readback.sh`.
  Nothing here was run against a push gate.

## The three arms (F-2026-09-11-parties-graded-coverage.md §4.1)

1. Blank `fullname` ⇒ a non-blank `fullname` wins as the display name (the only arm
   the committed corpus previously observed).
2. Instead, for a `PERSON` legal form, `firstname`, `middlename`, `lastname` are
   joined in that order, blank parts skipped.
3. For a non-person (entity), no joined name is produced.

## Results, client by client

| client | create | id | accountNo | status | legalForm | parts sent | parts read back (GET / DB) | displayName (GET) | display_name (DB) | arm |
|---|---|---|---|---|---|---|---|---|---|---|
| `OHNAMECAP-P1` | 200 | 13 | 000000013 | Pending | person (1) | firstname=`Синтетик`, middlename=`Туршилтын`, lastname=`Жишээ`; no fullname | all three present, no fullname | `Синтетик Туршилтын Жишээ` | `Синтетик Туршилтын Жишээ` | 2, no blank |
| `OHNAMECAP-P2` | 200 | 14 | 000000014 | Pending | person (1) | firstname=`Синтетик`, lastname=`Давхардалгүй`; middlename absent; no fullname | firstname + lastname, middlename absent | `Синтетик Давхардалгүй` | `Синтетик Давхардалгүй` | 2, blank-skip |
| `OHNAMECAP-E1` | 200 | 15 | 000000015 | Pending | entity (2) | firstname=`Байгууллага`, middlename=`Туршилтын`, lastname=`Жишээ`; no fullname | all three parts present, no fullname | key absent | `""` (empty string) | 3, no joined name |

All three creates returned HTTP 200 and the GETs HTTP 200. All clients are
`clientStatusType.pending`, `active:false`. Only `OHNAMECAP-E1` exercised the entity
arm; `OHNAMECAP-E2` was not needed (see "Entity does not require fullname").

### Arm attribution

- **P1 → arm 2 (complete join).** `fullname` is absent, so arm 1 cannot fire; the
  display name is the three parts in Fineract field order (`firstname middlename
  lastname`), verbatim in both the wire response and `m_client.display_name`.
- **P2 → arm 2 (blank-skip).** With `middlename` absent the join still yields a
  single separator: `Синтетик Давхардалгүй`, no doubled or trailing space. The
  column and the wire agree.
- **E1 → arm 3 (entity).** The three parts are stored and returned, but no name is
  joined: `m_client.display_name` is the empty string and the `GET /clients/15`
  writer **omits `displayName` entirely** (it also omits `fullname`). So the entity
  observation has two faces — empty string at the column, absent key on the wire.

## Name-part mapping used, and why

CLAUDE.md line 19 fixes the three fields as **ovog (clan), patronymic, given name**.
The Fineract client carries them in three physical columns, and the join order is
`firstname` → `middlename` → `lastname`. The mapping written into the request bodies:

| Mongolian part | Fineract field | value (synthetic) |
|---|---|---|
| given name (нэр) | `firstname` | `Синтетик` / `Байгууллага` |
| patronymic (эцгийн нэр) | `middlename` | `Туршилтын` |
| ovog (clan / family) | `lastname` | `Жишээ` / `Давхардалгүй` |

Why this way, per the brief: `lastname` is the family-name slot, so the **ovog**
belongs there; the patronymic is the middle slot; the given name leads. The
consequence the later grading run must confront is that the derived display name
therefore reads **given → patronymic → ovog** (`Синтетик Туршилтын Жишээ`), i.e. the
*reverse* of the canonical ovog → patronymic → given ordering named in CLAUDE.md.
The capture records the oracle's actual order; it does not decide the port's.

Values are synthetic and Mongolian-shaped (Cyrillic). `Синтетик` = "synthetic",
`Туршилтын` = "experimental/of the test", `Жишээ` = "example", `Байгууллага` =
"organisation", `Давхардалгүй` = "without duplication". No real person's name is used.

## Observations a grader should not miss

1. **Entity does not require `fullname`.** A body with `legalFormId:2`, three parts
   and no `fullname` was **accepted (HTTP 200)** in this build. The hypothesis in the
   brief — "if the oracle requires a `fullname` for an entity" — is refuted here; the
   entity arm produces no name rather than demanding one. No refusal body exists.
2. **Entity display name is empty on the column and absent on the wire.** `GET`
   omits the `displayName` key for E1, while `m_client.display_name = ''`. A grader
   must not read "absent" as "not measured": the DB read-back is the corroboration.
3. **`fullname` is never set** in any of the three clients, so arm 1 stays unobserved
   by this capture (by design — arm 1 is already covered by `clients-1-raw.json`).
4. **Blank-skip is a single separator**, not a trim of a doubled space — P2 shows the
   join skipping the missing `middlename` before it is built.
5. **All clients are PENDING**; no activation date is in the create bodies. `GET`
   still exposes the parts and `displayName` for pending persons.

## Evidence index (all JSON; UTF-8)

For each `N` in `P1`, `P2`, `E1` under `req/` and `out/`:

- `req/OHNAMECAP-<N>-create.json` — request body exactly as sent (byte-stable).
- `out/OHNAMECAP-<N>-create-raw.json`, `out/OHNAMECAP-<N>-create.status` — create response and HTTP status.
- `out/OHNAMECAP-<N>-raw.json`, `out/OHNAMECAP-<N>.status` — `GET /clients/{id}` body and status.
- `out/OHNAMECAP-<N>-m-client.json` — read-only `SELECT id, firstname, middlename,
  lastname, fullname, display_name, legal_form_enum FROM m_client WHERE id IN (…)`
  from `gerege-oracle-db` (`fineract_gerege`), emitted as a JSON row array.

Cyrillic is UTF-8 in every artifact; request bodies are byte-stable (no re-encoding).
A psql dump is deliberately not produced — it cannot be cited.

## Reproduction

```
bash .softhouse/capture/parties-display-name/bin/step01-person-three-parts.sh
bash .softhouse/capture/parties-display-name/bin/step02-person-blank-middle.sh
bash .softhouse/capture/parties-display-name/bin/step03-entity-no-joined-name.sh
```

Each script POSTs, GETs, reads back, and prints a one-line GET-vs-DB comparison.
Re-running creates new client ids; the committed artifacts are ids 13/14/15.

This document was created by an AI agent (OpenHands) on behalf of the user.
