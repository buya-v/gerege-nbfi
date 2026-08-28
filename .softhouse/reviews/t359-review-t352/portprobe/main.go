// T359 port-side probe. Runs the port's own money reader against the EXACT
// characters the live reference oracle served back for T359's and T352's
// residue probes, so the "the port refuses" half of G-19 is re-derived rather
// than inherited from T352's handoff.
//
// No floating-point type appears anywhere in this file. Every input is a
// string literal typed by hand from the oracle's readback.
package main

import (
	"fmt"
	"os"


)

func main() {
	cases := []struct {
		text  string
		why   string
		scale int
	}{
		{"100.125000", "T359/T352 residue probe, MNT readback text", MNTMinorDigits},
		{"100.125", "the same amount as posted on the wire", MNTMinorDigits},
		{"0.125000", "T352 balance-scale discriminator debit leg", MNTMinorDigits},
		{"0.250000", "T352 balance-scale discriminator credit leg", MNTMinorDigits},
		{"100.123457", "T352 over-scale probe, as STORED by the oracle", MNTMinorDigits},
		{"12.340000", "T352 USD probe amount (2 minor digits)", 2},
		{"1200000.000000", "control: an amount the corpus already grades", MNTMinorDigits},
	}
	rc := 0
	for _, c := range cases {
		got, err := MinorUnitsFromDecimalText(c.text, c.scale)
		if err != nil {
			fmt.Printf("REFUSED  %-16s scale=%d  %s\n         err: %v\n", c.text, c.scale, c.why, err)
			continue
		}
		fmt.Printf("ACCEPTED %-16s scale=%d  -> %d minor units   %s\n", c.text, c.scale, int64(got), c.why)
	}
	os.Exit(rc)
}
