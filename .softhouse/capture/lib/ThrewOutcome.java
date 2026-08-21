/*
 * ThrewOutcome — the SHARED capture-rig throw recorder. Task T169, gerege-nbfi Fineract→Go
 * migration, Tier 0 / gate G-8.
 *
 * WHY THIS CLASS EXISTS
 * ---------------------
 * Every Java capture rig in this program descends from one source, and every one of them wrapped
 * the seam call in `catch (RuntimeException e)`. `java.lang.StackOverflowError` is an
 * `java.lang.Error`, NOT a `RuntimeException`, so it was precisely the throwable the handler could
 * not see. T159 found this by DETONATING it, not by reading it: the reference oracle's
 * `ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI` recurses into itself
 * (ProgressiveEMICalculator.java:1183 -> :1214) and blows the stack on some inputs, and it does so
 * NON-MONOTONICALLY — (B = 10001 minor, n = 2000) dies while (B = 10001, n = 3000) succeeds.
 *
 * On the pre-T169 rig that Error escaped run(), escaped main(), and killed the JVM before a single
 * byte of JSON reached stdout. So the integrity line every sweep in this program publishes —
 * "N asked / N observed / 0 errored / 0 skipped" — could never have printed anything but 0, in
 * either of the two ways a throw can happen:
 *
 *   an Error            -> uncaught -> no capture at all -> no integrity line at all;
 *   a RuntimeException  -> caught, but the old handler called e.printStackTrace(System.err) and
 *                          every runner refuses the run on non-empty stderr -> no integrity line.
 *
 * That makes "0 errored" a guard that cannot fail, which this program has ruled (P-22, P-35) is
 * worse than no guard, because it is believed. This class makes a throw a FIRST-CLASS OUTCOME:
 * neither an observation nor an absence.
 *
 * THE FATAL RULE — recorded deliberately, because a blanket catch nobody examined is its own defect
 * ---------------------------------------------------------------------------------------------
 * Catching Throwable risks swallowing something that SHOULD kill the process. The rule here is:
 *
 *   RECORD AND CONTINUE   StackOverflowError, and every RuntimeException / checked Exception.
 *                         A StackOverflowError is recoverable in the only sense that matters to a
 *                         capture rig: by the time the catch clause runs, the frames that
 *                         overflowed have been popped, the heap is untouched, and no shared state
 *                         of ours was mutated — the seam is a pure function of (MathContext,
 *                         LoanRepaymentScheduleModelData). The NEXT cell is therefore still
 *                         trustworthy, and the throw is the finding.
 *
 *   RECORD AND RE-THROW   VirtualMachineError other than StackOverflowError (chiefly
 *                         OutOfMemoryError, InternalError, UnknownError), ThreadDeath, and
 *                         LinkageError (NoClassDefFoundError, IncompatibleClassChangeError, ...).
 *                         For these the JVM itself, or the classpath, is no longer in a state in
 *                         which a LATER CELL'S NUMBERS COULD BE BELIEVED — and a capture rig whose
 *                         numbers cannot be believed must stop, loudly, not soldier on emitting
 *                         them. OutOfMemoryError in particular cannot be recorded richly (building
 *                         the JSON allocates), so announceFatal() prints only strings that already
 *                         exist — the cell id and the throwable's class name — and then the
 *                         re-throw kills the run with a non-zero exit the runner cannot miss.
 *
 * The improvement over the pre-T169 behaviour on the fatal path is NOT that the run survives. It is
 * that the run now names WHICH CELL killed it. Before, an Error produced a bare JVM stack trace and
 * an exit code, and the identity of the offending input had to be guessed.
 *
 * WHY THE FRAMES DO NOT GO TO STDERR
 * ----------------------------------
 * The old handler printed the trace to stderr. Every runner in this program refuses a run whose
 * stderr is non-empty, so that print converted a RECORDED cell into a FAILED RUN — the second way
 * "0 errored" was unfalsifiable. The frames now go into the cell's own JSON (errorStackTop, up to
 * maxFrames of them), which is where a reader looking at the capture will actually find them.
 * Nothing is discarded (T21 P1-9); it is relocated to the artefact that survives the run.
 *
 * PostgreSQL is the only permitted database in this program; this class opens no connection and
 * starts no server. "The oracle" in this program means the Fineract reference implementation,
 * never Oracle Database, which is prohibited.
 */
