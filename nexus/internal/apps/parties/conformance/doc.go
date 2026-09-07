// Package conformance is the parties context's golden-vector schema, comparator
// and grade machinery. It follows the collateral harness (the smallest existing
// harness) and is a separate schema on purpose.
//
// # What this harness grades
//
// The parties slice owns three enum vocabularies, none of which carries money:
//
//   - ClientStatus       (m_client.status_enum)   — ClientStatus.java
//   - LegalForm          (m_client.legal_form_enum) — LegalForm.java
//   - GroupingTypeStatus (m_group.status_enum)      — GroupingTypeStatus.java
//
// Fineract persists each of these enums as an ORDINAL (status_enum /
// legal_form_enum / status_enum), and a wrong ordinal is silent data corruption,
// not a crash — the same class of defect as the HALF_UP/HALF_EVEN rounding
// ordinal (4 versus 6). If the port maps ACTIVE to 300 while Fineract means 100,
// every row written is wrong and nothing throws.
//
// Each vector pins enum NAME <-> ORDINAL. The truth comes, read-only, from the
// running reference oracle (GET /clients/template clientLegalFormOptions,
// GET /clients/1, and the m_client read-back) and — where an ordinal is only
// visible in Java source — from the pinned source capture, cited file:line per
// vector.
//
// # Money representation
//
// There is none. This context carries no money token, no minor-unit parsing and
// no rounding logic. The only graded integer is the enum ordinal.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/parties/ and does
// not touch a database. It needs a store pin (PIN-parties.json) and a capability
// registry (capabilities-parties.json). With no vectors it REFUSES (exit 2). It
// reuses the shared no-float census, which scans the whole Go module.
package conformance
