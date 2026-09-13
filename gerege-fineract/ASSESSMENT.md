# Fineract as the core of Gerege NBFI, with Gerege capabilities as extensions — an assessment

*13 Sep 2026. An exploration for Buyan, not a decision. Everything cited from Fineract is from the build this project
already pins (`/Users/buv/fineract`, commit 426a23544, 12 Aug 2026).*

## The question

Today the program ports Fineract to Go, one bounded context at a time, and uses a running Fineract only as the
reference ("the oracle") that every Go port must match. The alternative: run Fineract itself as the production core,
configure it for Mongolia, and build what Gerege needs that Fineract lacks as extensions.

## Short answer

**It is the faster and cheaper road to a licensed, operating NBFI, and I would explore it seriously**. Keep it on two
conditions:

1. A short spike (1–2 weeks) proves that the Mongolia-specific needs fit as out-of-tree extensions, with no fork of Fineract.
2. Buyan re-ratifies a few non-negotiables that Fineract cannot meet as written (the list is below).

The Go port has proved the method works, but it has also measured its own pace: 100–165 working days for Tier A and B
business logic, and about $1,000–1,700 of model credit. Every one of those days re-implements behaviour Fineract
already has, and that behaviour is proven by its 938 replayed test scenarios (908 pass in MNT).

## What Fineract already provides for extension (checked in the pinned build)

Extensions live **outside** Fineract's core modules, in a `custom/` source set built into the same Spring Boot
application. The `custom/acme` example shows each extension type, and `docker-compose-custom.yml` packages it:

| Extension type | Where it is shown | What Gerege would use it for |
| --- | --- | --- |
| Override a platform service with a Spring bean | `custom/acme/note/service/…/AcmeNoteReadPlatformService.java` | Local rules without touching core code |
| Custom repayment-schedule transaction processor | `custom/acme/loan/processor/…/AcmeLoanRepaymentScheduleTransactionProcessor.java` (interface `LoanRepaymentScheduleTransactionProcessor`) | Mongolian allocation orders, if the standard ones do not fit |
| Close-of-business (COB) business steps | `custom/acme/loan/cob/…/AcmeNoopBusinessStep.java` (interface `COBBusinessStep`) | FRC-required daily steps, provisioning rules |
| Batch jobs | `custom/acme/loan/job/…` | Reconciliation, regulatory extracts |
| External events (to Kafka / ActiveMQ) | `custom/acme/event/…`, `ExternalEventService`, `BusinessEventNotifierService` | Feed Gerege Nexus, notifications, payment rails, a shadow ledger |
| Data tables (runtime custom fields) | `DatatablesApiResource` | Mongolian KYC fields, the three-part name, registration number |
| Webhooks | `infrastructure/hooks` | Simple integrations |
| Idempotency keys | `fineract-command/…/CommandProperties.java` | The mandatory `Idempotency-Key` on money POSTs (enforcement to be verified) |

Fineract also provides multi-tenancy, role-based permissions, maker-checker, an audit trail of every command,
accounting with journal entries, loan and savings products, charges, delinquency, and reports.

## Fit with Gerege's non-negotiables (CLAUDE.md)

| Requirement | Fineract as-is | What it would take |
| --- | --- | --- |
| PostgreSQL only; no Oracle Database | Native (the default driver) | Nothing |
| HALF_UP rounding, precision 19, per-tenant | Native (`MoneyHelper`) | Configure; our vectors already check it |
| MNT, ISO 4217 496, 2 minor digits | Native currency configuration | Configure |
| Asia/Ulaanbaatar time zone | Per-tenant time zone | Configure. **Asia/Hovd** (+07) is not expressible inside one tenant: accept UB time for the business date, or extend |
| No floating point in money | Money is `BigDecimal`; columns are `DECIMAL(19,6)` | Meets the no-float rule |
| **Integer minor units** | **Not met**: amounts are stored as decimals with 6 places | **Re-ratify**: accept decimal storage with currency-scale enforcement, plus a guard that rejects sub-minor residue at the API edge |
| **Balances derived, never written** | **Not met**: `m_loan.*_outstanding_derived` and similar columns are written | **Re-ratify**: treat them as caches; the journal stays the source of truth, with a nightly reconciliation job (extension) that proves they match |
| Double-entry, append-only ledger; corrections by reversal | Journal entries, with reversal entries | Verify in the spike that no path edits a posted entry |
| `Idempotency-Key` mandatory on money POSTs | Supported in the command layer | Verify that it can be *required* (not just honoured); if not, enforce it at the Gerege edge |
| **Three-part names (ovog, patronymic, given); never first/last** | **Not met**: clients have `firstname`/`middlename`/`lastname` | **Re-ratify** the storage mapping (ovog → lastname, patronymic → middlename, given → firstname, and document it), or keep the three fields in a data table behind a Gerege API facade |
| National ID (10 characters, structural check) | Client identifiers exist; no Mongolian validation | Extension: a validator on client create and update |
| Payment rails: Banksuljee RTGS, ACH+, NETC; threshold from config | Payment types exist; no rail integrations | Extension: payment-type mapping plus an integration service driven by external events |
| No deposit-taking (NBFI licence) | Savings is a full module | Configure no savings products, and remove the permissions and endpoints; prove it cannot be switched on |
| Never describe savings as insured | Not applicable if deposits are off | Review customer-facing templates |
| FRC regulatory reporting | Report engine exists | Extension: FRC report definitions |

