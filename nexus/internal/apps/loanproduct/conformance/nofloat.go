package conformance

import (
	floatguard "github.com/gerege/nexus/internal/floatguard"
)

// The no-float rule, REUSED rather than re-implemented.
//
// This harness grades enum STORED VALUES / codes / names (integers and strings),
// not money, but the module-wide no-float census is still part of the shared
// conformance contract every harness reports. A floating-point type on any money
// path is a first-order defect for the program as a whole, so the census walks
// the WHOLE module, loanproduct included.
var GuardedGoTreeRel = floatguard.GuardedGoTreeRel

// FloatingPointCensus is what the no-float scan inspected and found.
type FloatingPointCensus = floatguard.FloatingPointCensus

// ScanGoTreeForFloatingPoint tokenises every .go file under root and censuses
// forbidden identifiers, floating-point/imaginary literals and forbidden
// imports.
var ScanGoTreeForFloatingPoint = floatguard.ScanGoTreeForFloatingPoint
