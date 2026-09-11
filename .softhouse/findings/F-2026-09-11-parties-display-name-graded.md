# F-2026-09-11 — the three-field display-name rule is graded: one seam, four vectors, four drives, and `DeriveDisplayName` leaves `0.0%`

**Status:** RESOLVED. Closes §4.1 of
`F-2026-09-11-parties-graded-coverage.md` ("the name rule, NO complete observation →
needs a capture and a seam"). The capture it demanded was taken and committed first
(`OH-NAMECAP-AW`, merge `bd58361c`); this run adds the seam, the vectors and the drives
and grades it.
**Task:** `OH-NAMEGRADE-AY`, bounded context `parties`, branch `feat/OHNAMEGRADEay`.
**Subject target:** `internal/apps/parties/client.go:75` `DeriveDisplayName`, ported from
`Client.deriveDisplayName` [Client.java:457-481] — the code behind CLAUDE.md's
**"Names are three fields"**.
**No oracle was used and no `POST`/`PUT`/`DELETE` was issued by this run.** Every figure
is transcribed from an already-committed JSON capture.

## 1. The seam and the capability

The three pre-existing parties seams map an enum NAME to an integer ordinal
(`vector.go:126-135`, `admit.go:39-42`, `IsSchemaSeam`). None can carry a string, which is
why §4.1 said no existing seam could grade the name rule. The new seam is declared exactly
the way the three ordinal seams are:

* `.softhouse/capabilities-parties.json` — capability **`display-name`** with
  `in_graded_domain: true`, and seam **`parties-display-name`** with
  `status: {"display-name": "exercised"}`. The registry's `note` now says "Four
  capabilities are graded" and names the fourth.
* `conformance/vector.go` — `VocabularyDisplayName = "display-name"`, `SeamDisplayName =
  "parties-display-name"`, both added to `IsVocabulary`, `IsSchemaSeam` and
  `seamForVocabulary`; `Request` gains `legal_form` + `fullname` + `given_name` +
  `patronymic` + `ovog`; `Expect` gains `DisplayName`.
* `conformance/admit.go:39-42` admits the fourth seam and `:61-93` admits the display-name
  vocabulary: `legal_form` must name a `LegalForm` vocabulary member, `expect.ordinal` must
  be 0 (this seam grades no ordinal), and the ordinal vocabularies may not carry a
  display name.
* `conformance/grade.go` — `compareDisplayNameExpect` is selected by vocabulary; the
  display-name seam still grades **one** cell (`graded_cells=1`), a string instead of an
  integer.

**Request** is the party's legal form plus the four name fields. **Expect** is the
display-name string.

### Naming — names are three fields

Per the non-negotiable, no new identifier uses `first_name`/`last_name`. The three
name-part keys are named for what they carry and the mapping is stated in the `Request`
doc comment: `given_name` → Fineract `firstname`, `patronymic` → Fineract `middlename`,
`ovog` → Fineract `lastname`. `fullname` is Fineract's wire key verbatim because the
vector transcribes the wire value unchanged. `legal_form` carries the `LegalForm` enum NAME
(`PERSON`/`ENTITY`), the same stable identity the legal-form seam grades.

### How absent vs empty is graded (the entity arm)

E1 has two faces: `GET /clients/15` **omits** the `displayName` key, and
`m_client.display_name` holds the **empty string**. Go decodes an absent JSON key and an
explicit `""` to the same zero value, so the seam grades the entity arm as the empty
string, with `display_name` written **present-and-empty** in the vector so the intent is
explicit; it does not distinguish absent from empty, and nothing in the observation asks it
to. This is stated in `Expect`'s `EMPTY vs ABSENT` doc comment (`vector.go:162-168`).

## 2. The four promoted vectors

| vector | arm | request | expect | capture (JSON) | capture sha256 | vector sha256 |
|---|---|---|---|---|---|---|
| `DN-01-fullname-wins.json` | 1 | `PERSON`, `fullname="Path B Fixture Borrower"` | `"Path B Fixture Borrower"` | `capture/parties/out/clients-1-raw.json` | `e0144ecc…82c73df` | `7405c18e…25fd7da` |
| `DN-02-person-three-parts.json` | 2 | `PERSON`, given/patronymic/ovog all present | `"Синтетик Туршилтын Жишээ"` | `capture/parties-display-name/out/OHNAMECAP-P1-raw.json` | `1bc4a2d1…da8a170f6` | `5cd0f19e…608775e89` |
| `DN-03-person-blank-skip.json` | 2 | `PERSON`, patronymic absent | `"Синтетик Давхардалгүй"` | `capture/parties-display-name/out/OHNAMECAP-P2-raw.json` | `465eb5a3…ce8e97f225f` | `2dc62517…943f243688b` |
| `DN-04-entity-no-name.json` | 3 | `ENTITY`, three parts present | `""` | `capture/parties-display-name/out/OHNAMECAP-E1-m-client.json` | `d22527db…e705502664` | `91259f2d…cecbe9d4f1edf96` |

Every `capture_ref` is a JSON capture record and every `capture_sha256` was re-verified
against the bytes on disk after the vector was written (`shasum -a 256`, all four match).
Cyrillic is UTF-8 and was checked byte-for-byte against the captures. `DN-02`/`DN-03`
transcribe the GET bodies; `DN-04` transcribes the column read-back, because on the wire
the entity's `displayName` key is absent (recorded in the vector's `_note`). The four
vectors cite only committed captures.

