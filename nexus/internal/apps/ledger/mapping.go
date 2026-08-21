package ledger

// MappingRow is one row of acc_product_mapping.
//
// EVERY column that is nullable in the DDL is a pointer here, deliberately.
// Resolution turns on six of them being NULL simultaneously, and a Go zero
// value of 0 is NOT the same fact as SQL NULL: payment type 0 does not exist,
// but a port that modelled payment_type as int64 would make every core row look
// like "payment type 0" and the core-row predicate would stop distinguishing
// anything.
//
// Column list and nullability [VERIFIED: ProductToGLAccountMapping.java:42-81
// against 0001_initial_schema.xml:179-187,
// 0153_add_charge_off_reason_id_to_acc_product_mapping.xml:28,
// 0198_add_classification_id_to_acc_product_mapping.xml:28,:41 and
// 0199_write_off_reason_mapping_loan.xml:28].
type MappingRow struct {
	ID int64

	// GLAccountID is nullable in both the entity (@ManyToOne(optional=true))
	// and the DDL. A row with a NULL account is a mapping that resolves to
	// nothing, and the oracle's delete-one-mapping path explicitly skips such
	// rows [VERIFIED: ProductToGLAccountMappingHelper.java:757-764].
	GLAccountID *int64

	ProductID            *int64
	ProductType          *int32
	FinancialAccountType *int32

	// The SIX discriminators. The core-row query requires ALL SIX to be NULL.
	// [VERIFIED: ProductToGLAccountMappingRepository.java:38-40 — the JPQL
	// reads "... and mapping.paymentType is NULL and mapping.charge is NULL and
	// mapping.chargeOffReason is NULL and mapping.writeOffReason is NULL and
	// mapping.capitalizedIncomeClassification is NULL and
	// mapping.buydownFeeClassification is NULL". Six is the literal count in
	// the JPQL, re-read by this worker.]
	PaymentTypeID                     *int64
	ChargeID                          *int64
	ChargeOffReasonID                 *int64
	WriteOffReasonID                  *int64
	CapitalizedIncomeClassificationID *int64
	BuydownFeeClassificationID        *int64
}

// isCoreRow reports whether all six discriminators are NULL.
func (r MappingRow) isCoreRow() bool {
	return r.PaymentTypeID == nil &&
		r.ChargeID == nil &&
		r.ChargeOffReasonID == nil &&
		r.WriteOffReasonID == nil &&
		r.CapitalizedIncomeClassificationID == nil &&
		r.BuydownFeeClassificationID == nil
}

func (r MappingRow) matchesKey(productID int64, productType, financialAccountType int32) bool {
	return r.ProductID != nil && *r.ProductID == productID &&
		r.ProductType != nil && *r.ProductType == productType &&
		r.FinancialAccountType != nil && *r.FinancialAccountType == financialAccountType
}

// NullPaymentTypePolicy decides how a payment-type lookup issued with a NULL
// payment type behaves.
//
// THIS IS A CONTESTED READING, NOT A FACT, and it is exposed rather than
// hard-coded so that nobody inherits a silent choice. The loan resolution path
// calls the derived query with the caller's paymentTypeId and applies NO null
// check [VERIFIED: AccountingProcessorHelper.java:1199-1205 — the guard is
// `accountMappingTypeId == FUND_SOURCE` only], unlike the working-capital-loan
// path which additionally requires `paymentTypeId != null`
// [VERIFIED: :1015]. So the loan path can issue findBy...PaymentTypeId(..., null).
//
// Spring Data JPA conventionally translates a null bound to an
// equality-derived parameter into IS NULL, which would match the CORE row.
// [UNVERIFIED: not resolvable from the pinned checkout — no spring-data-jpa
// artefact is available locally to inspect the generated JPQL, and NO CAPTURE
// DISCRIMINATES THE TWO. The corpus's only loan-path fund-source resolutions
// carry a payment type: A2-084 (paymentTypeId 1, resolved to GL 16 via the
// override) and A2-085 (paymentTypeId 2, no override row, resolved to GL 2).]
//
// Where the two readings agree: whenever at most one row exists with
// payment_type NULL for the key, both readings return the same GL account,
// because the IS NULL reading simply re-selects the core row that was already
// selected.
//
// Where they DIVERGE, and it is not hypothetical: the payment-type query does
// NOT filter the other five discriminators. So a row with payment_type NULL but
// charge_id NOT NULL at financial_account_type 1 is invisible to the core query
// and VISIBLE to the IS NULL reading of the payment-type query — under which it
// would override the core row on an ordinary disbursement. They also diverge
// when two rows share payment_type NULL, which the missing unique constraint
// makes possible.
type NullPaymentTypePolicy int

