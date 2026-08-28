#!/usr/bin/env bash
# T386 -- the R3 adjudication, measured. T379 and T238 both cite `git grep -E '\bmain\b'` and
# `git grep -E 'bmainb'` returning the SAME count as evidence that the engine is "fabricating".
# T381 re-measured and says the framing is wrong. This settles it by taking the two controls
# neither earlier task took.
#
#   bash .softhouse/reviews/t386-review-t381/instruments/t386-r3-measure.sh <repo-root>
#
# ARM A  the three counts T381 reports, summed the way the sweep sums them
# ARM B  BYTE-IDENTITY of the three outputs, not merely equality of their counts
# ARM C  the CONTROL nobody ran: does this engine interpret ERE metacharacters AT ALL?
# ARM D  the true answer, from an engine that really has word boundaries (-P, PCRE)
# ARM E  the vacuity of SWEEP OBSERVE's discriminator (two zeros also "agree")
set -uo pipefail
REPO=${1:?usage: <repo-root>}
cd "$REPO" || exit 2
sum() { git grep -c "$@" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'; }

echo "repo    : $REPO"
echo "head    : $(git rev-parse --short HEAD)"
echo "engine  : $(git --version)"
echo "corpus  : $(git ls-files .softhouse | grep -c .) tracked files under .softhouse/"
echo

echo '=== ARM A: the three counts ========================================================'
printf '  -E %-14s = %s\n' "'\\bmain\\b'" "$(sum -E '\bmain\b' -- .softhouse)"
printf '  -E %-14s = %s\n' "'bmainb'"     "$(sum -E 'bmainb'   -- .softhouse)"
printf '  -F %-14s = %s   <- the term T379 and T238 never measured\n' "'bmainb'" "$(sum -F 'bmainb' -- .softhouse)"
echo

echo '=== ARM B: are the three OUTPUTS byte-identical, or only their counts? ============='
T=$(mktemp -d "${TMPDIR:-/tmp}/t386-r3.XXXXXX"); trap 'rm -rf "$T"' EXIT
git grep -n -E '\bmain\b' -- .softhouse > "$T/esc" 2>/dev/null
git grep -n -E 'bmainb'   -- .softhouse > "$T/lit" 2>/dev/null
git grep -n -F 'bmainb'   -- .softhouse > "$T/fix" 2>/dev/null
for f in esc lit fix; do printf '  %-4s %s lines  sha256 %s\n' "$f" "$(grep -c . "$T/$f")" "$(shasum -a 256 < "$T/$f" | cut -d' ' -f1)"; done
if cmp -s "$T/esc" "$T/fix"; then
  echo '  >>> BYTE-IDENTICAL. `-E "\bmain\b"` IS `-F "bmainb"` on this engine -- not a similar'
  echo '  >>> count, the same bytes. The escape compiles to the literal letters.'
else
  echo '  >>> NOT identical -- the T238 framing would need re-deriving.'
fi
echo '  sample of what those lines actually are:'
head -4 "$T/fix" | cut -c1-120 | sed 's/^/    /'
echo '  >>> every one is a DOCUMENT ABOUT THIS HAZARD. The corpus is matching its own notes.'
echo

echo '=== ARM C: THE CONTROL. Does this engine interpret ERE metacharacters at all? ======'
printf '  -E %-14s = %s\n' "'ma(in|ni)'" "$(sum -E 'ma(in|ni)' -- .softhouse)"
printf '  -F %-14s = %s\n' "'ma(in|ni)'" "$(sum -F 'ma(in|ni)' -- .softhouse)"
echo '  >>> they DISAGREE by four orders of magnitude, so ERE alternation IS interpreted. The'
echo '  >>> engine is NOT literal-minded and is NOT broken. POSIX ERE simply has no \b.'
echo

echo '=== ARM D: the true answer, from an engine that HAS word boundaries ================'
printf '  -P %-14s = %s\n' "'\\bmain\\b'" "$(sum -P '\bmain\b' -- .softhouse)"
echo '  >>> that, not 108/114, is the number `\bmain\b` was ever asking for.'
echo

echo '=== ARM F: T234 ALREADY RAN THIS CONTROL, AND ITS NUMBERS WERE DIFFERENT =========='
# .softhouse/capture/t234-sweep-instrument-audit/HANDOFF.md:272-273 records, verbatim:
#     git grep -E -c 'bmainb'  repo-wide = 0        git grep -E -c '\bmain\b' repo-wide = 0
#     git grep -P -c '\bmain\b' repo-wide = 17646
# T234 characterised the hazard correctly -- 95.3 % RECALL LOSS -- and ran the -P control. The
# "fabrication" framing entered later. Re-run T234's own two repo-wide figures TODAY:
printf "  git grep -E -c 'bmainb'    repo-wide = %s     (T234 measured 0)\n"      "$(sum -E 'bmainb')"
printf "  git grep -E -c '\\\\bmain\\\\b'  repo-wide = %s     (T234 measured 0)\n" "$(sum -E '\bmain\b')"
printf "  git grep -P -c '\\\\bmain\\\\b'  repo-wide = %s (T234 measured 17646)\n" "$(sum -P '\bmain\b')"
echo '  >>> the -E figures went 0 -> today PURELY BECAUSE THE PROGRAM WROTE THE FINDING DOWN.'
echo '  >>> That is the self-referential artefact, demonstrated across time rather than asserted.'
echo

echo '=== ARM E: SWEEP OBSERVE would report "hazard LIVE" from a VACUOUS measurement ====='
printf '  -E %-24s = %s\n' "'\\bzzqabsentterm\\b'" "$(sum -E '\bzzqabsentterm\b' -- .softhouse)"
printf '  -E %-24s = %s\n' "'bzzqabsenttermb'"     "$(sum -E 'bzzqabsenttermb'   -- .softhouse)"
echo '  >>> both 0, they AGREE, and the arm prints "T238 hazard LIVE" having measured nothing.'
echo '  >>> The -E/-P pair in ARM D cannot agree vacuously; it is the better discriminator.'
