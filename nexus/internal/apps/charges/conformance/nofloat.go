package conformance

import (
	loanscheduleconf "github.com/gerege/nexus/internal/apps/loanschedule/conformance"
)

// The no-float rule, REUSED rather than re-implemented.
//
// CLAUDE.md's first non-negotiable is that money is integer minor units with no
// floating-point type on any money path. The executable form of that sentence is
// loanschedule/conformance.ScanGoTreeForFloatingPoint, which tokenises every
// .go file under the module root and refuses on a floating-point type, literal
// or the math package. This package does NOT write a second census engine: it
// imports the one census and runs it over the same derived root.
//
// THE ROOT IS THE WHOLE MODULE, not the charges subtree. The loanschedule guard
// walks "nexus" recursively precisely because a hard-coded subtree reproduces
// the defect for the next package; a new package is covered by default wherever
// it lands. The charges conformance tree is therefore inside the guarded set
// automatically, and a float planted anywhere under it — including this package
// — is a refusal, not a pass.
var GuardedGoTreeRel = "nexus"

// ScanGoTreeForFloatingPoint is the loanschedule no-float census, reused so there
// is exactly one implementation of the rule in the module. It returns an error
// when it scanned zero files or zero packages: a guard that inspects nothing is
// an error, never a pass.
func ScanGoTreeForFloatingPoint(root string) (loanscheduleconf.FloatingPointCensus, error) {
	return loanscheduleconf.ScanGoTreeForFloatingPoint(root)
}
