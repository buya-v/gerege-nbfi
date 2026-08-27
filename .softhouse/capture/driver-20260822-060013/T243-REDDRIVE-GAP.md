# DRIVER RED-DRIVE OF T243's WIRED FAIL-OPEN GUARD — a DETECTION GAP, measured

**Driver, local fire `20260822-060013`, at merged `main` `9cb49a3`.** `T243` reported its fail-open
guard **RED 13/0**. That report is TRUE, and it is **narrower than it reads**. The driver drove the
guard itself rather than trusting the transcripts (P-22), and the first probe **failed to trip it**.

## What the driver did

1. **Probe 1** — planted a tracked instrument with a dead path `/nonexistent/worktree/...` plus an
   unconditional `echo "   (no hits)"`. **conformance.sh: exit 0, VERDICT PASS.** Not detected **at all**.
2. **Calibrated the probe rather than concluding** (P-72, and T239's rule: *"not found" is a statement
   about the search*). Re-planted with a dead path of the shape the linter's C1 actually matches —
   `/Users/buv/gerege-nbfi/.claude/worktrees/agent-adeadbeefdeadbeef`.
3. **Probe 2** — the linter now **names the file and the line**. But `conformance.sh` is still
   **exit 0, VERDICT PASS**, because the plant is classified **TIER 3**, and only TIER 1 + TIER 2 form
   the pinned frontier the gate compares.

## The gap, stated exactly

The classifier needs **C1 (dead path) AND C2 (reassuring failure arm)** for Tier 1. **C2 requires the
reassuring output to be an arm of the failing construct.** Two shapes, both fail-open, only one covered:

```sh
# COVERED — A2-33's sweep.sh:14.  C2 fires.
( cd "$WT" && git grep -n -I -i -E "$re" -- . ) || echo "   (no hits)"

# NOT COVERED — r11-hygiene.sh:77-79.  C2 does not fire.
cd /tmp/T138-merge 2>/dev/null && \
  git grep -n -a -E '17 capture scripts|...' -- . | sed 's/^/   /'
echo "   (searched the MERGED tree)"          # <-- UNCONDITIONAL, on the NEXT line
```

Both exit 0 having searched nothing, and both print a sentence the reader will take as a measurement.

**`r11-hygiene.sh` is flagged ZERO times by the linter** — driver-measured, `grep -c "r11-hygiene"` over
the linter's full output. **That is the site `T239` measured live this fire, and the site the driver
relayed to `T238` mid-flight as the second confirmed instance of the class.** The guard that was wired
to close the class does not see the case that motivated widening the task.

## What this does and does not mean

- **It does NOT unmerge `T243`.** The wiring is genuine, the gate is reached, the frontier pin is real
  and already caught drift nobody noticed (`T238`'s `lint.json` recorded 3 Tier-2 instruments; there are
  7 — five arrived with `T239` in the same fire).
- **It DOES narrow the claim.** "The fail-open class is now fail-closed" is true **for the `|| echo`
  shape**. The unconditional-next-line shape is undetected, and the sample of two known live sites splits
  one-and-one across the boundary.
- **`T243`'s own red drive could not have caught this**, because it planted the covered shape. **A guard
  driven red only on the shape it was built from is `P-22` satisfied in letter and not in substance** —
  the drive proves the wiring, not the coverage. That distinction is the finding.

Filed as **T248**.
