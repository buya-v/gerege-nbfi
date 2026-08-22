#!/bin/bash
# A2-31 — drive the I4-BUILDER population measurement in BOTH polarities (P-22, P-50).
#
# A measurement that has never been shown returning NON-ZERO cannot be distinguished from a
# measurement that is blind. So this script measures the real tree (expect 0) AND a /tmp
# SCRATCH COPY with three query-builder verbs planted (expect 3, and the real guard REFUSES).
#
# Nothing is written inside the worktree. The scratch tree lives under /tmp.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3fcb4c7f1ea451ee
S=/tmp/a231-i4b
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"

rm -rf "$S"
mkdir -p "$S"
cp -R "$R/nexus" "$S/nexuscopy"
mkdir -p "$S/nexuscopy/internal/apps/probe"
cat > "$S/nexuscopy/internal/apps/probe/planted.go" <<'GO'
package probe

type repo struct{}

func (repo) Update(x string) {}
func (repo) Delete(x string) {}
func (repo) Save(x string)   {}

func plant() {
	var r repo
	r.Update("journal_entry")
	r.Delete("acc_gl_journal_entry")
	r.Save("anything")
}
GO

( cd "$R/.softhouse/guards/ledgerguard" && go build -o "$S/ledgerguard" . ) || exit 1

echo "=== A2-31: I4-BUILDER population, BOTH POLARITIES (P-22 / P-50) ==="
echo "worktree HEAD: $(cd "$R" && git rev-parse --short HEAD)"
echo
echo "--- GREEN ARM: the real worktree tree ---"
( cd "$R/.softhouse/reviews/a2-31-dec2-rev4/probe-builderpop" && go run . "$R/nexus" )
echo
echo "--- RED ARM: /tmp scratch copy with three query-builder verbs planted ---"
( cd "$R/.softhouse/reviews/a2-31-dec2-rev4/probe-builderpop" && go run . "$S/nexuscopy" )
echo
echo "--- the REAL ledgerguard binary on the same two roots ---"
echo "[GREEN]"
"$S/ledgerguard" --root "$R/nexus" 2>&1 | grep -E 'I4-BUILDER|NIL-COVERAGE|^clean|^REFUSED'
echo "[RED]"
"$S/ledgerguard" --root "$S/nexuscopy" 2>&1 | grep -E 'I4-BUILDER|NIL-COVERAGE|^clean|^REFUSED'
