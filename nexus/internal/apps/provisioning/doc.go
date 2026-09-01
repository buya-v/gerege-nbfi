// Package provisioning is the Go port of Apache Fineract's loan-provisioning
// money core: the provisioning-criteria model (categories, age-band
// definitions, loan-product mappings) and the reserve computation that turns a
// loan product's outstanding balance and overdue age into a reserved amount
// posted against a liability/expense account pair.
//
// # Scope of this slice (tierA-provisioning-reporting)
//
// This slice owns the CORE provisioning architecture — the criteria aggregate,
// the age-band matching rule, the overlap invariant, and the reserve-amount
// arithmetic — the "compliance-spine capital" the development plan calls out.
// It deliberately does NOT own:
//
//   - the SQL that materialises per-loan overdue rows (the oracle's
//     ProvisioningEntriesReadPlatformService query). The input to the
//     computation is a plain struct the storage layer fills; this package is a
//     pure function of that input, so it can be graded without a database.
//   - journal-entry posting. The reserve amounts computed here are the VALUES
//     that A1's double-entry engine will post; the posting itself belongs to
//     tierA-gl-accounting.
//   - the 30 % / 70 % regulatory capital limits. Those are FRC compliance
//     constraints that reconcile against the native GL after the reserve
//     figures are derived; they are an additive reporting concern, not part of
//     the Fineract parity oracle, and are therefore not graded here.
//
// Reference oracle: Apache Fineract at /Users/buv/fineract (pinned commit
// 426a23544e8426a38ae43ae404670a0a7e85b9eb). Every behavioural claim carries a
// file:line citation to that tree.
//
// # Money and percentage representation
//
// Money is the integer-minor-unit convention used across the port (MinorUnits);
// the reserve percentage is the same DECIMAL(19,6) "whole per cent" value the
// oracle stores in m_provisioning_criteria_definition.provision_percentage,
// represented as Percent (percentage scaled by 10^6, "micro-per-cent"). See
// money.go for the exact HALF_UP rounding contract.
package provisioning
