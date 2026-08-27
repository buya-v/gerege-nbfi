#!/bin/bash
# A2-33 red/green driver for the I4-BUILDER population claim.
set -u
WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a5244bad2b6814a39
source "$WT/.softhouse/bin/go-env.sh"
cd /tmp/a233probe

echo "############ GREEN ARM — the real nexus/ tree at this review's HEAD ############"
go run . "$WT/nexus"
echo
echo "---- the REAL ledgerguard binary on the same tree ----"
cd "$WT/.softhouse/guards/ledgerguard" && go run . --root "$WT/nexus" 2>&1 | grep -E '^CENSUS ledger-invariants —|^CENSUS ledger-invariants SQL|^clean:|^REFUSED|^  \[|^NIL-COVERAGE'
echo

echo "############ RED ARM — scratch copy with builder verbs planted ############"
rm -rf /tmp/a233red
mkdir -p /tmp/a233red
cp -R "$WT/nexus/." /tmp/a233red/
mkdir -p /tmp/a233red/internal/apps/a233probe
cat > /tmp/a233red/internal/apps/a233probe/planted.go <<'PLANT'
package a233probe

type db struct{}

func (d *db) Update(x any) {}
func (d *db) Delete(x any) {}
func (d *db) Save(x any)   {}
func (d *db) Upsert(x any) {}

type journalEntry struct{ ID int64 }

func plant(d *db) {
	je := journalEntry{}
	d.Update(&je)
	d.Delete(&je)
	d.Save(&je)
	d.Upsert("acc_gl_journal_entry")
}
PLANT
cd /tmp/a233probe && go run . /tmp/a233red
echo
echo "---- the REAL ledgerguard binary on the RED tree ----"
cd "$WT/.softhouse/guards/ledgerguard" && go run . --root /tmp/a233red 2>&1 | grep -E '^CENSUS ledger-invariants —|^clean:|^REFUSED|^  \[|^NIL-COVERAGE'
echo "REAL-GUARD-RED-EXIT=${PIPESTATUS[0]}"
