# OH-PROVGRADE-BC — grade the provisioning UPPER band edges. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-provgrade` (branch `feat/OHPROVGRADEbc`)
Work ONLY in that directory. **Take no captures.** **A run works ONLY in its own worktree.** The driver
pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/provisioning.md` — the criteria seam OH-PROVCRIT-AJ added, its vectors PV-10..13, drives.
2. `.softhouse/capture/provisioning-upper-edge/OWNER.md` — the new observation.
3. `.softhouse/vectors/provisioning/PV-10-BAND-STANDARD.json` — **your template**; copy its shape exactly.

## The observation — committed, driver-reviewed
`.softhouse/capture/provisioning-upper-edge/out/ENT-04-entry-loan-products-raw.json` (entry dated 2026-09-03):
overdue **29 → STANDARD**, **59 → SUB-STANDARD**, **89 → DOUBTFUL** — every upper edge INSIDE its band. The
band definitions are unchanged from CRI-02 (criteria 1; the capture's OWNER re-read them — verify).

## The task
Promote THREE vectors on the existing criteria seam — overdue 29, 59, 89 — each citing the new ENT-04 as
the decision (path + sha256) and CRI-02 (or the re-read definitions) for the bands, exactly as PV-10..13 do.
**No port change, no new seam.**

Then measure `provisioning-wrong-band-half-open` WITHOUT and WITH your vectors: it died on ONE vector (age 0,
a lower edge) before; the brief expects it to die on your three as well — report the counts. If the half-open
drive only models the LOWER edge, add ONE drive for an exclusive UPPER bound and measure it both ways; register
it only if a new vector kills it. Measure every other provisioning drive both ways too.

## Measuring
`kills.sh provisioning <impl> <worktree>`; controls `loanschedule-wrong-days-in-year-365` → **48** (moved from
45 by OH-LSGRADE-AX), `parties-wrong-iota-ordinals` → 12. **An empty result means the MEASUREMENT FAILED.**

## Non-negotiables
- Money in integer minor units (percentages micro-per-cent, as PV-10..13); no float.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, the capture files, or `.softhouse/maps/`.**
- `capture_ref` must be a JSON capture record; `capture_sha256`; re-verify. **One bounded context: `provisioning`.**
- PostgreSQL only; **Oracle Database is prohibited.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~250 iterations. **Commit by iteration 80.**
**`git commit -F <file>`. Never commit TASK.md.**
