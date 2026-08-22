# T245 — independent review of the DRIVER's own correction to `.softhouse/reference-oracle.md`

**Reviewer worktree stamp:** repo commit `9b6c596c2b66769e7b7e7b5c2ca012b7f3df122a` (branch `main`,
`git status --porcelain` empty at start).
**Under review:** commit `358c3b9` — *"driver: the oracle PIN FILE did not name the database every
ledger vector came from"*, made by the `/softhouse-program` driver on local fire `20260822-060013`
at repo commit `c0be92b`, against its own file.
**Oracle:** REACHABLE this fire — `{"status":"UP","groups":["liveness","readiness"]}`,
`fineract-fineract-1` (`fineract:latest`) up 4 days healthy, `fineract-db-1` (`postgres:18.3`) up 5
days healthy.

Instrument and full recorded output: `measure.sh` / `measure-output.txt` in this directory. Every
figure below is reproducible by running `bash measure.sh`.

## Verdict

| claim | driver's statement | T245 finding |
|---|---|---|
| (1) | pin file's `Databases` row named only `fineract_tenants`, `fineract_default`; `fineract_gerege` named nowhere | **TRUE of the database name, OVERSTATED as written** — the pre-edit file named the **tenant** `gerege` on 7 lines, including a section heading |
| (2) | three Fineract databases; `fineract_gerege` 281 public tables, tenant 2 | **TRUE, all three parts** |
| (3) | tenant 1 `default` @ `Asia/Kolkata`, tenant 2 `gerege` @ `Asia/Ulaanbaatar` | **TRUE**; one transcription slip in tenant 2's `name` |
| (4) | `fineract_gerege` in 74 tracked files, `fineract_default` in 71 | **TRUE at `c0be92b`, STALE at `9b6c596`** (88 / 78) |
| (5) | the six ledger vectors were captured from tenant `gerege` — **INFERRED, not measured** | **TRUE, and now MEASURED three independent ways.** No ledger vector touches `fineract_default`. **No HIGH finding.** |

**One new HIGH finding, not in the driver's list and not reached by its edit:** the pin file's own
*"Connection facts for vector capture"* table still instructed every capture author to use
`tenantIdentifier=default` and `psql -U root -d fineract_default`. Corrected by this task.

## F-1 (HIGH) — the driver corrected the inventory and left the instruction

`.softhouse/reference-oracle.md` at `9b6c596`, lines 146–149, under the heading
**"Connection facts for vector capture"**:

```
| Tenant header/param | `tenantIdentifier=default` |
| Postgres | `psql -U root -d fineract_default` inside `fineract-db-1` |
```

The driver's own warning, ~60 lines above in the same file, reads: *"A capture taken against tenant
`default` because this file named its database and not the other one would be a capture at the wrong
offset, and nothing downstream would say so."* That is a precise description of lines 148–149, which
the same commit left untouched.

Sweep, all **5,129** tracked files at `9b6c596`, whole-file byte match: **10 files** carry a copyable
instruction naming tenant `default` / `fineract_default`. **Nine are deliberate negative controls** —
`pathb/t22-probe/{capture,repro}.sh`, `pathb/t22-audit/rerun-default.sh`,
`pathb/t149/capture-halfeven-arm.sh` (the `HALF_EVEN` arm), `reviews/T22-pathb-capture-audit.md`,
`reviews/T136-review-of-T125.md`, `reviews/A2-10-probe/poison-d3-manifest.py`,
`capture/pathb/PROVENANCE-INDEX.json`, `reviews/t246-dec2-rev6/measure-reversals.sh` (an explicit
population-scope control, P-66). **`reference-oracle.md` was the only prescriptive one.**

Measured severity, live at `9b6c596`: `fineract_default` holds **0 GL accounts, 0 journal entries,
0 loans** (10 loan products, 1 office, 2 clients). A ledger capture pointed there does not merely run
at `+05:30` — it finds no ledger at all, and the first symptom would be a 404/validation error a fire
could easily misfile as an oracle defect.

**Fixed by T245** in this branch: the table now names tenant `gerege`, both selection forms verified
HTTP 200 live, `psql -d fineract_gerege`, and `default` is relabelled as what it actually is in this
corpus — a negative control.

## F-2 (MEDIUM) — the `.http` tenant attestation is a hard-coded constant, not an echo

`cap.sh`, `cap8.sh` and `cap9.sh` all send `-H "$T"` where `$T` comes from `env.sh`
(`T='Fineract-Platform-TenantId: gerege'`). But all three write the sidecar line as a **literal**:

```sh
echo "Fineract-Platform-TenantId: gerege"
```

not `echo "$T"`. So the attestation is decoupled from the value in force: change `env.sh` and every
`.http` sidecar keeps saying `gerege` while the request goes elsewhere. The rig already knows the
right shape — `cap9.sh` writes `echo "Idempotency-Key: $KEY"`, the variable, four lines below the
hard-coded tenant. Today the sidecars are **true** (measured, F-3 below); the point is that they are
**constants, not evidence**, which is the fail-OPEN class this program has named four times (P-45).
This is why T245 did not rest claim (5) on them.

## F-3 — claim (5) established three independent ways

1. **The sidecars.** 9 of the 10 committed capture artefacts behind the six vectors carry
   `Fineract-Platform-TenantId: gerege`. The 10th (`A2-390`) is a DB read-back and records its
   transport verbatim: `docker exec -i fineract-db-1 psql -U root -d fineract_gerege -f - < …`.
2. **The live rows** — the decisive leg, independent of any sidecar. Every entity each vector names
   exists in `fineract_gerege` and is **absent from `fineract_default`**: transaction `a28f573f34c7`
   (LDG-01) with its exact three legs; `a28f573ffb9b` (LDG-04); `L25` / `L27` (LDG-02 / LDG-03) with
   all eight legs; GL accounts 1/4/6/8/10/16/17/18/21 by id, code, name and
   `manual_journal_entries_allowed` (LDG-REFUSE-01/02). `fineract_default` has **zero** GL accounts
   and **zero** journal entries, so those refusals could not have been produced there.
3. **Provenance digests.** All **12** `capture_sha256` / `request_capture_sha256` values in the six
   vectors match the committed artefacts byte-for-byte, so the vectors cite exactly the files
   inspected in (1). `MANIFEST.sha256` covers the `.http` sidecars as well as `.json` / `.req`.

## Cuts recommended by line

See `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T245.md`, section *"Overreach audit"*.

## Bar

Re-run after every edit in this branch; unchanged. Detail in the handoff.
