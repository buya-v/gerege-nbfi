# OH-VOCAB — cob, origination, parties: VOCABULARY parity, not money

Repo: /Users/buv/oh-gerege-vocab   Branch: feat/OHVOCAB-ordinals (checked out)

## Why these three are different

Every context graded so far carries money. These three do not:

    cob           379 lines, 0 money tokens — Close-of-Business step ORDER and the runner
    origination   663 lines, 0 money tokens — LoanOriginator status vocabulary + mappings
    parties       906 lines, 0 money tokens — Client/Group status and legal-form vocabularies

A money-parity harness would pin nothing here. What they DO own is ENUM VOCABULARY, and
that is worth pinning for a specific reason: **Fineract persists enums as ORDINALS**, and a
wrong ordinal is a silent data corruption, not a crash. The whole HALF_UP/HALF_EVEN problem
in this repo was one integer — rounding-mode 4 versus 6. Same class of defect.

So each vector pins: enum NAME <-> ORDINAL <-> the value the oracle actually stores or
returns. If the port maps ACTIVE to 300 and Fineract means 100, every row written is wrong
and nothing throws.

## A SMALL harness. Do not copy a money harness.

Build on the SHARED CORE `nexus/internal/conformance` — it already gives you the vector
envelope, provenance admission, the store loader, capability default-deny and the report
line. Read `nexus/internal/apps/collateral/conformance` first: it is the smallest existing
harness and the closest shape to yours.

You need NO money cells, NO minor-unit parsing, NO rounding logic. If your harness starts
looking like `loan`'s, you have copied the wrong thing. Include a `cmd/conformance` entrypoint.

## Where the truth comes from

READ-ONLY use of the oracle is allowed and expected. Another agent is writing to it in
parallel — you must NOT create, update or delete anything, and must NOT change any
configuration row.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'

    GET /clients/template, /groups/template, /codes, /codes/{id}/codevalues  for parties
    GET /jobs and the COB business-step configuration                        for cob
    read-only SQL against m_client, m_group, m_code_value, m_batch_job        to see ORDINALS

The pinned reference source is Fineract at commit 426a23544e8426a38ae43ae404670a0a7e85b9eb.
Where an ordinal is only visible in Java source, CITE THE FILE AND LINE in the vector's note.

Capture raw responses to `.softhouse/capture/<ctx>/out/<case>-raw.json` with a `.status`
file each, exactly as the money contexts do, and commit them BEFORE promoting.

## Vector rules — unchanged

`provenance.kind = "oracle-capture"`, `capture_ref`, a REAL `shasum -a 256` in
`capture_sha256`, and `tenant_params`. TRANSCRIBE; never compute. If the oracle did not show
it, it does not go in a vector. A vector's note names the capture and field each value came from.

In each MANIFEST set `roundingSurface` to an explicit "none — this context carries no money"
so the record is uniform with the money contexts rather than silently absent.

## DO NOT REGISTER YOUR SCHEMA

Do NOT edit `nexus/internal/apps/loanschedule/conformance/`. A parallel agent and this one
would collide; the driver registers all schemas in one pass. Until then
`go test ./internal/apps/loanschedule/...` FAILS its store census — EXPECTED, not yours to
fix, and not a reason to delete vectors.

## Constraints

* READ-ONLY on the oracle. No writes of any kind. NEVER the `default` tenant.
* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or another context's harness.
* NEVER remove an assertion, a refusal or a test.
* COMMIT AFTER EACH CONTEXT.

## Done means

Per context: `go run ./internal/apps/<ctx>/conformance/cmd/conformance --root <repo>` prints
VERDICT: PASS with parity_pass == vector count; `cd nexus && go build ./...` clean. PROVE the
harness can fail: change a pinned ordinal to a wrong value -> VERDICT FAIL; forge a
capture_sha256 -> UNUSABLE; restore -> PASS. Paste it.

## Report

Per context: vector count, the verdict line, WHICH ordinals you pinned and where each was
observed, and one `shasum -a 256` beside the `capture_sha256` a vector cites. If a context's
vocabulary turns out not to be observable at all, say so plainly and leave it out — that is
a real finding, and collateral's valuation arithmetic already turned out to be exactly that.
