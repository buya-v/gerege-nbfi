#!/usr/bin/env bash
# T440 supplement: the case NEITHER T408 nor T424 named -- git ls-files failing AFTER
# it has already emitted lines. Then grep -c . succeeds (rc 0) and pipefail's rightmost
# NON-ZERO is git's own status.
set -uo pipefail
SHIM=$(mktemp -d "${TMPDIR:-/tmp}/t440.shim2.XXXXXX")
GITBIN=$(command -v git)
cat > "$SHIM/git" <<EOF
#!/bin/sh
if [ "\$1" = "ls-files" ]; then printf 'a\nb\nc\n'; exit 128; fi
exec $GITBIN "\$@"
EOF
chmod +x "$SHIM/git"
SHIPPED="$1"; REPO="$2"
ANCH='SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .); _corpus_rc=$?'
s=$(grep -n -F "$ANCH" "$SHIPPED" | cut -d: -f1)
NEW=$(sed -n "${s},$((s+14))p" "$SHIPPED")
echo "== git ls-files fails at rc 128 but HAS ALREADY PRINTED 3 lines =="
out=$( set -o pipefail; PATH="$SHIM:$PATH" git ls-files .softhouse 2>/dev/null | grep -c . ); rc=$?
printf '  pipefail git(128,3 lines)|grep -c .(0) -> captured=[%s] rc=%s\n' "$out" "$rc"
echo "  -> pipefail's rightmost NON-ZERO is git's own 128 here, because grep SUCCEEDED."
out=$(cd "$REPO" && PATH="$SHIM:$PATH" bash -c "set -uo pipefail
$NEW
echo 'FELL THROUGH'" 2>&1); rc=$?
printf '  SHIPPED block -> rc=%s\n' "$rc"
printf '%s\n' "$out" | sed 's/^/    | /'
rm -rf "$SHIM"