const (
	// NullPaymentTypeMatchesIsNull is the Spring Data convention: a NULL
	// argument becomes IS NULL and matches rows whose payment_type is NULL.
	// It is the zero value because it is the conventional reading, NOT because
	// it has been verified.
	NullPaymentTypeMatchesIsNull NullPaymentTypePolicy = iota

	// NullPaymentTypeMatchesNothing is the literal `= NULL` reading, under
	// which a NULL argument matches no row at all.
	NullPaymentTypeMatchesNothing
)

// MappingRepository is the read surface resolution needs. It is an interface so
// that the in-memory store below can be swapped for a pgx-backed one without
// touching the resolver. PostgreSQL is the only permitted database; Go talks to
// it via pgx.
//
// Every method reproduces ONE named query and returns (nil, nil) on a miss,
// exactly as the oracle's repository returns null.
type MappingRepository interface {
	// FindCoreProductToFinAccountMapping reproduces
	// ProductToGLAccountMappingRepository.java:38-40.
	FindCoreProductToFinAccountMapping(productID int64, productType, financialAccountType int32) (*MappingRow, error)

	// FindByPaymentType reproduces the derived query
	// findByProductIdAndProductTypeAndFinancialAccountTypeAndPaymentTypeId
	// [VERIFIED: ProductToGLAccountMappingRepository.java:30-31]. It filters on
	// FOUR columns only — the other five discriminators are NOT constrained.
	FindByPaymentType(productID int64, productType, financialAccountType int32, paymentTypeID *int64) (*MappingRow, error)

	// FindByCharge reproduces
	// findProductIdAndProductTypeAndFinancialAccountTypeAndChargeId
	// [VERIFIED: ProductToGLAccountMappingRepository.java:33-36]. Note the JPQL
	// is `mapping.charge.id = :chargeId`, so a NULL chargeId matches nothing.
	FindByCharge(productID int64, productType, financialAccountType int32, chargeID *int64) (*MappingRow, error)

	// FindChargeOffReasonMapping reproduces
	// ProductToGLAccountMappingRepository.java:76-78. It keys on
	// (productId, productType, chargeOffReasonId) and does NOT filter on
	// financialAccountType at all.
	FindChargeOffReasonMapping(productID int64, productType int32, chargeOffReasonID int64) (*MappingRow, error)

	// FindWriteOffReasonMapping reproduces
	// ProductToGLAccountMappingRepository.java:109-111. Same shape.
	FindWriteOffReasonMapping(productID int64, productType int32, writeOffReasonID int64) (*MappingRow, error)

	// FindCapitalizedIncomeClassificationMapping reproduces
	// ProductToGLAccountMappingRepository.java:105-107. Same shape.
	FindCapitalizedIncomeClassificationMapping(productID int64, productType int32, classificationID int64) (*MappingRow, error)

	// FindBuydownFeeClassificationMapping reproduces
	// ProductToGLAccountMappingRepository.java:101-103. Same shape.
	FindBuydownFeeClassificationMapping(productID int64, productType int32, classificationID int64) (*MappingRow, error)
}

// InMemoryMappingStore is a MappingRepository over a slice of rows. It exists so
// that resolution can be graded against captured acc_product_mapping dumps with
// no database, and so that the single-result semantics are reproduced in ONE
// place rather than being a property of whatever SQL a caller writes.
//
// It carries the NullPaymentTypePolicy, because that reading belongs to the
// query layer, not to the resolver.
type InMemoryMappingStore struct {
	Rows                  []MappingRow
	NullPaymentTypePolicy NullPaymentTypePolicy
}

