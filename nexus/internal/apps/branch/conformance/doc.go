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
// Three seams are graded.
//
// The cashier-transaction seam grades direct cash movements: a txn_amount arrives
// as decimal text and is stored as DECIMAL(19,6) with NO rounding surface (the
// MANIFEST records "roundingSurface": "none"). The port normalises that text into
// integer minor units (branch.MinorUnitsFromDecimalText), refusing any
// sub-minor-unit residue rather than reproducing Fineract's DECIMAL(19,6)
// storage. A vector carries the amount as the exact decimal text the oracle
// received and expects the transaction type (id + value) and the amount as an
// INTEGER STRING of minor units.
//
// The cashier-summary seam grades the cashier summary read-back of the same row
// set. The captures read the SAME cashier at three moments — pre, post and final
// — with the allocate and settle movements between them. The pre and post reads
// bound a row set whose buckets (sumCashAllocation / sumCashSettlement / netCash)
// the port's derived summary fold (branch.FoldCashierSummary) reproduces, so a
// delta that a single read cannot show becomes gradeable: which figure each
// movement moved, and by how much. The final read is NOT promoted because it
// follows the 3dp probe's sub-minor-unit row (below).
//
// The teller-status seam grades the m_tellers.state stored integer behind the
// teller list's status label: the label the read-back serialised ("ACTIVE") maps
// through the port's TellerStatus enum to the stored value (300), so a port that
// re-encodes the lifecycle state as a contiguous ordinal goes red.
//
// # What this harness cannot grade
//
// The in/out cashier-transaction posting and its double-entry accounting is a
// later slice and is not in the branch package, and no capture in this context
// records a cash-in or cash-out row, so the summary fold's inward/outward buckets
// have no transcribed cell. The 3dp probe (40000.245) demonstrates that the
// oracle stores sub-minor-unit residue exactly; the port's 2dp minor-unit model
// refuses it.
//
// THAT REFUSAL IS A RATIFIED DELIBERATE DEPARTURE, not an open question.
// Buyan ratified it on 2026-09-09, closing gate G-19 and extending to this
// context the position DEC-2 already states as predicate G-08: "Refuse residue;
// do not truncate and do not round" -- a wire text carrying a non-zero digit
// beyond the currency's minor unit is ErrInvalidRequest, not a value. Truncating
// invents money in one direction and rounding in the other, and either makes a
// parity comparison pass while the two systems disagree by a fraction that
// accumulates.
//
// So no parity vector is derived from the final read that includes 40000.245,
// and none ever should be: there is no int64 count of MNT minor units equal to
// 40000.245, and any vector claiming one would have to invent a number neither
// system produced. The oracle's characters are recorded; the port's refusal is
// the graded answer. The ledger context records the same departure as
// LDG-DIV-01, and shares records a second instance (a stored 0.005 served back
// as 0.010000).
//
// ONE QUESTION STAYS OPEN and is attached to CUTOVER, not to this file: this
// seam performs no arithmetic on the amount, so it cannot show whether the
// oracle's OWN arithmetic can GENERATE residue. If a live instance ever computes
// an amount carrying residue, a port that refuses what the oracle stores would
// diverge on real traffic rather than on a probe. That is a parallel-run
// question and parallel-run sign-off is a user gate.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/branch/ and does
// not touch a database. It needs a store pin (PIN-branch.json) and a capability
// registry (capabilities-branch.json). With no vectors it REFUSES (exit 2) rather
// than reporting a vacuous pass. It reuses the shared no-float census, which scans
// the whole Go module, so no floating-point type or literal may appear here.
package conformance
