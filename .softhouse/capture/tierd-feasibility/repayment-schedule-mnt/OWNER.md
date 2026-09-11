# OWNER — Tier D `LoanRepaymentSchedule.feature` MNT capture

This directory owns the MNT read-backs captured by replaying the **whole**
`LoanRepaymentSchedule.feature` (12 progressive-schedule scenarios) against the throwaway
reference oracle. Capture only: no vector, no drive, no `.go`.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file: feature, scenarios, loans, and which read-back files belong to each |
| `replay-result-table.md` | the replay result table + the one UC10 failure |
| `replay-repsched-mnt.log` | raw cucumber/Gradle replay log (ANSI), 1,619 lines |
| `run-repsched-mnt.sh` | the exact driver used for the replay |
| `scenario-results.json` | machine-readable per-scenario PASSED/FAILED |
| `manifest-repsched.json` | full extraction manifest (all 12 loans; `committed` flag per entry) |
| `manifest-repsched-passed.json` | manifest of the committed files only (11 passed loans) |
| `summary-repsched.json` | extractor totals and per-loan counts |
| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |
| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |

## Source

- feature: `fineract-e2e-tests-runner/src/test/resources/features/LoanRepaymentSchedule.feature`
- throwaway tenant `tierd`; image `fineract:latest` `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`
  (proven identical to the standing reference oracle by `preflight.sh`)
- currency MNT (2 minor digits); money is quoted below in integer minor units
- capture: 159,152,907 B / 43,468 lines; extraction: 1,652 exchanges, 364 loan-keyed,
  12 loans, 424 files, 11,078,728 kept body bytes

## Scenario → loan map

One loan per scenario, created in scenario order; **loan `N` is UC`N`**. This is not assumed:
each loan's read-back `loanProductName` matches its scenario's product, and the sole failing
scenario names `resource 10` inside UC10.

| UC | feature line | result | loan | product | principal (minor) | read-backs | committed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UC1 | 5 | PASSED | loan 1 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` | 200000 | 16 | yes |
| UC2 | 76 | PASSED | loan 2 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` | 200000 | 16 | yes |
| UC3 | 147 | PASSED | loan 3 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` | 200000 | 16 | yes |
| UC4 | 218 | PASSED | loan 4 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` | 200000 | 16 | yes |
| UC5 | 272 | PASSED | loan 5 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` | 200000 | 16 | yes |
| UC6 | 326 | PASSED | loan 6 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` | 200000 | 16 | yes |
| UC7 | 380 | PASSED | loan 7 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` | 200000 | 21 | yes |
| UC8 | 528 | PASSED | loan 8 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` | 200000 | 21 | yes |
| UC9 | 676 | PASSED | loan 9 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` | 200000 | 21 | yes |
| UC10 | 824 | FAILED | loan 10 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` | 200000 | 13 | no (scenario failed) |
| UC11 | 1070 | PASSED | loan 11 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` | 200000 | 60 | yes |
| UC12 | 1315 | PASSED | loan 12 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` | 200000 | 60 | yes |

## Per-scenario read-back files

`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the
`create-request`, the `approve`/`disburse`/`repayment`/... command request+response pairs, and
the `GET` read-backs. The read-backs (kind `read`, all `LoansApi#retrieveOneLoan`) belonging to
each PASSED scenario are listed below. Files for the FAILED scenario (UC10 = loan 10) are
**not** committed; UC10 aborts at feature line 841, so its later read-backs never happen.

### UC1 — `PASSED` — loan 1 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation petiod: same as repayment  - UC1: 2nd disbursement on due date, interest recalculation enabled, partial period interest calculation enabled

- directory: `loans/loan-1/` · 23 files (1 create, 3 command requests, 3 command responses, 16 read-backs)

Read-backs:

- `loan-1-detail-associations-all-1.json` — line 22096, 11117 B, sha256 `e29806a5a18540927f5853911310bd41fd29fc7687303773b0b74de00a50cafd`
- `loan-1-detail-associations-empty.json` — line 22149, 6696 B, sha256 `027146d1184ecbffd9466bc29bdb5197054e85df0b01ba8f0de91f55addc1e0c`
- `loan-1-detail-no-associations-1.json` — line 22228, 8671 B, sha256 `f392b300b4604d227b5d1db49eca954d69b323403491400bebc7dfde26b7c070`
- `loan-1-detail-associations-all-2.json` — line 22252, 17957 B, sha256 `e19a65a00776e18ee684140fdac1a49977a9e7e234f0b986597d9808eceedb6a`
- `loan-1-detail-associations-transactions-1.json` — line 22276, 10591 B, sha256 `a22e44011bdec68405a7339aec881d070197241c361682c4a217976c5223544e`
- `loan-1-detail-associations-all-3.json` — line 22300, 17957 B, sha256 `e19a65a00776e18ee684140fdac1a49977a9e7e234f0b986597d9808eceedb6a`
- `loan-1-detail-associations-repaymentSchedule-1.json` — line 22353, 12971 B, sha256 `5cb03a1cb95b14346bf68c60f571629e0247f7115038ee51aa53f867edb70545`
- `loan-1-detail-associations-repaymentSchedule-2.json` — line 22377, 12971 B, sha256 `5cb03a1cb95b14346bf68c60f571629e0247f7115038ee51aa53f867edb70545`
- `loan-1-detail-associations-transactions-2.json` — line 22401, 10629 B, sha256 `fa6d61165b3c0a403d68974e7deb03f84518c9172837c1e986b06ad1eb3735bb`
- `loan-1-detail-no-associations-2.json` — line 22509, 8708 B, sha256 `83d2efb7dd19293fff8fba96f25f1c1ba5ac554a17b9dae2c46473c423578d0e`
- `loan-1-detail-associations-all-4.json` — line 22533, 20630 B, sha256 `421d5ddd71d2874844d6d2de9749dad9de60ae42413a590a0062949ec9734294`
- `loan-1-detail-associations-transactions-3.json` — line 22557, 12528 B, sha256 `efdc75c6d8a03be8ee7350e3d095d7e92679f426a8c7696d3f7a700ebf182b94`
- `loan-1-detail-associations-all-5.json` — line 22581, 20630 B, sha256 `421d5ddd71d2874844d6d2de9749dad9de60ae42413a590a0062949ec9734294`
- `loan-1-detail-associations-repaymentSchedule-3.json` — line 22634, 13441 B, sha256 `3be3cfdc2e6d071e80db608104428c0c9841a8f59c28458b80b30b7cbce5c55c`
- `loan-1-detail-associations-repaymentSchedule-4.json` — line 22658, 13441 B, sha256 `3be3cfdc2e6d071e80db608104428c0c9841a8f59c28458b80b30b7cbce5c55c`
- `loan-1-detail-associations-transactions-4.json` — line 22682, 64494 B, sha256 `036df06b9d7a17f93d704c5f91550e9349734f90ef2a74ada1fc3a4fc1fd5cde`

### UC2 — `PASSED` — loan 2 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC2: 2nd disbursement on due date, interest recalculation disabled, partial period interest calculation enabled

- directory: `loans/loan-2/` · 23 files (1 create, 3 command requests, 3 command responses, 16 read-backs)

Read-backs:

