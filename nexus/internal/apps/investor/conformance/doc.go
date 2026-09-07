// Package conformance is the investor context's golden-vector schema,
// comparator and grade machinery. It follows the collateral harness (the read
// seam over a single transcribed aggregate) rather than the loan/loanschedule
// harnesses, and it is a separate schema on purpose rather than a widening of
// any of them.
//
// # What this harness grades
//
// The investor slice owns the external asset owner aggregate and the
// loan-ownership transfer aggregate, whose derived outstanding-balance snapshot
// is the only arithmetic in the slice (ExternalAssetOwnerTransferDetails.
// DeriveTotalOutstanding, a sum of four integer minor-unit buckets). Of those,
// the running reference oracle exposes NO rounding surface through the API: the
// m_external_asset_owner_transfer row is read back verbatim, and
// purchase_price_ratio is a stored string the port performs no arithmetic on.
// The transfer-details arithmetic is OUTSIDE this harness's graded domain —
// the running oracle's m_external_asset_owner_transfer_details table is empty,
// so no read-back exposes a total-outstanding cell to transcribe, and inventing
// one would be a fabricated observation.
//
// What IS observable and transcribed is the read of the one transfer the
// capture recorded:
//
//   - seam "external-asset-owner-transfer-read": the m_external_asset_owner_transfer
//     row returned by GET /external-asset-owners/transfers?loanId=6 (transfer
//     id, owner external id, loan external id, transfer external id, purchase
//     price ratio, status, settlement date, effective-from and effective-to).
//
// # Money representation
//
// The transfer-read seam has no money cell: purchase_price_ratio is a verbatim
// string and the dates are calendar-date strings. The slice's money cells are
// integer minor units in the derived-balance snapshot, which is unreachable
// through the read-back this promotion transcribed. No floating-point type
// appears on any money path here or in the package it grades.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/investor/ and
// does not touch a database. It needs a store pin (PIN-investor.json) and a
// capability registry (capabilities-investor.json). With no vectors it REFUSES
// (exit 2) rather than reporting a vacuous pass. It reuses the shared no-float
// census, which scans the whole Go module.
package conformance
