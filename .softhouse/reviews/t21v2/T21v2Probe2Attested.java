import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;

import java.io.File;
import java.io.InputStream;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Properties;

/*
 * T35 — RC-5. Prints the provenance header that `t21v2-probe2-oracle-out.txt` was missing, then hands
 * straight over to T21v2Probe2.main.
 *
 * DELIBERATELY A WRAPPER, NOT AN EDIT. `T21v2Probe2.java` is the T21-v2 audit's evidence-generating
 * source and is cited by `PASS3-REPORT.md`; it is left byte-unchanged, so the 17 data rows below are
 * produced by literally the same class that produced the committed transcript. Row identity is then
 * a property of the code path, not a hope — and it is checked afterwards by diff.
 *
 * T27 §4.5 (RC-5): "That file is 17 bare data rows with no provenance header — no image digest, no
 * Fineract commit, no JVM string, no MoneyHelper.PRECISION line — unlike its sibling
 * t21v2-probe-oracle-out.txt:1-3, which prints all three."
 */
public class T21v2Probe2Attested {

    public static void main(String[] args) throws Exception {
        StringBuilder h = new StringBuilder();
        h.append("# ===================== PROVENANCE (T35, 2026-08-18) =====================\n");
        h.append("# Artefact : t21v2-probe2-oracle-out.txt — p12-vs-p19 divergence sweep, Path A seam.\n");
        h.append("# Re-emitted to close T27 review item RC-5 (the transcript carried no provenance header).\n");
        h.append("# Rows are produced by T21v2Probe2.main, unmodified; this class only prints this header.\n");
        h.append("# Values below marked (measured) are read inside this container during this run.\n");
        h.append("# Values marked (echoed) come from the runner's environment and are NOT measurements.\n");
        h.append("#\n");

        Properties git = new Properties();
        try (InputStream in = T21v2Probe2Attested.class.getResourceAsStream("/git.properties")) {
            if (in != null) {
                git.load(in);
            }
        }
        File jar = new File("/app/fineract-provider.jar");
        h.append("# reference oracle (Fineract)\n");
        h.append("#   git.commit.id from the jar's BOOT-INF/classes/git.properties (measured) : ")
                .append(git.getProperty("git.commit.id")).append("\n");
        h.append("#   git.commit.id.describe (measured)                                      : ")
                .append(git.getProperty("git.commit.id.describe")).append("\n");
        h.append("#   git.dirty (measured)                                                   : ")
                .append(git.getProperty("git.dirty")).append("\n");
        h.append("#   /app/fineract-provider.jar sha256 (measured)                           : ")
                .append(jar.isFile() ? sha256(jar.toPath()) : "JAR NOT FOUND").append("\n");
        h.append("#   docker image ref (echoed)                                              : ")
                .append(System.getenv("ATTEST_IMAGE_REF")).append("\n");
        h.append("#   docker image id  (echoed)                                              : ")
                .append(System.getenv("ATTEST_IMAGE_ID")).append("\n");
        h.append("#   pinned checkout commit (echoed)                                        : ")
                .append(System.getenv("ATTEST_PINNED_COMMIT")).append("\n");
        h.append("#\n# JVM (measured)\n");
        h.append("#   ").append(System.getProperty("java.vm.name")).append(" ")
                .append(System.getProperty("java.vm.version")).append(" / runtime ")
                .append(System.getProperty("java.runtime.version")).append(" / vendor ")
                .append(System.getProperty("java.vendor")).append("\n");
        h.append("#   os ").append(System.getProperty("os.name")).append(" ").append(System.getProperty("os.arch"))
                .append(", file.encoding ").append(System.getProperty("file.encoding"))
                .append(", user.timezone ").append(System.getProperty("user.timezone")).append("\n");

        String probe = "t35_rc5_probe";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, probe, probe, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(probe, 4);
        MathContext mc = MoneyHelper.getMathContext();
        RoundingMode rm = MoneyHelper.getRoundingMode();
        ThreadLocalContextUtil.reset();
        h.append("#\n# rounding seam (measured)\n");
        h.append("#   MoneyHelper.PRECISION                        : ").append(MoneyHelper.PRECISION).append("\n");
        h.append("#   effective MathContext for a tenant set to 4  : precision=").append(mc.getPrecision())
                .append(" roundingMode=").append(mc.getRoundingMode().name())
                .append(" ordinal=").append(rm.ordinal()).append("\n");
        h.append("#   ratified production setting                  : (19, HALF_UP), RoundingMode ordinal 4\n");
        h.append("#   matches ratified production setting          : ")
                .append(mc.getPrecision() == 19 && rm == RoundingMode.HALF_UP).append("\n");
        h.append("#   per-run tenant rounding mode inside the probe: value 4 (HALF_UP) is passed for EVERY run\n");
        h.append("#     [T21v2Probe2.java:29 initializeTenantRoundingMode(id, 4)] — and the oracle's own INFO\n");
        h.append("#     lines interleaved below independently corroborate it, one per run.\n");
        h.append("#   NOTE: the p12/p19 SWEEP ITSELF deliberately passes an explicit MathContext of precision\n");
        h.append("#     12 or 19 to generate() [T21v2Probe2.java:48-49]; that is the variable under test.\n");
        h.append("#     The rounding MODE is HALF_UP on both arms. Precision 12 is a DISCRIMINATION PROBE\n");
        h.append("#     setting, never a parity setting.\n");
        h.append("#\n# fixed inputs for every row, from the probe source\n");
        h.append("#   currency MNT, decimalPlaces 2, inMultiplesOf null [T21v2Probe2.java:30]\n");
        h.append("#   start/disbursement 2024-01-01, MONTHS/1, DAYS_30, DAYS_360, DECLINING_BALANCE,\n");
        h.append("#   downPayment 0, daysInYearCustomStrategy null, allowPartialPeriodInterestCalculation true,\n");
        h.append("#   allowFullTermForTranche false [T21v2Probe2.java:31-33]\n");
        h.append("#   verdict IDENTICAL/DIFFERENT is a FULL-SCHEDULE comparison, not a totals comparison\n");
        h.append("#   [T21v2Probe2.java:36-44, :64]\n");
        h.append("#\n# sources compiled for this run (measured)\n");
        String[] srcs = (System.getenv("ATTEST_SOURCES") == null ? "" : System.getenv("ATTEST_SOURCES")).split(":");
        for (String s : srcs) {
            if (s.isEmpty()) {
                continue;
            }
            Path p = Paths.get(s);
            h.append("#   ").append(Files.isRegularFile(p) ? sha256(p) : "MISSING").append("  ").append(s).append("\n");
        }
        h.append("#\n# emitted at (measured, UTC): ").append(Instant.now().toString()).append("\n");
        h.append("# ================== END PROVENANCE — rows follow ==================\n");
        System.out.print(h);
        System.out.flush();

        T21v2Probe2.main(args);
    }

    static String sha256(Path p) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = Files.newInputStream(p)) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) {
                md.update(buf, 0, n);
            }
        }
        StringBuilder s = new StringBuilder();
        for (byte b : md.digest()) {
            s.append(String.format("%02x", b));
        }
        return s.toString();
    }
}
