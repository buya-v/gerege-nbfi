#!/bin/bash
# T184: drive the narrow-catch lint RED through the REAL harness.
# P-52: the seam marker MUST be INSIDE the try, otherwise this is a BAD PROBE and
# T169 selftest cases (b)/(c) assert the lint must not fire on it.
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
mkdir -p "$W/.softhouse/capture/t184-probe/src"
cat > "$W/.softhouse/capture/t184-probe/src/CaptureT184Probe.java" <<'EOF'
class CaptureT184Probe {
  void run() {
    try {
      plan = generator.generate(mc, config);
      emit(plan);
    } catch (RuntimeException e) {
      record(e);
    }
  }
}
EOF
echo "=== RED run: new rig narrows the seam handler ==="
bash .softhouse/conformance.sh > /tmp/t184-red-catch.txt 2>&1
echo "EXIT=$?"
grep -n 'CENSUS\|REFUSED\|narrow load-bearing\|t184-probe\|HARD guard\|probe =\|VERDICT' /tmp/t184-red-catch.txt
