# OBLIGATIONS (T282 RED fixture 2)

| idiom | why it is a fail-open |
|---|---|
| `\|\| echo …` | **P-80**: prints an absence over an error. `grep` exits 1 on NO MATCH and >1 on ERROR; `\|\| echo 0` makes those the same number |
