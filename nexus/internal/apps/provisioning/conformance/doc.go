// Package conformance is the provisioning context's golden-vector schema,
// comparator and grade machinery. It follows the charges harness (the
// second-generation harness) rather than the first-generation ledger and
// loanschedule harnesses, and it is a separate schema on purpose rather than a
// widening of any of them.
//
// # What this harness grades
//
// The provisioning slice owns the criteria aggregate, the age-band matching
// rule, the overlap invariant and the reserve-amount arithmetic. Three of those
// have an observable form on the running reference oracle: the
// m_provision_category rows returned by GET /v1/provisioningcategory (seam
// "provisioning-category-read"), the aggregated reserve amount written by
// POST /provisioningentries and read back from
// GET /v1/provisioningentries/{id}/entries (seam "provisioning-entry-reserve"),
// and the age-band matching rule replayed from GET
// /v1/provisioningcriteria/{id} plus the decisions the reserve entries record
// (seam "provisioning-criteria-band").
// A category vector carries a category id and expects the category aggregate
// (id, name, description) the oracle returned for it; a reserve vector carries
// the per-loan reserve rows (outstanding balance, band percentage, identity)
// and expects the single aggregated reserve amount the oracle wrote, with its
// band identity; a criteria-band vector carries a criteria's definitions and
// one overdue age and expects the single definition the oracle's join predicate
// (pcd.min_age <= overdueInDays AND overdueInDays <= pcd.max_age) selects from
// them, as the observed decisions pin it: category, reserve percentage in
// integer micro-per-cent, and liability/expense GL account pair.
//
// # What this harness cannot grade
//
// The overlap invariant (Overlaps/ValidateRange) is still not directly
// observable from a committed capture: the oracle exposes no overlap refusal to
// transcribe without writing a deliberately-broken criteria to the shared
// server, which the capture contract forbids ("leave the tenant exactly as
// found"). That behaviour remains OUTSIDE this harness's graded domain; a
// vector that required it would be INADMISSIBLE, never guessed.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/provisioning/ and
// does not touch a database. It needs a store pin (PIN-provisioning.json) and a
// capability registry (capabilities-provisioning.json). With no vectors it
// REFUSES (exit 2) rather than reporting a vacuous pass. It reuses the shared
// no-float census, which scans the whole Go module, so no floating-point type or
// literal may appear in this package either.
package conformance