- `loan-2-detail-associations-all-1.json` — line 23570, 9619 B, sha256 `52fdb267deefe45512a7cac4f0a5ecd0cef3b0a91e4d71a370ac01c5747c3105`
- `loan-2-detail-associations-empty.json` — line 23623, 5198 B, sha256 `36c972dff1906f47fb414f33b588a99e98b9c3eadd8212b92e4705cd5c69009c`
- `loan-2-detail-no-associations-1.json` — line 23676, 7173 B, sha256 `5936b63099ff6a8417f9ac59ff76c0ea453e7f67cea66e63368190e63e567978`
- `loan-2-detail-associations-all-2.json` — line 23700, 13789 B, sha256 `0bd660514c18989d62beb559874afb0a712ef679cf3b1ea6aade48fe1a09355c`
- `loan-2-detail-associations-transactions-1.json` — line 23724, 9095 B, sha256 `5dc1442e25e3ecba2ef3aadea583a25e688a7b7b76016c1581d33b793061dcab`
- `loan-2-detail-associations-all-3.json` — line 23748, 13789 B, sha256 `0bd660514c18989d62beb559874afb0a712ef679cf3b1ea6aade48fe1a09355c`
- `loan-2-detail-associations-repaymentSchedule-1.json` — line 23801, 11473 B, sha256 `f26d486b3a1e100f1c7672becb5620210398bf25ed36f5d62c461f7661335ef6`
- `loan-2-detail-associations-repaymentSchedule-2.json` — line 23825, 11473 B, sha256 `f26d486b3a1e100f1c7672becb5620210398bf25ed36f5d62c461f7661335ef6`
- `loan-2-detail-associations-transactions-2.json` — line 23849, 9133 B, sha256 `0f99d98b26de3cae07bd5c1398a5f92a7533dd0f8ceddaaa0ec400303d790a5e`
- `loan-2-detail-no-associations-2.json` — line 23957, 7210 B, sha256 `e7ee1f6392ef15f5bf529f6c33a1ff5c93e04d6aeb675a48d735369a49147ec1`
- `loan-2-detail-associations-all-4.json` — line 23981, 16191 B, sha256 `1101f3bf30a226b8f46e9dc11cedac90fe18e5191847027810e30953e4f0b22d`
- `loan-2-detail-associations-transactions-3.json` — line 24005, 11034 B, sha256 `004f1375c3494d20258351b2a9ff5d00efff81cb76e64f1f08632a6eaf070664`
- `loan-2-detail-associations-all-5.json` — line 24029, 16191 B, sha256 `1101f3bf30a226b8f46e9dc11cedac90fe18e5191847027810e30953e4f0b22d`
- `loan-2-detail-associations-repaymentSchedule-3.json` — line 24082, 11943 B, sha256 `387b2eaeaf1717af775d8bc5b6bd06bc017365c9f88d3fcbd5f6647c18094ea0`
- `loan-2-detail-associations-repaymentSchedule-4.json` — line 24106, 11943 B, sha256 `387b2eaeaf1717af775d8bc5b6bd06bc017365c9f88d3fcbd5f6647c18094ea0`
- `loan-2-detail-associations-transactions-4.json` — line 24130, 63007 B, sha256 `7343011a77a4316d6419ea1ffb75b3edfe9b2c38672d2b59707a56a782cbbd09`

### UC3 — `PASSED` — loan 3 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC3: 2nd disbursement on due date, interest recalculation disabled, partial period interest calculation disabled

- directory: `loans/loan-3/` · 23 files (1 create, 3 command requests, 3 command responses, 16 read-backs)

Read-backs:

- `loan-3-detail-associations-all-1.json` — line 25016, 9617 B, sha256 `ae7b75a70930d2c342883556a402657af86f7fe26493b0c3323efd19b6c7e630`
- `loan-3-detail-associations-empty.json` — line 25069, 5196 B, sha256 `bd638ec68978425a423dcbb05f28c788aa20f2561b90aa0ba790b46e6895a111`
- `loan-3-detail-no-associations-1.json` — line 25122, 7171 B, sha256 `f6ac5acc1a23809d6be520b1da71adf16364d1a8b2f3ec61050c81990bf8a103`
- `loan-3-detail-associations-all-2.json` — line 25146, 13787 B, sha256 `53fb6d64d6e70a2de81dc6e8b12e2565befe31e00b0a5f86349362eaca6d53b3`
- `loan-3-detail-associations-transactions-1.json` — line 25170, 9093 B, sha256 `9a1e474d85aac4e052c2caab9247eeaf00b6427abcadef02de57b64672303578`
- `loan-3-detail-associations-all-3.json` — line 25194, 13787 B, sha256 `53fb6d64d6e70a2de81dc6e8b12e2565befe31e00b0a5f86349362eaca6d53b3`
- `loan-3-detail-associations-repaymentSchedule-1.json` — line 25247, 11471 B, sha256 `02fd1ac5335daa6752b68f4372df893f46614cc59781956432f8e379d72174f0`
- `loan-3-detail-associations-repaymentSchedule-2.json` — line 25271, 11471 B, sha256 `02fd1ac5335daa6752b68f4372df893f46614cc59781956432f8e379d72174f0`
- `loan-3-detail-associations-transactions-2.json` — line 25295, 9131 B, sha256 `adc702d24fbe1aa54f2570eaab91dcbce9bdeb4976355b6aba9bfa59d51450ab`
- `loan-3-detail-no-associations-2.json` — line 25403, 7208 B, sha256 `c9bf398633d62a9c0706a150dd291be4f66673cbe823fd0476d0d1c46d1b7627`
- `loan-3-detail-associations-all-4.json` — line 25427, 16189 B, sha256 `6936eaccb90f1c8938d7871b0905263db06157622aa64bead1edaa6bcb5c4a10`
- `loan-3-detail-associations-transactions-3.json` — line 25451, 11032 B, sha256 `c98418e537e032f937f9f37cab7cf15e2eb7190f84e9f6d15c446c17a86dd1c7`
- `loan-3-detail-associations-all-5.json` — line 25475, 16189 B, sha256 `6936eaccb90f1c8938d7871b0905263db06157622aa64bead1edaa6bcb5c4a10`
- `loan-3-detail-associations-repaymentSchedule-3.json` — line 25528, 11941 B, sha256 `208baf32b5b0c65a00ddcf7cda4967b0dbc8ebf7ddc75cfed92bc7310b74abac`
- `loan-3-detail-associations-repaymentSchedule-4.json` — line 25552, 11941 B, sha256 `208baf32b5b0c65a00ddcf7cda4967b0dbc8ebf7ddc75cfed92bc7310b74abac`
- `loan-3-detail-associations-transactions-4.json` — line 25576, 63005 B, sha256 `755bb6286ae49410264c175d71235dea739e1d25fde956f150f2d3bc8b2674f0`

### UC4 — `PASSED` — loan 4 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation petiod: same as repayment  - UC4: 2nd disbursement NOT on due date, interest recalculation enabled, partial period interest calculation enabled

- directory: `loans/loan-4/` · 23 files (1 create, 3 command requests, 3 command responses, 16 read-backs)

Read-backs:

- `loan-4-detail-associations-all-1.json` — line 26464, 11117 B, sha256 `07c47de6ae8f6f218eced69c3549a28bbe3b503ad9cf856ab7a8f1c185f368e6`
- `loan-4-detail-associations-empty.json` — line 26516, 6696 B, sha256 `676dbfd68a325a05f9b048c538c6c81fc91d2a860b2aeb0deaee1ec062cb8f90`
- `loan-4-detail-no-associations-1.json` — line 26569, 8671 B, sha256 `facb5356482734b5c16782260ed2225a606179228a2aa2ccad1aca5af9c66b83`
- `loan-4-detail-associations-all-2.json` — line 26593, 17959 B, sha256 `2fd1f8f169a496f2d7a6ad53a6bb97e37c401c7af7a2e57fbb5d5e721381c373`
- `loan-4-detail-associations-transactions-1.json` — line 26617, 10593 B, sha256 `bf301db7763b4bc05d909c400f13a837c1e5985d2bca671d81b5737e65d3eb2c`
- `loan-4-detail-associations-all-3.json` — line 26641, 17959 B, sha256 `2fd1f8f169a496f2d7a6ad53a6bb97e37c401c7af7a2e57fbb5d5e721381c373`
- `loan-4-detail-associations-repaymentSchedule-1.json` — line 26694, 12971 B, sha256 `ce8de86a0c92dee1a0ffdddaca3d7ee7a5adc6325c020825f71dc4420bfd3b42`
- `loan-4-detail-associations-repaymentSchedule-2.json` — line 26718, 12971 B, sha256 `ce8de86a0c92dee1a0ffdddaca3d7ee7a5adc6325c020825f71dc4420bfd3b42`
- `loan-4-detail-associations-transactions-2.json` — line 26742, 10631 B, sha256 `e2015909be688cf83365c86908b9c1b3d5839143e63c2c603753336707a2ac77`
- `loan-4-detail-no-associations-2.json` — line 26850, 8708 B, sha256 `85fc53a77cdd31357a7a09698796fd9a8c0b3fa84ec067137f45730d5bf56708`
- `loan-4-detail-associations-all-4.json` — line 26874, 20634 B, sha256 `cf8c9a7c155f9c5cd285fd21b35a4aa220a8bf522dda54663261e10ff3f7bcb3`
- `loan-4-detail-associations-transactions-3.json` — line 26898, 12534 B, sha256 `963c64ccddd9b68423620c375269290392187cc98a2a2ba42ca4fa8d10759c24`
- `loan-4-detail-associations-all-5.json` — line 26922, 20634 B, sha256 `cf8c9a7c155f9c5cd285fd21b35a4aa220a8bf522dda54663261e10ff3f7bcb3`
- `loan-4-detail-associations-repaymentSchedule-3.json` — line 26975, 13438 B, sha256 `1e978940e4b6c79376ddf05162af1fd5f482d9db8d2ca64d26f740d98a02ced3`
- `loan-4-detail-associations-repaymentSchedule-4.json` — line 26999, 13438 B, sha256 `1e978940e4b6c79376ddf05162af1fd5f482d9db8d2ca64d26f740d98a02ced3`
- `loan-4-detail-associations-transactions-4.json` — line 27023, 35058 B, sha256 `0430e55b601df803fda395dbf8a95e70d45fcc946aeecdf8b0266f14feea223d`

