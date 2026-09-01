// Package origination is the Go port of Fineract's loan-origination domain
// (tierB-loan-origination): the LoanOriginator aggregate, its ACTIVE/PENDING/
// INACTIVE status vocabulary, and the loan-to-originator mappings that record
// who originated a loan (including the working-capital mapping twin).
//
// # What this slice is, and is not
//
// It is the MODEL plus the pure validation/reconciliation logic the linking
// services wrap with persistence. The originator write path is mostly CRUD over
// m_loan_originator; the testable core (the part Fineract ships as ~1,657 test
// LOC) is the linking rule set:
//
//   - only an ACTIVE originator may be attached to a loan
//     [VERIFIED: AbstractLoanOriginatorLinkingServiceImpl.java:96-99];
//   - an originator may only be attached/detached while the loan is
//     SUBMITTED_AND_PENDING_APPROVAL
//     [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:197-209];
//   - a duplicate loan→originator attachment is refused
//     [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:214-216];
//   - an originator that is still referenced by any mapping cannot be deleted
//     [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:179-183];
//   - disbursement reconciliation drives the loan's mapping set to exactly the
//     requested set (remove the missing, add the new)
//     [VERIFIED: LoanOriginatorLinkingServiceImpl.java:102-138].
//
// The persistence layer and the JSON command/serialization plumbing around this
// are later slices and are not here.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Every behavioural claim
// carries a file:line citation to that tree.
package origination
