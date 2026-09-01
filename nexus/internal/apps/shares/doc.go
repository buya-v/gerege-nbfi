// Package shares is the Go port of Fineract's share-accounts domain
// (tierB-shares): share products and their market-price bands and charges, share
// accounts and the purchase lifecycle they carry, and the transaction ledger
// that records issued/redeemed shares and dividend/charge payments.
//
// It is the MODEL plus the pure, testable vocabulary: the account-status,
// purchase-status and transaction-type enumerations, and the money type every
// money column is normalised to. The JSON command plumbing and any general-
// ledger side-effects those transactions produce are later slices.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb; behavioural claims carry a
// file:line citation to that tree.
package shares
