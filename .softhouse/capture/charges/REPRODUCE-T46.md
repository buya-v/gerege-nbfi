# Reproducing T46's `charges` work

Every path below is derived from the script's own location (T44 finding **A-7**), so this recipe
survives the worktree being pruned. Override the root with `T40_WORKTREE=/path/to/repo` if you must.

Preconditions for anything that contacts the oracle: the pinned Fineract reference instance up on
`https://localhost:8443` with tenant `gerege`, and PostgreSQL as the only engine.
`bin/run-preconditions.sh` gates every capture and **aborts** on any of its 15 breaches, including T36's
behavioural half-cent canary.

## A-7 — the path fix and its proof

```sh
python3 bin/t46-fix-paths.py                 # idempotent; rewrites 11 bin/ files
sh      bin/capture.sh "$PWD/out/t46-reissue"   # re-issues all 21 requests
sh      bin/t46-reissue-identity.sh             # 21/21 must be BYTE-IDENTICAL to out/fc/
python3 bin/invariants.py                       # must reproduce out/INVARIANTS.md byte-for-byte
```

## A-3 / A-5 — the new captures

```sh
python3 bin/t46-mkcalcs.py     # authors req/calc-T46-CH-0*.json as TEXT (no float constructed)
sh      bin/t46-capture.sh     # -> out/t46/T46-CH-0*-raw.json   (additive; creates no charge row)
python3 bin/t46-defvsreq.py    # -> which input supplied the money, and the half-cent verdict
```

`bin/t46-capture.sh` is **additive only**: it creates, modifies and deletes **no** charge definition.
T40's `m_charge` ids 1–12 are used as they stand. Verify the tenant is unchanged afterwards:

```sh
docker exec fineract-db-1 psql -U postgres -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)"
# expected: 12|0|16
```

## A-4 — invariants with C5 relabelled as probe P5

```sh
python3 bin/t46-invariants.py              # exit 0; C5 is NOT among the invariants
python3 bin/t46-invariants.py --negative   # exit 1; proves the suite is failable
```

## T44-X1 — exact-text sidecars

```sh
python3 bin/t46-exacttext.py               # writes/refreshes every <capture>-exact.json, proves identity
python3 bin/t46-exacttext.py --negative    # exit 1; proves the identity check is failable
```

The sidecars are a **pure function of the committed raw bytes** and may be regenerated at any time.
The raw bytes are never rewritten.

## Corrections-leak marker

```sh
python3 bin/t46-mark-superseded.py         # idempotent; marks 11 restatement sites in the T39/T40 handoffs
```

## What must NOT be run against a shared oracle

Anything that writes the tenant's rounding mode. Separating the **ambient** from the **threaded**
rounding mode inside charge arithmetic (finding **N46-1**) needs exactly that, and T46 did not do it.
