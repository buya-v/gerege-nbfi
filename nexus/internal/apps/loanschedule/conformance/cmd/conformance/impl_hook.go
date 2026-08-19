package main

// The implementation hook.
//
// This file is the ONE place the conformance binary learns about a Go
// implementation of contract.ScheduleGenerator, and it is deliberately the only
// file in the harness that will ever name the port's package.
//
// WHEN THE GO PORT LANDS (task T10), add exactly one blank import below:
//
//	import _ "github.com/gerege/nexus/internal/apps/loanschedule/<portpackage>"
//
// whose init() calls
//
//	conformance.Register("<name>", <TheGenerator>)
//
// Nothing else changes. .softhouse/conformance.sh then grades it with no
// arguments, because a single registered implementation is selected
// automatically.
//
// WHY IT IS EMPTY TODAY, AND WHY THAT IS CORRECT. There is no Go implementation
// yet. With nothing registered the harness reports NO IMPLEMENTATION REGISTERED
// and exits 2 — a distinct, legible status that is neither a pass nor a crash.
// The alternative, a stub generator living here to "make the harness runnable",
// would be a schedule generator inside the harness that grades schedule
// generators, and the first thing a later task would do is borrow it. The
// pipeline's independence is worth more than a green run.
//
// The self-test path (-self-test, the replay implementation) exists precisely so
// that the harness can be proven to work without anything registered here. A
// replay answers from the vector store and computes nothing.