### UC5 — `PASSED` — loan 5 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC5: 2nd disbursement NOT on due date, interest recalculation disabled, partial period interest calculation enabled

- directory: `loans/loan-5/` · 23 files (1 create, 3 command requests, 3 command responses, 16 read-backs)

Read-backs:

- `loan-5-detail-associations-all-1.json` — line 27910, 9612 B, sha256 `e14189a864491d6224be63679633b41d8687f5c4182b5f7dc232a3d7f3618cd4`
- `loan-5-detail-associations-empty.json` — line 27963, 5191 B, sha256 `43c583f528a4319ff81c0ec08b0188a8cdc0b110f9e8ef21af903c16a5400222`
- `loan-5-detail-no-associations-1.json` — line 28016, 7166 B, sha256 `2fd0d26c49aae25fd125500e9b3c24889f1e591fd284f2d646d3f50e05d23b00`
- `loan-5-detail-associations-all-2.json` — line 28040, 13784 B, sha256 `31361d212e77f4b22a0fbfc1497375734dfb82bcbd05d5ae8abe3587a78a56c7`
- `loan-5-detail-associations-transactions-1.json` — line 28064, 9090 B, sha256 `543fb4c7c0de6144d0598facda9872cbbc56c961d4f1cd7c720f91d4ee9f8f48`
- `loan-5-detail-associations-all-3.json` — line 28088, 13784 B, sha256 `31361d212e77f4b22a0fbfc1497375734dfb82bcbd05d5ae8abe3587a78a56c7`
- `loan-5-detail-associations-repaymentSchedule-1.json` — line 28141, 11466 B, sha256 `6c8f65874b8bf6101a8c075fac2274dd12f118c259dd5fcaf0010965d4094cb5`
- `loan-5-detail-associations-repaymentSchedule-2.json` — line 28165, 11466 B, sha256 `6c8f65874b8bf6101a8c075fac2274dd12f118c259dd5fcaf0010965d4094cb5`
- `loan-5-detail-associations-transactions-2.json` — line 28189, 9128 B, sha256 `5591fe015413a86cd9e7ef58702128710824babe3372871f3b3e6137b1d687b9`
- `loan-5-detail-no-associations-2.json` — line 28297, 7203 B, sha256 `413408a26eabb4f06ea2588e20894f348b4bcc092442b8ce9e083b0dda9dcdf3`
- `loan-5-detail-associations-all-4.json` — line 28321, 16188 B, sha256 `dc67657e72a6c494e7a24efdf51a3e85af2d5a912ba8067e9c44c750e72f6e31`
- `loan-5-detail-associations-transactions-3.json` — line 28345, 11033 B, sha256 `43fa6bd78c3c76c287e6978b6c447069d7d86db7eccac96954c43e4ae7b66b46`
- `loan-5-detail-associations-all-5.json` — line 28369, 16188 B, sha256 `dc67657e72a6c494e7a24efdf51a3e85af2d5a912ba8067e9c44c750e72f6e31`
- `loan-5-detail-associations-repaymentSchedule-3.json` — line 28422, 11934 B, sha256 `8a66f960493cb3ae446cfc36ac12100e36ca7ffe60d757138ccbd61c26ad1931`
- `loan-5-detail-associations-repaymentSchedule-4.json` — line 28446, 11934 B, sha256 `8a66f960493cb3ae446cfc36ac12100e36ca7ffe60d757138ccbd61c26ad1931`
- `loan-5-detail-associations-transactions-4.json` — line 28470, 33558 B, sha256 `23d648515754cf5b942e166bca2cc0833a756ef77210b8ff5e2ae6b0508e1c1d`

### UC6 — `PASSED` — loan 6 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC6: 2nd disbursement NOT on due date, interest recalculation disabled, partial period interest calculation disabled

- directory: `loans/loan-6/` · 23 files (1 create, 3 command requests, 3 command responses, 16 read-backs)

Read-backs:

- `loan-6-detail-associations-all-1.json` — line 29357, 9618 B, sha256 `fba1521aef0a4b600f043c7b816e413b66e6a8299cdaa2bea23898cbe8e435f1`
- `loan-6-detail-associations-empty.json` — line 29410, 5197 B, sha256 `9836ccc333b0381671645131278299af749d204081f396a436418afdde75c97f`
- `loan-6-detail-no-associations-1.json` — line 29463, 7172 B, sha256 `1bbce00cb383b80eb6637053e6adbc1e908e3ab1f761c4f5cc94e2673397e280`
- `loan-6-detail-associations-all-2.json` — line 29487, 13791 B, sha256 `5cd9902ccdf36c5cc14f0e286d3fdffb25e321091d36c995642b8da283c10464`
- `loan-6-detail-associations-transactions-1.json` — line 29511, 9096 B, sha256 `cf5cacbd739450c507f0f649f7fd29ead97dbc8508f542d82207451a0a878413`
- `loan-6-detail-associations-all-3.json` — line 29535, 13791 B, sha256 `5cd9902ccdf36c5cc14f0e286d3fdffb25e321091d36c995642b8da283c10464`
- `loan-6-detail-associations-repaymentSchedule-1.json` — line 29588, 11473 B, sha256 `bc04e263ce2668e21d2deca3cc0852675c5fa3e2169752f251cdd188959d1a4e`
- `loan-6-detail-associations-repaymentSchedule-2.json` — line 29612, 11473 B, sha256 `bc04e263ce2668e21d2deca3cc0852675c5fa3e2169752f251cdd188959d1a4e`
- `loan-6-detail-associations-transactions-2.json` — line 29636, 9134 B, sha256 `fd7f081902fb29a904f2cc49a290ed81c9acc3d95dba7c0af2b5770a6eefc4be`
- `loan-6-detail-no-associations-2.json` — line 29744, 7209 B, sha256 `e13f3c2cb280c8679b87033edbc2a790187746d4b122657ece370db69fd08e73`
- `loan-6-detail-associations-all-4.json` — line 29768, 16195 B, sha256 `86cc840242cbc5b1af49290bdc10f9b04aec0e5a564a5aa8ea9a8c5f189ab147`
- `loan-6-detail-associations-transactions-3.json` — line 29792, 11039 B, sha256 `e4eb92a71ed806153dc86a4491ce463eee1948fc395d7533dcd6809589562922`
- `loan-6-detail-associations-all-5.json` — line 29816, 16195 B, sha256 `86cc840242cbc5b1af49290bdc10f9b04aec0e5a564a5aa8ea9a8c5f189ab147`
- `loan-6-detail-associations-repaymentSchedule-3.json` — line 29869, 11941 B, sha256 `4cbb5858af9baf43a3065e30cab797ae5e6fbc81079975a87d2376e523975c7a`
- `loan-6-detail-associations-repaymentSchedule-4.json` — line 29893, 11941 B, sha256 `4cbb5858af9baf43a3065e30cab797ae5e6fbc81079975a87d2376e523975c7a`
- `loan-6-detail-associations-transactions-4.json` — line 29917, 33564 B, sha256 `7cdb667d47faf281f131fb1a8c0d710b6700bb96d2f5d01d9e79e5b975813a46`

