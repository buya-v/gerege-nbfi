package ledger

import "fmt"

// PortfolioProductType is the product family that owns a product-to-account
// mapping row. It is the acc_product_mapping.product_type discriminator.
//
// TRAP 1 LIVES HERE. In the oracle this enum has TWO integer mappings that do
// not agree, and a Go port that defines one and uses it in both directions is
// silently wrong on exactly three of the six members.
//
//   - Everything that WRITES or READS the database uses getValue()
//     [VERIFIED: PortfolioProductType.java:26-31; write sites
//     ProductToGLAccountMappingHelper.java:80, :140, :605, :637, :665-666,
//     :698-699; every finder call in AccountingProcessorHelper.java takes
//     ...getValue()].
//   - PortfolioProductType.fromInt follows DECLARATION order
//     [VERIFIED: PortfolioProductType.java:51-59 — case 3 -> CLIENT,
//     case 4 -> PROVISIONING, case 5 -> SHARES], which is NOT the inverse of
//     getValue().
//
// So fromInt(x).getValue() != x for x in {3,4,5}, a 3-cycle 3 -> 5 -> 4 -> 3:
// fromInt(3) is CLIENT whose value is 5; fromInt(4) is PROVISIONING whose value
// is 3; fromInt(5) is SHARES whose value is 4. 1, 2 and 6 round-trip.
//
// This file therefore ships THREE functions, not two, and they are tested
// separately:
//
//	StoredValue()                   encode   — the persisted integer
//	ProductTypeFromStoredValue(v)   decode   — the TRUE inverse of StoredValue
//	FineractFromIntQuirk(v)          neither — the oracle's defective decoder,
//	                                          reproduced for fidelity only
//
// Never decode a stored product_type with FineractFromIntQuirk.
type PortfolioProductType int32

// The six members. The constant's numeric identity is deliberately NOT the
// persisted value: the persisted value is what StoredValue returns, and keeping
// the two apart is what stops a future edit from quietly reintroducing the
// oracle's permutation. Declaration order here matches the oracle's declaration
// order so that FineractFromIntQuirk can be expressed as "the v'th declared
// member" without a second table.
const (
	ProductLoan PortfolioProductType = iota
	ProductSaving
	ProductClient
	ProductProvisioning
	ProductShares
	ProductWorkingCapitalLoan
)

// productTypeStoredValue is the ONE authoritative encode table: the integer
// written to acc_product_mapping.product_type.
// [VERIFIED: PortfolioProductType.java:26-31]
var productTypeStoredValue = map[PortfolioProductType]int32{
	ProductLoan:               1,
	ProductSaving:             2,
	ProductClient:             5,
	ProductProvisioning:       3,
	ProductShares:             4,
	ProductWorkingCapitalLoan: 6,
}

// productTypeName reproduces the oracle's toString(), which is
// name().replace("_", " ") [VERIFIED: PortfolioProductType.java:44-46]. It is
// what appears in the ProductToGLAccountMappingNotFoundException message, e.g.
// "Mapping for product of type LOAN with Id 46 does not exist ..."
// [graded against capture A2-224-chargeoff-unmapped].
var productTypeName = map[PortfolioProductType]string{
	ProductLoan:               "LOAN",
	ProductSaving:             "SAVING",
	ProductClient:             "CLIENT",
	ProductProvisioning:       "PROVISIONING",
	ProductShares:             "SHARES",
	ProductWorkingCapitalLoan: "WORKING CAPITAL LOAN",
}

// productTypeDeclarationOrder is the oracle's DECLARATION order, which is the
// only thing FineractFromIntQuirk depends on.
// [VERIFIED: PortfolioProductType.java:26-31]
var productTypeDeclarationOrder = [...]PortfolioProductType{
	ProductLoan, ProductSaving, ProductClient,
	ProductProvisioning, ProductShares, ProductWorkingCapitalLoan,
}

// productTypeFromStored is the true inverse of productTypeStoredValue. It is
// BUILT from that table at init rather than written out, so the two can never
// drift: a hand-written inverse is exactly the edit that reintroduces trap 1.
var productTypeFromStored = map[int32]PortfolioProductType{}

func init() {
	for t, v := range productTypeStoredValue {
		if prev, dup := productTypeFromStored[v]; dup {
			// D-1 in docs/analysis/tierA-a2-behaviour.md §10 asks for a
			// bijection assertion at construction. A duplicate stored value
			// would make decoding ambiguous and would silently reroute a
			// posting, so it is fatal at init rather than at posting time.
			panic(fmt.Sprintf(
				"ledger: product_type encode table is not injective: %v and %v both store as %d",
				prev, t, v))
		}
		productTypeFromStored[v] = t
	}
	if len(productTypeFromStored) != len(productTypeStoredValue) {
		panic("ledger: product_type encode table is not a bijection")
	}
	if len(productTypeStoredValue) != len(productTypeDeclarationOrder) {
		panic("ledger: product_type declaration order and encode table disagree in size")
	}
	if len(productTypeName) != len(productTypeStoredValue) {
		panic("ledger: product_type name table is incomplete")
	}
}

// StoredValue returns the integer written to acc_product_mapping.product_type.
// This is the ONLY value that may be persisted or used as a query key.
func (t PortfolioProductType) StoredValue() int32 {
	v, ok := productTypeStoredValue[t]
	if !ok {
		panic(fmt.Sprintf("ledger: unknown PortfolioProductType %d", int32(t)))
	}
	return v
}

// String reproduces the oracle's toString() — name() with underscores replaced
// by spaces — because it is user-visible in refusal messages.
func (t PortfolioProductType) String() string {
	if n, ok := productTypeName[t]; ok {
		return n
	}
	return fmt.Sprintf("PortfolioProductType(%d)", int32(t))
}

// ProductTypeFromStoredValue decodes a value read back from
// acc_product_mapping.product_type. It is the true inverse of StoredValue and
// it is the ONLY function that may be used for that job.
//
// ok is false for an integer no member stores, which is the oracle's behaviour
// too (its fromInt returns null on default) — but note that the SET of integers
// accepted is the same for both functions while the MAPPING differs on 3, 4
// and 5, so a wrong choice cannot be detected by an out-of-range check.
func ProductTypeFromStoredValue(v int32) (PortfolioProductType, bool) {
	t, ok := productTypeFromStored[v]
	return t, ok
}

// FineractFromIntQuirk reproduces PortfolioProductType.fromInt EXACTLY,
// permutation and all, for the single purpose of predicting what the oracle
// renders when IT decodes a stored product_type.
//
// IT IS NOT A DECODER. fromInt(3) is CLIENT, fromInt(4) is PROVISIONING and
// fromInt(5) is SHARES, while the rows carrying 3, 4 and 5 were written by
// PROVISIONING, SHARES and CLIENT respectively. Using this to interpret a
// stored value mislabels every provisioning, shares and client mapping, and
// labels every loan, savings and working-capital-loan mapping correctly — so a
// test built from loan fixtures cannot see the defect.
//
// The oracle reaches this function from AccountingEnumerations.java:84 and
// JournalEntryMapper.java:79. [UNVERIFIED: whether either call site is ever
// passed a stored 3, 4 or 5 — the permutation is verified, the blast radius is
// not; this worker did not trace those callers.]
func FineractFromIntQuirk(v int32) (PortfolioProductType, bool) {
	if v < 1 || int(v) > len(productTypeDeclarationOrder) {
		return 0, false
	}
	return productTypeDeclarationOrder[v-1], true
}
