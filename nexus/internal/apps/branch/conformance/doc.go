// Package conformance is the branch context's golden-vector schema, comparator
// and grade machinery. It follows the provisioning harness (the second-generation
// harness) and is a separate schema on purpose rather than a widening of any
// existing one.
//
// # What this harness grades
//
// The branch slice is the MODEL plus the pure, testable vocabulary of Fineract's
// organisation/teller domain: the teller status state machine, the cashier
// transaction-type table, and the money type every money column is normalised to.
// The running reference oracle's allocate/settle captures are direct cash
// movements: a txn_amount arrives as decimal text and is stored as DECIMAL(19,6)
// with NO rounding surface (the MANIFEST records "roundingSurface": "none"). The
// one gradeable, observable money computation is the port's normalisation of that
// decimal text into integer minor units (branch.MinorUnitsFromDecimalText), which
// refuses any sub-minor-unit residue rather than reproducing Fineract's
// DECIMAL(19,6) storage. A vector therefore carries a cashier-transaction amount
// as the exact decimal text the oracle received, and expects the transaction type
// (id + value) and the amount as an INTEGER STRING of minor units.
//
// # What this harness cannot grade
//
// The summary aggregation (sumCashAllocation / sumCashSettlement / netCash) and
// the double-entry posting the in/out movements feed are later slices and are not
// in the branch package. The 3dp probe (40000.245) demonstrates that the oracle
// stores sub-minor-unit residue exactly, but the port's 2dp minor-unit model
// refuses it, so there is no rounding cell to pin and no parity vector is derived
// from it.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/branch/ and does
// not touch a database. It needs a store pin (PIN-branch.json) and a capability
// registry (capabilities-branch.json). With no vectors it REFUSES (exit 2) rather
// than reporting a vacuous pass. It reuses the shared no-float census, which scans
// the whole Go module, so no floating-point type or literal may appear here.
package conformance
