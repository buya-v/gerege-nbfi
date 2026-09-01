package collateral

import "testing"

func dec(t *testing.T, text string, scale int) ScaledInt {
	t.Helper()
	v, err := ScaledIntFromText(text, scale)
	if err != nil {
		t.Fatalf("ScaledIntFromText(%q, %d): %v", text, scale, err)
	}
	return v
}

func TestDecimalRoundTrip(t *testing.T) {
	for _, c := range []struct {
		text  string
		scale int
	}{
		{"0.00000", 5},
		{"150000.00000", 5},
		{"80.00000", 5},
		{"-12.34500", 5},
		{"2500000.000000", 6},
		{"0.000000", 6},
	} {
		d := dec(t, c.text, c.scale)
		if got := d.FormatDecimal(c.scale); got != c.text {
			t.Errorf("ScaledInt(%d).FormatDecimal(%d) = %q, want %q", int64(d), c.scale, got, c.text)
		}
	}
}

func TestScaledIntFromTextRefusesResidue(t *testing.T) {
	if _, err := ScaledIntFromText("80.000001", 5); err == nil {
		t.Errorf("ScaledIntFromText(80.000001, 5) succeeded, want refusal")
	}
	if _, err := ScaledIntFromText("2500000.0000001", 6); err == nil {
		t.Errorf("ScaledIntFromText(2500000.0000001, 6) succeeded, want refusal")
	}
}

func TestClientCollateralTotal(t *testing.T) {
	product := CollateralProduct{
		BasePrice: dec(t, "150000.00000", 5),
		PctToBase: dec(t, "80.00000", 5),
	}
	c := NewClientCollateral(7, dec(t, "10.00000", 5), product)

	if got := c.Total().FormatDecimal(DecimalScale); got != "1500000.00000" {
		t.Errorf("Total() = %q, want 1500000.00000", got)
	}
	// 80% of the total value.
	if got := c.TotalCollateral(c.Total()).FormatDecimal(DecimalScale); got != "1200000.00000" {
		t.Errorf("TotalCollateral(Total()) = %q, want 1200000.00000", got)
	}
}

func TestClientCollateralTotalZero(t *testing.T) {
	product := CollateralProduct{
		BasePrice: dec(t, "150000.00000", 5),
		PctToBase: dec(t, "80.00000", 5),
	}
	c := NewClientCollateral(7, 0, product)
	if got := c.Total(); got != 0 {
		t.Errorf("Total() = %d, want 0", int64(got))
	}
	if got := c.TotalCollateral(0); got != 0 {
		t.Errorf("TotalCollateral(0) = %d, want 0", int64(got))
	}
}

func TestUpdateQuantityAfterLoanClosed(t *testing.T) {
	c := NewClientCollateral(7, dec(t, "10.00000", 5), CollateralProduct{})
	c.UpdateQuantityAfterLoanClosed(dec(t, "3.50000", 5))
	if got := c.Quantity.FormatDecimal(DecimalScale); got != "13.50000" {
		t.Errorf("Quantity after release = %q, want 13.50000", got)
	}
}