// single reproduces getSingleResult(): zero rows is a miss (nil, nil), one row
// is the answer, and MORE THAN ONE IS AN ERROR — it is not "take the first".
// Taking the first would be a silent, plausible, wrong answer at exactly the
// point the oracle refuses, and the oracle's refusal is observed
// (A2-086-disburse-loan3-dupchannel).
func single(matches []MappingRow) (*MappingRow, error) {
	switch len(matches) {
	case 0:
		return nil, nil
	case 1:
		row := matches[0]
		return &row, nil
	default:
		return nil, newErr(ErrNonUniqueMappingResult, "A2-086-disburse-loan3-dupchannel",
			"More than one result was returned from Query.getSingleResult()")
	}
}

func (s *InMemoryMappingStore) FindCoreProductToFinAccountMapping(productID int64, productType, financialAccountType int32) (*MappingRow, error) {
	var out []MappingRow
	for _, r := range s.Rows {
		if r.matchesKey(productID, productType, financialAccountType) && r.isCoreRow() {
			out = append(out, r)
		}
	}
	return single(out)
}

func (s *InMemoryMappingStore) FindByPaymentType(productID int64, productType, financialAccountType int32, paymentTypeID *int64) (*MappingRow, error) {
	if paymentTypeID == nil && s.NullPaymentTypePolicy == NullPaymentTypeMatchesNothing {
		return nil, nil
	}
	var out []MappingRow
	for _, r := range s.Rows {
		if !r.matchesKey(productID, productType, financialAccountType) {
			continue
		}
		if paymentTypeID == nil {
			if r.PaymentTypeID == nil {
				out = append(out, r)
			}
			continue
		}
		if r.PaymentTypeID != nil && *r.PaymentTypeID == *paymentTypeID {
			out = append(out, r)
		}
	}
	return single(out)
}

func (s *InMemoryMappingStore) FindByCharge(productID int64, productType, financialAccountType int32, chargeID *int64) (*MappingRow, error) {
	// The JPQL is `mapping.charge.id = :chargeId`, an equality on a joined id.
	// A NULL argument matches nothing under either reading of the null
	// question, because there is no `charge.id IS NULL` row: a row with a NULL
	// charge has no joined charge to compare.
	if chargeID == nil {
		return nil, nil
	}
	var out []MappingRow
	for _, r := range s.Rows {
		if r.matchesKey(productID, productType, financialAccountType) &&
			r.ChargeID != nil && *r.ChargeID == *chargeID {
			out = append(out, r)
		}
	}
	return single(out)
}

func (s *InMemoryMappingStore) findByReason(productID int64, productType int32, want int64, pick func(MappingRow) *int64) (*MappingRow, error) {
	var out []MappingRow
	for _, r := range s.Rows {
		if r.ProductID == nil || *r.ProductID != productID {
			continue
		}
		if r.ProductType == nil || *r.ProductType != productType {
			continue
		}
		if v := pick(r); v != nil && *v == want {
			out = append(out, r)
		}
	}
	return single(out)
}

func (s *InMemoryMappingStore) FindChargeOffReasonMapping(productID int64, productType int32, chargeOffReasonID int64) (*MappingRow, error) {
	return s.findByReason(productID, productType, chargeOffReasonID,
		func(r MappingRow) *int64 { return r.ChargeOffReasonID })
}

func (s *InMemoryMappingStore) FindWriteOffReasonMapping(productID int64, productType int32, writeOffReasonID int64) (*MappingRow, error) {
	return s.findByReason(productID, productType, writeOffReasonID,
		func(r MappingRow) *int64 { return r.WriteOffReasonID })
}

func (s *InMemoryMappingStore) FindCapitalizedIncomeClassificationMapping(productID int64, productType int32, classificationID int64) (*MappingRow, error) {
	return s.findByReason(productID, productType, classificationID,
		func(r MappingRow) *int64 { return r.CapitalizedIncomeClassificationID })
}

func (s *InMemoryMappingStore) FindBuydownFeeClassificationMapping(productID int64, productType int32, classificationID int64) (*MappingRow, error) {
	return s.findByReason(productID, productType, classificationID,
		func(r MappingRow) *int64 { return r.BuydownFeeClassificationID })
}
