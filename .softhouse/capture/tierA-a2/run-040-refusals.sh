#!/bin/sh
# GL-account refusal battery. Every one of these is EXPECTED to be refused —
# the refusal, verbatim, IS the observation. A 200 here would itself be the finding.
DIR=$(cd "$(dirname "$0")" && pwd)
for n in bad-040-dup-glcode bad-041-empty-body bad-042-no-name bad-043-no-glcode \
         bad-044-no-type bad-045-no-usage bad-046-type-9 bad-047-type-0 \
         bad-048-usage-5 bad-049-parent-missing bad-050-type-mismatch-parent \
         bad-051-glcode-too-long bad-052-name-too-long bad-053-unknown-param \
         bad-054-blank-name bad-055-blank-glcode; do
  sh "$DIR/cap.sh" "A2-${n}" POST /glaccounts "req/$n.json"
done
