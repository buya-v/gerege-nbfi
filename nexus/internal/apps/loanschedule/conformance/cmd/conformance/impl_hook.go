package main

// The implementation hook.
//
// This file is the ONE place the conformance binary learns about a Go
// implementation of contract.ScheduleGenerator, and it is deliberately the only
// file in the harness that will ever name the port's package.
//
// THE GO PORT HAS LANDED (task T10) and is registered below.
//
// The hook's original instruction was a BLANK import of the port whose own
// init() called conformance.Register. That is not what this does, and the
// difference is deliberate: a blank import would make the production package
// import the conformance harness, so every binary that generates a schedule
// would link the grading rig, its vector loader and its capability registry. The
// dependency is inverted here instead — the harness's own command imports the
// port and registers it — which keeps the port free of any knowledge that it is
// graded, and keeps this file the single place the binary learns of an
// implementation. Nothing else about the arrangement changes.
//
// WHY IT WAS EMPTY UNTIL NOW, AND WHY THAT WAS CORRECT. With nothing registered
// the harness reports NO IMPLEMENTATION REGISTERED and exits 2 — a distinct,
// legible status that is neither a pass nor a crash. The alternative, a stub
// generator living here to "make the harness runnable", would have been a
// schedule generator inside the harness that grades schedule generators, and the
// first thing this task would have done is borrow it. The pipeline's
// independence is worth more than a green run, and the port below was written
// from the reference oracle's own source with nothing borrowed from this tree.
//
// The self-test path (-self-test, the replay implementation) still exists so the
// harness can be proven to work independently of whatever is registered here. A
// replay answers from the vector store and computes nothing.
//
// ONE PROOF IN .softhouse/conformance.sh GOES STALE WITH THIS CHANGE, and it is
// reported rather than fixed, because the harness is not this task's to edit.
// `--prove` case 1 asserts that `$bin -oracle-probe=up` exits 2 with the label
// "no implementation to grade". Its premise is "no implementation registered",
// which registering the port necessarily negates — the same way a refusal vector
// goes STALE the moment its capability enters the graded domain (grade.go's own
// term). Every other proof is unaffected, including case 8, which stays exit 2
// because a self-test fixture buys no parity.

import (
	"github.com/gerege/nexus/internal/apps/loanschedule"
	"github.com/gerege/nexus/internal/apps/loanschedule/conformance"
)

func init() {
	conformance.Register("loanschedule-go", loanschedule.New())
}