**Three non-negotiables need Buyan's re-ratification before this road is viable:** integer minor units in storage,
never-written balances, and the name fields. All are Buyan's to decide; the Go port was designed around them.

## What we would gain and what we would pay

**Gains**

- **Time to a pilot.** Roughly 6–10 weeks (configuration, the extensions in the table above, and acceptance testing)
  instead of 100–165 working days of porting, then parallel runs. A rough estimate, to be firmed up by the spike.
- **Maturity.** Years of production use at other institutions; our own replay runs 938 of its scenarios in MNT with 908
  passing, and the failures we inspected were Fineract disagreeing with its own tests, not with MNT.
- **Cost.** Apache 2.0 licensing, no fee. Model credit goes to extensions and tests instead of re-implementation.

**Costs and risks**

- **Two stacks.** Fineract is Java and Spring on the JVM; Gerege Nexus is Go. Someone must operate, patch and upgrade
  the JVM service.
- **Upgrade discipline.** Fineract releases regularly. Staying out-of-tree (the `custom/` modules, events, data tables)
  keeps upgrades cheap; a fork would make every upgrade a merge. The spike must show nothing needs a core patch.
- **Less control of the core.** Fineract's model decides some things (the naming fields, derived balances, the single
  tenant time zone). Where it disagrees with Gerege, the choice is to adapt Gerege or to extend around it.
- **Regulatory acceptance.** FRC acceptance and a parallel run are still required. They are no easier or harder than
  for the Go core.

## What carries over from the work already done

Very little is wasted:

- **The reference environment.** The standing Fineract instance, the MNT tenant set-up and the throwaway replay rig
  become the development and acceptance environments.
- **938 replayed scenarios and 322 golden vectors.** They become the regression suite for the configured Fineract and
  for every extension, and for each Fineract upgrade.
- **The Go ports.** The graded journal-entry and schedule code (about 25,600 lines) can serve as an independent
  **shadow ledger**: fed by Fineract's external events, it recomputes each posting and flags any disagreement. That is
  a strong control for FRC and audit, and it reuses exactly what was built.
- **Gerege Nexus.** It becomes the channel, identity and integration layer in front of Fineract, behind the same
  adapter contract (DEC-1). The contract stays; only the implementation behind it changes.

## Options

| | A. Go port (today) | B. Fineract core + Go edge | C. Fineract now, strangle later |
| --- | --- | --- | --- |
| Core ledger and products | Go, ported context by context | Fineract | Fineract at first |
| Mongolian capabilities | In Go | Fineract extensions + Nexus services | As B |
| Time to pilot | Longest (100–165 working days + parallel run) | Shortest | Shortest |
| Control of the core | Full | Partial | Partial, rising over time |
| Uses the Go work already done | Fully | As shadow ledger and edge | As shadow ledger; ports move into production only where needed |

**My recommendation is B, keeping C open:** launch on Fineract, extend it the upstream way, and run the graded Go
postings as a shadow ledger. Port a context into Go later only if a concrete reason appears (performance, an FRC
requirement Fineract cannot meet, or the cost of an extension).

## A spike to decide it (1–2 weeks, in `gerege-fineract/` only)

1. **Configure** a Gerege tenant on a throwaway Fineract: MNT, HALF_UP, Asia/Ulaanbaatar, two representative loan
   products, no savings products.
2. **Build three out-of-tree extensions** in a `custom/`-style module:
   - national-ID validation on client create;
   - the three-part name held in a data table, behind a small API facade;
   - an external-event consumer that feeds a stub payment-rail service, with the RTGS/ACH+ threshold in config.
3. **Acceptance.** Replay the existing golden vectors and Fineract scenarios against this tenant; nothing may regress.
4. **Prove the constraints.** Show that no savings endpoint can be enabled, that `Idempotency-Key` can be required on
   money POSTs, and that a Fineract version bump leaves the extensions untouched.
5. **Decide with evidence.** Write up the effort per extension, what needed a core change (target: none) and a firm
   pilot estimate.

## Decisions for Buyan

1. Whether to explore this at all (the spike above), while the Go port stays suspended.
2. Whether to re-ratify the three non-negotiables Fineract cannot meet as written: integer minor-unit storage, written
   derived balances, and the name fields.
3. Whether Asia/Hovd needs its own business date, or UB time is acceptable.
4. Who operates a JVM service in production.

Cutover, FRC sign-off and licence facts remain yours whichever road is chosen.
