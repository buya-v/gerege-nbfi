// T46 -- F39-1: is the month-end special case separable BY ITSELF anywhere?
//
// Runs inside the pinned oracle image (docker run --rm fineract:latest), on the SAME JDK the
// reference oracle runs, so the java.time semantics measured here are the oracle's own.
//
// Three readings of `numberOfPeriodBetweenSeedDateAndActualRepaymentPeriod`
// (ProgressiveEMICalculator.java:1423-1439, the MONTHS arm at :1425-1437):
//
//   nOracle  = packed months, WITH the month-end special case (:1432-1433)   -- the pinned source
//   nPacked  = packed months, special case OMITTED (T44's reading R3)
//   nNaive   = "calendar months, step back one if plusMonths overshoots",
//              special case OMITTED (T44's reading R4 -- the mis-port a porter writes)
//
// calculatePeriodRatio's return value is a pure function of
// (seedDate, fromDate, dueDate, n) -- n is the ONLY thing these three readings change
// [VERIFIED: :1441-1458 reads n at :1441 and :1449 and nowhere else].  So equal n on a
// (seed, fromDate) pair means byte-equal ratio for EVERY dueDate, hence equal money.
//
// This sweep is EXHAUSTIVE over ordered date pairs in 2000-01-01 .. 2040-12-31.
// It also measures the YEARS arm (:1424, no special case at all) for comparison.
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;

public class T46MonthDiffExhaustive {

    static int nPacked(LocalDate seed, LocalDate from) {
        return (int) ChronoUnit.MONTHS.between(seed, from);
    }

    static int nNaive(LocalDate seed, LocalDate from) {
        int k = (from.getYear() * 12 + from.getMonthValue()) - (seed.getYear() * 12 + seed.getMonthValue());
        if (seed.plusMonths(k).isAfter(from)) {
            k = k - 1;
        }
        return k;
    }

    static boolean fires(LocalDate seed, LocalDate from) {
        int seedDay = seed.getDayOfMonth();
        int targetDay = from.getDayOfMonth();
        int targetLast = ((LocalDate) TemporalAdjusters.lastDayOfMonth().adjustInto(from)).getDayOfMonth();
        return targetLast == targetDay && seedDay > targetDay;
    }

    static int yPacked(LocalDate seed, LocalDate from) {
        return (int) ChronoUnit.YEARS.between(seed, from);
    }

    static int yNaive(LocalDate seed, LocalDate from) {
        int k = from.getYear() - seed.getYear();
        if (seed.plusYears(k).isAfter(from)) {
            k = k - 1;
        }
        return k;
    }

    public static void main(String[] args) {
        final LocalDate lo = LocalDate.of(2000, 1, 1);
        final LocalDate hi = LocalDate.of(2040, 12, 31);

        long pairs = 0;
        long fireCount = 0;
        long packedNeNaive = 0;
        long firesAndPackedEqNaive = 0;      // special case fires but packed was already right
        long notFiresAndPackedNeNaive = 0;   // packed wrong without the special case firing
        long oracleNeNaive = 0;              // <-- the separability question: R2 vs R4
        long oracleNePacked = 0;             // <-- what the T39-ME family actually grades: R2 vs R3
        long yearsPackedNeNaive = 0;
        long firstFireSeed = 0;

        String firstOracleNeNaive = "(none)";
        String firstYearsSeparator = "(none)";

        for (LocalDate seed = lo; !seed.isAfter(hi); seed = seed.plusDays(1)) {
            for (LocalDate from = seed; !from.isAfter(hi); from = from.plusDays(1)) {
                pairs++;
                int p = nPacked(seed, from);
                int nv = nNaive(seed, from);
                boolean f = fires(seed, from);
                int o = f ? nPacked(seed, from.plusDays(1)) : p;
                if (f) {
                    fireCount++;
                    if (firstFireSeed == 0) {
                        firstFireSeed = 1;
                        System.out.println("first firing pair                           : seed=" + seed + " from=" + from
                                + "  nPacked=" + p + " nNaive=" + nv + " nOracle=" + o);
                    }
                }
                if (p != nv) {
                    packedNeNaive++;
                    if (!f) {
                        notFiresAndPackedNeNaive++;
                    }
                } else if (f) {
                    firesAndPackedEqNaive++;
                }
                if (o != nv) {
                    oracleNeNaive++;
                    if ("(none)".equals(firstOracleNeNaive)) {
                        firstOracleNeNaive = "seed=" + seed + " from=" + from + " nOracle=" + o + " nNaive=" + nv;
                    }
                }
                if (o != p) {
                    oracleNePacked++;
                }
                if (yPacked(seed, from) != yNaive(seed, from)) {
                    yearsPackedNeNaive++;
                    if ("(none)".equals(firstYearsSeparator)) {
                        firstYearsSeparator = "seed=" + seed + " from=" + from + " yPacked=" + yPacked(seed, from)
                                + " yNaive=" + yNaive(seed, from);
                    }
                }
            }
        }

        System.out.println("T46 exhaustive month-difference sweep");
        System.out.println("domain                                      : ordered pairs (seed <= from), " + lo + " .. " + hi);
        System.out.println("java.vm.version                             : " + System.getProperty("java.vm.version"));
        System.out.println("ordered date pairs swept                    : " + pairs);
        System.out.println("month-end special case FIRES (:1432)        : " + fireCount);
        System.out.println("nPacked != nNaive                           : " + packedNeNaive);
        System.out.println("fires AND nPacked == nNaive                 : " + firesAndPackedEqNaive);
        System.out.println("does NOT fire AND nPacked != nNaive         : " + notFiresAndPackedNeNaive);
        System.out.println("nOracle != nNaive   [R2 vs R4]              : " + oracleNeNaive);
        System.out.println("nOracle != nPacked  [R2 vs R3]              : " + oracleNePacked);
        System.out.println("first R2-vs-R4 separator found              : " + firstOracleNeNaive);
        System.out.println("YEARS arm: yPacked != yNaive                : " + yearsPackedNeNaive);
        System.out.println("first YEARS separator found                 : " + firstYearsSeparator);
    }
}
