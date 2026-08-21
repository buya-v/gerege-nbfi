package ledger

import (
	"errors"
	"fmt"
)

// The refusal surface.
//
// Every globalisation code below was OBSERVED in a committed capture under
// .softhouse/capture/tierA-a2/out/, not inferred from source, and each carries
// its capture id. Where source and observation disagreed, the observation wins
// and the disagreement is written down — see ErrGLCodeDuplicate.
//
// These codes are wire contract: a port that "fixes" a misleading one changes
// what a client sees. Two are known to be misleading and are reproduced anyway
// [VERIFIED: GLAccountInvalidUsageException.java:29 emits
// error.msg.glaccount.classification.invalid while
// GLAccountInvalidClassificationException.java:29 emits
// error.msg.glaccount.usage.invalid — the two are swapped relative to their
// class names].

// LedgerError is a refusal carrying the oracle's globalisation code and HTTP
// status, so a caller can reproduce the wire response exactly.
type LedgerError struct {
	// Code is userMessageGlobalisationCode.
	Code string
	// HTTPStatus is the status the oracle returns for this refusal.
	HTTPStatus int
	// Message is developerMessage / defaultUserMessage.
	Message string
	// Capture names the committed capture that observed this refusal, or is
	// empty when the refusal is source-derived and has not been observed.
	Capture string
	// ApplicableSlotName is set on a product-to-account-mapping miss. Message
	// reproduces the oracle's own rendering, which for a loan ALWAYS goes
	// through AccrualAccountsForLoan even on a cash-based product; this field
	// carries the name from the enum that ACTUALLY APPLIES. The two differ at
	// codes 22, 24 and 25 — trap 2 surfacing inside the oracle's own error
	// path. It is diagnostic only and is never put on the wire.
	ApplicableSlotName string
}

func (e *LedgerError) Error() string {
	return fmt.Sprintf("%s (HTTP %d): %s", e.Code, e.HTTPStatus, e.Message)
}

// Is compares on the globalisation code alone, so errors.Is works against the
// sentinels below regardless of the interpolated message.
func (e *LedgerError) Is(target error) bool {
	var t *LedgerError
	if !errors.As(target, &t) {
		return false
	}
	return t.Code == e.Code
}

