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
// WHICH CHECKOUT IT GRADES, and why that is not the one you are standing in.
// The repository root is anchored to the tree this binary was COMPILED from,
// never to the working directory, and it is printed in the report header along
// with what the working directory would have resolved to. -repo-root (or
// CONFORMANCE_REPO_ROOT) overrides it and is validated just as strictly; there
// is no working-directory fallback, so a binary that cannot establish a root
// refuses instead of guessing. See conformance/reporoot.go for the measurement
// that made this necessary (T165).
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
		repoRootFlag  = flag.String("repo-root", "",
			"the checkout to grade. Default: the tree this binary was COMPILED from (runtime anchor). "+
				"There is no working-directory fallback — see reporoot.go and T165.")
	)
	flag.Parse()

	// T165. This used to be `conformance.FindRepoRoot(".")`, which resolved the
	// graded corpus, the no-float census root, the frozen-contract digest and
	// every capture_ref from THE CALLER'S WORKING DIRECTORY. One binary,
	// compiled from a tree carrying an unratified edit to the frozen DEC-1
	// contract, reported `VERDICT: UNUSABLE (exit 2) — frozen contract digest
	// does not match the store pin` from its own tree and `VERDICT: PASS
	// (exit 0) — 43 parity vectors` from a clean sibling checkout, with nothing
	// in the passing report naming which contract.go it had hashed. The anchor
	// is now the compiled-in source path, the resolution is printed on every
	// run, and a root that cannot be established is a refusal rather than a
	// guess. Full account and transcripts: conformance/reporoot.go.
	rootRes, err := conformance.ResolveRepoRoot(*repoRootFlag)
	if err != nil {
		fmt.Fprintf(os.Stderr, "conformance: %v\n", err)
		os.Exit(2)
	}
	repoRoot := rootRes.Root
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
		RepoRootRes:   rootRes,
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
