# Task: build the `charges` conformance harness (NO vector capture)

WORKING DIRECTORY: /Users/buv/oh-gerege-charges
Git worktree on branch `port/charges-vectors`. NEVER commit to `main`.
NEVER touch /Users/buv/gerege-nbfi — another pipeline is writing there right now.

## SCOPE CHANGE — read this first
An earlier version of this brief asked you to capture parity vectors. DO NOT.
It is currently impossible, and attempting it would produce a forged witness.

Measured against the running oracle at 2026-09-03:
  fineract_tenants.tenants has exactly ONE row: `default`, Asia/Kolkata.
  The `gerege` tenant and the fineract_gerege schema DO NOT EXIST.
  CLAUDE.md ratifies Asia/Ulaanbaatar, MNT, HALF_UP (RoundingMode ordinal 4).
  The running tenant serves ordinal 6 = HALF_EVEN.

A vector captured from that tenant would record HALF_EVEN arithmetic under a
HALF_UP contract. It would be worse than no vector, because it would look like
evidence. Another task (T520/T521) owns provisioning the ratified tenant. Do not
attempt it, do not modify the oracle, do not create tenants or schemas.

## What to do
1. STUDY, do not rebuild:
     nexus/internal/apps/loanschedule/conformance/   (15,630 lines)
     nexus/internal/apps/ledger/conformance/         (11,763 lines)
   These contain census / exemption / admit / grade machinery. REUSE it.
   If you find yourself writing a second census engine, STOP and reuse theirs.
2. Build nexus/internal/apps/charges/conformance/ on that pattern, for the
   715 lines in nexus/internal/apps/charges.
3. The harness must COMPILE and its tests must PASS with zero vectors present —
   an empty vector set is a legitimate state and must not be a failure. It must
   REFUSE (non-zero) if asked to grade with no vectors, rather than pass
   vacuously. A harness that reports PASS on an empty corpus is the exact
   fail-open this project has been bitten by; do not build one.
4. Write nexus/internal/apps/charges/conformance/README.md stating what the
   harness grades, what it cannot grade, and what it needs from a tenant.

## Non-negotiables
- No float in any money path, tests included. Integer minor units.
- PostgreSQL via pgx only.
- Every behavioural claim carries file:line to /Users/buv/fineract @ 426a23544.
- NEVER synthesise, transcribe or hand-write a vector.

## DONE means these exit 0. Paste RAW output including exit codes:
   cd nexus && go build ./... && go test ./...
   cd /Users/buv/oh-gerege-charges/.softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-charges/nexus

## Report exactly these three numbers, and nothing dressed up as success:
   1. harness lines written (excluding anything you copied verbatim — say what you copied)
   2. lines you REUSED rather than rewrote
   3. wall-clock minutes

Do NOT say "complete", "done", or "goal achieved". Report exit codes.
If a gate refuses, fix the code. Never edit a gate. Never add an exemption.
If you cannot make something pass, say so plainly and why. A truthful refusal
is worth more than a false pass.
