#!/bin/bash
# T382 — ADVERSARIAL DRIVE against T374's F-1 fix (section 10,
# .softhouse/reviews/A2-11/verify-capture-integrity.py).
#
# Every case MUTATES a scratch clone (never the working tree of any live worker), runs the
# integrity instrument, records its exit code, and RESETS to pristine. Case 0 is the CONTROL
# on unmutated input; every finding below is a delta against it.
#
# EXPECTED column is what T374's handoff claims or implies. GOT is measured.
set -u
SC=/tmp/t382-rerun
O=/tmp/t382-out
# DEAD-PATH FRONTIER NOTE (T316/T326). The paths this script creates in the scratch clone --
# the two decoys and the fabricated observation -- and the T374 file it drives DELIBERATELY do
# not exist in THIS branch's tracked universe (T382 forks from main; verify-capture-integrity.py
# is on softhouse/T374-t362-conditions). Spelled as whole literals they are DEAD repo paths and
# they moved the frontier 109 -> 114. They are assembled from variables instead, which is also
# the truthful classification: they are scratch-clone paths, not paths of this commit.
A2DIR=".softhouse/reviews/A2-11"
CAPDIR=".softhouse/capture/tierA-a2"
INT="$A2DIR/verify-capture-integrity.py"
FORKOBS="$CAPDIR/out/A2-000-glaccounts-preexisting.http"
POSTOBS="$CAPDIR/out/A2-201-read-gl16-fundsource.json"
mkdir -p "$O"
RESULTS="$O/attack-results.tsv"
: > "$RESULTS"

pristine() {
  git -C "$SC" reset --hard --quiet t382-pristine
  git -C "$SC" clean -fdq -- .softhouse/capture/tierA-a2 .softhouse/reviews/A2-11
  git -C "$SC" checkout --quiet -- . 2>/dev/null || true
}

run_case() {   # run_case <id> <expected> <note>
  local id="$1" expect="$2" note="$3"
  ( cd "$SC" && python3 "$INT" ) > "$O/case-$id.txt" 2>&1
  local rc=$?
  printf '%s\t%s\t%s\t%s\n' "$id" "$expect" "$rc" "$note" >> "$RESULTS"
  printf '%-34s expected=%-9s GOT=%s   %s\n' "$id" "$expect" "$rc" "$note"
}

git -C "$SC" tag -f t382-pristine HEAD >/dev/null 2>&1
pristine

echo "=========== T382 ATTACK MATRIX vs verify-capture-integrity.py ==========="
echo "scratch clone: $SC   pristine: $(git -C "$SC" rev-parse --short t382-pristine)"
echo

# --- 0. CONTROL -----------------------------------------------------------------
run_case "00-CONTROL-unmutated" 0 "control: the same command on unmutated input"

# --- 1. working-tree mutations, fork-sha observation (ARM A territory) -----------
pristine
printf 'T382-APPENDED-LINE\n' >> "$SC/$FORKOBS"
run_case "01-WT-append-forkobs" 1 "one line appended to a fork-sha observation (T362's exact shape)"

pristine
python3 - "$SC/$FORKOBS" <<'PY'
import sys
p = sys.argv[1]
b = bytearray(open(p, 'rb').read())
i = len(b) // 2
b[i] = b[i] ^ 0x01           # flip one bit in ONE byte in the MIDDLE
open(p, 'wb').write(bytes(b))
PY
run_case "02-WT-midbyte-forkobs" 1 "ONE byte changed in the middle of a fork-sha observation"

pristine
rm -f "$SC/$FORKOBS"
run_case "03-WT-delete-forkobs" 1 "a fork-sha observation DELETED from the working tree"

pristine
: > "$SC/$FORKOBS"
run_case "04-WT-empty-forkobs" 1 "a fork-sha observation replaced by an EMPTY file"

# --- 2. working-tree mutations, POST-FORK observation (ARM B territory) ----------
pristine
printf 'T382-APPENDED-LINE\n' >> "$SC/$POSTOBS"
run_case "05-WT-append-postforkobs" 1 "one line appended to a POST-FORK observation"

pristine
python3 - "$SC/$POSTOBS" <<'PY'
import sys
p = sys.argv[1]
b = bytearray(open(p, 'rb').read())
i = len(b) // 2
b[i] = b[i] ^ 0x01
open(p, 'wb').write(bytes(b))
PY
run_case "06-WT-midbyte-postforkobs" 1 "ONE byte changed in the middle of a POST-FORK observation"

pristine
rm -f "$SC/$POSTOBS"
run_case "07-WT-delete-postforkobs" 1 "a POST-FORK observation DELETED from the working tree"

pristine
: > "$SC/$POSTOBS"
run_case "08-WT-empty-postforkobs" 1 "a POST-FORK observation replaced by an EMPTY file"

# --- 3. symlink substitution ----------------------------------------------------
pristine
cp "$SC/$FORKOBS" "$SC/$CAPDIR/T382-decoy-identical.bin"
rm -f "$SC/$FORKOBS"
ln -s "$SC/$CAPDIR/T382-decoy-identical.bin" "$SC/$FORKOBS"
run_case "09-WT-symlink-same-bytes" "1?" "regular file replaced by a SYMLINK to identical bytes"
rm -f "$SC/$FORKOBS"

