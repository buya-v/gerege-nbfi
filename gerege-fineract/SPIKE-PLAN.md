# Spike plan — Fineract as the Gerege NBFI core

Decided by Buyan on 13 Sep 2026 (see `DECISIONS.md`, FD-1..6). Target: one to two weeks. The work is executed by
OpenHands runs on DeepSeek, one isolated worktree each, and reviewed by the driver before merge.

**Scope rule:** every file this spike creates lives under `gerege-fineract/`. No run touches any other folder of the
repository, and nothing is written into the pinned Fineract checkout (`/Users/buv/fineract`) or the standing
reference instance (port 8443, tenants `gerege` and `default`).

## Steps

| Step | What it proves | Runs in | Throwaway |
| --- | --- | --- | --- |
| **S1 — tenant** | A Gerege tenant configures natively. It also measures: deposits can be hidden; the `Idempotency-Key` behaviour; reversals are appended, not edited | `spike/s1-tenant/` | `gf1-*` containers, port 8445 |
| **S2 — build** | A Gerege module builds into Fineract's custom image **out of tree** and loads at runtime | `extensions/`, `spike/s2-build/` | `gf2-*` containers, port 8446 |
| **S3 — extensions** | Three real extensions: national-ID validation on client create; the three-part name (FD-4); an event consumer feeding a stub payment rail, with the RTGS / ACH+ threshold in config. Plus whatever S1 shows config cannot do (deposit lock-out, a mandatory `Idempotency-Key`) | `extensions/`, `spike/s3-*` | as S2 |
| **S4 — acceptance** | The existing golden vectors and replayed Fineract scenarios still hold on the Gerege-configured, extended Fineract; a version bump leaves the extensions untouched | `spike/s4-acceptance/` | as S2 |
| **S5 — decision** | Effort per extension, any core change needed (target: none), operations notes for Gerege's own team (FD-6), a firm pilot estimate | `REPORT.md` | — |

S1 and S2 run in parallel: S1 needs no build, and S2 needs no tenant configuration. S3 needs S2's build path, and
S4 needs S1 and S3.

## Tooling facts the briefs rely on (checked 13 Sep)

- Image `fineract:latest` (id `e596339626bf`) is present locally. It is the build the project already pins
  (426a23544).
- Fineract's `settings.gradle` includes every `custom/<company>/<category>/<module>` directory automatically, and
  `:custom:docker` builds an image containing them. The `custom/acme` example shows the module layout.
- The host has no Java runtime. Gradle runs inside Docker with the local `eclipse-temurin:21-jdk` image, as the
  replay rig already does.
- Ports 8443 and 5432–5439 are taken; the spike uses 8445 and 8446. Disk: 136 GB free.

## Rules for every spike run

- Commit only under `gerege-fineract/`, with `git commit -F <file> </dev/null` and the message file inside the
  worktree. Never create or edit `AGENTS.md`, and never bypass a git hook. If a commit hangs, stop and report it.
- Throwaway containers carry the run's own prefix (`gf1-`, `gf2-`) and are removed at the end. Never stop, restart or
  write to any other container.
- Read-only SQL on the standing reference is allowed only to prove it was untouched.
- Money in anything the run writes is integer minor units (MNT has 2 digits). Raw oracle bodies are kept verbatim.
- PostgreSQL only. **Oracle Database is prohibited.**
- Every command runs in the foreground with a bound: `--max-time` for curl, `timeout` inside containers. No `&`,
  `jobs`, `wait`, or `sleep` over 60 seconds.
