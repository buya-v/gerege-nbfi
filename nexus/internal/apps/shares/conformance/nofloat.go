package conformance

import (
	floatguard "github.com/gerege/nexus/internal/floatguard"
)

// The no-float rule, REUSED rather than re-implemented.
var GuardedGoTreeRel = floatguard.GuardedGoTreeRel

// FloatingPointCensus is what the no-float scan inspected and found.
type FloatingPointCensus = floatguard.FloatingPointCensus

// ScanGoTreeForFloatingPoint tokenises every .go file under root and censuses
// forbidden identifiers, floating-point/imaginary literals and forbidden imports.
var ScanGoTreeForFloatingPoint = floatguard.ScanGoTreeForFloatingPoint
