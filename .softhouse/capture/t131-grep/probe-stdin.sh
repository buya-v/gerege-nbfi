#!/bin/bash
# T131 — shape T108 did NOT test: the money guard reads from a PIPE, not a file.
# Does BSD grep's UTF-8 blindness survive stdin, and does it survive -Eq?
D="$(cd "$(dirname "$0")" && pwd)/corpus"
mkdir -p "$D"
python3 -c "
open('$D/vec-float-poisoned.json','wb').write(b'{\n  \"note\": here_\xe2 principal_minor 1250000.75,\n  \"ok\": 1\n}\n')
open('$D/vec-float-clean.json','wb').write(b'{\n  \"note\": here principal_minor 1250000.75,\n  \"ok\": 1\n}\n')
"
PAT='[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]'
for f in vec-float-clean vec-float-poisoned; do
  for loc in C.UTF-8 en_US.UTF-8 C; do
    for g in "grep -Eq" "grep -aEq" "grep -Eqa"; do
      # exactly conformance.sh's shape: perl | grep -Eq  (STDIN)
      if perl -0pe 's/"(\\.|[^"\\])*"//g' "$D/$f.json" | LC_ALL=$loc $g "$PAT"; then v="FLOAT FOUND"; else v="clean - PASSES"; fi
      printf "PIPE  %-20s %-12s %-10s -> %s\n" "$f" "$loc" "$g" "$v"
    done
  done
done
echo "--- same but grep reads the FILE directly (no pipe) ---"
for f in vec-float-poisoned; do
  for loc in C.UTF-8 C; do
    if LC_ALL=$loc grep -Eq "$PAT" "$D/$f.json"; then v="FLOAT FOUND"; else v="clean - PASSES"; fi
    printf "FILE  %-20s %-12s -> %s\n" "$f" "$loc" "$v"
  done
done