### UC7 — `PASSED` — loan 7 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC7: 2nd disbursement is in the middle of 2nd period + backdated repayment, interest recalculation enabled, partial period interest calculation enabled

- directory: `loans/loan-7/` · 30 files (1 create, 4 command requests, 4 command responses, 21 read-backs)

Read-backs:

- `loan-7-detail-associations-all-1.json` — line 30803, 11116 B, sha256 `8507fcbf8094e38c9ea28e16e9b1788eead4e205f8d0d84759c45082e6e60ea8`
- `loan-7-detail-associations-empty.json` — line 30856, 6695 B, sha256 `04fb5959a6d86d4d6353c8a89ae7d652abd900a2a95089599d0adb5fb088226a`
- `loan-7-detail-no-associations-1.json` — line 30909, 8670 B, sha256 `2424eeee61c67758d2b06fcec824454a743c2f856d572b0166887546f941c114`
- `loan-7-detail-associations-all-2.json` — line 30933, 17961 B, sha256 `bf65c6d48d5ba7641d2e95246c0747fac1f3419016ca6f2bdcb9c397e011f968`
- `loan-7-detail-associations-transactions-1.json` — line 30957, 10594 B, sha256 `c19504da009c7ef799d2159e1074d6dd7f2987add8c329f2168c7632ea5d3542`
- `loan-7-detail-associations-all-3.json` — line 30981, 17961 B, sha256 `bf65c6d48d5ba7641d2e95246c0747fac1f3419016ca6f2bdcb9c397e011f968`
- `loan-7-detail-associations-repaymentSchedule-1.json` — line 31034, 12971 B, sha256 `29ce6d7b52000e066e2ef980d199d5b4b423ca623d4e95ede6a135721f05fd51`
- `loan-7-detail-associations-repaymentSchedule-2.json` — line 31058, 12971 B, sha256 `29ce6d7b52000e066e2ef980d199d5b4b423ca623d4e95ede6a135721f05fd51`
- `loan-7-detail-associations-transactions-2.json` — line 31082, 10632 B, sha256 `5047ea4fa56261dffe512a2a5860e36711387aa159e54afeffa17c1620346189`
- `loan-7-detail-no-associations-2.json` — line 31273, 8881 B, sha256 `c55df2bca6ff5b46748dd8b473075e4e6d77bc4a3d699da63dd1aee6c5475cc7`
- `loan-7-detail-associations-all-4.json` — line 31297, 72963 B, sha256 `bb2ed8565fcfe3207bf679eac0f235649ee1bf49cddd0a15c519b9d276e67b4a`
- `loan-7-detail-associations-transactions-3.json` — line 31321, 64715 B, sha256 `c32646962cf51e85d5382041d16990a62f1f41ab5706e9b9379fbcf0dcbf1bff`
- `loan-7-detail-associations-all-5.json` — line 31345, 72963 B, sha256 `bb2ed8565fcfe3207bf679eac0f235649ee1bf49cddd0a15c519b9d276e67b4a`
- `loan-7-detail-associations-repaymentSchedule-3.json` — line 31398, 13660 B, sha256 `7d88124bb0fc50b303ef530645cfb8c9fbb720f1182f76199a951f782f516ef5`
- `loan-7-detail-associations-repaymentSchedule-4.json` — line 31422, 13660 B, sha256 `7d88124bb0fc50b303ef530645cfb8c9fbb720f1182f76199a951f782f516ef5`
- `loan-7-detail-associations-transactions-4.json` — line 31446, 88973 B, sha256 `723e587dcb2ee63676e1e10fe972200ad7d9aa10e8f050c2d8d7ad239637e616`
- `loan-7-detail-associations-transactions-5.json` — line 31499, 90726 B, sha256 `b5aa472c61afe30f86c5732d530262f1acedc9d88b4b2eb6144682717f69695d`
- `loan-7-detail-associations-all-6.json` — line 31523, 99039 B, sha256 `47e55addbfefcfd120624036ee7b91472804be25e0a174253b9ad4e58c6734bc`
- `loan-7-detail-associations-repaymentSchedule-5.json` — line 31547, 13552 B, sha256 `908aa75b594711f01a9fc4ddd64745dc7e66a024cd3a4dc9c7cdff3469d822e8`
- `loan-7-detail-associations-repaymentSchedule-6.json` — line 31571, 13552 B, sha256 `908aa75b594711f01a9fc4ddd64745dc7e66a024cd3a4dc9c7cdff3469d822e8`
- `loan-7-detail-associations-transactions-6.json` — line 31595, 90726 B, sha256 `b5aa472c61afe30f86c5732d530262f1acedc9d88b4b2eb6144682717f69695d`

### UC8 — `PASSED` — loan 8 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC8: 2nd disbursement is in the middle of 2nd period + backdated repayment, interest recalculation disabled, partial period interest calculation enabled

- directory: `loans/loan-8/` · 30 files (1 create, 4 command requests, 4 command responses, 21 read-backs)

Read-backs:

- `loan-8-detail-associations-all-1.json` — line 32483, 9616 B, sha256 `6f99bd241dd02efb3b9b4f323c3c624ce711b53a306b53175ebbf5d39dc61dc0`
- `loan-8-detail-associations-empty.json` — line 32536, 5195 B, sha256 `0851a74cdadaa2f70407d644d2211b02d040a157986e824865343bf08fb6a330`
- `loan-8-detail-no-associations-1.json` — line 32589, 7170 B, sha256 `541e9ad8d1c4f2cb80168c849f33de84f05e58cbc12f08c6823be392a951915a`
- `loan-8-detail-associations-all-2.json` — line 32613, 13789 B, sha256 `9c548cd1d133ad569cca81a85258b4f9db7f315a340072721b447a2ae0f854bd`
- `loan-8-detail-associations-transactions-1.json` — line 32637, 9094 B, sha256 `a173c511caa378acd97ebe47b90134d6e0e5ae732704426ebb35d322e477fb36`
- `loan-8-detail-associations-all-3.json` — line 32661, 13789 B, sha256 `9c548cd1d133ad569cca81a85258b4f9db7f315a340072721b447a2ae0f854bd`
- `loan-8-detail-associations-repaymentSchedule-1.json` — line 32714, 11471 B, sha256 `da1daf6e62128d2fef16d1e9fa0db674397994665e5ffbfca82c87158560b7d6`
- `loan-8-detail-associations-repaymentSchedule-2.json` — line 32738, 11471 B, sha256 `da1daf6e62128d2fef16d1e9fa0db674397994665e5ffbfca82c87158560b7d6`
- `loan-8-detail-associations-transactions-2.json` — line 32762, 9132 B, sha256 `d1b909a9ed206e40c307e5d81c153b1e5b35bef63f31cdaae103b25b7e7961e4`
- `loan-8-detail-no-associations-2.json` — line 32954, 7381 B, sha256 `72ed85741a2a9a1256c49bf2a1abd4d6113549535b9fbab8a10cbb3b13fd41f7`
- `loan-8-detail-associations-all-4.json` — line 32978, 68491 B, sha256 `acbd87e42f060aec37597e70e0817122f1fcc32f9a5699e53f40ff7cb4d3a62d`
- `loan-8-detail-associations-transactions-3.json` — line 33002, 63215 B, sha256 `0cc8ea416394413ca0e1ffa15ba1b9071133abe035bcb8460d60b7b8f77fd12d`
- `loan-8-detail-associations-all-5.json` — line 33026, 68491 B, sha256 `acbd87e42f060aec37597e70e0817122f1fcc32f9a5699e53f40ff7cb4d3a62d`
- `loan-8-detail-associations-repaymentSchedule-3.json` — line 33079, 12160 B, sha256 `96e35835221bb9edf0ba6743f2d24fa798eb9565b74c7685412f8f8a633ddddb`
- `loan-8-detail-associations-repaymentSchedule-4.json` — line 33103, 12160 B, sha256 `96e35835221bb9edf0ba6743f2d24fa798eb9565b74c7685412f8f8a633ddddb`
- `loan-8-detail-associations-transactions-4.json` — line 33127, 87473 B, sha256 `4588871cf82c6732565fdc29ee1f7b2b8ac69523e042fa93ad185c495ff3dbf6`
- `loan-8-detail-associations-transactions-5.json` — line 33180, 89226 B, sha256 `73bef93b7caafa7700f7749c2ab6a4122633bc0bee7f06d2bc31f529b8a9d597`
- `loan-8-detail-associations-all-6.json` — line 33204, 94567 B, sha256 `40b977ff114e7318b27a5a41da102da6117f977c3373d1b85c4fb9dbea4ed852`
- `loan-8-detail-associations-repaymentSchedule-5.json` — line 33228, 12052 B, sha256 `cebb0c13f2639ec1a9c2832c4c57a7da29f2b7b09e3d5da2cb574232155104b9`
- `loan-8-detail-associations-repaymentSchedule-6.json` — line 33252, 12052 B, sha256 `cebb0c13f2639ec1a9c2832c4c57a7da29f2b7b09e3d5da2cb574232155104b9`
- `loan-8-detail-associations-transactions-6.json` — line 33276, 89226 B, sha256 `73bef93b7caafa7700f7749c2ab6a4122633bc0bee7f06d2bc31f529b8a9d597`

