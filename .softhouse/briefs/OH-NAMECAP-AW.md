# OH-NAMECAP-AW — CAPTURE ONLY. The client display-name derivation, arm by arm.

Worktree: `/Users/buv/oh-gerege-namecap` (branch `feat/OHNAMECAPaw`)
Work ONLY in that directory. **You hold the oracle server.** A parallel run (`OH-LSCAP-AV`) uses an
in-process library call and never touches it.
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/parties.md` — captures, vectors, port functions.
2. `.softhouse/findings/F-2026-09-11-parties-graded-coverage.md` §4.1 — the target and exactly what a
   capture needs.
3. `.softhouse/capture/loan-writeoff-paid-instalment/req/client-OHWOPAID-C01-create.json` — a client-create
   body that the oracle ACCEPTED today. **Start from its shape** (office, legal form, dates, activation).

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE
**Do NOT write a vector, a drive, or any `.go` file.** A later run extends the seam and grades it.

## WHY
`DeriveDisplayName` [`nexus/internal/apps/parties/client.go:75`, ported from `Client.java:457-481`] is the
code behind CLAUDE.md's **"Names are three fields"**. It has three arms; the committed corpus observes
only the first (a non-blank `fullname` wins — `clients-1-raw.json`). No capture carries separate name parts.

## THE OBJECTIVE — three clients, each read back with its parts AND its derived display name
1. **Person, three distinct non-blank parts** — `firstname`, `middlename`, `lastname` all set. Use
   Mongolian-shaped values in Cyrillic (e.g. an ovog in `lastname`, a patronymic in `middlename`, a given name in
   `firstname` — record which Fineract field carries which, since that MAPPING is the whole point of the
   non-negotiable). **Synthetic names only — never a real person's.**
2. **Person, blank middle part** — `middlename` absent or empty: observes the blank-skip.
3. **Entity** (legal form ENTITY) — observes the arm that yields no joined name. If the oracle requires a
   `fullname` for an entity, **that requirement is the observation** — record it.

For each: save the request body, the create response, `GET /clients/{id}` (it exposes `displayName` and
the parts), and a **read-only** `SELECT id, firstname, middlename, lastname, fullname, display_name,
legal_form_enum FROM m_client WHERE id IN (…)` from **`gerege-oracle-db`** (NOT `fineract-db-1`) as
corroboration. Clients may be created PENDING — do not activate them unless the create requires it.

**If the oracle refuses a body, THE REFUSAL IS THE RESULT** — capture status and error body; commit; move
to the next arm. Do not SQL-insert anything. **Tenant `gerege` only — never `default`. SQL is read-only.**

Write `.softhouse/capture/parties-display-name/OWNER.md`: per client, the parts sent, the parts read back,
the `displayName` read back, and which of the three arms it observes — plus the field→ovog/patronymic/
given mapping you used and why.

## Rules of evidence
- Every record a vector will cite must be **JSON** (a psql dump cannot be cited — the wire-float guard
  refuses it). **Request bodies byte-stable.** Cyrillic must survive as UTF-8 in every file — check it.
- "The oracle" is the Fineract reference; **Oracle Database is prohibited.** PostgreSQL only.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/`, or `.softhouse/maps/`.**

## The bar and the budget
The bar must still pass: `go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY
with `§4.4.2-RECORDED-DECISION-EXIT`. ~300 iterations. **Commit after each client.**
**Write commit messages to a file (`git commit -F`). Never commit TASK.md.**