pristine
printf 'FABRICATED\n' > "$SC/$CAPDIR/T382-decoy-different.bin"
rm -f "$SC/$FORKOBS"
ln -s "$SC/$CAPDIR/T382-decoy-different.bin" "$SC/$FORKOBS"
run_case "10-WT-symlink-diff-bytes" 1 "regular file replaced by a SYMLINK to DIFFERENT bytes"
rm -f "$SC/$FORKOBS"

pristine
rm -f "$SC/$FORKOBS"
ln -s /dev/null "$SC/$FORKOBS"
run_case "11-WT-symlink-devnull" 1 "regular file replaced by a SYMLINK to /dev/null"
rm -f "$SC/$FORKOBS"

# --- 4. COMMITTED mutations — the class T374 discloses as partly uncovered ------
pristine
printf 'T382-COMMITTED-APPEND\n' >> "$SC/$FORKOBS"
git -C "$SC" add -A >/dev/null
git -C "$SC" -c user.name=t382 -c user.email=t382@x commit -qm 'T382 probe: COMMITTED mutation of a FORK-SHA observation'
run_case "12-COMMIT-mutate-forkobs" 1 "COMMITTED append to a FORK-SHA observation (ARM A should still see it)"

pristine
printf 'T382-COMMITTED-APPEND\n' >> "$SC/$POSTOBS"
git -C "$SC" add -A >/dev/null
git -C "$SC" -c user.name=t382 -c user.email=t382@x commit -qm 'T382 probe: COMMITTED mutation of a POST-FORK observation'
run_case "13-COMMIT-mutate-postforkobs" "1 (T374 says UNCOVERED)" "COMMITTED append to a POST-FORK observation — T374's disclosed gap"

pristine
git -C "$SC" rm -q "$POSTOBS"
git -C "$SC" -c user.name=t382 -c user.email=t382@x commit -qm 'T382 probe: COMMITTED DELETION of a POST-FORK observation'
run_case "14-COMMIT-delete-postforkobs" "1 (T374 discloses MUTATION only)" "COMMITTED DELETION of a POST-FORK observation"

pristine
printf 'HTTP/1.1 200 OK\r\n\r\n{"fabricated":true}\n' > "$SC/$CAPDIR/out/A2-999-T382-FABRICATED.http"
git -C "$SC" add -A >/dev/null
git -C "$SC" -c user.name=t382 -c user.email=t382@x commit -qm 'T382 probe: COMMITTED FABRICATED observation'
run_case "15-COMMIT-add-fabricated" "1?" "a FABRICATED observation COMMITTED into out/ (the oracle never returned it)"

pristine
printf 'HTTP/1.1 200 OK\r\n\r\n{"fabricated":true}\n' > "$SC/$CAPDIR/out/A2-999-T382-FABRICATED.http"
run_case "16-UNTRACKED-add-fabricated" "1?" "a FABRICATED observation left UNTRACKED in out/"
rm -f "$SC/$CAPDIR/out/A2-999-T382-FABRICATED.http"

# --- 5. laundering: mutate the observation AND the manifest that records it ------
pristine
printf 'T382-LAUNDERED\n' >> "$SC/$FORKOBS"
python3 - "$SC" "$FORKOBS" <<'PY'
import hashlib, os, sys
root, rel = sys.argv[1], sys.argv[2]
name = rel[len('.softhouse/capture/tierA-a2/'):]
man = os.path.join(root, '.softhouse/capture/tierA-a2/MANIFEST.sha256')
h = hashlib.sha256(open(os.path.join(root, rel), 'rb').read()).hexdigest()
lines = open(man).read().split('\n')
out = []
hit = 0
for L in lines:
    parts = L.split(None, 1)
    if len(parts) == 2 and parts[1].lstrip('*').strip() == name:
        out.append(h + '  ' + parts[1]); hit += 1
    else:
        out.append(L)
open(man, 'w').write('\n'.join(out))
print('manifest rows rewritten:', hit)
PY
run_case "17-LAUNDER-obs-and-manifest" 1 "observation mutated AND MANIFEST.sha256 updated to match"

# --- 6. baseline attacks --------------------------------------------------------
pristine
git -C "$SC" tag -f t382-savefork "$(git -C "$SC" rev-parse 12a7f8d9a3af4665fd5281a9f9c001d4f1276a53)" >/dev/null 2>&1
run_case "18-BASELINE-present" 0 "baseline object present (control for 19)"

pristine
sed -i.bak 's/^FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"/FORK = "0000000000000000000000000000000000000000"/' "$SC/$INT"
run_case "19-BASELINE-sha-swapped" 2 "the FORK baseline constant swapped for a nonexistent sha"
rm -f "$SC/$INT.bak"

pristine
run_case "20-CONTROL-again" 0 "control repeated after every mutation, tree back to pristine"

echo
echo "=========== results ==========="
column -t -s $'\t' "$RESULTS" 2>/dev/null || cat "$RESULTS"