final class ThrewOutcome {

    private ThrewOutcome() {
    }

    /**
     * True for throwables after which no later cell in the same JVM may be graded. See the FATAL
     * RULE above. StackOverflowError is deliberately excluded: the stack has already unwound.
     */
    static boolean isFatal(Throwable t) {
        if (t instanceof StackOverflowError) {
            return false;
        }
        // ThreadDeath is matched BY NAME, deliberately. `t instanceof ThreadDeath` compiles, but the
        // class is terminally deprecated on Java 21 and javac emits a removal note ON STDERR — and
        // every runner in this program REFUSES a run whose stderr is non-empty. A shared class that
        // makes every future capture run refuse itself is not a fix. [VERIFIED: the first T169 Post
        // run emitted exactly that note, 145 bytes of stderr, from this line.]
        if ("java.lang.ThreadDeath".equals(t.getClass().getName())) {
            return true;
        }
        return t instanceof VirtualMachineError || t instanceof LinkageError;
    }

    /**
     * Announce a fatal throwable on stderr using only strings that already exist, so the announce
     * path allocates as little as possible under OutOfMemoryError. The caller re-throws.
     */
    static void announceFatal(String cellId, Throwable t) {
        System.err.print("FATAL-THROW cell=");
        System.err.print(cellId);
        System.err.print(" class=");
        System.err.println(t.getClass().getName());
        System.err.flush();
    }

    /**
     * Append the THREW outcome for a cell: outcome, class, message, top frames and cause. The
     * caller has already appended the cell's id, purpose and inputs; this method writes the cell's
     * closing brace.
     *
     * `"outcome": "threw"` is what makes a threw cell impossible to grade as an observation: the
     * classifier keys on it, and `"observed"` is null beside it.
     */
    static void appendThrew(StringBuilder b, Throwable t, int maxFrames) {
        b.append("      \"outcome\": \"threw\",\n");
        b.append("      \"observed\": null,\n");
        b.append("      \"errorClass\": ").append(q(t.getClass().getName())).append(",\n");
        b.append("      \"errorMessage\": ").append(q(t.getMessage())).append(",\n");
        // Legacy key, kept byte-compatible with every pre-T169 capture so existing readers that key
        // on "error" keep working. It is a CONVENIENCE, not the record: errorClass/errorMessage are.
        b.append("      \"error\": \"").append(t.getClass().getName()).append(": ")
                .append(String.valueOf(t.getMessage()).replace("\"", "'").replace("\n", " ")).append("\",\n");
        b.append("      \"errorStackTop\": [");
        StackTraceElement[] st = t.getStackTrace();
        int n = Math.min(st.length, maxFrames);
        for (int i = 0; i < n; i++) {
            b.append(i == 0 ? "" : ", ").append(q(st[i].toString()));
        }
        b.append("],\n");
        b.append("      \"errorStackDepthCaptured\": ").append(n).append(",\n");
        b.append("      \"errorStackDepthTotal\": ").append(st.length).append(",\n");
        Throwable cause = t.getCause();
        b.append("      \"errorCause\": ")
                .append(q(cause == null ? null : cause.getClass().getName() + ": " + cause.getMessage())).append("\n");
        b.append("    }");
    }

    private static String esc(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ").replace("\r", " ")
                .replace("\t", " ");
    }

    /** JSON string literal, or the bare token null. */
    private static String q(String s) {
        return s == null ? "null" : "\"" + esc(s) + "\"";
    }
}