// Sentinels. Compare with errors.Is; the concrete error returned by this
// package carries the interpolated message and the same Code.
var (
	// ErrProductToGLAccountMappingNotFound is the LOAN and WORKING-CAPITAL-LOAN
	// miss. Savings, shares and all three charge paths do NOT raise it — they
	// dereference nil (see ErrMappingNilDereference).
	// [OBSERVED: A2-224-chargeoff-unmapped, A2-225-goodwillcredit-unmapped,
	// A2-092-chargeoff-loan1-unmapped — all HTTP 404]
	ErrProductToGLAccountMappingNotFound = &LedgerError{
		Code: "error.msg.productToAccountMapping.not.found", HTTPStatus: 404,
	}

	// ErrMappingNilDereference reproduces the oracle's NullPointerException on
	// the savings, shares and charge resolution paths, which call
	// accountMapping.getGlAccount() with no null check
	// [VERIFIED: AccountingProcessorHelper.java:1237 (loan charge), :1268
	// (savings charge), :1293 (savings product), :1317 (shares product), :1337
	// (shares charge)]. The oracle surfaces this as an HTTP 500, not as a typed
	// refusal. This port raises a TYPED error instead of panicking, because a
	// Go panic in a posting path is strictly worse than an error, and records
	// here that the STATUS CODE differs from the oracle's.
	// [UNVERIFIED: the oracle's exact 500 body — no capture exercises a savings
	// or shares mapping miss; this tenant has no savings or share product.]
	ErrMappingNilDereference = &LedgerError{
		Code: "gerege.ledger.mapping.nil.dereference", HTTPStatus: 500,
	}

	// ErrNonUniqueMappingResult is what a DUPLICATE mapping row produces. The
	// finders return a single entity, and acc_product_mapping's JPA
	// @UniqueConstraint named financial_action IS NOT IN THE DDL
	// [VERIFIED: ProductToGLAccountMapping.java:42-43 declares it; a grep of
	// fineract-provider/src/main/resources/db/ for "financial_action" returns
	// zero hits], so duplicates are physically possible.
	// [OBSERVED: A2-086-disburse-loan3-dupchannel — HTTP 403,
	// error.msg.data.integrity.issue, "More than one result was returned from
	// Query.getSingleResult()", on product 27 which holds two rows at
	// (27, 1, 1, payment_type 1) pointing at GL accounts 16 and 2
	// (A2-150-db-final-state.txt)]
	ErrNonUniqueMappingResult = &LedgerError{
		Code: "error.msg.data.integrity.issue", HTTPStatus: 403,
		Message: "More than one result was returned from Query.getSingleResult()",
	}

	// ErrFinancialActivityAccountNotFound is the STEP 0 miss.
	// [VERIFIED: FinancialActivityAccountRepositoryWrapper.java:45-51;
	// FinancialActivityAccountNotFoundException.java:40-43]
	// [UNVERIFIED: no capture exercises it — the tenant has all three of its
	// financial activities mapped.]
	ErrFinancialActivityAccountNotFound = &LedgerError{
		Code: "error.msg.financialActivityAccount.not.found", HTTPStatus: 404,
	}

	// ErrFinancialActivityAccountDuplicate is a second row for one activity.
	// [OBSERVED: A2-fin-102-duplicate-activity — HTTP 403,
	// "Mapping for activity already exists 200". This RESOLVES an open
	// [UNVERIFIED] in docs/analysis/tierA-a2-behaviour.md §11 item 3: the
	// oracle's substring match on the driver message
	// (FinancialActivityAccountWritePlatformServiceImpl.java:144) DOES fire on
	// PostgreSQL's auto-named index.]
	ErrFinancialActivityAccountDuplicate = &LedgerError{
		Code: "error.msg.financialActivityAccount.exists", HTTPStatus: 403,
	}

	// ErrFinancialActivityAccountInvalid is the activity/classification pairing
	// refusal. [OBSERVED: A2-fin-103-wrong-account-type — HTTP 403]
	ErrFinancialActivityAccountInvalid = &LedgerError{
		Code: "error.msg.financialActivityAccount.invalid", HTTPStatus: 403,
	}

	// ErrGLAccountNotFound. [OBSERVED: A2-bad-049-parent-missing,
	// A2-125-delete-not-found, A2-fin-105-missing-account — all HTTP 404,
	// "General Ledger account with identifier 99999 does not exist "]
	ErrGLAccountNotFound = &LedgerError{
		Code: "error.msg.glaccount.id.invalid", HTTPStatus: 404,
	}

	// ErrGLAccountInvalidParent — a DETAIL account may not be a parent.
	// [VERIFIED: GLAccountWritePlatformServiceJpaRepositoryImpl.java:229-231]
	// [UNVERIFIED: not observed — the corpus's parent-refusal capture
	// A2-bad-050-type-mismatch-parent returns HTTP 200, because a type mismatch
	// is NOT refused; no capture parents an account under a DETAIL account.]
	ErrGLAccountInvalidParent = &LedgerError{
		Code: "error.msg.glaccount.parent.invalid", HTTPStatus: 403,
	}

	// ErrGLAccountAttachedToProduct — cannot DISABLE a mapped account.
	// [OBSERVED: A2-112-update-disable-mapped — HTTP 403]
	ErrGLAccountAttachedToProduct = &LedgerError{
		Code: "error.msg.glaccount.attached.to.product", HTTPStatus: 403,
	}

	// ErrGLAccountSameAsParent. [VERIFIED:
	// GLAccountWritePlatformServiceJpaRepositoryImpl.java:124-126]
	// [UNVERIFIED: not observed.]
	ErrGLAccountSameAsParent = &LedgerError{
		Code: "error.msg.glaccount.id.and.parentid.must.not.same", HTTPStatus: 403,
	}

	// ErrGLAccountUpdateTransactionsLogged — usage changed to HEADER with
	// entries posted. [VERIFIED:
	// GLAccountWritePlatformServiceJpaRepositoryImpl.java:153-159]
	// [UNVERIFIED: not observed.]
	ErrGLAccountUpdateTransactionsLogged = &LedgerError{
		Code: "error.msg.glaccount.glcode.invalid.update.transactions.logged", HTTPStatus: 403,
	}

	// ErrGLAccountDeleteHasChildren. [OBSERVED: A2-120-delete-has-children]
	ErrGLAccountDeleteHasChildren = &LedgerError{
		Code: "error.msg.glaccount.glcode.invalid.delete.has.children", HTTPStatus: 403,
	}

	// ErrGLAccountDeleteTransactionsLogged. [OBSERVED: A2-122-delete-three-guards]
	ErrGLAccountDeleteTransactionsLogged = &LedgerError{
		Code: "error.msg.glaccount.glcode.invalid.delete.transactions.logged", HTTPStatus: 403,
	}

	// ErrGLAccountDeleteProductMapping. [OBSERVED: A2-121-delete-product-mapped
	// (DELETE /glaccounts/13) and A2-123 (DELETE /glaccounts/6) — both HTTP
	// 403. Note that A2-123's file name says "finactivity-mapped" and that name
	// is misleading: GL account 6 is mapped by products 22/23/24/27/28 at slot
	// OVERPAYMENT, so the product-mapping guard fires first and the capture
	// says nothing about financial activities. Naming a capture after its
	// intent rather than its outcome is how a later reader infers a rule the
	// bytes do not support; recorded rather than propagated.]
	ErrGLAccountDeleteProductMapping = &LedgerError{
		Code: "error.msg.glaccount.glcode.invalid.delete.product.mapping", HTTPStatus: 403,
	}

	// ErrDataIntegrity is the PLATFORM-WIDE generic integrity code, and it is a
	// DIFFERENT code from ErrGLAccountDataIntegrity. deleteGLAccount has no
	// try/catch of its own [VERIFIED:
	// GLAccountWritePlatformServiceJpaRepositoryImpl.java:191-217], so a
	// database refusal propagates to the platform handler, while create and
	// update catch it and re-map it (:169-175, :241-249).
	//
	// This is what deleting an account referenced ONLY by a financial activity
	// row produces. There is no financial-activity delete guard at all — the
	// delete path checks children, journal entries and product mappings and
	// nothing else — so the FK FK_office_mapping_acc_gl_account (RESTRICT,
	// 0001_initial_schema.xml:8486-8489) refuses it at the database with a
	// generic error instead of a domain error.
	// [OBSERVED: A2-124-delete-clean-success — DELETE /glaccounts/21, HTTP 403,
	// error.msg.data.integrity.issue. GL account 21 is the financial activity
	// account for LIABILITY_TRANSFER(200) after A2-114 repointed it
	// (A2-150-db-final-state.txt row id 1: activity 200 -> gl_account_id 21)
	// and is in no acc_product_mapping row.]
	ErrDataIntegrity = &LedgerError{
		Code: "error.msg.data.integrity.issue", HTTPStatus: 403,
	}

	// ErrGLAccountDataIntegrity is the generic fall-through.
	//
	// IT IS WHAT A DUPLICATE glCode ACTUALLY RETURNS, and that CONTRADICTS the
	// source reading. GLAccountWritePlatformServiceJpaRepositoryImpl.java:242
	// matches the substring "acc_gl_code" in the driver's message and would
	// emit error.msg.glaccount.glcode.duplicate; but Liquibase declares the
	// uniqueness inline and UNNAMED (0001_initial_schema.xml:58-60), so
	// PostgreSQL auto-names the index and the substring never matches.
	// [OBSERVED: A2-bad-040-dup-glcode — HTTP 403,
	// error.msg.glAccount.unknown.data.integrity.issue. This RESOLVES the
	// open [UNVERIFIED] at docs/analysis/tierA-a2-behaviour.md §2.6 C14 and
	// §11 item 3, and it resolves it AGAINST the source reading.]
	// Also observed for a create with `usage` omitted
	// (A2-bad-045-no-usage, HTTP 403): the validator does not require usage
	// (GLAccountCommand.java:54-55 applies no notNull), so the NOT NULL column
	// refuses it at the database.
	ErrGLAccountDataIntegrity = &LedgerError{
		Code: "error.msg.glAccount.unknown.data.integrity.issue", HTTPStatus: 403,
	}

	// ErrGLCodeDuplicate is the code the SOURCE intends for a duplicate glCode
	// and which THIS ORACLE INSTANCE DOES NOT EMIT — see
	// ErrGLAccountDataIntegrity. It is defined so that a port can be switched
	// to it if a future deployment names the index acc_gl_code, and so that
	// nobody re-derives the source reading and "fixes" the port back.
	// [UNVERIFIED as a live behaviour: never observed; refuted for this
	// instance by A2-bad-040-dup-glcode.]
	ErrGLCodeDuplicate = &LedgerError{
		Code: "error.msg.glaccount.glcode.duplicate", HTTPStatus: 403,
	}

	// ErrValidation is the parameter-validation family.
	// [OBSERVED: the whole A2-bad-04x / A2-bad-05x set — HTTP 400]
	ErrValidation = &LedgerError{
		Code: "validation.msg.validation.errors.exist", HTTPStatus: 400,
	}

	// ErrProductToGLAccountMappingInvalidType — the slot's GL account is of the
	// wrong classification. [OBSERVED: A2-214-create-fundsource-retyped and
	// A2-prod-063-map-wrong-type — both HTTP 403, both
	// error.msg.fundSourceAccountId.invalid.account.type. The code is
	// PARAMETER-SPECIFIC: it interpolates the write-side parameter name, so
	// there is no single constant for it — use MappingInvalidTypeError.]
	ErrProductToGLAccountMappingInvalidType = &LedgerError{
		Code: "error.msg.productToAccountMapping.invalid.account.type", HTTPStatus: 403,
	}
)

// newErr clones a sentinel with an interpolated message, so errors.Is still
// matches on the code.
func newErr(base *LedgerError, capture, format string, args ...any) *LedgerError {
	return &LedgerError{
		Code:       base.Code,
		HTTPStatus: base.HTTPStatus,
		Message:    fmt.Sprintf(format, args...),
		Capture:    capture,
	}
}
