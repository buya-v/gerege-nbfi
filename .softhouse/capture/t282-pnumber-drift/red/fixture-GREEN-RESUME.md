# STANDING INSTRUCTIONS (T282 RED fixture)

Three citations below are VERBATIM BYTES lifted from merged files in this repo.
Provenance is on the line above each one. Nothing here is invented.

<!-- from docs/adr/DEC-2-gl-accounting-adapter.md:294 -- cites P-79, states P-80 -->
> section number and restates no number** — `P-80`: never fix a rotted number, make the second site
> READ the first.

<!-- from .softhouse/capture/t256-verdict-predicate/RULES-failopen.md:17 -- cites P-80, states P-81 -->
| `\|\| echo …` | **P-81**: prints an absence over an error. `grep` exits 1 on NO MATCH and >1 on ERROR; `\|\| echo 0` makes those the same number |

<!-- from .softhouse/tasks.json:2427 -- cites P-80, states P-81 -->
Three separate workers last fire wrote fail-opens INTO instruments meant to enforce the rule they broke (P-81) — check T250's own instruments before you check anything else.
