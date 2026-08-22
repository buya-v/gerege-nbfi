import io, sys
p = sys.argv[1]
src = io.open(p, encoding="utf-8").read()
old = '''  WN=$(basename "$W")
  WB="softhouse/rescued-$WN-$STAMP"
'''
new = '''  WN=$(basename "$W")
  # T202: a git ref may not contain a space (or ~ ^ : ? * [ \\ or a control char),
  # so a worktree whose path has one produced a branch name `git checkout -b`
  # rejects — the sweep then logged "rescuing to ..." and rescued NOTHING
  # [measured: scenario S6, 0 branches created]. Fold anything outside the safe
  # set to `-`; every real worktree name (`agent-<hex>`) is unchanged by this.
  WN="${WN//[^A-Za-z0-9._-]/-}"
  WB="softhouse/rescued-$WN-$STAMP"
'''
n = src.count(old)
if n != 1:
    raise SystemExit(f"anchor matched {n}, expected 1")
io.open(p, "w", encoding="utf-8").write(src.replace(old, new))
print("patched", p)
