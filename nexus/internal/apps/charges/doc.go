// Package charges is the Go port of Fineract's charge domain: the four
// m_charge enum columns, the Charge aggregate's construction invariants, and
// the pure fee arithmetic (percentage-of and min/max capping).
//
// # Scope of this slice (tierA-charges-rates-tax)
//
// This slice owns the CORE charge architecture: the ChargeTimeType,
// ChargeCalculationType, ChargeAppliesTo and ChargePaymentMode stored-value
// tables plus the Charge struct's validation and amount math. It deliberately
// does NOT own tax-group persistence, VAT reporting, or e-Barimt.
//
// # Mongolian VAT / e-Barimt is ADDITIVE — spec it, do not invent parity
//
// The plan is explicit [development_plan.md §7.2 row 3]: Mongolian VAT and
// e-Barimt receipting are additive to Fineract. Fineract has no Mongolian VAT
// engine and therefore no oracle vectors for it. The charge math here ports the
// Fineract semantics only; the VAT layer will be specced as a separate additive
// package that composes on top of these types and is NEVER graded against
// invented parity vectors. Until then, no VAT behaviour is present here.
//
// Reference oracle: Apache Fineract at /Users/buv/fineract (pinned commit
// 426a23544e8426a38ae43ae404670a0a7e85b9eb). Every enum carries a Java line
// citation.
package charges
