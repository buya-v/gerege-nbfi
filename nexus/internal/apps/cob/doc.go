// Package cob ports the Fineract Close-of-Business business-step core.
//
// Scope boundary [development_plan.md §4, tierA-cob-batch]: this package
// carries the pure COB orchestration model only — the ordered business-step
// contract, the step-name/order configuration, and the sequential runner. It
// deliberately reuses Nexus's existing scheduler and does NOT port Fineract's
// Spring Batch job framework, partitioner, item reader/writer, or the
// Spring-bean registration machinery that COBBusinessStepServiceImpl depends
// on.
//
// The concrete loan business steps themselves (apply charge to overdue loans,
// delinquency classification, accrual, and so on) live in the loan application
// context, not here; this package provides the interfaces and ordering model
// they plug into.
package cob
