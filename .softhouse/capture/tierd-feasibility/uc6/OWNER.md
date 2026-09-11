# Capture owner — UC6 Tier-D feasibility replay

- Instance: throwaway Fineract container used by `OH-TIERD2-BH` and `OH-TIERD3-BJ`
- Tenant identifier: `tierd`
- This is NOT tenant `gerege`; data here is from a throwaway PostgreSQL container
  created only for the feasibility replay.
- Source logs: `/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-uc6.log`
- Pinned Fineract source: `/Users/buv/fineract-tierd` (disposable `cp` of `/Users/buv/fineract`) @ `426a23544`
- Tenant config (from `../throwaway/docker-compose.tierd.yml`): timezone `Asia/Ulaanbaatar`,
  rounding mode `4` (HALF_UP), currency observed in the read-backs is **EUR** (decimalPlaces 2),
  port 8444, DB `fineract_tierd`. **Not** gerege's MNT.

## Provenance rule

These bodies are oracle output from the same pinned commit as the committed gerege captures
(`426a23544`), but they were produced on a **throwaway tenant** (`tierd`) with different seed
data and a different currency (EUR, not MNT). Per the task brief, **no vector may be promoted
from this capture** until the driver records the provenance decision (see
`F-2026-09-11-tierd-feasibility.md`, THIRD PASS). The tenant identifier is deliberately different
precisely so this data cannot be mistaken for a graded-tenant reading.

## Verified extraction (OH-TIERD3-BJ)

All bodies below were re-extracted direct from `feign-uc6.log` by line number and byte-compared
against the files on disk. Each body is byte-identical to the log (`req_body` for `*-request*`,
`resp_body` for the read-backs). Source line = 1-based line of the `[Api#method] ---> METHOD url`
arrow.

| file | source line | bytes | sha256 |
|---|---|---|---|
| `loan-1-create-request.json` | 22116 | 590 | `6fe65b32faa78d00617c0d3673ad81b192a601d373046f6a903589d63dd5527b` |
| `loan-1-approve-request.json` | 22169 | 149 | `8c20e909e14b61a90b89292109f6ad1b7dfaf9035700050a24aad44544c66718` |
| `loan-1-disburse-request.json` | 22301 | 129 | `f8babf6c1403fc47782096e1ddbe3e9331443e0d3d9d0535685757e3e6f5bd2c` |
| `loan-1-repayment-request.json` | 22450 | 123 | `fe7a36bd1ce488cf56683e2535c4921661da481ac5f11c2de5da8fe28f893fe4` |
| `loan-1-detail-associations-all.json` | 22145 | 14236 | `b38d5d38d621745b7dadd8c6c9e3b981600cc5225197c3fe902a378a2217460a` |
| `loan-1-schedule-repaymentSchedule.json` | 22527 | 16158 | `a087ced6e236036c56e5b3bce780ac04f76751d5a4e28d4f80aac0b520301e5c` |
| `loan-10-create-request.json` | 34891 | 780 | `80f00f4fee137db8977a4cc528712f05d2895e35eccf4ab2d0d27973aac99cd4` |
| `loan-10-approve-request.json` | 34944 | 149 | `8c20e909e14b61a90b89292109f6ad1b7dfaf9035700050a24aad44544c66718` |
| `loan-10-disburse-request-1.json` | 35045 | 128 | `1af3faa810d47f5fada5b952ecb75d90047fd2691c9371018c57771e0fa458ac` |
| `loan-10-disburse-request-2.json` | 35302 | 128 | `6e307f0e31e72fd6600dca42d010c4cf952e76366b932187b07a95e7ea49f227` |
| `loan-10-disburse-request-3.json` | 35451 | 128 | `e0b93e133c7fdfe24953a4003877e419e94c5134ec6565a4d9d81fa2c9a56950` |
| `loan-10-disburse-request-4.json` | 35480 | 128 | `d06c2725ec0caf19472e21e254e41477282be56cfd9ec87a4c5236dbbb5d2361` |
| `loan-10-repayment-request-1.json` | 35701 | 124 | `482a62fdc6baa5afff060f48d281ff83c1eee6d7ad39041280ac4263d024959e` |
| `loan-10-detail-all.json` | 34920 | 15213 | `f000ee66ea7a8ca5547d0c69f721a4612e1f7c7728f8e5278a46c13ac954cc6f` |
| `loan-10-schedule-repaymentSchedule.json` | 35777 | 17256 | `9d8c1d41c0e325e671fabb7feafabe54dc90545251f2e9506ff1ee5cc61484f0` |

### Correction — the salvaged extraction had 4 fabricated bodies

The capture salvaged by `OH-TIERD2-BH` had mis-attributed bodies. Re-extraction found and
replaced them (`OH-TIERD3-BJ`):

- `loan-10-create-request.json` held **loan 1's** create body (590 B, productId 50, clientId 1).
  It is now loan 10's own body (780 B, productId 96, clientId 10, three-tranche
  `disbursementData` 300/200/500). Confirmed against the `POST /loans` response `resourceId: 10`.
- `loan-10-disburse-request-2.json` and `-3.json` both held loan 1's 300 disbursement. They are
  now the true chain: disburse 2 = 200.00 (02 Jan), disburse 3 = 700.00 **rejected HTTP 403**
  (03 Jan, over the 1000 approved), disburse 4 = 500.00 (03 Jan). The 4 files now follow
  chronological log order, and file 3 documents the rejected over-disbursement.
- `loan-10-detail-all.json` was verified faithful as-is (it matches source line 34920, the
  `associations=all&exclude` read while status was
  `loanStatusType.submitted.and.pending.approval`).

Loan 1's files were verified unchanged. Every remaining file was byte-compared to the log.
