# Driver measurement: `git merge` does NOT corrupt a running script's read offset

**Taken by** the driver of fire `20260827-230001`, immediately before merging T309, because T309's
diff grows `.softhouse/bin/fire-program.sh` **while this fire's wrapper is executing it**. This is
T301's exact scenario, so the driver measured instead of assuming — in either direction.

## The live hazard, measured first

```
$ ps -p 68244 -o pid,command
68244 /bin/zsh /Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh

$ lsof -p 68244 | grep fire-program
zsh  68244  buv  10r  REG  1,16  64888  10016673  …/.softhouse/bin/fire-program.sh

$ stat -f 'inode=%i size=%z' .softhouse/bin/fire-program.sh
inode=10016673 size=64888

$ git cat-file -s <blob at softhouse/t309-…:.softhouse/bin/fire-program.sh>
88714
```

So the premise is real and not hypothetical: a live `zsh` holds **fd 10 on inode 10016673**, and the
pending merge would grow that path by **23,826 bytes** (64,888 → 88,714) mid-execution.

## The test

The question T301 raises is whether `git merge` writes **in place** (same inode: truncate + rewrite,
which shifts every byte after the running shell's current offset) or **via rename** (new inode: the
running process keeps its own file). Driven in a throwaway repo under `mktemp -d`, with an fd held
open exactly the way a running shell holds one:

```
git init; commit "AAAA\n" on main; commit a longer "BBBB…\n" on other
exec 9< f.txt          # ← hold the fd, like a running script
git merge other
```

| measurement | value |
|---|---|
| inode before merge | `13859188` |
| inode after merge | **`13859198`** |
| `cat <&9` after the merge | **`AAAA`** — the ORIGINAL content |

**Result: NEW INODE.** Git wrote a temp file and renamed it over the path. The held fd still refers to
the old inode, which is unlinked but alive, and the process reading through it sees the **pre-merge
bytes for its entire remaining life.**

## What this means for T301 — and it partly cuts AGAINST T301's stated mechanism

T301's premise has two clauses. The first — *"zsh reads a script incrementally by byte offset"* — is
correct and is not in question here. The second, that a `git merge` therefore corrupts the running
wrapper, **does not follow on this filesystem with this git**, because the merge never mutates the
inode the wrapper is reading.

So the driver merged T309 rather than deferring it. **T301 is not thereby closed** — it should be
re-scoped by whoever runs it, to the writers that genuinely *do* reuse an inode, and to whether any
path in this repo writes `fire-program.sh` other than through git.

## Honest limits — this is ONE measurement and it should not be over-read

- `[VERIFIED]` for `git merge` on this host (APFS, case-insensitive) at this fire. `[UNVERIFIED]` for
  `git checkout`, `git stash`, `git apply`, `git restore`, or a rebase, none of which were driven.
- `[UNVERIFIED]` for any non-git writer. A shell redirect (`> file`) **does** truncate in place and
  would reproduce the corruption; `sed -i` on macOS renames, but that was not driven either.
- This does **not** establish that the T288 incident T301 describes did not happen. It establishes
  that `git merge` is not a sufficient explanation for it. **Someone should find out what actually
  wrote those bytes** — an incident with a refuted mechanism is an incident with no mechanism, and
  that is worse than an open one, because the guard will be built against the wrong thing.
