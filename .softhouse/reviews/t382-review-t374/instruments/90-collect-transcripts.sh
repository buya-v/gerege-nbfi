#!/bin/bash
# T382 — copy every transcript this review cites out of /tmp and into the grant, so the
# evidence is committed alongside the instruments that produced it.
set -u
O=/tmp/t382-out
DEST="$(cd "$(dirname "$0")/.." && pwd)/out"
mkdir -p "$DEST"
cp -f "$O"/POPULATIONS.txt "$DEST"/ 2>/dev/null
cp -f "$O"/ATTACK-MATRIX.txt "$DEST"/ 2>/dev/null
cp -f "$O"/ATTACK-MATRIX-RUN1.txt "$DEST"/ 2>/dev/null
cp -f "$O"/ATTACK-MATRIX-RUN2-partial.txt "$DEST"/ 2>/dev/null
cp -f "$O"/attack-results-RUN2-partial.tsv "$DEST"/ 2>/dev/null
cp -f "$O"/FRONTIER.txt "$DEST"/ 2>/dev/null
cp -f "$O"/SATURATION.txt "$DEST"/ 2>/dev/null
cp -f "$O"/SATURATION-CLEAN.txt "$DEST"/ 2>/dev/null
cp -f "$O"/DEFEAT-BASELINE.txt "$DEST"/ 2>/dev/null
cp -f "$O"/MANIFEST-COVERAGE.txt "$DEST"/ 2>/dev/null
cp -f "$O"/PROVER-RERUN.txt "$DEST"/ 2>/dev/null
cp -f "$O"/prover-rerun.txt "$DEST"/ 2>/dev/null
cp -f "$O"/00-baseline-runall.txt "$DEST"/ 2>/dev/null
cp -f "$O"/census-mine.txt "$DEST"/ 2>/dev/null
mkdir -p "$DEST/cases"
for f in "$O"/run1-cases/case-*.txt; do cp -f "$f" "$DEST/cases"/ 2>/dev/null; done
for f in "$O"/sat-*.txt "$O"/sat31-*.txt; do cp -f "$f" "$DEST"/ 2>/dev/null; done
for f in "$O"/defeat-*.txt; do cp -f "$f" "$DEST"/ 2>/dev/null; done
cp -f "$O"/pinrows-main.txt "$O"/pinrows-t374.txt "$DEST"/ 2>/dev/null
cp -f "$O"/pop-fork.txt "$O"/pop-head.txt "$O"/pop-postfork.txt "$DEST"/ 2>/dev/null
cp -f "$O"/man430.txt "$O"/man430-nonobs.txt "$DEST"/ 2>/dev/null
ls -1 "$DEST" | wc -l
