// Package conformance is the provisioning context's golden-vector schema,
// comparator and grade machinery. It follows the charges harness (the
// second-generation harness) rather than the first-generation ledger and
// loanschedule harnesses, and it is a separate schema on purpose rather than a
// widening of any of them.
//
// # What this harness grades
//
// The provisioning slice owns the criteria aggregate, the age-band matching
// rule, the overlap invariant and the reserve-amount arithmetic. Of those, ONLY
// the criteria aggregate has an observable form on the running reference oracle
// as it stands: the m_provision_category rows returned by
// GET /v1/provisioningcategory (seam "provisioning-category-read"). A vector
// therefore carries a category id and expects the category aggregate
// (id, name, description) the oracle returned for it.
//
// # What this harness cannot grade
//
// The reserve-amount arithmetic (PercentageOf), the age-band matching rule
// (Matches/ReserveRate) and the overlap invariant (Overlaps/ValidateRange) are
// pure functions of criteria DEFINITIONS and per-loan overdue rows. The gerege
// tenant currently holds ZERO provisioning criteria, ZERO criteria definitions,
// ZERO loan-product mappings, ZERO loans and ZERO provisioning entries, so the
// oracle exposes no reserve amount, no matched band and no overlap refusal to
// transcribe. Producing any of those would require writing a criteria, mapping
// or loan to the shared server, which the capture contract forbids ("leave the
// tenant exactly as found"). Those behaviours are therefore NOT in this
// harness's graded domain; a vector that required them would be INADMISSIBLE,
// never guessed.
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
