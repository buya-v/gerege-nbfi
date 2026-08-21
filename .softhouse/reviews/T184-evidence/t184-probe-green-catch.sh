#!/bin/bash
# T184: the GREEN half (P-50) for the narrow-catch lint, in two parts.
#   G1 = the SAME rig with the T169 seam handler (Throwable + isFatal rethrow) -> must PASS
#   G2 = the SAME rig with a narrow catch that does NOT wrap the seam -> must ALSO PASS
#        (P-52 control: proves the lint keys on the SEAM, not on "a new .java file exists")
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
J="$W/.softhouse/capture/t184-probe/src/CaptureT184Probe.java"

cat > "$J" <<'EOF'
class CaptureT184Probe {
  void run() {
    try {
      plan = generator.generate(mc, config);
      emit(plan);
    } catch (Throwable t) {
      if (ThrewOutcome.isFatal(t)) { throw t; }
      ThrewOutcome.appendThrew(b, t, 25);
    }
  }
}
EOF
echo "=== G1: same rig, seam handler widened to Throwable ==="
bash .softhouse/conformance.sh > /tmp/t184-green-catch1.txt 2>&1
echo "EXIT=$?"
grep -n 'CENSUS narrow\|narrow load-bearing\|REFUSED\|probe =\|VERDICT' /tmp/t184-green-catch1.txt

cat > "$J" <<'EOF'
class CaptureT184Probe {
  void run() {
    try {
      readSomeProperties();
    } catch (RuntimeException e) {
      record(e);
    }
    try {
      plan = generator.generate(mc, config);
    } catch (Throwable t) {
      if (ThrewOutcome.isFatal(t)) { throw t; }
    }
  }
}
EOF
echo "=== G2: narrow catch AWAY from the seam, seam itself widened ==="
bash .softhouse/conformance.sh > /tmp/t184-green-catch2.txt 2>&1
echo "EXIT=$?"
grep -n 'CENSUS narrow\|narrow load-bearing\|REFUSED\|probe =\|VERDICT' /tmp/t184-green-catch2.txt
