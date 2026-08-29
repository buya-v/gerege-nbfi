"""T464 — ATTACK T455's SHIPPED SECTION-10 PREDICATES. Which smuggling shapes evade them?

T455 ships two predicates and states that PREDICATE 2 "closes (B)". PREDICATE 2 asks: does
every payload the tooling actually EMITS that states a false claim carry the tag INSIDE the
payload? Its emitter recogniser is `emitted_payload`, which recognises a line only if it
starts with `echo ` or `print(`. So the question this file asks is: what happens to abuse B
through a DIFFERENT emitter?

The real functions are LIFTED OUT OF THE SHIPPED GRADER by source extraction — nothing is
re-implemented here, because a re-implementation would only prove that my copy behaves as I
wrote it.

    python3 60-t464-sec10-evasion.py <path-to-verify-capture-integrity.py>

The grader's path is an ARGUMENT, not a literal.

EXIT 0  the classifier behaved as recorded below (including the evasions).  EXIT 1 it did not.
"""
import re
import sys

src = open(sys.argv[1], encoding="utf-8").read()
ns_src = re.search(r"FALSE_CLAIMS = tuple\(.*?\n\)\)\n", src, re.S).group(0)
ns_src += 'TAG = "QUOTED-" + "FALSE-CLAIM"\n'
for fn in ("states_a_false_claim", "strip_trailing_comment", "emitted_payload",
           "tagged_blocks", "grade_binding"):
    m = re.search(r"\ndef %s\(.*?\n(?=\n\n)" % fn, src, re.S)
    if not m:
        print("REFUSED: %s is not in the grader at this ref; nothing to attack." % fn)
        sys.exit(3)
    ns_src += m.group(0)
ns = {}
exec(ns_src, ns)
grade = ns["grade_binding"]
TAG = ns["TAG"]
SENT = "There is no " + ns["FALSE_CLAIMS"][3] + "."   # assembled, never a literal here

GOOD = ('  echo "  [%s] %s"\n'
        '  echo "THE BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION."\n' % (TAG, SENT))

# label -> (fixture, expected verdict)
CASES = [
    ("control: correctly tagged quotation", GOOD, "PASSES"),
    ("B  : echo, tag in trailing comment", GOOD + '  echo "%s"  # %s\n' % (SENT, TAG), "CAUGHT"),
    ("C  : quotation deleted, 3 bare tags", ('  # %s (tidied)\n' % TAG) * 3, "CAUGHT"),
    ("B' : printf, tag in trailing comment",
     GOOD + '  printf "%s\\n"  # %s\n' % (SENT, TAG), "PASSES"),
    ("B'': `>&2 echo`, tag in trailing comment",
     GOOD + '  >&2 echo "%s"  # %s\n' % (SENT, TAG), "PASSES"),
    ("B''': sys.stdout.write, tagged comment",
     GOOD + '  sys.stdout.write("%s")  # %s\n' % (SENT, TAG), "PASSES"),
    ("B'''': heredoc body, untagged",
     GOOD + '  cat <<EOF\n%s\nEOF\n' % SENT, "CAUGHT"),
    ("B''''': echo -e, tag in trailing comment",
     GOOD + '  echo -e "%s"  # %s\n' % (SENT, TAG), "CAUGHT"),
]

print("############ T464 — WHICH SMUGGLING SHAPES EVADE SECTION 10?")
print("  PREDICATE 1 = no UNTAGGED line states a claim AND a de-wrapped tagged block quotes one")
print("  PREDICATE 2 = every EMITTED payload stating a claim carries the tag inside the payload")
print()
bad = []
for label, text, want in CASES:
    untagged, quoted, printed = grade(text)
    p1 = (not untagged) and quoted >= 1
    p2 = not printed
    got = "PASSES" if (p1 and p2) else "CAUGHT"
    by = ",".join([n for n, ok in (("P1", not p1), ("P2", not p2)) if ok]) or "-"
    flag = "OK  " if got == want else "BAD "
    if got != want:
        bad.append(label)
    print("  %s %-42s untagged=%d quoted=%d printed=%d  -> %-6s by %s"
          % (flag, label, len(untagged), quoted, len(printed), got, by))
print()
print("  READ THE FOUR `PASSES` ROWS THAT ARE NOT THE CONTROL. They are abuse B — the exact")
print("  construction T448 found and T455 shipped PREDICATE 2 to close — re-achieved through")
print("  an emitter `emitted_payload` does not recognise. PREDICATE 1 does not see them either,")
print("  because the tag IS on the source line. `printf` is not exotic: it is already used 12x")
print("  in 10-drive-conditions.sh and 5x in run-all.sh, two of the four files section 10")
print("  guards. PREDICATE 2 closes abuse B FOR `echo` AND `print(`, and that scope is not")
print("  published beside the claim (P-29: publish the edit that should trip it but won't).")
print()
if bad:
    print("T464 SECTION-10 EVASION: %d case(s) did not behave as recorded: %s" % (len(bad), bad))
    sys.exit(1)
print("T464 SECTION-10 EVASION: every case as recorded. EXIT 0")