### UC9 — `PASSED` — loan 9 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC9: 2nd disbursement is in the middle of 2nd period + backdated repayment, interest recalculation disabled, partial period interest calculation disabled

- directory: `loans/loan-9/` · 30 files (1 create, 4 command requests, 4 command responses, 21 read-backs)

Read-backs:

- `loan-9-detail-associations-all-1.json` — line 34163, 9616 B, sha256 `1ab587108a65242d3761dc2d486bcd919afd4e1f04ea7d17a21f32c764ad2f6a`
- `loan-9-detail-associations-empty.json` — line 34216, 5195 B, sha256 `b6cf84599bbb5919b1ac4cdd6ade93ca5fc516ef2ef6803ca01577dc5f0ad40c`
- `loan-9-detail-no-associations-1.json` — line 34269, 7170 B, sha256 `ed28aacc767d60958d7092887f6a19a625b9b9f3f7ffb75d7ac67545c01a87bb`
- `loan-9-detail-associations-all-2.json` — line 34293, 13789 B, sha256 `d015954f70d6308eb2530e3d15649044b9bde0227b7dbd9cb0d5df3f0a3dfd64`
- `loan-9-detail-associations-transactions-1.json` — line 34317, 9094 B, sha256 `7699a9d6a9e5cbe65cbfb48b730c5a78d9b9b69e20ac040240d7bf6c3cd2077d`
- `loan-9-detail-associations-all-3.json` — line 34341, 13789 B, sha256 `d015954f70d6308eb2530e3d15649044b9bde0227b7dbd9cb0d5df3f0a3dfd64`
- `loan-9-detail-associations-repaymentSchedule-1.json` — line 34394, 11471 B, sha256 `d081409b5b098ec558da7dc8e4d36ee4316e3aec9308aa2729eb9bb80ef9cdd4`
- `loan-9-detail-associations-repaymentSchedule-2.json` — line 34418, 11471 B, sha256 `d081409b5b098ec558da7dc8e4d36ee4316e3aec9308aa2729eb9bb80ef9cdd4`
- `loan-9-detail-associations-transactions-2.json` — line 34442, 9132 B, sha256 `1a34bf211fdc92c37caaed1fd96c3d53810777d9a453546b18c850ef4c1ec990`
- `loan-9-detail-no-associations-2.json` — line 34634, 7381 B, sha256 `8ef518981d526742ac48af0e5a64c47e63ae01b438463bc570ed8a84acf3f438`
- `loan-9-detail-associations-all-4.json` — line 34658, 68491 B, sha256 `4afcc94aeccb90d48611f87304badaacfe7e9aa2a55ca629ead89d9ddfafda20`
- `loan-9-detail-associations-transactions-3.json` — line 34682, 63215 B, sha256 `98d0255dfdd8653c2f72c7767c518b581dcc1e82db81cfd8708fa5c3080466a2`
- `loan-9-detail-associations-all-5.json` — line 34706, 68491 B, sha256 `4afcc94aeccb90d48611f87304badaacfe7e9aa2a55ca629ead89d9ddfafda20`
- `loan-9-detail-associations-repaymentSchedule-3.json` — line 34759, 12160 B, sha256 `97bb7dc7cd790b3e4a737cd3d13c94b4fe9cfea584e6e75a799692f74517bb58`
- `loan-9-detail-associations-repaymentSchedule-4.json` — line 34783, 12160 B, sha256 `97bb7dc7cd790b3e4a737cd3d13c94b4fe9cfea584e6e75a799692f74517bb58`
- `loan-9-detail-associations-transactions-4.json` — line 34807, 87473 B, sha256 `3f5f37cfcd781778fb191c8971531c6140c70fe263153b91cfd51663af7a8f1e`
- `loan-9-detail-associations-transactions-5.json` — line 34860, 89226 B, sha256 `29b117d4a345792cc2a80da536c2640713dc225211cd1fcfc5d0b7b675254ccd`
- `loan-9-detail-associations-all-6.json` — line 34884, 94567 B, sha256 `515caaf5df6e6ad4fe031900592c1353bda4860b02ca8ded4652db2e7e0833fb`
- `loan-9-detail-associations-repaymentSchedule-5.json` — line 34908, 12052 B, sha256 `268da561790ae6d5a3c41a101033c6eac5e9484b8fd4a4e3445d19b960b24b89`
- `loan-9-detail-associations-repaymentSchedule-6.json` — line 34932, 12052 B, sha256 `268da561790ae6d5a3c41a101033c6eac5e9484b8fd4a4e3445d19b960b24b89`
- `loan-9-detail-associations-transactions-6.json` — line 34956, 89226 B, sha256 `29b117d4a345792cc2a80da536c2640713dc225211cd1fcfc5d0b7b675254ccd`

### UC10 — `FAILED` — loan 10 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC10: complex transactions, interest recalculation enabled, partial period interest calculation enabled

- NOT committed (scenario failed at feature line 841; see `replay-result-table.md`).
- partial capture: 22 exchanges retained in `manifest-repsched.json`, `committed: false`.

### UC11 — `PASSED` — loan 11 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC11: complex transactions, interest recalculation disabled, partial period interest calculation enabled

- directory: `loans/loan-11/` · 87 files (1 create, 13 command requests, 13 command responses, 60 read-backs)

Read-backs:

