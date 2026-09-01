// Package parties is the Go port of Fineract's client-and-group domain
// (tierB-clients-groups): the Client and Group aggregates, their status and
// legal-form vocabularies, and the group-level catalogue. It is the party
// master data that loans, savings and collateral reference by client_id /
// group_id.
//
// The testable core is:
//
//   - Client.deriveDisplayName: fullname wins outright, otherwise a person's
//     firstname/middlename/lastname are space-joined; an entity contributes
//     nothing [VERIFIED: Client.java:378-398];
//   - ClientStatus and GroupingTypeStatus predicates (pending/active/closed/
//     rejected/withdrawn/under-transfer);
//   - LegalForm PERSON/ENTITY with the isPerson/isEntity tests
//     [VERIFIED: LegalForm.java:24-58];
//   - GroupLevel's Center/Group classification by level name
//     [VERIFIED: GroupLevel.java:73-81].
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Behavioural claims carry
// file:line citations to that tree.
package parties
