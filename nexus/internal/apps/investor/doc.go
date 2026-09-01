// Package investor is the Go port of Fineract's investor / external asset
// owner domain (tierB-investor). It owns the external asset owner aggregate,
// the loan-ownership transfer aggregate with its derived outstanding-balance
// snapshot, the transfer status/sub-status vocabularies, and the per-loan-product
// outstanding-interest-strategy attribute that controls how a transfer prices
// the interest the new owner acquires.
//
// # What this slice is, and is not
//
// It is the MODEL plus the pure, testable core of the ownership-transfer rules.
// The write path is CRUD over m_external_asset_owner /
// m_external_asset_owner_transfer and their mapping tables; the testable core
// is the transfer-details arithmetic (total outstanding is DERIVED from the four
// component buckets, never stored independently) and the status vocabulary the
// transfer state machine consumes. The double-entry posting and the JSON
// command/serialization plumbing are later slices and are not here.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Every behavioural claim
// carries a file:line citation to that tree. "The oracle" here always means the
// FINERACT REFERENCE IMPLEMENTATION; Oracle Database is a prohibited product in
// this program and appears nowhere in this stack.
package investor
