#!/usr/bin/env bash
# T446 probe: which byte sequences does THIS filesystem fold onto an existing name?
# We are testing whether the claim "an all-lowercase ASCII path is unbeatable in a
# checkout collision" survives non-ASCII folding equivalents (long s, Kelvin sign,
# NFD decomposition) on APFS.
set -u
W="$1"
rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1

probe() {
  local label="$1" variant="$2"
  rm -rf t; mkdir t; cd t || return
  printf 'REAL\n' > 'conformance.sh'
  printf 'DECOY\n' > "$variant" 2>/dev/null
  local n; n=$(ls -1 | wc -l | tr -d ' ')
  local body; body=$(cat 'conformance.sh' 2>/dev/null | tr -d '\n')
  printf '%-28s files=%s  conformance.sh reads=%s' "$label" "$n" "$body"
  if [ "$n" = "1" ]; then printf '   <== FOLDS (collision!)\n'; else printf '   (distinct)\n'; fi
  cd ..
}

echo "== filesystem: $(df -T apfs . 2>/dev/null | tail -1 || df . | tail -1)"
echo "== macOS: $(sw_vers -productVersion 2>/dev/null)"
echo

probe "uppercase C"        "$(printf 'Conformance.sh')"
probe "uppercase H (.sH)"  "$(printf 'conformance.sH')"
probe "long s U+017F"      "$(printf 'conformance.\xc5\xbfh')"
probe "Kelvin U+212A (n/a)" "$(printf 'conformance.sh\xe2\x84\xaa')"
probe "NFD-irrelevant ascii" "$(printf 'conformance.sh ')"
echo
echo "== NFD/NFC folding test on a NON-ascii name (\xc3\xa9 vs e+\xcc\x81) =="
rm -rf u; mkdir u; cd u || exit 1
printf 'NFC\n' > "$(printf 'caf\xc3\xa9.sh')"
printf 'NFD\n' > "$(printf 'cafe\xcc\x81.sh')" 2>/dev/null
echo "files=$(ls -1 | wc -l | tr -d ' ')"
ls -b
for f in *; do printf '%s -> %s\n' "$(printf '%s' "$f" | xxd -p)" "$(cat "$f")"; done