- `loan-11-detail-associations-all-1.json` — line 37331, 9613 B, sha256 `5772ececf77e733134ab5b0ff4a7bc1e0f29c5cc58736c005a9ee655a125afc3`
- `loan-11-detail-associations-empty.json` — line 37384, 5192 B, sha256 `c4079f3f3b74183f2784c16d2a922a1a830b14541346e672da6dfc2036d8811a`
- `loan-11-detail-no-associations-1.json` — line 37437, 7167 B, sha256 `32017340c328ce22421473893e74db5608461cb0a31f89c41b09119757152a65`
- `loan-11-detail-associations-all-2.json` — line 37461, 13788 B, sha256 `b35d0a23f0e7ffb37b53ea7128eb1edc67143747daacda4520b560fa9fb9de81`
- `loan-11-detail-associations-transactions-1.json` — line 37485, 9092 B, sha256 `1d61ddceb09ca4529724515d070bafdf973bf9b189588ab9a66c047dc6546b96`
- `loan-11-detail-associations-all-3.json` — line 37509, 13788 B, sha256 `b35d0a23f0e7ffb37b53ea7128eb1edc67143747daacda4520b560fa9fb9de81`
- `loan-11-detail-no-associations-2.json` — line 37759, 7378 B, sha256 `8fe56e3a57a0ea42ccd687ef6ef28bc20c5e4f9a192e8a75b3d47244317c1b4c`
- `loan-11-detail-associations-all-4.json` — line 37783, 92802 B, sha256 `831b483f9c11dd24c0db9da56542e641135018e51c425a26eafd137002ab2a4a`
- `loan-11-detail-associations-transactions-2.json` — line 37807, 87516 B, sha256 `8918a6707dd54d3084165e25143748fa86e8ad83bff91a9da3f08ebcb4519289`
- `loan-11-detail-associations-all-5.json` — line 37831, 92802 B, sha256 `831b483f9c11dd24c0db9da56542e641135018e51c425a26eafd137002ab2a4a`
- `loan-11-detail-associations-transactions-3.json` — line 37884, 89271 B, sha256 `14883924a127e6a21f9ba85eff21072c7e7e3dfee9abda71562960c81bb03133`
- `loan-11-detail-associations-all-6.json` — line 37908, 94628 B, sha256 `9e726de5dde2ac213756e779d87b09458f27b30e841a660728e10fbf28af9c77`
- `loan-11-detail-associations-repaymentSchedule-1.json` — line 37932, 12063 B, sha256 `6786fe4f0a63a1782c06d71062736313d43676f0c758e614d9d59707be6446f2`
- `loan-11-detail-associations-repaymentSchedule-2.json` — line 37956, 12063 B, sha256 `6786fe4f0a63a1782c06d71062736313d43676f0c758e614d9d59707be6446f2`
- `loan-11-detail-associations-transactions-4.json` — line 38093, 139749 B, sha256 `a661d91f5446e17344170806c49ee6a1987408d9eb0c19a0cfcfaace81c43128`
- `loan-11-detail-associations-all-7.json` — line 38117, 145203 B, sha256 `6c61b8ee62ce399e94c95d5489f395e19400006c9048e972950c58187c6afff4`
- `loan-11-detail-associations-repaymentSchedule-3.json` — line 38141, 12159 B, sha256 `6deeef59c43d95a340b735d668a4ec1bb8f3d03dc85548073ff25f9b63eb6e7e`
- `loan-11-detail-associations-repaymentSchedule-4.json` — line 38165, 12159 B, sha256 `6deeef59c43d95a340b735d668a4ec1bb8f3d03dc85548073ff25f9b63eb6e7e`
- `loan-11-detail-associations-transactions-5.json` — line 38302, 143439 B, sha256 `83ffeb032d1cbb2db834fcc920b1ca77a0e454bcb49326b5878065418ccf593d`
- `loan-11-detail-associations-all-8.json` — line 38326, 148922 B, sha256 `dd093a5a23343b18d13f7c3b9abc622b40c4716314f9d3d23a731988becdccee`
- `loan-11-detail-associations-repaymentSchedule-5.json` — line 38350, 12208 B, sha256 `c1abb5f32b94783669b2c97099bfcefc4ac4e6c26cef721dde65a7bd3f8ba758`
- `loan-11-detail-associations-repaymentSchedule-6.json` — line 38374, 12208 B, sha256 `c1abb5f32b94783669b2c97099bfcefc4ac4e6c26cef721dde65a7bd3f8ba758`
- `loan-11-detail-associations-all-9.json` — line 38537, 152763 B, sha256 `218b70fde3790276fb1bc06e586909d97b3f0aa2b0aa3575abb2a5e65d9256c0`
- `loan-11-transactions-409-no-associations.json` — line 38561, 1936 B, sha256 `61d82cf42cd1b6dddad85d0354b1062efead0c7c30c1dda05a4addad32c95b7a`
- `loan-11-detail-associations-repaymentSchedule-7.json` — line 38587, 12230 B, sha256 `a28736fca44bbf1910b1a2bf59a7346b315ca8e0252f9b3e8d451580424d80bc`
- `loan-11-detail-associations-repaymentSchedule-8.json` — line 38611, 12230 B, sha256 `a28736fca44bbf1910b1a2bf59a7346b315ca8e0252f9b3e8d451580424d80bc`
- `loan-11-detail-associations-transactions-6.json` — line 38748, 152712 B, sha256 `b3cadbe7f510a2899e41d9d26ff3b930c1bc7e9816df3f4a21a7e254b38e8a6f`
- `loan-11-detail-associations-all-10.json` — line 38772, 158231 B, sha256 `b067ef850ee30ff8b986d956165b18507807cdacb9c3c86c3f66c37b0c3dc1ae`
- `loan-11-detail-no-associations-3.json` — line 38796, 7304 B, sha256 `012a1b67f4527f40e2c6b946b30bd2b5c70dba84276d7fe6394090fe2065d544`
- `loan-11-detail-no-associations-4.json` — line 38820, 7304 B, sha256 `012a1b67f4527f40e2c6b946b30bd2b5c70dba84276d7fe6394090fe2065d544`
- `loan-11-detail-associations-repaymentSchedule-9.json` — line 38844, 12317 B, sha256 `c94d638cbd0b6ad44a99fd128befe80d3cf4661c57e4f6e7bc2136f6e6b1df71`
- `loan-11-detail-associations-repaymentSchedule-10.json` — line 38868, 12317 B, sha256 `c94d638cbd0b6ad44a99fd128befe80d3cf4661c57e4f6e7bc2136f6e6b1df71`
- `loan-11-detail-associations-transactions-7.json` — line 38976, 152712 B, sha256 `b3cadbe7f510a2899e41d9d26ff3b930c1bc7e9816df3f4a21a7e254b38e8a6f`
- `loan-11-detail-associations-all-11.json` — line 39028, 158185 B, sha256 `265b52e6416b55bf9db99f3a824c896d9da54861aea28ba4e6557a64328a4118`
- `loan-11-detail-no-associations-5.json` — line 39052, 7255 B, sha256 `c11896c4a69342ba568bd56ddd2804a8b600fc80f1a2b62acf12315ccb4f9055`
- `loan-11-detail-associations-repaymentSchedule-11.json` — line 39076, 12239 B, sha256 `8b277dea23bda997eacccfdc34bffbdf865a411b535d3f84e102de0610b2d72c`
- `loan-11-detail-associations-repaymentSchedule-12.json` — line 39100, 12239 B, sha256 `8b277dea23bda997eacccfdc34bffbdf865a411b535d3f84e102de0610b2d72c`
- `loan-11-detail-associations-transactions-8.json` — line 39153, 154640 B, sha256 `8086be0e4c85e96bff1e643e89ce6f3538cc5395c48dcc69d2bba06df413672f`
- `loan-11-detail-associations-all-12.json` — line 39177, 160159 B, sha256 `4a8ad9472510675b5581746ab556af34214998cb787412ecd8d0788f1503015b`
- `loan-11-detail-no-associations-6.json` — line 39201, 7280 B, sha256 `085576b2de9081af924a3e130fd2694dc8be296b7cfd85559f25819e48e9ca0a`
- `loan-11-detail-no-associations-7.json` — line 39225, 7280 B, sha256 `085576b2de9081af924a3e130fd2694dc8be296b7cfd85559f25819e48e9ca0a`
- `loan-11-detail-associations-repaymentSchedule-13.json` — line 39249, 12293 B, sha256 `af9793eb127bc00e466081d30b37db2d8fbd71bef671732a9646d7265e9ce220`
- `loan-11-detail-associations-repaymentSchedule-14.json` — line 39273, 12293 B, sha256 `af9793eb127bc00e466081d30b37db2d8fbd71bef671732a9646d7265e9ce220`
- `loan-11-detail-associations-all-13.json` — line 39326, 162132 B, sha256 `1edb1bb67ff0b264539fdbc49dd2964e8cb58c095e2788c9527c05a3729a89a0`
- `loan-11-detail-no-associations-8.json` — line 39350, 7322 B, sha256 `d81967a28022d3e2956e1ef8c31f5d3ddb098f5a90d9d20c00f44554080e1c78`
- `loan-11-detail-no-associations-9.json` — line 39374, 7322 B, sha256 `d81967a28022d3e2956e1ef8c31f5d3ddb098f5a90d9d20c00f44554080e1c78`
- `loan-11-detail-associations-repaymentSchedule-15.json` — line 39398, 12335 B, sha256 `5e9c023b4fd615739b4f6731dec0fc303e3b4a50721d0a19747e75f76593f86b`
- `loan-11-detail-associations-repaymentSchedule-16.json` — line 39422, 12335 B, sha256 `5e9c023b4fd615739b4f6731dec0fc303e3b4a50721d0a19747e75f76593f86b`
- `loan-11-detail-associations-transactions-9.json` — line 39446, 156613 B, sha256 `f12e6edd046768abd551cb439fffdafb28370e4556cd3b485c58a4cb6d67d21d`
- `loan-11-detail-associations-all-14.json` — line 39499, 164140 B, sha256 `13b0c0226f7a105726f09f505600d24ce43584f7afcef88e0d3b88154f9256c5`
- `loan-11-transactions-415-no-associations.json` — line 39523, 1936 B, sha256 `edbc8da8d2d9e9396b1ffaf4c4e05b1dbb85d2b3752951a11587d69a443ea542`
- `loan-11-detail-associations-repaymentSchedule-17.json` — line 39549, 12255 B, sha256 `b0789c2cdf14362bef492032d81c34cccf03084e55346f155688590c4311e593`
- `loan-11-detail-associations-repaymentSchedule-18.json` — line 39573, 12255 B, sha256 `b0789c2cdf14362bef492032d81c34cccf03084e55346f155688590c4311e593`
- `loan-11-detail-associations-transactions-10.json` — line 39626, 160606 B, sha256 `8f0797e32779400dbc766353f19eb4b6e82d4ab90557813f097b96be8ad7850e`
- `loan-11-detail-associations-all-15.json` — line 39650, 166133 B, sha256 `f79b438adbd05bcb75e901efa01d5e928c76abbfba3db179376b42efae2d1a3e`
- `loan-11-detail-no-associations-10.json` — line 39674, 7323 B, sha256 `2966b33f14d70ed0afb08e725aa9e6ac3b531c17b24177848efc9d8aebde4514`
- `loan-11-detail-no-associations-11.json` — line 39698, 7323 B, sha256 `2966b33f14d70ed0afb08e725aa9e6ac3b531c17b24177848efc9d8aebde4514`
- `loan-11-detail-associations-repaymentSchedule-19.json` — line 39722, 12344 B, sha256 `a3474c7607504c642fa1ce7f95b2a7959a767a5266ff33293d65cf2af0c8201f`
- `loan-11-detail-associations-repaymentSchedule-20.json` — line 39746, 12344 B, sha256 `a3474c7607504c642fa1ce7f95b2a7959a767a5266ff33293d65cf2af0c8201f`
- `loan-11-detail-associations-transactions-11.json` — line 39770, 160606 B, sha256 `8f0797e32779400dbc766353f19eb4b6e82d4ab90557813f097b96be8ad7850e`

