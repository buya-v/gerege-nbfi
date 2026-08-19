// Command conformance replays the golden-vector store through the Go
// loan-schedule implementation and grades it against the reference oracle's
// captured output.
//
// It is normally invoked through .softhouse/conformance.sh, which sources the
// repo-local Go toolchain, probes the reference oracle and runs the HARD grep
// guards before handing over. Running this binary directly is supported; a caller
// that does so and forgets to say whether the oracle is reachable gets exit 2,
// because the flag defaults to "down".
//
// Exit codes: 0 all graded vectors pass and at least one PARITY vector was
// graded; 1 a mismatch or an invariant violation; 2 the harness, corpus or oracle
// is unusable. Never a false PASS.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/gerege/nexus/internal/apps/loanschedule/conformance"
)

func main() {
	var (
		contextFilter = flag.String("context", "", "grade only this context directory of the vector store")
		storeRoot     = flag.String("store", "", "vector store root (default <repo>/.softhouse/vectors)")
		implName      = flag.String("impl", "", "registered implementation to grade (default: the only one, if exactly one is registered)")
		oracleProbe   = flag.String("oracle-probe", "down", `reference-oracle reachability as measured by the caller: "up", "down" or "skipped". Defaults to "down" so a caller that forgets cannot obtain exit 0.`)
		selfTest      = flag.Bool("self-test", false, "grade the HARNESS using the replay implementation instead of a port. Never a conformance PASS.")
		replayStore   = flag.String("replay-store", "", "with -self-test: the PRISTINE store the replay implementation answers from. Point -store at a perturbed copy to prove the harness goes red.")
		listImpls     = flag.Bool("list-implementations", false, "print the registered implementations and exit")
	)
	flag.Parse()

	repoRoot, err := conformance.FindRepoRoot(".")
	if err != nil {
		fmt.Fprintf(os.Stderr, "conformance: %v\n", err)
		os.Exit(2)
	}
	store := *storeRoot
	if store == "" {
		store = filepath.Join(repoRoot, ".softhouse", "vectors")
	}

	if *listImpls {
		names := conformance.RegisteredNames()
		if len(names) == 0 {
			fmt.Println("(no implementation registered — see cmd/conformance/impl_hook.go)")
		}
		for _, n := range names {
			fmt.Println(n)
		}
		return
	}

	opts := conformance.Options{
		RepoRoot:      repoRoot,
		StoreRoot:     store,
		ContextFilter: *contextFilter,
		OracleProbe:   *oracleProbe,
		SelfTestMode:  *selfTest,
	}

	switch {
	case *selfTest:
		src := *replayStore
		if src == "" {
			src = store
		}
		impl, n, rerr := conformance.NewReplayImplementation(src, *contextFilter)
		if rerr != nil {
			fmt.Fprintf(os.Stderr, "conformance: self-test replay store: %v\n", rerr)
			os.Exit(2)
		}
		opts.Implementation = impl
		opts.ImplementationName = fmt.Sprintf("replay[%s] (%d answers) — SELF-TEST ONLY, COMPUTES NOTHING", src, n)
	case *implName != "":
		impl, ok := conformance.Lookup(*implName)
		if !ok {
			fmt.Fprintf(os.Stderr, "conformance: no implementation named %q is registered (have: %v)\n",
				*implName, conformance.RegisteredNames())
			os.Exit(2)
		}
		opts.Implementation = impl
		opts.ImplementationName = *implName
	default:
		names := conformance.RegisteredNames()
		if len(names) == 1 {
			impl, _ := conformance.Lookup(names[0])
			opts.Implementation = impl
			opts.ImplementationName = names[0]
		}
		// Zero registered implementations leaves Implementation nil on purpose.
		// Run reports it as a fatal reason and the exit code is 2. It is NOT a
		// pass over zero work, and it is NOT a crash either: "there is no port
		// yet" is a legitimate, legible state of this program.
	}

	summary, err := conformance.Run(context.Background(), opts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "conformance: %v\n", err)
		os.Exit(2)
	}
	conformance.WriteReport(os.Stdout, summary)
	os.Exit(summary.ExitCode())
}
