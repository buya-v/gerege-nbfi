package conformance

import (
	floatguard "github.com/gerege/nexus/internal/floatguard"
)

// The no-float guard lives in one neutral package, nexus/internal/floatguard,
// so that BOTH conformance harnesses — loanschedule (this package) and charges
// — can run the single census without either importing the other (a cycle).
// The guard itself, its rationale and its derived module root are documented in
// floatguard/nofloat.go; these three re-exports keep this package's callers
// (grade.go, report.go and the conformance tests) unchanged.

// GuardedGoTreeRel is the tree the no-float rule binds, relative to the
// repository root. It is the GO MODULE ROOT, walked recursively.
var GuardedGoTreeRel = floatguard.GuardedGoTreeRel

// FloatingPointCensus is what the no-float scan inspected and found.
type FloatingPointCensus = floatguard.FloatingPointCensus

// ScanGoTreeForFloatingPoint tokenises every .go file under root and censuses
// forbidden identifiers, floating-point/imaginary literals and forbidden
// imports. It returns an error when the walk failed or scanned zero files or
// zero packages.
var ScanGoTreeForFloatingPoint = floatguard.ScanGoTreeForFloatingPoint
