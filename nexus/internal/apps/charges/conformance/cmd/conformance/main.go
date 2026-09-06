// Command conformance replays the golden-vector store through the Go charges
// implementation and grades it against the recorded reference oracle. With no
// vectors present it refuses (exit 2) rather than reporting a pass over zero
// work.
//
// Exit codes: 0 all graded vectors pass and at least one PARITY vector was
// graded; 1 a mismatch or an invariant violation; 2 the harness, corpus, pin or
// capability registry is unusable. Never a false PASS.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/gerege/nexus/internal/apps/charges/conformance"
)

func main() {
	var (
		root      = flag.String("root", "", "checkout to grade (the directory that contains nexus/). No working-directory fallback.")
		store     = flag.String("store", "", "vector store root (default <root>/.softhouse/vectors)")
		ctxFilter = flag.String("context", "charges", "grade only this context directory of the vector store")
		pinPath   = flag.String("pin", "", "store pin JSON (default <root>/.softhouse/PIN-charges.json)")
		regPath   = flag.String("registry", "", "capability registry JSON (default <root>/.softhouse/capabilities-charges.json)")
		implName  = flag.String("impl", "", "registered implementation to grade (default: the only CORRECT one, if exactly one is registered)")
		listImpls = flag.Bool("list-implementations", false, "print the registered implementations and exit")
	)
	flag.Parse()

	if *root == "" {
		fmt.Fprintln(os.Stderr, "conformance: -root is required and has no working-directory fallback")
		os.Exit(2)
	}
	repoRoot := *root

	storeRoot := *store
	if storeRoot == "" {
		storeRoot = filepath.Join(repoRoot, ".softhouse", "vectors")
	}
	if *pinPath == "" {
		*pinPath = filepath.Join(repoRoot, ".softhouse", "PIN-charges.json")
	}
	if *regPath == "" {
		*regPath = filepath.Join(repoRoot, ".softhouse", "capabilities-charges.json")
	}

	if *listImpls {
		names := conformance.RegisteredNames()
		for _, n := range names {
			if defect, bad := conformance.IsRegisteredWrong(n); bad {
				fmt.Printf("%s   DELIBERATELY WRONG: %s\n", n, defect)
				continue
			}
			fmt.Println(n)
		}
		return
	}

	opts := conformance.Options{
		RepoRoot:      repoRoot,
		StoreRoot:     storeRoot,
		ContextFilter: *ctxFilter,
	}

	if p, err := conformance.LoadPin(*pinPath); err != nil {
		fmt.Fprintf(os.Stderr, "conformance: %v\n", err)
		os.Exit(2)
	} else {
		opts.Pin = p
	}
	if r, err := conformance.LoadCapabilityRegistry(*regPath); err != nil {
		fmt.Fprintf(os.Stderr, "conformance: %v\n", err)
		os.Exit(2)
	} else {
		opts.Registry = r
	}

	switch {
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
		names := conformance.CorrectImplementationNames()
		if len(names) == 1 {
			impl, _ := conformance.Lookup(names[0])
			opts.Implementation = impl
			opts.ImplementationName = names[0]
		}
		// Zero CORRECT registered implementations leaves Implementation nil on
		// purpose: Run reports it as a fatal reason and the exit code is 2. A
		// deliberately-wrong implementation must never become the default.
	}

	summary, err := conformance.Run(context.Background(), opts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "conformance: %v\n", err)
		os.Exit(2)
	}
	conformance.WriteReport(os.Stdout, summary)
	os.Exit(summary.ExitCode())
}
