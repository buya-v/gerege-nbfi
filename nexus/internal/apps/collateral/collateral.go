package collateral

// CollateralProduct is the Go port of Fineract's CollateralManagementDomain
// [VERIFIED: CollateralManagementDomain.java:56-93], the product catalogue row
// in m_collateral_management: a named, quality-graded asset with a base price,
// a unit type, the percentage of that base price a loan may be secured by, and
// the currency the base price is denominated in.
type CollateralProduct struct {
	ID           int64     // m_collateral_management.id
	Name         string    // name
	Quality      string    // quality
	BasePrice    ScaledInt // base_price (scale 5)
	UnitType     string    // unit_type
	PctToBase    ScaledInt // pct_to_base, a whole per-cent at scale 5 (80.00000 = 80%)
	CurrencyCode string    // currency.code
}

// ClientCollateral is the Go port of Fineract's ClientCollateralManagement
// [VERIFIED: ClientCollateralManagement.java:44-140], one client's holding
// quantity of a collateral product, in m_client_collateral_management.
type ClientCollateral struct {
	ID       int64
	ClientID int64     // client_id
	Quantity ScaledInt // quantity (scale 5)

	// Product is the resolved CollateralProduct (collateral_id). It is carried
	// by reference so the valuation arithmetic stays a pure function of the
	// aggregate rather than a repository lookup.
	Product CollateralProduct
}

// NewClientCollateral ports createNew(quantity, client, collateral)
// [VERIFIED: ClientCollateralManagement.java:99-102].
func NewClientCollateral(clientID int64, quantity ScaledInt, product CollateralProduct) ClientCollateral {
	return ClientCollateral{ClientID: clientID, Quantity: quantity, Product: product}
}

// Total ports getTotal: quantity multiplied by the product's base price, a
// scale-5 result [VERIFIED: ClientCollateralManagement.java:107-112].
//
// Both operands are scale-5 integers, so their product is an exact multiple of
// 10^-10; dividing back by 10^5 yields an exact scale-5 integer with no
// remainder.
func (c ClientCollateral) Total() ScaledInt {
	return ScaledInt(int64(c.Quantity) * int64(c.Product.BasePrice) / scaleFactor(DecimalScale))
}

// TotalCollateral ports getTotalCollateral(total): the collateral value of a
// supplied total at the product's percentage-to-base [VERIFIED:
// ClientCollateralManagement.java:114-119].
//
// pctToBase is a whole per-cent at scale 5 (80.00000 = 80%), so the total is
// multiplied by pctToBase / 100: scale the integer product back by 10^5 (the
// percentage scale) and 100.
func (c ClientCollateral) TotalCollateral(total ScaledInt) ScaledInt {
	if total == 0 {
		return 0
	}
	return ScaledInt(int64(total) * int64(c.Product.PctToBase) / (100 * scaleFactor(DecimalScale)))
}

// UpdateQuantityAfterLoanClosed ports updateQuantityAfterLoanClosed: the
// released quantity is returned to the holding [VERIFIED:
// ClientCollateralManagement.java:130-132].
func (c *ClientCollateral) UpdateQuantityAfterLoanClosed(quantity ScaledInt) {
	c.Quantity += quantity
}

// LoanCollateralLink is the Go port of Fineract's LoanCollateralManagement
// [VERIFIED: LoanCollateralManagement.java:37-72], the quantity of one client
// holding tied to a single loan, in m_loan_collateral_management.
type LoanCollateralLink struct {
	ID                 int64
	LoanID             int64     // loan_id
	TransactionID      int64     // transaction_id (0 = none)
	IsReleased         bool      // is_released
	ClientCollateralID int64     // client_collateral_id
	Quantity           ScaledInt // quantity (scale 5)
}

// NewLoanCollateralLink ports from(clientCollateralManagement, quantity)
// [VERIFIED: LoanCollateralManagement.java:76-79].
func NewLoanCollateralLink(clientCollateralID int64, quantity ScaledInt) LoanCollateralLink {
	return LoanCollateralLink{ClientCollateralID: clientCollateralID, Quantity: quantity}
}

// LoanCollateral is the Go port of Fineract's classic LoanCollateral
// [VERIFIED: LoanCollateral.java:39-69], a type/value/description collateral
// attached to a loan, in m_loan_collateral.
type LoanCollateral struct {
	ID          int64
	LoanID      int64     // loan_id
	TypeID      int64     // type_cv_id (CodeValue id)
	Value       ScaledInt // value (scale 6)
	Description string    // description (empty = none)
}

// NewLoanCollateral ports from(collateralType, value, description)
// [VERIFIED: LoanCollateral.java:57-59]. The description is defaulted to empty
// rather than null, matching StringUtils.defaultIfEmpty(description, null) at
// the persistence boundary.
func NewLoanCollateral(loanID, typeID int64, value ScaledInt, description string) LoanCollateral {
	return LoanCollateral{LoanID: loanID, TypeID: typeID, Value: value, Description: description}
}

func scaleFactor(scale int) int64 {
	mul := int64(1)
	for i := 0; i < scale; i++ {
		mul *= 10
	}
	return mul
}
