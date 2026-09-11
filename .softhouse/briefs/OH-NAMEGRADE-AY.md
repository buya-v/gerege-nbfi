# OH-NAMEGRADE-AY — grade the three-field display-name rule: add a seam. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-namegrade` (branch `feat/OHNAMEGRADEay`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/parties.md`.
2. `.softhouse/capture/parties-display-name/OWNER.md` — the three observed arms, with every figure.
3. `.softhouse/findings/F-2026-09-11-parties-graded-coverage.md` §4.1 — why no existing seam can carry a
   name, and what the seam needs.

## The target
`DeriveDisplayName` [`nexus/internal/apps/parties/client.go:75`, ported from `Client.java:457-481`] — the
code behind CLAUDE.md's **"Names are three fields"**. Three arms: a non-blank `fullname` wins; else a
person's present parts space-joined in the order firstname, middlename, lastname, blanks skipped; an
ENTITY yields no joined name. **Read-only today at 0.0%**: `Request` is `{vocabulary, name}` → ordinal.

## The observations — committed
* Arm 1, fullname wins: `.softhouse/capture/parties/out/clients-1-raw.json` (already cited by `CS-03`).
* Arms 2 and 3: `.softhouse/capture/parties-display-name/out/` — P1 (three parts → "Синтетик Туршилтын
  Жишээ"), P2 (middle absent → "Синтетик Давхардалгүй"), E1 (entity, three parts → no display name).
  **Verify every string against the files — Cyrillic, UTF-8.**

## The task — ONE property
> **The display name is the fullname if one is given; otherwise a person's present name parts joined by
> single spaces in Fineract's order, blanks skipped; an entity gets none.**

1. Add a seam (e.g. `parties-display-name`) and a capability in the graded domain, declared exactly the
   way the existing three ordinal seams are (`.softhouse/capabilities-parties.json`,
   `conformance/vector.go:126-135`, `admit.go:39-42`, `IsSchemaSeam`). Request: legal form + the four name
   fields; Expect: the display-name string (empty for the entity arm — say how absent vs empty is graded).
2. Promote FOUR vectors (arm 1 from clients-1, P1, P2, E1), each citing its JSON capture and sha256.
3. Drives, each discriminated here:
   * **ovog first** (lastname, firstname, middlename) — P1 and P2 move;
   * **no blank-skip** (a blank middle part leaves a double space) — P2 moves;
   * **entity joins its parts** — E1 moves;
   * **parts win over fullname** — arm 1 moves.
   Measure each WITHOUT and WITH your vectors; report every count.

Coverage of `DeriveDisplayName` must move off 0.0% from the committed-store test (`-count=1`).

**Do not change `DeriveDisplayName`'s behaviour.** It reproduces Fineract, which is what parity requires.
The driver has recorded that Fineract's order renders "given patronymic ovog" under the chosen field
mapping; how Gerege *displays* a name is a separate, later decision — not this run's.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or delete it with the
argument. **Do not manufacture coverage.**

## Non-negotiables (a violation is a rejection)
- **Names are three fields — never `first_name`/`last_name`** in any NEW identifier you write: name Go
  fields and JSON keys for what they carry (e.g. `given_name`, `patronymic`, `ovog`) or for Fineract's
  wire field verbatim where the vector transcribes the wire — and say which in the doc comment.
- **Do not touch `.softhouse/guards/`** (12 pairs), `.softhouse/conformance.sh` (census **17**), or
  `.softhouse/maps/`. No float. PostgreSQL only; **Oracle Database is prohibited.**
- `capture_ref` must be a **JSON** capture record; `capture_sha256`; **re-verify after writing**.
- **One bounded context: `parties`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure.** ~400 iterations. **Commit by
iteration 120.** **Write commit messages to a file (`git commit -F`). Never commit TASK.md.**
