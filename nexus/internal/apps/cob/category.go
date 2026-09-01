package cob

// Category identifies which Close-of-Business job a business step belongs to.
//
// It mirrors org.apache.fineract.cob.BusinessStepCategory. Only the Loan
// category is in scope for the Tier A money core; the savings and shareholder
// categories exist to keep the enum faithful to the source and are not wired
// into any job yet.
type Category string

const (
	CategoryLoan        Category = "LOAN"
	CategorySavings     Category = "SAVINGS"
	CategoryShareholder Category = "SHAREHOLDER"
)

// String returns the enum-styled name, matching Fineract's serialized form.
func (c Category) String() string {
	return string(c)
}