### UC12 — `PASSED` — loan 12 — Verify Loan repayment schedule for progressive loan, interest type: Declining balance, interest calculation period: same as repayment - UC12: complex transactions, interest recalculation disabled, partial period interest calculation disabled

- directory: `loans/loan-12/` · 87 files (1 create, 13 command requests, 13 command responses, 60 read-backs)

Read-backs:

- `loan-12-detail-associations-all-1.json` — line 40657, 9620 B, sha256 `1df6780f173230eefde91837113ecce39cc4780118a11278a24d6de7eef40136`
- `loan-12-detail-associations-empty.json` — line 40710, 5199 B, sha256 `f7b6c4b6d5cc15531418595729ddcee4fdce27261abce17daa81423fc92f4f6e`
- `loan-12-detail-no-associations-1.json` — line 40763, 7174 B, sha256 `c87c63e189bdc85a2568477d090216b9f43a84b343c9c74b67ef67072406fe46`
- `loan-12-detail-associations-all-2.json` — line 40787, 13795 B, sha256 `0eb751ce2c4931fb160f45a980fccbeefe636e5d66548f08979a60bad5b4c901`
- `loan-12-detail-associations-transactions-1.json` — line 40811, 9099 B, sha256 `7568b2e870412326614c1c341f146bd472242585faedf3219f87b7a12c8e0294`
- `loan-12-detail-associations-all-3.json` — line 40835, 13795 B, sha256 `0eb751ce2c4931fb160f45a980fccbeefe636e5d66548f08979a60bad5b4c901`
- `loan-12-detail-no-associations-2.json` — line 41085, 7385 B, sha256 `1aec42a38011ef4a644e1573520081f54eb9490dd829087f7db6f975b2f48ee5`
- `loan-12-detail-associations-all-4.json` — line 41109, 92809 B, sha256 `7536fb4aa80d9ae155f513b5a1f4388a1360cec5530e21e04c933220e06d2b33`
- `loan-12-detail-associations-transactions-2.json` — line 41133, 87523 B, sha256 `f6a72dca6292e5084e10bf2aef91baa656edfbc2b4c20eae881c27df6f37078e`
- `loan-12-detail-associations-all-5.json` — line 41157, 92809 B, sha256 `7536fb4aa80d9ae155f513b5a1f4388a1360cec5530e21e04c933220e06d2b33`
- `loan-12-detail-associations-transactions-3.json` — line 41210, 89278 B, sha256 `cdf7e79e1ab4cb5c5517ce65314ffe2216b0691de788b7d51bec7630e429abee`
- `loan-12-detail-associations-all-6.json` — line 41234, 94635 B, sha256 `490da9644061755bcd4e678b49346be5e986e3591b5d9b53bc49813d1663e435`
- `loan-12-detail-associations-repaymentSchedule-1.json` — line 41258, 12070 B, sha256 `c68c910d46a0bf526b0bc28dfbf414214bb5508b1830b3283daccbb6cb1757b5`
- `loan-12-detail-associations-repaymentSchedule-2.json` — line 41282, 12070 B, sha256 `c68c910d46a0bf526b0bc28dfbf414214bb5508b1830b3283daccbb6cb1757b5`
- `loan-12-detail-associations-transactions-4.json` — line 41419, 139756 B, sha256 `35ec7a5af40d4c7b08273b43f420f8f5304f476ddca922cbd2aab719b1b5a1c6`
- `loan-12-detail-associations-all-7.json` — line 41443, 145210 B, sha256 `3bebe99e7f4d3b5ab24e4c9b52f3691c4a4209d9bc0210951b4866c37950ec35`
- `loan-12-detail-associations-repaymentSchedule-3.json` — line 41467, 12166 B, sha256 `bb5da1c3be6aaf5cca3f4c41ea7e297580cb032ead6a8705f0eaa42459ba53d1`
- `loan-12-detail-associations-repaymentSchedule-4.json` — line 41491, 12166 B, sha256 `bb5da1c3be6aaf5cca3f4c41ea7e297580cb032ead6a8705f0eaa42459ba53d1`
- `loan-12-detail-associations-transactions-5.json` — line 41628, 143446 B, sha256 `0fb5687a4d0a48bae0ecf1ca3cf229fa198ee7eb374c4cb3f4e6b0596d44416f`
- `loan-12-detail-associations-all-8.json` — line 41652, 148929 B, sha256 `80add9ec6b38467b2c8ea1eacf29112189779f1b7e600b7efc126c2ffc761d2c`
- `loan-12-detail-associations-repaymentSchedule-5.json` — line 41676, 12215 B, sha256 `48e407541561239d2b6849a5577b0aab47c29757c1c8f2005f94a90785b625a7`
- `loan-12-detail-associations-repaymentSchedule-6.json` — line 41700, 12215 B, sha256 `48e407541561239d2b6849a5577b0aab47c29757c1c8f2005f94a90785b625a7`
- `loan-12-detail-associations-all-9.json` — line 41837, 152770 B, sha256 `f1a132dc822937668c3ea279b8839c42e6017e826225ca51e55c4774c7ff9cfb`
- `loan-12-transactions-496-no-associations.json` — line 41861, 1936 B, sha256 `6ac6e4d76fc9f321ff171d8f5bcf4666e619b3bc0f8418269d00b878c330f803`
- `loan-12-detail-associations-repaymentSchedule-7.json` — line 41887, 12237 B, sha256 `ce64d8472eb0b5d6027ee851fee327c529d5ba7e673790dfeff33f0f28cb9e60`
- `loan-12-detail-associations-repaymentSchedule-8.json` — line 41911, 12237 B, sha256 `ce64d8472eb0b5d6027ee851fee327c529d5ba7e673790dfeff33f0f28cb9e60`
- `loan-12-detail-associations-transactions-6.json` — line 42048, 152719 B, sha256 `77d504f12ff7981f84c2144fbbc58a589fffb48d9623c862333fdb0f0b6d163e`
- `loan-12-detail-associations-all-10.json` — line 42072, 158238 B, sha256 `bb851c53e70f277f8f03a56ed3aa694e7e5d17094a411b505c7bec1656ebb626`
- `loan-12-detail-no-associations-3.json` — line 42096, 7311 B, sha256 `d83ecd94dec51afe109d77d0e6ea3faa387802d9c3fccb36f6f8622aa0b42fc2`
- `loan-12-detail-no-associations-4.json` — line 42120, 7311 B, sha256 `d83ecd94dec51afe109d77d0e6ea3faa387802d9c3fccb36f6f8622aa0b42fc2`
- `loan-12-detail-associations-repaymentSchedule-9.json` — line 42144, 12324 B, sha256 `1ba446c82d3a0565c6eaa7ed7a7d12145b535c18f1648d1623d7ab6b4666e884`
- `loan-12-detail-associations-repaymentSchedule-10.json` — line 42168, 12324 B, sha256 `1ba446c82d3a0565c6eaa7ed7a7d12145b535c18f1648d1623d7ab6b4666e884`
- `loan-12-detail-associations-transactions-7.json` — line 42275, 152719 B, sha256 `77d504f12ff7981f84c2144fbbc58a589fffb48d9623c862333fdb0f0b6d163e`
- `loan-12-detail-associations-all-11.json` — line 42328, 158192 B, sha256 `612752ccc17ee2765929712dd3df05f68cf0cde5a83b0d82186cd112a922235f`
- `loan-12-detail-no-associations-5.json` — line 42352, 7262 B, sha256 `489f478fad6aba03052d0fd0d43141e71ab5c658e0cbad0546d2b6e5f62259cf`
- `loan-12-detail-associations-repaymentSchedule-11.json` — line 42376, 12246 B, sha256 `612a4b3a9e47644bb6e254bcef74b48bfa890a879d4d238484e40b946f23f276`
- `loan-12-detail-associations-repaymentSchedule-12.json` — line 42400, 12246 B, sha256 `612a4b3a9e47644bb6e254bcef74b48bfa890a879d4d238484e40b946f23f276`
- `loan-12-detail-associations-transactions-8.json` — line 42453, 154647 B, sha256 `cf88765b00fc95cbaea2ece54b50d72ee392ad1c4a5f3c0ce2f54b4decc0056d`
- `loan-12-detail-associations-all-12.json` — line 42477, 160166 B, sha256 `1eccabcaef84177ad1ca0eba1fc2a2b7d20899faf729a42292c894e02dde28f9`
- `loan-12-detail-no-associations-6.json` — line 42501, 7287 B, sha256 `153a7d747c0d584ff2fa33a1a7a3967fa61e0bdfbcc64b83104da6ae1fd94b21`
- `loan-12-detail-no-associations-7.json` — line 42525, 7287 B, sha256 `153a7d747c0d584ff2fa33a1a7a3967fa61e0bdfbcc64b83104da6ae1fd94b21`
- `loan-12-detail-associations-repaymentSchedule-13.json` — line 42549, 12300 B, sha256 `3cb8d0f723df93adc2de904a33c1ec9f8949317d07b3d367dc929cccba0220a2`
- `loan-12-detail-associations-repaymentSchedule-14.json` — line 42573, 12300 B, sha256 `3cb8d0f723df93adc2de904a33c1ec9f8949317d07b3d367dc929cccba0220a2`
- `loan-12-detail-associations-all-13.json` — line 42626, 162139 B, sha256 `9d0878b0c9fd79fb1536178a73663171d53ad1556e30143394f0072b2d8b7aa9`
- `loan-12-detail-no-associations-8.json` — line 42650, 7329 B, sha256 `7faf459a5fc6861ea87b19ed485965b36d511f86a9614f3fb4f35303adf169e4`
- `loan-12-detail-no-associations-9.json` — line 42674, 7329 B, sha256 `7faf459a5fc6861ea87b19ed485965b36d511f86a9614f3fb4f35303adf169e4`
- `loan-12-detail-associations-repaymentSchedule-15.json` — line 42698, 12342 B, sha256 `e9f5de5bbc5e6f7f87847537f7a6a883780b955e6b5805a6859d908ccb912c0e`
- `loan-12-detail-associations-repaymentSchedule-16.json` — line 42722, 12342 B, sha256 `e9f5de5bbc5e6f7f87847537f7a6a883780b955e6b5805a6859d908ccb912c0e`
- `loan-12-detail-associations-transactions-9.json` — line 42746, 156620 B, sha256 `64d0b45e210c909467415d2e6fb9719f2bca378afd07e2a7d348f9077b335afb`
- `loan-12-detail-associations-all-14.json` — line 42799, 164147 B, sha256 `54e2b78e343068d79c077e27c087bad55562dfdd4701341e46b5ef20f74ccf4e`
- `loan-12-transactions-502-no-associations.json` — line 42823, 1936 B, sha256 `cbeed0d3d69a54b4a85ea7f19a4696adc9530081603352e8042de9b712715bd6`
- `loan-12-detail-associations-repaymentSchedule-17.json` — line 42849, 12262 B, sha256 `4dabb8f16612933390f120372435ca4072926b5534d3c62b69ec26d55a8570a6`
- `loan-12-detail-associations-repaymentSchedule-18.json` — line 42873, 12262 B, sha256 `4dabb8f16612933390f120372435ca4072926b5534d3c62b69ec26d55a8570a6`
- `loan-12-detail-associations-transactions-10.json` — line 42926, 160613 B, sha256 `7ae0b1550131047840c2f4091aa90777ebf2db77ae1f505054a0156f59ec8e93`
- `loan-12-detail-associations-all-15.json` — line 42950, 166140 B, sha256 `0fb3a1b466d28db6dbcade571777a96c867215fe12bc9ad52a23b199720a9715`
- `loan-12-detail-no-associations-10.json` — line 42974, 7330 B, sha256 `cfd331a5db2a79603f3b2ede2510453c29fd7db3c786a37d189cd23e4f40ba75`
- `loan-12-detail-no-associations-11.json` — line 42998, 7330 B, sha256 `cfd331a5db2a79603f3b2ede2510453c29fd7db3c786a37d189cd23e4f40ba75`
- `loan-12-detail-associations-repaymentSchedule-19.json` — line 43022, 12351 B, sha256 `3a5dc9252a6c9c5177f690e54f28ca27d88712d2d71e4b0d282f625fd3b29bed`
- `loan-12-detail-associations-repaymentSchedule-20.json` — line 43046, 12351 B, sha256 `3a5dc9252a6c9c5177f690e54f28ca27d88712d2d71e4b0d282f625fd3b29bed`
- `loan-12-detail-associations-transactions-11.json` — line 43070, 160613 B, sha256 `7ae0b1550131047840c2f4091aa90777ebf2db77ae1f505054a0156f59ec8e93`

