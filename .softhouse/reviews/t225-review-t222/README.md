# T225 — artefacts of the independent review of T222

The review itself is
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T225.md`.
**Verdict: REJECTED** (rework, no revert; the bar is green and the committed
corpus is unaffected).

| file | what |
|---|---|
| `t225_probe_test.go.txt` | The reviewer's probe suite. **Not a member of the shipped test suite** — it is stored as `.txt` deliberately so `go test ./...` does not pick it up. Copy it into `nexus/internal/apps/loanschedule/conformance/t225_probe_test.go` to re-run, and delete it afterwards. |
| `conformance-after-restore.txt` | `bash .softhouse/conformance.sh` on `main` (`d8db450`) **after** every mutation drill was reverted — the proof that nothing was left behind. Probe line at `:78` reads `up`; the exemption-grounding population line at `:247-248`. |
| `conformance-prove.txt` | `bash .softhouse/conformance.sh --prove` — `PROOFS: 23 passed, 0 failed`. |

Nothing here writes. No file under `.softhouse/vectors/` was created, modified or
read for writing; the vector tree digest is unchanged at
`73c3ea7b43dd75f04884072719a87fc8e1d255c1`.
