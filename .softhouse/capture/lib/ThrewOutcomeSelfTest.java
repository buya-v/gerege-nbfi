/*
 * ThrewOutcomeSelfTest — T169. P-22: ship no guard you have not driven RED.
 *
 * ThrewOutcome's RECORD-AND-CONTINUE branch is driven red against the reference oracle itself, by
 * the T169 probe (a real java.lang.StackOverflowError out of ProgressiveEMICalculator). Its
 * RECORD-AND-RE-THROW branch cannot be driven that way: this program will not deliberately exhaust
 * the oracle container's heap, and a LinkageError needs a corrupted classpath, which would
 * invalidate the very attestation the rigs depend on. So the FATAL branch is driven red HERE, with
 * throwables constructed in this file. Nothing in this file claims anything about Fineract; it
 * tests T169's own handler and says so.
 *
 * Every check below FAILS THE PROCESS if it does not hold. Run:
 *   javac -d /tmp/cls ThrewOutcome.java ThrewOutcomeSelfTest.java && java -cp /tmp/cls ThrewOutcomeSelfTest
 */
public final class ThrewOutcomeSelfTest {

    private static int checks = 0;
    private static int failures = 0;

    private static void check(String what, boolean ok) {
        checks++;
        if (!ok) {
            failures++;
            System.out.println("FAIL  " + what);
        } else {
            System.out.println("ok    " + what);
        }
    }

    /**
     * The handler shape T169 installs in every rig, isolated so it can be driven. Returns the JSON
     * fragment for a recorded throw; RE-THROWS anything the fatal rule calls fatal.
     */
    static String handle(String cellId, Throwable t) {
        StringBuilder b = new StringBuilder();
        if (ThrewOutcome.isFatal(t)) {
            ThrewOutcome.announceFatal(cellId, t);
            if (t instanceof RuntimeException re) {
                throw re;
            }
            throw (Error) t;
        }
        ThrewOutcome.appendThrew(b, t, 25);
        return b.toString();
    }

    public static void main(String[] args) {
        // ---- 1. THE FATAL RULE, class by class ------------------------------------------------
        check("OutOfMemoryError is FATAL", ThrewOutcome.isFatal(new OutOfMemoryError("synthetic")));
        check("InternalError is FATAL", ThrewOutcome.isFatal(new InternalError("synthetic")));
        check("UnknownError is FATAL", ThrewOutcome.isFatal(new UnknownError("synthetic")));
        check("NoClassDefFoundError (LinkageError) is FATAL", ThrewOutcome.isFatal(new NoClassDefFoundError("synthetic")));
        check("IncompatibleClassChangeError (LinkageError) is FATAL",
                ThrewOutcome.isFatal(new IncompatibleClassChangeError("synthetic")));
        // Constructed reflectively: ThreadDeath is terminally deprecated on Java 21 and a direct
        // `new ThreadDeath()` makes javac write a removal note to STDERR, which every runner in this
        // program treats as a refusal.
        Throwable threadDeath = null;
        try {
            threadDeath = (Throwable) Class.forName("java.lang.ThreadDeath").getDeclaredConstructor().newInstance();
        } catch (ReflectiveOperationException e) {
            threadDeath = null;
        }
        check("ThreadDeath is FATAL", threadDeath != null && ThrewOutcome.isFatal(threadDeath));

        check("StackOverflowError is NOT fatal — it is the finding", !ThrewOutcome.isFatal(new StackOverflowError()));
        check("ArithmeticException is NOT fatal", !ThrewOutcome.isFatal(new ArithmeticException("/ by zero")));
        check("NullPointerException is NOT fatal", !ThrewOutcome.isFatal(new NullPointerException()));
        check("AssertionError is NOT fatal", !ThrewOutcome.isFatal(new AssertionError("synthetic")));
        check("a checked Exception is NOT fatal", !ThrewOutcome.isFatal(new java.io.IOException("synthetic")));

        // ---- 2. THE FATAL BRANCH RE-THROWS, and it is driven RED here -------------------------
        boolean rethrown = false;
        try {
            handle("T169-SELFTEST-OOM", new OutOfMemoryError("synthetic — not a real heap exhaustion"));
        } catch (OutOfMemoryError e) {
            rethrown = true;
        }
        check("OutOfMemoryError is announced and RE-THROWN, not swallowed", rethrown);

        rethrown = false;
        try {
            handle("T169-SELFTEST-LINKAGE", new NoClassDefFoundError("synthetic"));
        } catch (NoClassDefFoundError e) {
            rethrown = true;
        }
        check("NoClassDefFoundError is announced and RE-THROWN, not swallowed", rethrown);

        // ---- 3. THE RECORD BRANCH RECORDS, and records the CLASS AND THE MESSAGE --------------
        StackOverflowError soe = new StackOverflowError();
        soe.setStackTrace(new StackTraceElement[] {
                new StackTraceElement("org.apache.fineract.portfolio.loanproduct.calc.ProgressiveEMICalculator",
                        "calculateLastUnpaidRepaymentPeriodEMI", "ProgressiveEMICalculator.java", 1214),
                new StackTraceElement("java.base/java.util.Optional", "ifPresent", "Optional.java", 178) });
        String soeJson = handle("T169-SELFTEST-SOE", soe);
        check("StackOverflowError is RECORDED, not re-thrown", soeJson.contains("\"outcome\": \"threw\""));
        check("the recorded cell carries observed: null", soeJson.contains("\"observed\": null"));
        check("the recorded cell names the CLASS",
                soeJson.contains("\"errorClass\": \"java.lang.StackOverflowError\""));
        check("the recorded cell names the MESSAGE slot even when the message is null",
                soeJson.contains("\"errorMessage\": null"));
        check("the recorded cell keeps the FRAMES", soeJson.contains("ProgressiveEMICalculator.java:1214"));
        check("the recorded cell reports how many frames it kept and how many there were",
                soeJson.contains("\"errorStackDepthCaptured\": 2") && soeJson.contains("\"errorStackDepthTotal\": 2"));

        String npeJson = handle("T169-SELFTEST-NPE", new IllegalStateException("a \"quoted\" message\nwith a newline"));
        check("a message with a quote and a newline does not break the JSON",
                npeJson.contains("\"errorMessage\": \"a \\\"quoted\\\" message with a newline\""));

        // ---- 4. A THREW CELL IS NEVER AN OBSERVATION ------------------------------------------
        check("no threw fragment ever emits an observed object", !soeJson.contains("\"observed\": {"));

        // ---- 5. FRAME CAP ---------------------------------------------------------------------
        StackOverflowError deep = new StackOverflowError();
        StackTraceElement[] many = new StackTraceElement[400];
        for (int i = 0; i < many.length; i++) {
            many[i] = new StackTraceElement("C", "m", "C.java", i);
        }
        deep.setStackTrace(many);
        String deepJson = handle("T169-SELFTEST-DEEP", deep);
        check("frames are capped at 25 and the TOTAL depth is still reported",
                deepJson.contains("\"errorStackDepthCaptured\": 25") && deepJson.contains("\"errorStackDepthTotal\": 400"));

        System.out.println();
        System.out.println("ThrewOutcomeSelfTest: " + checks + " checks, " + failures + " failures");
        if (failures != 0) {
            System.exit(1);
        }
    }
}
