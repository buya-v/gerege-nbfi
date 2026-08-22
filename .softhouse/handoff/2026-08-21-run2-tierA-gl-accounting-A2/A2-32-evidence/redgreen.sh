#!/bin/bash
# A2-32 — I4-BUILDER population, BOTH POLARITIES (P-22 / P-50).
# GREEN arm: the real nexus/ tree in the A2-32 worktree.
# RED   arm: a /tmp scratch copy with three builder verbs planted, to prove the probe
#            and the REAL guard binary both SEE a member when one exists — i.e. the zero
#            on the green arm is a measurement and not a broken probe.
# Writes NOTHING inside the repo. The scratch tree lives under /tmp and is rebuilt here.
set -u
WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a356a016636abdd7e
cd "$WT" || exit 9
. .softhouse/bin/go-env.sh

GUARD_BIN=/tmp/a2-32/ledgerguard
(cd "$WT/.softhouse/guards/ledgerguard" && go build -o "$GUARD_BIN" .) || exit 1
PROBE_BIN=/tmp/a2-32/builderpop-bin
(cd /tmp/a2-32/builderpop && go build -o "$PROBE_BIN" .) || exit 1

echo "=== A2-32 I4-BUILDER population, both polarities ==="
echo "worktree HEAD: $(git rev-parse --short HEAD)"
echo

echo "--- GREEN: A2-32's own probe over the real tree ---"
"$PROBE_BIN" "$WT/nexus"
echo

echo "--- GREEN: the REAL ledgerguard binary over the same tree (control) ---"
"$GUARD_BIN" --root "$WT/nexus" 2>&1 | grep -a -E '^CENSUS ledger-invariants —|^clean:|I4-BUILDER|^REFUSED'
echo

RED=/tmp/a2-32/red-tree
rm -rf "$RED"
mkdir -p "$RED"
cp -R "$WT/nexus/." "$RED/"
mkdir -p "$RED/internal/apps/probe"
cat > "$RED/internal/apps/probe/planted.go" <<'EOF'
package probe

type JournalEntry struct{ Amount int64 }

type db struct{}

func (d db) Update(x any) {}
func (d db) Delete(x any) {}
func (d db) Save(x any)   {}

func plant(d db) {
	var journalEntry JournalEntry
	d.Update(journalEntry)
	d.Delete(journalEntry)
	d.Save(journalEntry)
}
EOF

echo "--- RED: A2-32's own probe over the scratch tree with three builder verbs planted ---"
"$PROBE_BIN" "$RED"
echo

echo "--- RED: the REAL ledgerguard binary over the scratch tree (control) ---"
"$GUARD_BIN" --root "$RED" 2>&1 | grep -a -E 'I4-BUILDER|^REFUSED|^clean:'
echo
echo "=== end ==="
