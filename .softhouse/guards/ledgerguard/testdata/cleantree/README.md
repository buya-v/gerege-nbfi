# `cleantree` — the guard's NEGATIVE CONTROL, and why it is a committed fixture

`ledgerguard --selftest` needs one tree it asserts is CLEAN. Until T509 that tree was
`nexus/` itself, and the assertion was "the real Go tree must exit 0".

**That was a moving target, and it failed in the alarming direction.** When `nexus/` acquired
findings the guard was *supposed* to report, case (n) failed, and the head printed:

```
ledger-invariants: the guard FAILED ITS OWN SELFTEST (exit 1, 15 cases observed,
ledger-invariants:   14 drove it RED, 1 drove it GREEN — both are required).
ledger-invariants: it can no longer be shown to refuse the defect it exists to refuse.
```

All fourteen planted-defect cases had driven it RED correctly. The instrument was fine. The
transcript said it was broken, in the strongest words available, because it conflated two
claims a reader must never confuse:

* **the instrument is untrustworthy** — what the text says; and
* **the tree has known findings** — what was actually true.

It is also unpassable BY DESIGN going forward: the four `loanproduct` sites stay RED on a
recorded, argued, test-pinned decision (T502 / T505 / T514), so case (n) could never have gone
green again. A selftest that cannot pass is a selftest that gets ignored — P-45's shape.

So the negative control is now **this fixture**: a FIXED artefact the guard's authors own and
change deliberately. Every construct in it is the CORRECT way to write something the guard
refuses in its incorrect form, and each file says which. If a change to the guard turns this
tree red, that is a real over-match and the selftest fails — which is exactly the signal case
(n) was supposed to give and could not.

The real tree is still walked on every selftest run. Its result is now reported as a CENSUS
OBSERVATION with its finding count, not as a pass/fail assertion.

`testdata/` is ignored by the Go toolchain, so nothing here is built or vetted by
`go build ./...`; it exists only to be walked by the guard.
