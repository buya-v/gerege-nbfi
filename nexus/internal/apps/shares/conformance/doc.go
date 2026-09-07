// Package conformance is the shares context's golden-vector schema, comparator
// and grade machinery. It follows the branch harness (the third-generation
// harness) and is a separate schema on purpose rather than a widening of any
// existing one.
//
// # What this harness grades
//
// The shares slice is the MODEL plus the pure, testable vocabulary of Fineract's
// share-accounts domain: the share-account status and purchase-status
// enumerations, and the money type every money column is normalised to. The
// running oracle's captures (T15/T16 family) expose two observable money
// surfaces, each graded by its own seam:
//
//   - share-account: the account aggregate readback. The purchase total is
//     requestedShares * unitPrice = 100 * 100 = 10000.00, an integer-times-
//     integer minor-unit product, so there is NO rounding surface (the MANIFEST
//     records this). The harness grades the account status, the purchase status,
//     and the normalisation of the purchased price and amount into integer minor
//     units.
//   - share-dividend: the share-product dividend amount. The oracle received
//     dividendAmount "0.005" and STORED "0.010000" — the HALF_UP-rounded
//     read-back (the MANIFEST records HALF_UP 0.01 / HALF_EVEN 0.00, verdict
//     HALF_UP). This harness grades the normalisation of that STORED amount to
//     one minor unit. The rounding itself is NOT graded: see below.
//
// # What this harness cannot grade
//
// The dividend create command's HALF_UP rounding (0.005 -> 0.01) is a LATER
// slice and is not in the shares package. The port's exact-money parser
// (shares.MinorUnitsFromDecimalText) REFUSES sub-minor-unit residue rather than
// reproducing the oracle's Money.setScale(2, HALF_UP), exactly as the branch and
// ledger ports refuse a 3dp or residue amount. There is therefore no rounding
// cell the port can produce: a parity vector whose request carried "0.005" would
// be refused by the implementation, not rounded. The dividend vector instead
// transcribes the STORED read-back (0.010000), which the port normalises to one
// minor unit, and the provenance note names the 0.005 request and the HALF_UP
// verdict so the observation is not silently dropped.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/shares/ and does
// not touch a database. It needs a store pin (PIN-shares.json) and a capability
// registry (capabilities-shares.json). With no vectors it REFUSES (exit 2)
// rather than reporting a vacuous pass. It reuses the shared no-float census,
// which scans the whole Go module, so no floating-point type or literal may
// appear here.
package conformance
