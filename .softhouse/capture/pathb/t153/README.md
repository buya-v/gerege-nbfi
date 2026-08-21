# T153 — the reviewer's own evidence for the independent review of T149

This directory is **not** a promotable capture set and carries **no attestation**. It is
the evidence T153 produced while reviewing T149's promotion of
`.softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json`. Nothing
here is promoted, and nothing here is a substitute for `t149/out/gerege/attestation.json`,
which remains the attested provenance of the vector itself.

Everything was taken live from the pinned reference oracle
(`https://localhost:8443/fineract-provider`, Fineract `426a23544e…`, PostgreSQL 18.3) on
2026-08-21 with `POST /loans?command=calculateLoanSchedule`, which persists nothing —
re-verified here rather than assumed: `select count(*) from m_loan` on `fineract_gerege`
read **4** immediately before and **4** immediately after a re-post of T149's own tie
request. **No container was restarted, rebuilt, re-seeded or reconfigured, and no
tenant row, product row or `c_configuration` row was written.** A review that mutates the
oracle to check a claim has destroyed the thing every other task is grading against.

## The requests, and why each exists

| request | sha256 | posted to | what it establishes |
|---|---|---|---|
| `t153-reobs-p9.json` | `b126725a…` | `gerege` | **(a)** the tie, re-observed. Textually identical to T149's `calc-t149-tie-p9.json` except for a trailing newline; written from the vector's own declared inputs rather than copied. |
| `t153-gerege-p11.json` | `7dd9f5ee…` | `gerege` | product 11 is ACT/ACT; confirms T149's byte-identity claim without taking it on report. |
| `t153-gerege-p1.json` | `d0894b4a…` | `gerege` | HALF_UP arm of a **same-product** counterfactual. |
| `t153-default-p1.json` | `d0894b4a…` | `default` | HALF_EVEN arm of it — **the same request bytes, the same product id, the other tenant.** |
| `t153-default-p10.json` | `06c75954…` | `default` | default's twin of gerege's canary product 11. |
| `t153-default-p9.json` | `b126725a…` | `default` | product ids do **not** align across tenants: id 9 on `default` is `T22 mode probe mult1`, not the 30/360 product. Recorded so a later reader does not repeat the mistake. |
| `t153-ctrl-p9-1m2-2026*.json` / `…-2024-c2.json` | — | `gerege` | **(b)** whether the schedule start year, which differs between the Path A vector `P-MNT-1M2` (2024-01-01) and T149's Path B control (2026-01-01), moves anything on this shape. |

## What came back

| response | sha256 | period-1 interest | total interest |
|---|---|---|---|
| `t153-gerege-p9-raw.json` | `39f56dc2…` | **20925.05** | 140457.89 |
| `t153-gerege-p11-raw.json` | `39f56dc2…` | 20925.05 | 140457.89 |
| `t153-gerege-p1-raw.json` | `39f56dc2…` | 20925.05 | 140457.89 |
| `t153-default-p1-raw.json` | `140ce792…` | **20925.04** | 140457.88 |
| `t153-default-p10-raw.json` | `140ce792…` | 20925.04 | 140457.88 |
| `t153-ctrl-p9-1m2-2026-raw.json` | `713a3560…` | 21600.00 | 144988.47 |
| `t153-ctrl-p9-1m2-2024-c2-raw.json` | `ff92fc5d…` | 21600.00 | 144988.47 |

`39f56dc2…` is byte-for-byte T149's committed `t149/out/gerege/T149-TIE-P9-raw.json`, and
`140ce792…` is byte-for-byte its committed HALF_EVEN arm
`t149/out/default-HALF-EVEN-ARM/pmode2-default-raw.json`. `713a3560…` is the digest of the
committed `pathb/out/B-01-baseline-raw.json` captured by T36 in a different fire.

`t153-ctrl-p9-1m2-2024-REFUSED-HTTP403-NOT-A-CAPTURE.json` is **an error body, not a
capture**: client 1 on `gerege` is activated 2026-01-01, so a 2024 submission is refused by
`error.msg.loan.submittal.cannot.be.before.client.activation.date`. It is kept under a name
that cannot be mistaken for a capture, and the measurement was re-taken on client 2
(activated 2023-01-01) as `…-2024-c2`. Filing a 403 body as a capture is the failure
`attest.py` aborts on; a reviewer's scratch directory does not get an exemption.

## The scripts

| script | what it asserts |
|---|---|
| `verify-transcription.py` | every `expect` cell of the vector is the exact text T153's **own** capture emitted, and every cell in `unrecorded_fields` is genuinely **absent** from the response. |
| `rederive-schedule-exact.py` | the whole 12-period schedule rebuilt in exact rational arithmetic from four declared inputs — principal, `27/125` p.a., n = 12, HALF_UP at 2 minor digits — agrees with the vector in every money cell. No float anywhere, including intermediates. |

## `verify/` — transcripts

| file | |
|---|---|
| `transcription-vs-t153-own-capture.txt` | 0 mismatches, 13 rows. |
| `rederive-schedule-exact.txt` | 12 of 12 periods and the total, re-derived. |
| `redgreen-three-arms-rerun.txt` | T149's `prove-redgreen.sh` re-run by T153 on the P-24 scratch merge. |
| `p24-scratch-merge-conformance.txt` | `bash .softhouse/conformance.sh` on the merge of T149 into **current** `main` (`9308679`). |
| `conformance-prove-selftest.txt` | `bash .softhouse/conformance.sh --prove`. |

Invoked with `bash` throughout, never `sh`.
