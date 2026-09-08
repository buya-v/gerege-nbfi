// Package conformance is the shares context's golden-vector schema, comparator
// and grade machinery. It follows the branch harness (the third-generation
// harness) and is a separate schema on purpose rather than a widening of any
// existing one.
//
// # What this harness grades
//
// The shares slice is the MODEL plus the pure, testable vocabulary of Fineract's
// share-accounts domain: the share-account, purchase-status and dividend-status
// enumerations, and the money type every money column is normalised to. The
// running oracle's captures (T15/T16 family) expose the vocabulary across three
// seams, each graded behind its own request kind:
//
//   - share-account: the account aggregate readback AND one row of the
//     share-account list. The aggregate purchase total is requestedShares *
//     unitPrice = 100 * 100 = 10000.00, an integer-times-integer minor-unit
//     product, so there is NO rounding surface. The harness grades the stored
//     account status, the summary's approved and pending share counts and — when
//     the read-back carried the purchase group — the stored purchase status and
//     the normalisation of the purchased price and amount into integer minor
//     units. A share-account LIST row serialises no purchase group and no money,
//     so it is graded on its stored status and summary counts only.
//   - share-dividend: the share-product dividend amount and its stored status.
//     The oracle received dividendAmount "0.005" and STORED "0.010000" — the
//     HALF_UP-rounded read-back (the MANIFEST records HALF_UP 0.01 / HALF_EVEN
//     0.00, verdict HALF_UP). This harness grades the normalisation of that
//     STORED amount to one minor unit; when the read-back carried the dividend
//     row (the account aggregate's dividends list does), it also pins the row's
//     stored status integer (100, initiated), never the label. The rounding
//     itself is NOT graded: see below.
//   - share-product: the share-product detail read or one row of the share-
//     product list. The harness grades the normalisation of the unit price and
//     the share capital into integer minor units and the total share count. One
//     captured row carries a PRESENT-but-ZERO share capital (0.00), so a
//     serialiser that drops a zero money cell is a visible defect.
//
// Every money figure above is exact 2dp decimal text the oracle stored,
// transcribed to integer minor units; no figure is ever computed by the
// harness. The graded cells per vector: SH-01 account aggregate grades 7 cells
// (account status, approved, pending, purchase shares, purchase price, purchase
// amount, purchase status), SH-02/03 the dividend amount and status, SH-04/05/06
// the three product cells, SH-07 the account-list status and summary cells.
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
