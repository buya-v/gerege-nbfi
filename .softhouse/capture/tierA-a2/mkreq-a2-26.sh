#!/bin/sh
# A2-26 request-body builder for the A2-3xx series.
#
# DELIBERATELY NOT PYTHON, AND DELIBERATELY NOT A JSON ROUND TRIP.
# ----------------------------------------------------------------
# The brief warns that several mkreq*.py in this directory are one float literal away
# from a defect, and A2-11/T163 already found that resolve7.py RESHAPED money literals in
# a body POSTed to the reference oracle. The defect class is structural: the moment a
# money literal passes through a language's default JSON parser it becomes a binary
# double and comes back out with a different spelling.
#
# So this builder never parses JSON at all. It is `sed` over two STRING fields
# (`shortName` and `name`), which cannot reach a numeric token. Every money field,
# every GL account id and every enum in the emitted body is byte-identical to the body
# the reference oracle originally accepted — which is the whole point of a G-10(c)
# re-admission probe: if the bytes changed, the probe would not be testing the stored
# mapping.
#
# The names MUST change: `m_product_loan` has unique constraints on name and shortName,
# so re-sending the original names would return a duplicate-name refusal and MASK the
# mapping verdict this probe exists to observe. That is a disclosed deviation from
# byte-identity, and `verify` below proves it is the ONLY one.
#
#   sh mkreq-a2-26.sh build     -> (re)write req/a2-26-admit-p*.json
#   sh mkreq-a2-26.sh verify    -> exit 0 only if each emitted body differs from its
#                                  source in nothing but those two string fields
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
R="$DIR/req"

# src-file | out-suffix | old-shortName | new-shortName | old-name | new-name
rows() {
  cat <<'ROWS'
prod-060-cash-with-channel-override.json|p22|A2C1|N22R|A2 Cash Mapping With Channel Override
prod-061-cash-no-override.json|p23|A2C2|N23R|A2 Cash Mapping No Override
prod-062-map-header-account.json|p24|A2R1|N24R|A2 Map Header Account
prod-067-duplicate-channel.json|p27|A2R5|N27R|A2 Duplicate Channel
prod-069-accrual-complete.json|p28|A2A1|N28R|A2 Accrual Complete
a2-7-prod-210-cash-nine-mandatory.json|p46|A7M1|N46R|A2-7 Cash Nine Mandatory Only
ROWS
}

newname() { echo "A2-26 G10c readmit of product ${1#p} mapping"; }

build() {
  rows | while IFS='|' read -r src sfx oldsn newsn oldnm; do
    nn=$(newname "$sfx")
    sed "s/\"shortName\": \"$oldsn\"/\"shortName\": \"$newsn\"/; s/\"name\": \"$oldnm\"/\"name\": \"$nn\"/" \
        "$R/$src" > "$R/a2-26-admit-$sfx.json"
    echo "built req/a2-26-admit-$sfx.json from req/$src"
  done
}

verify() {
  bad=0
  rows | while IFS='|' read -r src sfx oldsn newsn oldnm; do
    nn=$(newname "$sfx")
    # Reverse the two substitutions and demand byte-identity with the source.
    sed "s/\"shortName\": \"$newsn\"/\"shortName\": \"$oldsn\"/; s/\"name\": \"$nn\"/\"name\": \"$oldnm\"/" \
        "$R/a2-26-admit-$sfx.json" > "$R/.verify.$sfx.tmp"
    if cmp -s "$R/.verify.$sfx.tmp" "$R/$src"; then
      echo "OK   a2-26-admit-$sfx.json == $src apart from shortName+name"
    else
      echo "FAIL a2-26-admit-$sfx.json differs from $src beyond shortName+name" >&2
      diff "$R/.verify.$sfx.tmp" "$R/$src" >&2 || true
      bad=1
    fi
    rm -f "$R/.verify.$sfx.tmp"
    [ "$bad" -eq 0 ] || exit 1
  done
}

case "${1:-verify}" in
  build) build ;;
  verify) verify ;;
  *) echo "usage: mkreq-a2-26.sh build|verify" >&2; exit 2 ;;
esac
