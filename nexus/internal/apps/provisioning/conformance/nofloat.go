package conformance

import (
	floatguard "github.com/gerege/nexus/internal/floatguard"
)

// The no-float rule, REUSED rather than re-implemented.
//
// The first non-negotiable of this program is that money is integer minor units
// with no floating-point type on any money path. The executable form of that
// sentence is nexus/internal/floatguard.ScanGoTreeForFloatingPoint, which
// tokenises every .go file under the module root and refuses on a floating-point
// type, literal or the math package. There is exactly one census engine, shared
// by the loanschedule, ledger and charges harnesses, so this package imports it
// rather than forking it.
//
// THE ROOT IS THE WHOLE MODULE, not the provisioning subtree. The guard walks
// "nexus" recursively precisely because a hard-coded subtree reproduces the
// defect for the next package; the provisioning conformance tree is inside the
// guarded set automatically, and a float planted anywhere under it is a refusal.
var GuardedGoTreeRel = floatguard.GuardedGoTreeRel

// FloatingPointCensus is what the no-float scan inspected and found.
type FloatingPointCensus = floatguard.FloatingPointCensus

// ScanGoTreeForFloatingPoint tokenises every .go file under root and censuses
// forbidden identifiers, floating-point/imaginary literals and forbidden
// imports. It returns an error when the walk failed or scanned zero files or
// zero packages: a guard that inspects nothing is an error, never a pass.
var ScanGoTreeForFloatingPoint = floatguard.ScanGoTreeForFloatingPoint
