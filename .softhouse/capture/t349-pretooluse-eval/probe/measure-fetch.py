#!/usr/bin/env python3
"""T349 -- the candidate gate needs origin's CONTENT, not just its tip sha, so it must
`git fetch origin main`, not `git ls-remote`. Cost that against the real GitHub origin."""
import subprocess
import sys
import time

repo = sys.argv[1]
xs = []
for i in range(8):
    t = time.time()
    p = subprocess.run(["git", "-C", repo, "fetch", "--quiet", "origin", "main"],
                       capture_output=True, text=True)
    dt = (time.time() - t) * 1000
    xs.append(dt)
    if i == 0:
        print("  first sample rc=%d stderr=%r" % (p.returncode, p.stderr.strip()[:80]))
xs.sort()
print("  git fetch origin main, %d samples, ms: min=%.0f median=%.0f p90=%.0f max=%.0f"
      % (len(xs), xs[0], xs[len(xs) // 2], xs[int(len(xs) * .9)], xs[-1]))
