#!/usr/bin/env bash
# T298 — can the MARKER DRIVE be satisfied without being true? Attacks on the extractor itself.
set -u -o pipefail
REPO="$1"
SRC="$REPO/.softhouse/reference-oracle.md"
W="$(mktemp -d /tmp/t298markers.XXXXXX)"
trap 'rm -rf "$W"' EXIT

extract () {  # $1 = doc
  awk '
    /T256-ACTIVATION-LINE:BEGIN/ { inblk=1; next }
    /T256-ACTIVATION-LINE:END/   { inblk=0 }
    inblk && /^```/              { fence=!fence; next }
    inblk && fence               { print }
  ' "$1"
}

show () { echo "  extracted -> [$(extract "$1" | tr '\n' '~')]  lines=$(extract "$1" | grep -c . || true)"; }

echo "== M0 CONTROL: the document as committed"; show "$SRC"

echo "== M1 both markers DELETED (someone 'tidies up' the HTML comments)"
grep -v 'T256-ACTIVATION-LINE' "$SRC" > "$W/m1.md"; show "$W/m1.md"

echo "== M2 END marker deleted only"
grep -v 'T256-ACTIVATION-LINE:END' "$SRC" > "$W/m2.md"; show "$W/m2.md"

echo "== M3 a SECOND fenced block added between the markers"
awk '{print} /^\. "\$\(git rev-parse --show-toplevel\)\/\.softhouse\/bin\/go-env\.sh"$/ && !d {
        print "```"; print ""; print "```bash"; print ". /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh"; d=1 }' \
    "$SRC" > "$W/m3.md"; show "$W/m3.md"

echo "== M4 the host-pinned line moved OUTSIDE the fence but INSIDE the markers (prose position)"
awk '/T256-ACTIVATION-LINE:END/ && !d { print "Run: . /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh"; d=1 } {print}' \
    "$SRC" > "$W/m4.md"; show "$W/m4.md"

echo "== M5 a SECOND, host-pinned activation block added ELSEWHERE in the document (outside the markers)"
printf '\n```bash\n. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh\n```\n' > "$W/tail.md"
cat "$SRC" "$W/tail.md" > "$W/m5.md"; show "$W/m5.md"
