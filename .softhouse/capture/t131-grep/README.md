# T131 evidence — independent re-derivation of T108's grep ruling

Every script here was written by T131 and is re-runnable. **No copy of T108's rig is kept here** (P-27):
re-run T108's own matrix with

```sh
git checkout softhouse/T108-grep-adjudication -- .softhouse/capture/t108-grep/
bash .softhouse/capture/t108-grep/run-matrix.sh    # -> 360 cells, SILENT-MISS 12, LOUD-MISS 0
```

T131 did exactly that in a scratch copy and got `out/matrix.tsv` **byte-identical** to the committed one
(361 lines, `diff` clean), and `gen-corpus.py` regenerates all 13 corpus files byte-identically.

| script | what it establishes |
|---|---|
| `run-bsd.sh` | 24-cell BSD-only sweep. Blind **only** when the invalid byte is before the match on the same line, in a UTF-8 locale. `LC_ALL=C` fixes; `-a` does not. |
| `probe-t80-bash.sh` | Rebuilds bash's `unbound variable` diagnostic from first principles and hexdumps it: a **lone `0xE2`**, before the match, same line. `grep -ac` → 0 / exit 1; `LC_ALL=C grep -ac` → 1 / exit 0. |
| `probe-commandv.sh` | **F-T131-1.** `command -v` *reports* shell functions in both bash and zsh; only `command <cmd>` bypasses. |
| `probe-ignorefiles.sh` | **F-T131-2.** `--ignore-files` is a second silent-miss mode under recursion, and neither `LC_ALL=C` nor `-a` fixes it. Must be *typed into the Bash tool* — a script never sees the function. |
| `probe-stdin.sh` | F-T108-1 on the **pipe** shape the real guard uses (T108's matrix used file arguments only), across 3 locales × 3 flag sets. |
| `probe-extra-shapes.sh` | Four shapes T108 did not test: float on both sides of the poison; a **valid** em dash; poison **inside** a JSON string; a **truncated** em dash. |
| `probe-vector-bytes.py` | Byte census of the committed vector store. **Run `--selftest` first — it drives the detector red and green.** |
| `probe-vector-utf8.py` | Characterises those bytes: valid vs invalid UTF-8, inside vs outside a string literal, float to the right on the same line. |
| `probe-go-bytes.py` | Same census over `nexus/internal/apps/loanschedule`. |

`out/repo-root-ab.txt` is the A/B at the identical start point that proves F-T131-2 (Bash-tool grep: exit 1, no output; BSD grep with both tokens: two hits, exit 0). `out/canary.txt` holds the string it searches for; `out/t80-diag.txt` is the
captured bash diagnostic; `out/mergetree.txt` is the non-destructive merge test of T108 into `main`.

`corpus/` and `ignoretest/` are generated fixtures. Nothing here is a vector and nothing here is promotable.
