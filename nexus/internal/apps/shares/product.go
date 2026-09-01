package shares

import "time"

// ShareProduct is the m_share_product aggregate root: a tradable equity product
// a client may subscribe to, with the share-count bounds, the current market
// price band, and the charges levied on subscriptions.
//
// [VERIFIED: ShareProduct.java — name, short_name, external_id, description,
// currency, digits_after_decimal, in_multiples_of, minimum_shares,
// nominal_shares, maximum_shares, market_price (computed), allow_dividend_calculation,
// lockin_period, minimum_active_period, accounting_type.]
type ShareProduct struct {
	ID                       int64
	Name                     string
	ShortName                string
	ExternalID               string
	Description              string
	CurrencyCode             string
	DigitsAfterDecimal       int32
	InMultiplesOf            int32
	MinimumShares            int64
	NominalShares            int64
	MaximumShares            int64
	AllowDividendCalculation bool
	LockinPeriod             int32
	MinimumActivePeriod      int32
	AccountingType           int32
	MarketPrices             []ShareProductMarketPrice
	Charges                  []ShareProductCharge
}

// ShareProductMarketPrice is one m_share_product_market_price row: a market
// price effective for an inclusive date range.
//
// [VERIFIED: ShareProductMarketPrice.java — from_date, to_date, share_value.]
type ShareProductMarketPrice struct {
	ID         int64
	ProductID  int64
	FromDate   time.Time
	ToDate     time.Time
	ShareValue MinorUnits
}

// ShareProductCharge is one m_share_product_charge row linking a product to a
// charge.
//
// [VERIFIED: ShareProductCharge.java — product_id, charge_id.]
type ShareProductCharge struct {
	ID        int64
	ProductID int64
	ChargeID  int64
}