## 3. The four drives, each discriminated by construction

Registered in `conformance/impl.go` (the `-list-implementations` names):

| drive | defect | designed to move |
|---|---|---|
| `parties-wrong-display-ovog-first` | joins the parts ovog → given → patronymic (family order) instead of Fineract's firstname → middlename → lastname | DN-02 **and** DN-03 |
| `parties-wrong-display-no-blank-skip` | joins all three slots without skipping blanks, leaving a double space | DN-03 only (`"Синтетик  Давхардалгүй"`); DN-02's three parts join identically |
| `parties-wrong-display-entity-joins-parts` | joins an ENTITY's present parts instead of yielding no name | DN-04 only |
| `parties-wrong-display-parts-over-fullname` | drops the fullname-wins arm and always derives from parts | DN-01 only |

### Measured WITHOUT and WITH the four vectors

`kills.sh parties <drive> <worktree>` over the 16-vector store (DN files temporarily
removed) vs the 20-vector committed store (DN files restored):

| drive | WITHOUT (16 vectors) | WITH (20 vectors) |
|---|---:|---:|
| `parties-wrong-display-ovog-first` | **0** | **2** |
| `parties-wrong-display-no-blank-skip` | **0** | **1** |
| `parties-wrong-display-entity-joins-parts` | **0** | **1** |
| `parties-wrong-display-parts-over-fullname` | **0** | **1** |

**No drive is inert, and no coverage was manufactured.** Each drive kills zero against the
corpus that existed before this run and kills the vector(s) it was built to see against the
committed corpus: the rule on inert drives is satisfied by measurement, not assertion. The
`WITHOUT` column is the whole discrimination argument — without the new vectors the four
drives are dead, with them each is live.

## 4. Coverage moved off `0.0%`

Prescribed command, from `nexus/`, `-count=1`:

    go test -count=1 -coverpkg=./internal/apps/parties \
        -coverprofile=/tmp/c.cov ./internal/apps/parties/conformance/...

| function | before | after |
|---|---:|---:|
| `client.go:75` `DeriveDisplayName` | **0.0%** | **100.0%** |
| `client.go:54` `NewClient` | **0.0%** | **100.0%** |
| package total | 6.4% | **11.8%** |

The reach is vector-driven: the committed-store test drives `LoadStore` → `Admit` → `Run`
against `parties-go`, and `DeriveDisplayName` is reached only through `DN-01..04`. Every
arm is exercised — fullname, complete join, blank-skip join, entity — so the 100% is all
four arms, not a partial path.

`go run ./internal/apps/parties/conformance/cmd/conformance -root ..` over the committed
store:

    VERDICT: PASS (exit 0)
    vectors_loaded=20 parity_pass=20 parity_fail=0 refused=0 inadmissible=0
    harness_error=0 graded_cells=20 invariant_violations=0
    nofloat: packages=48 files=393 tokens=408133 imports=1167 violations=0

`capcount.sh … parties parties-go` → **0**: the reference fails no vector, so the new
seam does not make the correct port wrong. `DeriveDisplayName`'s behaviour was not
changed; it reproduces Fineract, which is what parity requires. The driver's note stands:
Fineract's order renders given → patronymic → ovog under the chosen field mapping; how
Gerege *displays* a name is a separate, later decision.

## 5. Controls after the change

* `go build ./...` — clean; `gofmt -l` on the conformance package — clean.
* `go test ./...` — all packages pass (`-count=1` on the committed-store test).
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `§4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline`. **No `HARD guard failed`.**
  The wrong-ledger census stays pinned at **17**; exemption, P-number and wallet pins
  unchanged. The harness reported the six uncommitted-only-at-measure-time edits and
  accepted them (an uncommitted edit is accepted and printed); all six are committed here.
* Control `kills.sh parties parties-wrong-iota-ordinals` → **12** (unchanged).
* `redcount.sh <worktree> parties` → **8** (the four pre-existing drives and the four new
  ones all kill).
* `capcount.sh <worktree> parties parties-go` → **0**.
* The four capture `sha256`s were re-verified from disk after the vectors were written.

## 6. One bounded context

Every change is `parties`: one capability registry, one conformance package, four vectors
in `.softhouse/vectors/parties/`, one finding. `.softhouse/guards/` (12 pairs),
`.softhouse/conformance.sh` (census 17) and `.softhouse/maps/` are untouched. No float, no
PostgreSQL/Oracle access, no capture, no `POST`/`PUT`/`DELETE`.

This document was created by an AI agent (OpenHands) on behalf of the user.
