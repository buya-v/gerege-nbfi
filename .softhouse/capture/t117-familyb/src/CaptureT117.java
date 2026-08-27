/*
 * Golden-vector capture harness, T83 — gerege-nbfi Fineract→Go migration, Tier 0. Gate G-8.
 *
 * THIS IS PASS 3g's RIG WITH A NEW CASE LIST AND PASS 3i's FIELD SPLIT. Every attestation field,
 * every emitted column and every emission rule of Capture3g.java is preserved byte-for-byte, so the
 * `observed` block of a case whose inputs match a pass-3g case must equal pass 3g's committed block
 * cell for cell. That is what makes the two RIG CALIBRATIONS below meaningful. The one structural
 * change is pass 3i's separation of `CurrencyData.inMultiplesOf` from
 * `installmentAmountInMultiplesOf` (T21 required change P1-8); EVERY case here passes null for
 * both, so both keys emit exactly as pass 3g emitted them.
 *
 * WHY THIS PASS EXISTS — task T117, gate G-8. Family B (600.0 % p.a., MNT 0.01, n >= 104) is a
 * GENUINE non-amortization that the Go port reproduces cell for cell, and it is measured at 29
 * cells and still UNCAUSED. Two things about its EXTENT are unknown: whether it is a half-line in
 * n (every n above some threshold) or a bounded island — nothing above n = 250 has ever been asked
 * at that shape — and whether the failing principal can exceed ONE MINOR UNIT — every family-B cell
 * ever measured is at B = 1 minor unit. T117 asks the oracle both questions directly: 166 cells at
 * B = 1 over n = 300..1000 (contiguous 300..400, a ladder to 1000, contiguous 995..999), and 32
 * cells at B = 2..5 across the whole family-B n range and above it. Two CTRL cells re-ask both
 * sides of the known n = 103/104 boundary under new tenant ids.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t117-familyb/PREDICTION.md and prediction.json, committed in an ANCESTOR
 * COMMIT of the one carrying this file, and the classification is done afterwards by
 * classify_t117.py reading only the emitted JSON.
 *
 * TWO RIG CALIBRATIONS, both ALREADY-PROMOTED parity vectors at the rounding floor at dp 2:
 *
 *   P-CAL-ZPA   inputs byte-identical to pass 3g's T64-ZP-A (MNT 0.28 / 56 x 21.6%), tenant id
 *               included. Longest term and smallest principal in the promoted corpus at the time.
 *   P-CAL-ZPB   inputs byte-identical to pass 3g's T64-ZP-B (MNT 0.28 / 55 x 21.6%), tenant id
 *               included. The ONLY shape in the committed corpus carrying a ZERO-EMI TAIL — i.e.
 *               the nearest committed neighbour of the region this pass measures.
 *
 * Neither is a parity candidate of this pass. If either fails to reproduce pass 3g cell for cell,
 * run-t83.sh refuses the run and nothing else here is believed.
 *
 * PRODUCTION SETTINGS. Buyan ratified the tenant parameters on 2026-08-18: rounding mode HALF_UP,
 * licence NBFI. Precision is not a choice — MoneyHelper.PRECISION = 19 is a compile-time constant and
 * getMathContext() returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35, 91-93]. So the
 * PRODUCTION MathContext is (19, HALF_UP). Every case in this pass runs at it.
 *
 * PostgreSQL remains the only permitted database for this program; this seam opens no database
 * connection at all and starts no Fineract server. "The oracle" here is the Fineract reference
 * implementation, never Oracle Database (a prohibited product).
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearCustomStrategyType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlan;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDisbursementPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDownPaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.lang.management.ManagementFactory;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.TimeZone;

public class CaptureT117 {

    /**
     * One capture run. Pass 3g's Case record with pass 3i's ONE structural fix carried over: the
     * two multiples-of inputs are SEPARATE components (T21 required change P1-8). Passes 3..3h
     * spent a single {@code installmentMultiplesOf} field on the 4th argument of
     * {@code new CurrencyData(...)} (which is {@code CurrencyData.inMultiplesOf},
     * Money.java:48-51) AND on the 12th argument of {@code LoanRepaymentScheduleModelData} (which
     * is {@code installmentAmountInMultiplesOf}, ProgressiveEMICalculator.java:1761-1776), so no
     * capture taken through them could attribute a difference to either.
     *
     * EVERY CASE IN THIS HARNESS PASSES **NULL** FOR BOTH, which is what makes the calibration
     * against pass 3g valid: pass 3g emitted both keys from one null field, this harness emits them
     * from two null fields, and the emitted JSON is therefore identical.
     */
    record Case(String id, String purpose, LocalDate startDate, LocalDate disbursementDate, BigDecimal principal,
            int noRepayments, BigDecimal annualRate, int precision, RoundingMode mode, String currencyCode,
            int currencyDigits, DaysInMonthType dim, DaysInYearType diy, DaysInYearCustomStrategyType diyCustom,
            BigDecimal downPaymentPct, Integer currencyMultiplesOf, Integer installmentMultiplesOf,
            Integer fixedLength,
            boolean interestRecognitionOnDisbursementDate, boolean allowPartialPeriodInterestCalculation,
            boolean allowFullTermForTranche, String tenantId, Integer tenantRoundingMode) {
    }

    static final LocalDate D_2024_01_01 = LocalDate.of(2024, 1, 1);

    /** C-00's inputs exactly, varied only by the fields a caller overrides. */
    static Case tenantCase(String id, String purpose, BigDecimal principal, int noRepayments, BigDecimal rate,
            int precision, Integer installmentMultiplesOf, boolean allowFullTermForTranche, String currencyCode,
            String tenantId, Integer tenantRoundingMode) {
        return new Case(id, purpose, D_2024_01_01, D_2024_01_01, principal, noRepayments, rate, precision,
                RoundingMode.HALF_UP, currencyCode, 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, installmentMultiplesOf, null, false, true, allowFullTermForTranche, tenantId,
                tenantRoundingMode);
    }

    /** Production settings: tenant rounding HALF_UP(4), so the ambient context is (19, HALF_UP). */
    static Case prod(String id, String purpose, BigDecimal principal, int noRepayments, BigDecimal rate,
            int precision, Integer installmentMultiplesOf, boolean allowFullTermForTranche, String currencyCode,
            String tenantId) {
        return tenantCase(id, purpose, principal, noRepayments, rate, precision, installmentMultiplesOf,
                allowFullTermForTranche, currencyCode, tenantId, 4);
    }

    /**
     * Production settings with an EXPLICIT schedule-start and disbursement date, which may differ.
     * Every other field is C-00's, exactly as {@link #prod} leaves them; only the two dates move.
     * This is the ONLY structural addition pass 3e makes to pass 3d's harness.
     */
    static Case prodDates(String id, String purpose, LocalDate startDate, LocalDate disbursementDate,
            BigDecimal principal, int noRepayments, BigDecimal rate, String tenantId) {
        return new Case(id, purpose, startDate, disbursementDate, principal, noRepayments, rate, 19,
                RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, null, false, true, false, tenantId, 4);
    }

    public static void main(String[] args) throws Exception {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATIONS — reproduce values ALREADY OBSERVED in the committed corpus ------
        // Inputs byte-identical to pass 3g's T64-ZP-A and T64-ZP-B, TENANT ID INCLUDED, so the whole
        // observed block of each must equal the committed entry of the same shape in
        // .softhouse/capture/out/capture-prod3g-raw.json. Both are ALREADY-PROMOTED parity vectors
        // at the rounding floor at dp 2 — the nearest committed neighbours of the region this pass
        // measures. If either differs by one cell, run-t83.sh refuses the run.
        cases.add(prodDates("P-CAL-ZPA", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-A, an already-promoted parity vector at the rounding floor; must reproduce it digit for digit; NOT a parity vector and NOT part of the sweep",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 56, new BigDecimal("21.6"), "cap_t64_zp_a"));

        cases.add(prodDates("P-CAL-ZPB", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-B, the ONLY shape in the committed corpus carrying a zero-EMI tail; must reproduce it digit for digit; NOT a parity vector and NOT part of the sweep",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 55, new BigDecimal("21.6"), "cap_t64_zp_b"));

        // ---- T84 SECOND PROBE ----
        cases.add(prodDates("T117-NC-R600p0-N398-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 398, new BigDecimal("600.0"), "t117_nc_r600p0_n398_b1"));
        cases.add(prodDates("T117-BS-R600p0-N121-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 121, new BigDecimal("600.0"), "t117_bs_r600p0_n121_b3"));
        cases.add(prodDates("T117-NC-R600p0-N331-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 331, new BigDecimal("600.0"), "t117_nc_r600p0_n331_b1"));
        cases.add(prodDates("T117-BS-R600p0-N104-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 104, new BigDecimal("600.0"), "t117_bs_r600p0_n104_b3"));
        cases.add(prodDates("T117-BS-R600p0-N500-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 500, new BigDecimal("600.0"), "t117_bs_r600p0_n500_b3"));
        cases.add(prodDates("T117-NL-R600p0-N930-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 930, new BigDecimal("600.0"), "t117_nl_r600p0_n930_b1"));
        cases.add(prodDates("T117-BS-R600p0-N121-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 121, new BigDecimal("600.0"), "t117_bs_r600p0_n121_b5"));
        cases.add(prodDates("T117-NL-R600p0-N730-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 730, new BigDecimal("600.0"), "t117_nl_r600p0_n730_b1"));
        cases.add(prodDates("T117-NT-R600p0-N997-B1", "T117 family-B extent probe (NT) — contiguous n sweep 995..999", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 997, new BigDecimal("600.0"), "t117_nt_r600p0_n997_b1"));
        cases.add(prodDates("T117-NL-R600p0-N920-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 920, new BigDecimal("600.0"), "t117_nl_r600p0_n920_b1"));
        cases.add(prodDates("T117-NC-R600p0-N357-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 357, new BigDecimal("600.0"), "t117_nc_r600p0_n357_b1"));
        cases.add(prodDates("T117-BS-R600p0-N150-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 150, new BigDecimal("600.0"), "t117_bs_r600p0_n150_b4"));
        cases.add(prodDates("T117-BS-R600p0-N104-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 104, new BigDecimal("600.0"), "t117_bs_r600p0_n104_b4"));
        cases.add(prodDates("T117-BS-R600p0-N250-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 250, new BigDecimal("600.0"), "t117_bs_r600p0_n250_b2"));
        cases.add(prodDates("T117-NC-R600p0-N373-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 373, new BigDecimal("600.0"), "t117_nc_r600p0_n373_b1"));
        cases.add(prodDates("T117-NC-R600p0-N364-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 364, new BigDecimal("600.0"), "t117_nc_r600p0_n364_b1"));
        cases.add(prodDates("T117-NC-R600p0-N388-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 388, new BigDecimal("600.0"), "t117_nc_r600p0_n388_b1"));
        cases.add(prodDates("T117-NC-R600p0-N383-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 383, new BigDecimal("600.0"), "t117_nc_r600p0_n383_b1"));
        cases.add(prodDates("T117-NL-R600p0-N470-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 470, new BigDecimal("600.0"), "t117_nl_r600p0_n470_b1"));
        cases.add(prodDates("T117-NL-R600p0-N980-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 980, new BigDecimal("600.0"), "t117_nl_r600p0_n980_b1"));
        cases.add(prodDates("T117-NL-R600p0-N520-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 520, new BigDecimal("600.0"), "t117_nl_r600p0_n520_b1"));
        cases.add(prodDates("T117-NL-R600p0-N840-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 840, new BigDecimal("600.0"), "t117_nl_r600p0_n840_b1"));
        cases.add(prodDates("T117-NL-R600p0-N950-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 950, new BigDecimal("600.0"), "t117_nl_r600p0_n950_b1"));
        cases.add(prodDates("T117-NL-R600p0-N600-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 600, new BigDecimal("600.0"), "t117_nl_r600p0_n600_b1"));
        cases.add(prodDates("T117-NC-R600p0-N332-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 332, new BigDecimal("600.0"), "t117_nc_r600p0_n332_b1"));
        cases.add(prodDates("T117-NC-R600p0-N370-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 370, new BigDecimal("600.0"), "t117_nc_r600p0_n370_b1"));
        cases.add(prodDates("T117-NC-R600p0-N392-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 392, new BigDecimal("600.0"), "t117_nc_r600p0_n392_b1"));
        cases.add(prodDates("T117-NC-R600p0-N330-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 330, new BigDecimal("600.0"), "t117_nc_r600p0_n330_b1"));
        cases.add(prodDates("T117-BS-R600p0-N104-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 104, new BigDecimal("600.0"), "t117_bs_r600p0_n104_b5"));
        cases.add(prodDates("T117-NL-R600p0-N480-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 480, new BigDecimal("600.0"), "t117_nl_r600p0_n480_b1"));
        cases.add(prodDates("T117-NL-R600p0-N420-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 420, new BigDecimal("600.0"), "t117_nl_r600p0_n420_b1"));
        cases.add(prodDates("T117-NL-R600p0-N500-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 500, new BigDecimal("600.0"), "t117_nl_r600p0_n500_b1"));
        cases.add(prodDates("T117-NC-R600p0-N338-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 338, new BigDecimal("600.0"), "t117_nc_r600p0_n338_b1"));
        cases.add(prodDates("T117-BS-R600p0-N250-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 250, new BigDecimal("600.0"), "t117_bs_r600p0_n250_b5"));
        cases.add(prodDates("T117-NC-R600p0-N353-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 353, new BigDecimal("600.0"), "t117_nc_r600p0_n353_b1"));
        cases.add(prodDates("T117-BS-R600p0-N300-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 300, new BigDecimal("600.0"), "t117_bs_r600p0_n300_b2"));
        cases.add(prodDates("T117-NC-R600p0-N340-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 340, new BigDecimal("600.0"), "t117_nc_r600p0_n340_b1"));
        cases.add(prodDates("T117-NC-R600p0-N390-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 390, new BigDecimal("600.0"), "t117_nc_r600p0_n390_b1"));
        cases.add(prodDates("T117-NL-R600p0-N580-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 580, new BigDecimal("600.0"), "t117_nl_r600p0_n580_b1"));
        cases.add(prodDates("T117-NC-R600p0-N400-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 400, new BigDecimal("600.0"), "t117_nc_r600p0_n400_b1"));
        cases.add(prodDates("T117-CTRL-R600p0-N103-B1", "T117 family-B extent probe (CTRL) — T84 measured CLEAN at this shape; re-asked under a new tenant id", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 103, new BigDecimal("600.0"), "t117_ctrl_r600p0_n103_b1"));
        cases.add(prodDates("T117-NC-R600p0-N302-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 302, new BigDecimal("600.0"), "t117_nc_r600p0_n302_b1"));
        cases.add(prodDates("T117-NC-R600p0-N326-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 326, new BigDecimal("600.0"), "t117_nc_r600p0_n326_b1"));
        cases.add(prodDates("T117-NC-R600p0-N307-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 307, new BigDecimal("600.0"), "t117_nc_r600p0_n307_b1"));
        cases.add(prodDates("T117-NC-R600p0-N377-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 377, new BigDecimal("600.0"), "t117_nc_r600p0_n377_b1"));
        cases.add(prodDates("T117-NL-R600p0-N850-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 850, new BigDecimal("600.0"), "t117_nl_r600p0_n850_b1"));
        cases.add(prodDates("T117-NC-R600p0-N320-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 320, new BigDecimal("600.0"), "t117_nc_r600p0_n320_b1"));
        cases.add(prodDates("T117-NC-R600p0-N309-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 309, new BigDecimal("600.0"), "t117_nc_r600p0_n309_b1"));
        cases.add(prodDates("T117-NC-R600p0-N336-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 336, new BigDecimal("600.0"), "t117_nc_r600p0_n336_b1"));
        cases.add(prodDates("T117-NC-R600p0-N378-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 378, new BigDecimal("600.0"), "t117_nc_r600p0_n378_b1"));
        cases.add(prodDates("T117-NT-R600p0-N998-B1", "T117 family-B extent probe (NT) — contiguous n sweep 995..999", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 998, new BigDecimal("600.0"), "t117_nt_r600p0_n998_b1"));
        cases.add(prodDates("T117-NC-R600p0-N349-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 349, new BigDecimal("600.0"), "t117_nc_r600p0_n349_b1"));
        cases.add(prodDates("T117-NC-R600p0-N300-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 300, new BigDecimal("600.0"), "t117_nc_r600p0_n300_b1"));
        cases.add(prodDates("T117-NC-R600p0-N354-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 354, new BigDecimal("600.0"), "t117_nc_r600p0_n354_b1"));
        cases.add(prodDates("T117-NL-R600p0-N880-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 880, new BigDecimal("600.0"), "t117_nl_r600p0_n880_b1"));
        cases.add(prodDates("T117-NC-R600p0-N342-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 342, new BigDecimal("600.0"), "t117_nc_r600p0_n342_b1"));
        cases.add(prodDates("T117-NC-R600p0-N361-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 361, new BigDecimal("600.0"), "t117_nc_r600p0_n361_b1"));
        cases.add(prodDates("T117-NL-R600p0-N540-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 540, new BigDecimal("600.0"), "t117_nl_r600p0_n540_b1"));
        cases.add(prodDates("T117-NC-R600p0-N371-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 371, new BigDecimal("600.0"), "t117_nc_r600p0_n371_b1"));
        cases.add(prodDates("T117-NC-R600p0-N333-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 333, new BigDecimal("600.0"), "t117_nc_r600p0_n333_b1"));
        cases.add(prodDates("T117-BS-R600p0-N300-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 300, new BigDecimal("600.0"), "t117_bs_r600p0_n300_b4"));
        cases.add(prodDates("T117-NC-R600p0-N384-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 384, new BigDecimal("600.0"), "t117_nc_r600p0_n384_b1"));
        cases.add(prodDates("T117-NC-R600p0-N376-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 376, new BigDecimal("600.0"), "t117_nc_r600p0_n376_b1"));
        cases.add(prodDates("T117-NC-R600p0-N323-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 323, new BigDecimal("600.0"), "t117_nc_r600p0_n323_b1"));
        cases.add(prodDates("T117-NL-R600p0-N720-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 720, new BigDecimal("600.0"), "t117_nl_r600p0_n720_b1"));
        cases.add(prodDates("T117-NC-R600p0-N379-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 379, new BigDecimal("600.0"), "t117_nc_r600p0_n379_b1"));
        cases.add(prodDates("T117-NC-R600p0-N352-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 352, new BigDecimal("600.0"), "t117_nc_r600p0_n352_b1"));
        cases.add(prodDates("T117-NC-R600p0-N301-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 301, new BigDecimal("600.0"), "t117_nc_r600p0_n301_b1"));
        cases.add(prodDates("T117-BS-R600p0-N250-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 250, new BigDecimal("600.0"), "t117_bs_r600p0_n250_b4"));
        cases.add(prodDates("T117-NL-R600p0-N900-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 900, new BigDecimal("600.0"), "t117_nl_r600p0_n900_b1"));
        cases.add(prodDates("T117-NL-R600p0-N960-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 960, new BigDecimal("600.0"), "t117_nl_r600p0_n960_b1"));
        cases.add(prodDates("T117-NL-R600p0-N770-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 770, new BigDecimal("600.0"), "t117_nl_r600p0_n770_b1"));
        cases.add(prodDates("T117-BS-R600p0-N108-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 108, new BigDecimal("600.0"), "t117_bs_r600p0_n108_b3"));
        cases.add(prodDates("T117-NC-R600p0-N389-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 389, new BigDecimal("600.0"), "t117_nc_r600p0_n389_b1"));
        cases.add(prodDates("T117-NC-R600p0-N319-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 319, new BigDecimal("600.0"), "t117_nc_r600p0_n319_b1"));
        cases.add(prodDates("T117-NT-R600p0-N999-B1", "T117 family-B extent probe (NT) — contiguous n sweep 995..999", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 999, new BigDecimal("600.0"), "t117_nt_r600p0_n999_b1"));
        cases.add(prodDates("T117-NL-R600p0-N910-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 910, new BigDecimal("600.0"), "t117_nl_r600p0_n910_b1"));
        cases.add(prodDates("T117-NC-R600p0-N314-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 314, new BigDecimal("600.0"), "t117_nc_r600p0_n314_b1"));
        cases.add(prodDates("T117-NT-R600p0-N996-B1", "T117 family-B extent probe (NT) — contiguous n sweep 995..999", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 996, new BigDecimal("600.0"), "t117_nt_r600p0_n996_b1"));
        cases.add(prodDates("T117-NL-R600p0-N610-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 610, new BigDecimal("600.0"), "t117_nl_r600p0_n610_b1"));
        cases.add(prodDates("T117-NC-R600p0-N316-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 316, new BigDecimal("600.0"), "t117_nc_r600p0_n316_b1"));
        cases.add(prodDates("T117-NL-R600p0-N760-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 760, new BigDecimal("600.0"), "t117_nl_r600p0_n760_b1"));
        cases.add(prodDates("T117-NL-R600p0-N510-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 510, new BigDecimal("600.0"), "t117_nl_r600p0_n510_b1"));
        cases.add(prodDates("T117-NL-R600p0-N790-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 790, new BigDecimal("600.0"), "t117_nl_r600p0_n790_b1"));
        cases.add(prodDates("T117-NC-R600p0-N391-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 391, new BigDecimal("600.0"), "t117_nc_r600p0_n391_b1"));
        cases.add(prodDates("T117-NC-R600p0-N306-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 306, new BigDecimal("600.0"), "t117_nc_r600p0_n306_b1"));
        cases.add(prodDates("T117-NC-R600p0-N368-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 368, new BigDecimal("600.0"), "t117_nc_r600p0_n368_b1"));
        cases.add(prodDates("T117-NL-R600p0-N680-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 680, new BigDecimal("600.0"), "t117_nl_r600p0_n680_b1"));
        cases.add(prodDates("T117-NC-R600p0-N385-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 385, new BigDecimal("600.0"), "t117_nc_r600p0_n385_b1"));
        cases.add(prodDates("T117-NC-R600p0-N310-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 310, new BigDecimal("600.0"), "t117_nc_r600p0_n310_b1"));
        cases.add(prodDates("T117-NC-R600p0-N393-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 393, new BigDecimal("600.0"), "t117_nc_r600p0_n393_b1"));
        cases.add(prodDates("T117-NC-R600p0-N346-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 346, new BigDecimal("600.0"), "t117_nc_r600p0_n346_b1"));
        cases.add(prodDates("T117-BS-R600p0-N500-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 500, new BigDecimal("600.0"), "t117_bs_r600p0_n500_b4"));
        cases.add(prodDates("T117-BS-R600p0-N121-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 121, new BigDecimal("600.0"), "t117_bs_r600p0_n121_b4"));
        cases.add(prodDates("T117-NL-R600p0-N780-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 780, new BigDecimal("600.0"), "t117_nl_r600p0_n780_b1"));
        cases.add(prodDates("T117-NC-R600p0-N322-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 322, new BigDecimal("600.0"), "t117_nc_r600p0_n322_b1"));
        cases.add(prodDates("T117-CTRL-R600p0-N250-B1", "T117 family-B extent probe (CTRL) — T100 measured FAMILY B at this shape, the largest n ever asked at it; re-asked", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 250, new BigDecimal("600.0"), "t117_ctrl_r600p0_n250_b1"));
        cases.add(prodDates("T117-BS-R600p0-N150-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 150, new BigDecimal("600.0"), "t117_bs_r600p0_n150_b3"));
        cases.add(prodDates("T117-NL-R600p0-N990-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 990, new BigDecimal("600.0"), "t117_nl_r600p0_n990_b1"));
        cases.add(prodDates("T117-NC-R600p0-N358-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 358, new BigDecimal("600.0"), "t117_nc_r600p0_n358_b1"));
        cases.add(prodDates("T117-BS-R600p0-N300-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 300, new BigDecimal("600.0"), "t117_bs_r600p0_n300_b3"));
        cases.add(prodDates("T117-NL-R600p0-N690-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 690, new BigDecimal("600.0"), "t117_nl_r600p0_n690_b1"));
        cases.add(prodDates("T117-NL-R600p0-N660-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 660, new BigDecimal("600.0"), "t117_nl_r600p0_n660_b1"));
        cases.add(prodDates("T117-NL-R600p0-N830-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 830, new BigDecimal("600.0"), "t117_nl_r600p0_n830_b1"));
        cases.add(prodDates("T117-NC-R600p0-N339-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 339, new BigDecimal("600.0"), "t117_nc_r600p0_n339_b1"));
        cases.add(prodDates("T117-NC-R600p0-N347-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 347, new BigDecimal("600.0"), "t117_nc_r600p0_n347_b1"));
        cases.add(prodDates("T117-NC-R600p0-N356-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 356, new BigDecimal("600.0"), "t117_nc_r600p0_n356_b1"));
        cases.add(prodDates("T117-NL-R600p0-N640-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 640, new BigDecimal("600.0"), "t117_nl_r600p0_n640_b1"));
        cases.add(prodDates("T117-NC-R600p0-N337-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 337, new BigDecimal("600.0"), "t117_nc_r600p0_n337_b1"));
        cases.add(prodDates("T117-NC-R600p0-N363-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 363, new BigDecimal("600.0"), "t117_nc_r600p0_n363_b1"));
        cases.add(prodDates("T117-NL-R600p0-N860-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 860, new BigDecimal("600.0"), "t117_nl_r600p0_n860_b1"));
        cases.add(prodDates("T117-BS-R600p0-N150-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 150, new BigDecimal("600.0"), "t117_bs_r600p0_n150_b5"));
        cases.add(prodDates("T117-NC-R600p0-N334-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 334, new BigDecimal("600.0"), "t117_nc_r600p0_n334_b1"));
        cases.add(prodDates("T117-NL-R600p0-N570-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 570, new BigDecimal("600.0"), "t117_nl_r600p0_n570_b1"));
        cases.add(prodDates("T117-NL-R600p0-N450-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 450, new BigDecimal("600.0"), "t117_nl_r600p0_n450_b1"));
        cases.add(prodDates("T117-NC-R600p0-N341-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 341, new BigDecimal("600.0"), "t117_nc_r600p0_n341_b1"));
        cases.add(prodDates("T117-NL-R600p0-N550-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 550, new BigDecimal("600.0"), "t117_nl_r600p0_n550_b1"));
        cases.add(prodDates("T117-NC-R600p0-N372-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 372, new BigDecimal("600.0"), "t117_nc_r600p0_n372_b1"));
        cases.add(prodDates("T117-NL-R600p0-N410-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 410, new BigDecimal("600.0"), "t117_nl_r600p0_n410_b1"));
        cases.add(prodDates("T117-NC-R600p0-N394-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 394, new BigDecimal("600.0"), "t117_nc_r600p0_n394_b1"));
        cases.add(prodDates("T117-BS-R600p0-N1000-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 1000, new BigDecimal("600.0"), "t117_bs_r600p0_n1000_b5"));
        cases.add(prodDates("T117-NC-R600p0-N321-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 321, new BigDecimal("600.0"), "t117_nc_r600p0_n321_b1"));
        cases.add(prodDates("T117-BS-R600p0-N121-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 121, new BigDecimal("600.0"), "t117_bs_r600p0_n121_b2"));
        cases.add(prodDates("T117-NC-R600p0-N395-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 395, new BigDecimal("600.0"), "t117_nc_r600p0_n395_b1"));
        cases.add(prodDates("T117-NC-R600p0-N355-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 355, new BigDecimal("600.0"), "t117_nc_r600p0_n355_b1"));
        cases.add(prodDates("T117-BS-R600p0-N150-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 150, new BigDecimal("600.0"), "t117_bs_r600p0_n150_b2"));
        cases.add(prodDates("T117-NC-R600p0-N328-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 328, new BigDecimal("600.0"), "t117_nc_r600p0_n328_b1"));
        cases.add(prodDates("T117-NC-R600p0-N348-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 348, new BigDecimal("600.0"), "t117_nc_r600p0_n348_b1"));
        cases.add(prodDates("T117-NL-R600p0-N820-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 820, new BigDecimal("600.0"), "t117_nl_r600p0_n820_b1"));
        cases.add(prodDates("T117-NL-R600p0-N490-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 490, new BigDecimal("600.0"), "t117_nl_r600p0_n490_b1"));
        cases.add(prodDates("T117-NL-R600p0-N670-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 670, new BigDecimal("600.0"), "t117_nl_r600p0_n670_b1"));
        cases.add(prodDates("T117-BS-R600p0-N500-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 500, new BigDecimal("600.0"), "t117_bs_r600p0_n500_b2"));
        cases.add(prodDates("T117-NC-R600p0-N359-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 359, new BigDecimal("600.0"), "t117_nc_r600p0_n359_b1"));
        cases.add(prodDates("T117-NC-R600p0-N350-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 350, new BigDecimal("600.0"), "t117_nc_r600p0_n350_b1"));
        cases.add(prodDates("T117-NC-R600p0-N360-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 360, new BigDecimal("600.0"), "t117_nc_r600p0_n360_b1"));
        cases.add(prodDates("T117-NC-R600p0-N386-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 386, new BigDecimal("600.0"), "t117_nc_r600p0_n386_b1"));
        cases.add(prodDates("T117-NL-R600p0-N650-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 650, new BigDecimal("600.0"), "t117_nl_r600p0_n650_b1"));
        cases.add(prodDates("T117-NL-R600p0-N870-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 870, new BigDecimal("600.0"), "t117_nl_r600p0_n870_b1"));
        cases.add(prodDates("T117-BS-R600p0-N104-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 104, new BigDecimal("600.0"), "t117_bs_r600p0_n104_b2"));
        cases.add(prodDates("T117-BS-R600p0-N300-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 300, new BigDecimal("600.0"), "t117_bs_r600p0_n300_b5"));
        cases.add(prodDates("T117-NC-R600p0-N329-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 329, new BigDecimal("600.0"), "t117_nc_r600p0_n329_b1"));
        cases.add(prodDates("T117-NC-R600p0-N305-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 305, new BigDecimal("600.0"), "t117_nc_r600p0_n305_b1"));
        cases.add(prodDates("T117-NL-R600p0-N710-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 710, new BigDecimal("600.0"), "t117_nl_r600p0_n710_b1"));
        cases.add(prodDates("T117-NC-R600p0-N362-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 362, new BigDecimal("600.0"), "t117_nc_r600p0_n362_b1"));
        cases.add(prodDates("T117-NC-R600p0-N303-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 303, new BigDecimal("600.0"), "t117_nc_r600p0_n303_b1"));
        cases.add(prodDates("T117-NC-R600p0-N311-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 311, new BigDecimal("600.0"), "t117_nc_r600p0_n311_b1"));
        cases.add(prodDates("T117-NC-R600p0-N366-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 366, new BigDecimal("600.0"), "t117_nc_r600p0_n366_b1"));
        cases.add(prodDates("T117-NL-R600p0-N620-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 620, new BigDecimal("600.0"), "t117_nl_r600p0_n620_b1"));
        cases.add(prodDates("T117-NC-R600p0-N399-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 399, new BigDecimal("600.0"), "t117_nc_r600p0_n399_b1"));
        cases.add(prodDates("T117-NC-R600p0-N397-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 397, new BigDecimal("600.0"), "t117_nc_r600p0_n397_b1"));
        cases.add(prodDates("T117-NC-R600p0-N308-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 308, new BigDecimal("600.0"), "t117_nc_r600p0_n308_b1"));
        cases.add(prodDates("T117-NL-R600p0-N740-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 740, new BigDecimal("600.0"), "t117_nl_r600p0_n740_b1"));
        cases.add(prodDates("T117-NL-R600p0-N430-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 430, new BigDecimal("600.0"), "t117_nl_r600p0_n430_b1"));
        cases.add(prodDates("T117-NC-R600p0-N344-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 344, new BigDecimal("600.0"), "t117_nc_r600p0_n344_b1"));
        cases.add(prodDates("T117-NL-R600p0-N700-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 700, new BigDecimal("600.0"), "t117_nl_r600p0_n700_b1"));
        cases.add(prodDates("T117-NL-R600p0-N1000-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 1000, new BigDecimal("600.0"), "t117_nl_r600p0_n1000_b1"));
        cases.add(prodDates("T117-BS-R600p0-N250-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 250, new BigDecimal("600.0"), "t117_bs_r600p0_n250_b3"));
        cases.add(prodDates("T117-NL-R600p0-N800-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 800, new BigDecimal("600.0"), "t117_nl_r600p0_n800_b1"));
        cases.add(prodDates("T117-NC-R600p0-N375-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 375, new BigDecimal("600.0"), "t117_nc_r600p0_n375_b1"));
        cases.add(prodDates("T117-NC-R600p0-N351-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 351, new BigDecimal("600.0"), "t117_nc_r600p0_n351_b1"));
        cases.add(prodDates("T117-BS-R600p0-N1000-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 1000, new BigDecimal("600.0"), "t117_bs_r600p0_n1000_b4"));
        cases.add(prodDates("T117-NC-R600p0-N318-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 318, new BigDecimal("600.0"), "t117_nc_r600p0_n318_b1"));
        cases.add(prodDates("T117-NC-R600p0-N313-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 313, new BigDecimal("600.0"), "t117_nc_r600p0_n313_b1"));
        cases.add(prodDates("T117-NT-R600p0-N995-B1", "T117 family-B extent probe (NT) — contiguous n sweep 995..999", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 995, new BigDecimal("600.0"), "t117_nt_r600p0_n995_b1"));
        cases.add(prodDates("T117-NC-R600p0-N380-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 380, new BigDecimal("600.0"), "t117_nc_r600p0_n380_b1"));
        cases.add(prodDates("T117-NC-R600p0-N304-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 304, new BigDecimal("600.0"), "t117_nc_r600p0_n304_b1"));
        cases.add(prodDates("T117-BS-R600p0-N108-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 108, new BigDecimal("600.0"), "t117_bs_r600p0_n108_b5"));
        cases.add(prodDates("T117-NC-R600p0-N312-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 312, new BigDecimal("600.0"), "t117_nc_r600p0_n312_b1"));
        cases.add(prodDates("T117-NC-R600p0-N315-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 315, new BigDecimal("600.0"), "t117_nc_r600p0_n315_b1"));
        cases.add(prodDates("T117-NC-R600p0-N324-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 324, new BigDecimal("600.0"), "t117_nc_r600p0_n324_b1"));
        cases.add(prodDates("T117-NC-R600p0-N396-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 396, new BigDecimal("600.0"), "t117_nc_r600p0_n396_b1"));
        cases.add(prodDates("T117-BS-R600p0-N1000-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 1000, new BigDecimal("600.0"), "t117_bs_r600p0_n1000_b2"));
        cases.add(prodDates("T117-NL-R600p0-N970-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 970, new BigDecimal("600.0"), "t117_nl_r600p0_n970_b1"));
        cases.add(prodDates("T117-NL-R600p0-N750-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 750, new BigDecimal("600.0"), "t117_nl_r600p0_n750_b1"));
        cases.add(prodDates("T117-NL-R600p0-N560-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 560, new BigDecimal("600.0"), "t117_nl_r600p0_n560_b1"));
        cases.add(prodDates("T117-NC-R600p0-N335-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 335, new BigDecimal("600.0"), "t117_nc_r600p0_n335_b1"));
        cases.add(prodDates("T117-NL-R600p0-N890-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 890, new BigDecimal("600.0"), "t117_nl_r600p0_n890_b1"));
        cases.add(prodDates("T117-NC-R600p0-N381-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 381, new BigDecimal("600.0"), "t117_nc_r600p0_n381_b1"));
        cases.add(prodDates("T117-NL-R600p0-N940-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 940, new BigDecimal("600.0"), "t117_nl_r600p0_n940_b1"));
        cases.add(prodDates("T117-NL-R600p0-N590-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 590, new BigDecimal("600.0"), "t117_nl_r600p0_n590_b1"));
        cases.add(prodDates("T117-NC-R600p0-N327-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 327, new BigDecimal("600.0"), "t117_nc_r600p0_n327_b1"));
        cases.add(prodDates("T117-NL-R600p0-N460-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 460, new BigDecimal("600.0"), "t117_nl_r600p0_n460_b1"));
        cases.add(prodDates("T117-NC-R600p0-N387-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 387, new BigDecimal("600.0"), "t117_nc_r600p0_n387_b1"));
        cases.add(prodDates("T117-NL-R600p0-N630-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 630, new BigDecimal("600.0"), "t117_nl_r600p0_n630_b1"));
        cases.add(prodDates("T117-NC-R600p0-N325-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 325, new BigDecimal("600.0"), "t117_nc_r600p0_n325_b1"));
        cases.add(prodDates("T117-NC-R600p0-N343-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 343, new BigDecimal("600.0"), "t117_nc_r600p0_n343_b1"));
        cases.add(prodDates("T117-NC-R600p0-N382-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 382, new BigDecimal("600.0"), "t117_nc_r600p0_n382_b1"));
        cases.add(prodDates("T117-BS-R600p0-N108-B4", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 108, new BigDecimal("600.0"), "t117_bs_r600p0_n108_b4"));
        cases.add(prodDates("T117-NL-R600p0-N440-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 440, new BigDecimal("600.0"), "t117_nl_r600p0_n440_b1"));
        cases.add(prodDates("T117-NC-R600p0-N367-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 367, new BigDecimal("600.0"), "t117_nc_r600p0_n367_b1"));
        cases.add(prodDates("T117-BS-R600p0-N1000-B3", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 1000, new BigDecimal("600.0"), "t117_bs_r600p0_n1000_b3"));
        cases.add(prodDates("T117-NC-R600p0-N345-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 345, new BigDecimal("600.0"), "t117_nc_r600p0_n345_b1"));
        cases.add(prodDates("T117-BS-R600p0-N108-B2", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 108, new BigDecimal("600.0"), "t117_bs_r600p0_n108_b2"));
        cases.add(prodDates("T117-NC-R600p0-N365-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 365, new BigDecimal("600.0"), "t117_nc_r600p0_n365_b1"));
        cases.add(prodDates("T117-NC-R600p0-N374-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 374, new BigDecimal("600.0"), "t117_nc_r600p0_n374_b1"));
        cases.add(prodDates("T117-NL-R600p0-N810-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 810, new BigDecimal("600.0"), "t117_nl_r600p0_n810_b1"));
        cases.add(prodDates("T117-BS-R600p0-N500-B5", "T117 family-B extent probe (BS) — principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 500, new BigDecimal("600.0"), "t117_bs_r600p0_n500_b5"));
        cases.add(prodDates("T117-NC-R600p0-N369-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 369, new BigDecimal("600.0"), "t117_nc_r600p0_n369_b1"));
        cases.add(prodDates("T117-NL-R600p0-N530-B1", "T117 family-B extent probe (NL) — ladder n 410..1000 step 10", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 530, new BigDecimal("600.0"), "t117_nl_r600p0_n530_b1"));
        cases.add(prodDates("T117-NC-R600p0-N317-B1", "T117 family-B extent probe (NC) — contiguous n sweep 300..400", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 317, new BigDecimal("600.0"), "t117_nc_r600p0_n317_b1"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"t83\",\n");
        sb.append("  \"harness\": \"CaptureT117.java\",\n");
        sb.append("  \"extends\": \"Capture3g.java / capture-prod3g-raw.json — same rig, same attestation, same emitted columns, same emission rules, with pass 3i's CurrencyData.inMultiplesOf / installmentAmountInMultiplesOf field split carried over (both null on every case here, so both keys emit exactly as pass 3g emitted them). NEW CASE LIST: two rig calibrations byte-identical to pass 3g T64-ZP-A and T64-ZP-B, then a CONTIGUOUS PRINCIPAL SWEEP in minor units over four annual rates x eight repayment counts, taken for gate G-8 (task T83) to measure the exact boundary of the region where the reference oracle emits a graded-domain schedule whose outstanding-balance column does not reach zero. Every sweep cell is emitted, clean or not; this harness classifies nothing.\",\n");
        sb.append("  \"moneyHelperPrecision\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append(attestation());
        sb.append("  \"captures\": [\n");
        for (int i = 0; i < cases.size(); i++) {
            sb.append(run(cases.get(i)));
            if (i < cases.size() - 1) {
                sb.append(",");
            }
            sb.append("\n");
        }
        sb.append("  ]\n}\n");
        System.out.println(sb);
    }

    // ---------------------------------------------------------------------------------------
    // ATTESTATION — T21 P0-2. Everything outside "runnerSupplied" is read inside this JVM, in this
    // container, during this run. Everything inside "runnerSupplied" is an echo of an environment
    // variable the runner script set; it is labelled as an echo and is NOT a measurement.
    // ---------------------------------------------------------------------------------------
    static String attestation() throws Exception {
        StringBuilder a = new StringBuilder();
        a.append("  \"attestation\": {\n");
        a.append("    \"capturePath\": \"Path A — embeddable progressive-loan schedule-generator seam, in-process. No Fineract server is started and no database connection is opened.\",\n");
        a.append("    \"capturedAtUtc\": \"").append(Instant.now().toString()).append("\",\n");

        // --- the oracle's own identity, from the jar the classpath was built out of ---
        Properties git = new Properties();
        try (InputStream in = CaptureT117.class.getResourceAsStream("/git.properties")) {
            if (in != null) {
                git.load(in);
            }
        }
        String jarPath = System.getenv("ATTEST_JAR_PATH") == null ? "/app/fineract-provider.jar"
                : System.getenv("ATTEST_JAR_PATH");
        File jar = new File(jarPath);
        a.append("    \"fineract\": {\n");
        a.append("      \"gitPropertiesSource\": \"BOOT-INF/classes/git.properties inside ").append(esc(jarPath)).append("\",\n");
        a.append("      \"gitCommitId\": ").append(q(git.getProperty("git.commit.id"))).append(",\n");
        a.append("      \"gitCommitIdDescribe\": ").append(q(git.getProperty("git.commit.id.describe"))).append(",\n");
        a.append("      \"gitCommitTime\": ").append(q(git.getProperty("git.commit.time"))).append(",\n");
        a.append("      \"gitBranch\": ").append(q(git.getProperty("git.branch"))).append(",\n");
        a.append("      \"gitDirty\": ").append(q(git.getProperty("git.dirty"))).append(",\n");
        a.append("      \"gitBuildVersion\": ").append(q(git.getProperty("git.build.version"))).append(",\n");
        a.append("      \"providerJarPath\": ").append(q(jarPath)).append(",\n");
        a.append("      \"providerJarSizeBytes\": ").append(jar.isFile() ? String.valueOf(jar.length()) : "null").append(",\n");
        a.append("      \"providerJarSha256\": ").append(q(jar.isFile() ? sha256File(jar.toPath()) : null)).append("\n");
        a.append("    },\n");

        // --- JVM identity and flags ---
        a.append("    \"jvm\": {\n");
        a.append("      \"javaVersion\": ").append(q(System.getProperty("java.version"))).append(",\n");
        a.append("      \"javaRuntimeVersion\": ").append(q(System.getProperty("java.runtime.version"))).append(",\n");
        a.append("      \"javaVmName\": ").append(q(System.getProperty("java.vm.name"))).append(",\n");
        a.append("      \"javaVmVersion\": ").append(q(System.getProperty("java.vm.version"))).append(",\n");
        a.append("      \"javaVendor\": ").append(q(System.getProperty("java.vendor"))).append(",\n");
        a.append("      \"javaHome\": ").append(q(System.getProperty("java.home"))).append(",\n");
        a.append("      \"osName\": ").append(q(System.getProperty("os.name"))).append(",\n");
        a.append("      \"osVersion\": ").append(q(System.getProperty("os.version"))).append(",\n");
        a.append("      \"osArch\": ").append(q(System.getProperty("os.arch"))).append(",\n");
        a.append("      \"fileEncoding\": ").append(q(System.getProperty("file.encoding"))).append(",\n");
        a.append("      \"defaultLocale\": ").append(q(java.util.Locale.getDefault().toString())).append(",\n");
        a.append("      \"defaultTimeZone\": ").append(q(TimeZone.getDefault().getID())).append(",\n");
        a.append("      \"userTimezoneProperty\": ").append(q(System.getProperty("user.timezone"))).append(",\n");
        List<String> flags = ManagementFactory.getRuntimeMXBean().getInputArguments();
        a.append("      \"inputArguments\": [");
        for (int i = 0; i < flags.size(); i++) {
            a.append(i == 0 ? "" : ", ").append(q(flags.get(i)));
        }
        a.append("],\n");
        a.append("      \"inputArgumentCount\": ").append(flags.size()).append("\n");
        a.append("    },\n");

        // --- the rounding seam, as it actually is in this JVM ---
        // Probed under a tenant of its own so no capture tenant is disturbed.
        String probeTenant = "attest_probe";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, probeTenant, probeTenant, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(probeTenant, 4);
        MathContext probeMc = MoneyHelper.getMathContext();
        RoundingMode probeRm = MoneyHelper.getRoundingMode();
        a.append("    \"moneyHelper\": {\n");
        a.append("      \"precisionCompileTimeConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        a.append("      \"probeTenantId\": ").append(q(probeTenant)).append(",\n");
        a.append("      \"probeTenantRoundingModeValueRequested\": 4,\n");
        a.append("      \"effectiveMathContextPrecision\": ").append(probeMc.getPrecision()).append(",\n");
        a.append("      \"effectiveMathContextRoundingMode\": ").append(q(probeMc.getRoundingMode().name())).append(",\n");
        a.append("      \"effectiveMathContextRoundingModeOrdinal\": ").append(probeMc.getRoundingMode().ordinal()).append(",\n");
        a.append("      \"effectiveRoundingMode\": ").append(q(probeRm.name())).append(",\n");
        a.append("      \"effectiveRoundingModeOrdinal\": ").append(probeRm.ordinal()).append(",\n");
        a.append("      \"effectiveMathContextToString\": ").append(q(probeMc.toString())).append(",\n");
        a.append("      \"ratifiedProductionSetting\": \"(19, HALF_UP) — RoundingMode.HALF_UP ordinal 4\",\n");
        a.append("      \"matchesRatifiedProductionSetting\": ")
                .append(probeMc.getPrecision() == 19 && probeRm == RoundingMode.HALF_UP).append("\n");
        a.append("    },\n");
        ThreadLocalContextUtil.reset();

        // --- what was compiled, and what it was compiled against ---
        String srcList = System.getenv("ATTEST_SOURCES") == null
                ? "/cap/src/CaptureT117.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
                : System.getenv("ATTEST_SOURCES");
        a.append("    \"sources\": [");
        String[] srcs = srcList.split(":");
        for (int i = 0; i < srcs.length; i++) {
            Path p = Paths.get(srcs[i]);
            a.append(i == 0 ? "\n" : ",\n");
            a.append("      {\"file\": ").append(q(srcs[i])).append(", \"sha256\": ")
                    .append(q(Files.isRegularFile(p) ? sha256File(p) : null)).append("}");
        }
        a.append("\n    ],\n");

        String[] cp = System.getProperty("java.class.path").split(File.pathSeparator);
        List<String> lines = new ArrayList<>();
        for (String entry : cp) {
            Path p = Paths.get(entry);
            String d = Files.isRegularFile(p) ? sha256File(p) : "DIRECTORY_OR_MISSING";
            lines.add(d + "  " + entry);
        }
        List<String> sorted = new ArrayList<>(lines);
        java.util.Collections.sort(sorted);
        String aggregate = sha256Bytes(String.join("\n", sorted).getBytes(StandardCharsets.UTF_8));
        String cpOut = System.getenv("ATTEST_CLASSPATH_OUT") == null
                ? "/cap/out/capture-prod3g-classpath-sha256.txt" : System.getenv("ATTEST_CLASSPATH_OUT");
        try {
            Files.write(Paths.get(cpOut), (String.join("\n", sorted) + "\n").getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            // recorded, never silently swallowed
            cpOut = "WRITE_FAILED: " + e.getClass().getName() + ": " + e.getMessage();
        }
        a.append("    \"classpath\": {\n");
        a.append("      \"entryCount\": ").append(cp.length).append(",\n");
        a.append("      \"aggregateSha256\": ").append(q(aggregate)).append(",\n");
        a.append("      \"aggregateSha256Definition\": \"sha256 over the newline-joined, lexicographically sorted list of '<sha256>  <classpath entry>' lines\",\n");
        a.append("      \"perEntryDigestFile\": ").append(q(cpOut)).append("\n");
        a.append("    },\n");

        // --- echoes, explicitly not measurements ---
        a.append("    \"runnerSupplied\": {\n");
        a.append("      \"NOTE\": \"ECHOED from the runner's environment. NOT measured inside the container — the container cannot read the docker image id or the host checkout. The runner script asserts these independently and fails the run on mismatch.\",\n");
        a.append("      \"dockerImageRef\": ").append(q(System.getenv("ATTEST_IMAGE_REF"))).append(",\n");
        a.append("      \"dockerImageId\": ").append(q(System.getenv("ATTEST_IMAGE_ID"))).append(",\n");
        a.append("      \"pinnedFineractCommit\": ").append(q(System.getenv("ATTEST_PINNED_COMMIT"))).append(",\n");
        a.append("      \"pinnedFineractPath\": ").append(q(System.getenv("ATTEST_PINNED_PATH"))).append(",\n");
        a.append("      \"runId\": ").append(q(System.getenv("ATTEST_RUN_ID"))).append("\n");
        a.append("    }\n");
        a.append("  },\n");
        return a.toString();
    }

    static String sha256File(Path p) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = Files.newInputStream(p)) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) {
                md.update(buf, 0, n);
            }
        }
        return hex(md.digest());
    }

    static String sha256Bytes(byte[] b) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(b));
    }

    static String hex(byte[] b) {
        StringBuilder s = new StringBuilder();
        for (byte x : b) {
            s.append(String.format("%02x", x));
        }
        return s.toString();
    }

    static String esc(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ").replace("\r", " ").replace("\t", " ");
    }

    /** JSON string literal, or the bare token null. */
    static String q(String s) {
        return s == null ? "null" : "\"" + esc(s) + "\"";
    }

    /** Every BigDecimal leaves this harness through here — T21 P1-9, toPlainString(). */
    static String pl(BigDecimal d) {
        return d == null ? "null" : d.toPlainString();
    }

    static String run(final Case c) {
        // Establish (or deliberately withhold) the tenant context for THIS case only.
        String ambientMathContext;
        String ambientPrecision;
        String ambientRoundingMode;
        String ambientRoundingModeOrdinal;
        if (c.tenantId() == null) {
            ThreadLocalContextUtil.reset();
            ambientMathContext = "null (no tenant context)";
            ambientPrecision = "null";
            ambientRoundingMode = "null";
            ambientRoundingModeOrdinal = "null";
        } else {
            ThreadLocalContextUtil.setTenant(
                    new FineractPlatformTenant(1L, c.tenantId(), c.tenantId(), "Asia/Ulaanbaatar", null));
            MoneyHelper.initializeTenantRoundingMode(c.tenantId(), c.tenantRoundingMode());
            try {
                MathContext ambient = MoneyHelper.getMathContext();
                ambientMathContext = String.valueOf(ambient);
                ambientPrecision = String.valueOf(ambient.getPrecision());
                ambientRoundingMode = "\"" + ambient.getRoundingMode().name() + "\"";
                ambientRoundingModeOrdinal = String.valueOf(ambient.getRoundingMode().ordinal());
            } catch (RuntimeException e) {
                ambientMathContext = e.getClass().getName() + ": " + e.getMessage();
                ambientPrecision = "null";
                ambientRoundingMode = "null";
                ambientRoundingModeOrdinal = "null";
            }
        }

        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.currencyMultiplesOf(), c.currencyCode(), c.currencyCode());

        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), 1, "MONTHS", c.annualRate(),
                BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0, c.dim(), c.diy(), c.downPaymentPct(),
                c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(), c.diyCustom(),
                InterestMethod.DECLINING_BALANCE, c.allowPartialPeriodInterestCalculation(),
                c.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(c.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(pl(c.principal())).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentFrequency\": 1,\n");
        b.append("        \"repaymentFrequencyType\": \"MONTHS\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(pl(c.annualRate())).append("\",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append("        \"mathContextRoundingModeOrdinal\": ").append(c.mode().ordinal()).append(",\n");
        b.append("        \"tenantId\": ").append(c.tenantId() == null ? "null" : "\"" + c.tenantId() + "\"").append(",\n");
        b.append("        \"tenantRoundingModeValue\": ").append(c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambientMathContext).append("\",\n");
        b.append("        \"ambientMoneyHelperPrecision\": ").append(ambientPrecision).append(",\n");
        b.append("        \"ambientMoneyHelperRoundingMode\": ").append(ambientRoundingMode).append(",\n");
        b.append("        \"ambientMoneyHelperRoundingModeOrdinal\": ").append(ambientRoundingModeOrdinal).append(",\n");
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.currencyMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategy\": ").append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"downPaymentEnabled\": ").append(BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0).append(",\n");
        b.append("        \"downPaymentPercentage\": \"").append(pl(c.downPaymentPct())).append("\",\n");
        b.append("        \"installmentAmountInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"fixedLength\": ").append(c.fixedLength()).append(",\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ").append(c.interestRecognitionOnDisbursementDate()).append(",\n");
        b.append("        \"interestMethod\": \"DECLINING_BALANCE\",\n");
        b.append("        \"allowPartialPeriodInterestCalculation\": ").append(c.allowPartialPeriodInterestCalculation()).append(",\n");
        b.append("        \"allowFullTermForTranche\": ").append(c.allowFullTermForTranche()).append("\n");
        b.append("      },\n");

        final LoanSchedulePlan plan;
        try {
            plan = generator.generate(mc, config);
        } catch (RuntimeException e) {
            // T21 P1-9: keep the frames. A discarded stack trace is a lost finding.
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\"", "'").replace("\n", " ")).append("\",\n");
            b.append("      \"errorStackTop\": [");
            StackTraceElement[] st = e.getStackTrace();
            int n = Math.min(st.length, 25);
            for (int i = 0; i < n; i++) {
                b.append(i == 0 ? "" : ", ").append(q(st[i].toString()));
            }
            b.append("],\n");
            Throwable cause = e.getCause();
            b.append("      \"errorCause\": ").append(q(cause == null ? null : cause.getClass().getName() + ": " + cause.getMessage())).append("\n");
            b.append("    }");
            e.printStackTrace(System.err);
            return b.toString();
        }

        b.append("      \"observed\": {\n");
        b.append("        \"loanTermInDays\": ").append(plan.getLoanTermInDays()).append(",\n");
        b.append("        \"totalDisbursedAmount\": \"").append(pl(plan.getTotalDisbursedAmount())).append("\",\n");
        b.append("        \"totalPrincipalAmount\": \"").append(pl(plan.getTotalPrincipalAmount())).append("\",\n");
        b.append("        \"totalInterestAmount\": \"").append(pl(plan.getTotalInterestAmount())).append("\",\n");
        b.append("        \"totalFeeAmount\": \"").append(pl(plan.getTotalFeeAmount())).append("\",\n");
        b.append("        \"totalPenaltyAmount\": \"").append(pl(plan.getTotalPenaltyAmount())).append("\",\n");
        b.append("        \"totalRepaymentAmount\": \"").append(pl(plan.getTotalRepaymentAmount())).append("\",\n");
        b.append("        \"totalOutstandingAmount\": \"").append(pl(plan.getTotalOutstandingAmount())).append("\",\n");
        b.append("        \"periods\": [\n");

        final List<String> rows = new ArrayList<>();
        for (LoanSchedulePlanPeriod period : plan.getPeriods()) {
            if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                rows.add("          {\"type\": \"DISBURSEMENT\", \"periodFromDate\": \"" + dp.periodFromDate()
                        + "\", \"dueDate\": \"" + dp.periodDueDate()
                        + "\", \"principal\": \"" + pl(dp.getPrincipalAmount())
                        + "\", \"balance\": \"" + pl(dp.getOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"periodFromDate\": \"" + dpp.periodFromDate()
                        + "\", \"dueDate\": \"" + dpp.periodDueDate() + "\", \"balance\": \""
                        + pl(dpp.getOutstandingLoanBalance()) + "\", \"principal\": \"" + pl(dpp.getPrincipalAmount())
                        + "\", \"total\": \"" + pl(dpp.getTotalDueAmount()) + "\", \"totalOutstandingBalance\": \""
                        + pl(dpp.getTotalOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"periodFromDate\": \"" + rp.periodFromDate()
                        + "\", \"dueDate\": \"" + rp.periodDueDate() + "\", \"balance\": \""
                        + pl(rp.getOutstandingLoanBalance()) + "\", \"principal\": \"" + pl(rp.getPrincipalAmount())
                        + "\", \"interest\": \"" + pl(rp.getInterestAmount())
                        + "\", \"feeAmount\": \"" + pl(rp.getFeeAmount())
                        + "\", \"penaltyAmount\": \"" + pl(rp.getPenaltyAmount())
                        + "\", \"total\": \"" + pl(rp.getTotalDueAmount()) + "\", \"totalOutstandingBalance\": \""
                        + pl(rp.getTotalOutstandingLoanBalance()) + "\"}");
            } else {
                rows.add("          {\"type\": \"UNKNOWN:" + period.getClass().getName() + "\"}");
            }
        }
        b.append(String.join(",\n", rows)).append("\n");
        b.append("        ]\n");
        b.append("      }\n");
        b.append("    }");
        return b.toString();
    }
}
