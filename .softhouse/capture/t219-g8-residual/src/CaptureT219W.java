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
 * WHY THIS PASS EXISTS - task T116, gate G-8, option (a). T116 carries an explicit PROMOTION
 * mandate: promote a parity vector over the family-B region with a narrow, declared
 * invariant_exemptions entry. Family B (600.0 % p.a., MNT 0.01, n >= 104) is a GENUINE
 * non-amortization that the Go port reproduces cell for cell, so the FAIL it produces without an
 * exemption is purely an invariant FAIL and the exemption is decisive; family A is a CELL DIFF,
 * over which an exemption has no power, and T116 does not attempt it.
 *
 * T116 re-captures the three cells it intends to promote from the live oracle rather than
 * transcribing another task's committed bytes: n = 103 (the amortizing cell below the boundary,
 * promotable with NO exemption), n = 104 (the lowest family-B cell ever observed) and n = 108 (the
 * cell T100's exemption demo graded at 761 cells / 0 diffs).
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t116-familyb-promotion/PREDICTION.md and prediction.json, committed in an
 * ANCESTOR COMMIT of the one carrying this file, and the classification is done afterwards by
 * classify_t116.py reading only the emitted JSON.
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

public class CaptureT219W {

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

        // ---- T219 RUN 2 — RE-ASK OF THE TWO CELLS THAT THREW IN RUN 1 ----
        // Run 1 asked every cell EXACTLY ONCE. Seven were observed; two returned
        // java.lang.StackOverflowError and no schedule at all (G-8's THIRD OUTCOME):
        // T219-R600p0-N3000-B1999 and T219-R600p0-N3000-B4501.
        //
        // T177 measured that this throw is a function of JVM STATE, not of the cell's inputs, and
        // that ~50 prior seam calls on a never-throwing cell buys observation (3/3) while 1 and 10
        // do not (0/3, 0/3). This run applies exactly that recipe: 50 WARM-UP calls on the ZP-A
        // shape (21.6 % / MNT 0.28 / n = 56 — an already-promoted parity vector that has never
        // thrown), then the two cells, in run 1's relative order.
        //
        // THIS IS A SECOND ASK OF TWO CELLS AND IT IS DECLARED AS ONE. It re-asks NOTHING that was
        // observed in run 1: no money figure from run 1 is re-measured, revised or replaced here.
        // THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING.
        cases.add(prodDates("T219-WARM-00", "T177 warm-up call 1 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_00"));
        cases.add(prodDates("T219-WARM-01", "T177 warm-up call 2 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_01"));
        cases.add(prodDates("T219-WARM-02", "T177 warm-up call 3 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_02"));
        cases.add(prodDates("T219-WARM-03", "T177 warm-up call 4 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_03"));
        cases.add(prodDates("T219-WARM-04", "T177 warm-up call 5 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_04"));
        cases.add(prodDates("T219-WARM-05", "T177 warm-up call 6 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_05"));
        cases.add(prodDates("T219-WARM-06", "T177 warm-up call 7 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_06"));
        cases.add(prodDates("T219-WARM-07", "T177 warm-up call 8 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_07"));
        cases.add(prodDates("T219-WARM-08", "T177 warm-up call 9 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_08"));
        cases.add(prodDates("T219-WARM-09", "T177 warm-up call 10 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_09"));
        cases.add(prodDates("T219-WARM-10", "T177 warm-up call 11 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_10"));
        cases.add(prodDates("T219-WARM-11", "T177 warm-up call 12 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_11"));
        cases.add(prodDates("T219-WARM-12", "T177 warm-up call 13 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_12"));
        cases.add(prodDates("T219-WARM-13", "T177 warm-up call 14 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_13"));
        cases.add(prodDates("T219-WARM-14", "T177 warm-up call 15 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_14"));
        cases.add(prodDates("T219-WARM-15", "T177 warm-up call 16 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_15"));
        cases.add(prodDates("T219-WARM-16", "T177 warm-up call 17 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_16"));
        cases.add(prodDates("T219-WARM-17", "T177 warm-up call 18 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_17"));
        cases.add(prodDates("T219-WARM-18", "T177 warm-up call 19 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_18"));
        cases.add(prodDates("T219-WARM-19", "T177 warm-up call 20 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_19"));
        cases.add(prodDates("T219-WARM-20", "T177 warm-up call 21 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_20"));
        cases.add(prodDates("T219-WARM-21", "T177 warm-up call 22 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_21"));
        cases.add(prodDates("T219-WARM-22", "T177 warm-up call 23 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_22"));
        cases.add(prodDates("T219-WARM-23", "T177 warm-up call 24 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_23"));
        cases.add(prodDates("T219-WARM-24", "T177 warm-up call 25 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_24"));
        cases.add(prodDates("T219-WARM-25", "T177 warm-up call 26 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_25"));
        cases.add(prodDates("T219-WARM-26", "T177 warm-up call 27 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_26"));
        cases.add(prodDates("T219-WARM-27", "T177 warm-up call 28 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_27"));
        cases.add(prodDates("T219-WARM-28", "T177 warm-up call 29 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_28"));
        cases.add(prodDates("T219-WARM-29", "T177 warm-up call 30 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_29"));
        cases.add(prodDates("T219-WARM-30", "T177 warm-up call 31 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_30"));
        cases.add(prodDates("T219-WARM-31", "T177 warm-up call 32 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_31"));
        cases.add(prodDates("T219-WARM-32", "T177 warm-up call 33 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_32"));
        cases.add(prodDates("T219-WARM-33", "T177 warm-up call 34 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_33"));
        cases.add(prodDates("T219-WARM-34", "T177 warm-up call 35 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_34"));
        cases.add(prodDates("T219-WARM-35", "T177 warm-up call 36 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_35"));
        cases.add(prodDates("T219-WARM-36", "T177 warm-up call 37 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_36"));
        cases.add(prodDates("T219-WARM-37", "T177 warm-up call 38 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_37"));
        cases.add(prodDates("T219-WARM-38", "T177 warm-up call 39 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_38"));
        cases.add(prodDates("T219-WARM-39", "T177 warm-up call 40 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_39"));
        cases.add(prodDates("T219-WARM-40", "T177 warm-up call 41 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_40"));
        cases.add(prodDates("T219-WARM-41", "T177 warm-up call 42 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_41"));
        cases.add(prodDates("T219-WARM-42", "T177 warm-up call 43 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_42"));
        cases.add(prodDates("T219-WARM-43", "T177 warm-up call 44 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_43"));
        cases.add(prodDates("T219-WARM-44", "T177 warm-up call 45 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_44"));
        cases.add(prodDates("T219-WARM-45", "T177 warm-up call 46 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_45"));
        cases.add(prodDates("T219-WARM-46", "T177 warm-up call 47 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_46"));
        cases.add(prodDates("T219-WARM-47", "T177 warm-up call 48 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_47"));
        cases.add(prodDates("T219-WARM-48", "T177 warm-up call 49 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_48"));
        cases.add(prodDates("T219-WARM-49", "T177 warm-up call 50 of 50 on the never-throwing ZP-A shape; NOT a probe cell, NOT a parity candidate, classified by nothing.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("21.6"), "t219_warm_49"));
        cases.add(prodDates("T219-R600p0-N3000-B4501-RUN2", "T219 G-8 residual-record probe RUN 2 - 600.0 %% p.a., 4501 minor units, n = 3000. RE-ASK of a cell that threw StackOverflowError in run 1, after 50 T177 warm-up calls. This harness asserts nothing and predicts nothing; the registered prediction is in ../PREDICTION.md, committed in an ANCESTOR commit.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4501).movePointLeft(2), 3000, new BigDecimal("600.0"), "t219_run2_r600p0_n3000_b4501"));
        cases.add(prodDates("T219-R600p0-N3000-B1999-RUN2", "T219 G-8 residual-record probe RUN 2 - 600.0 %% p.a., 1999 minor units, n = 3000. RE-ASK of a cell that threw StackOverflowError in run 1, after 50 T177 warm-up calls. This harness asserts nothing and predicts nothing; the registered prediction is in ../PREDICTION.md, committed in an ANCESTOR commit.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1999).movePointLeft(2), 3000, new BigDecimal("600.0"), "t219_run2_r600p0_n3000_b1999"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"t83\",\n");
        sb.append("  \"harness\": \"CaptureT219W.java\",\n");
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
        try (InputStream in = CaptureT219W.class.getResourceAsStream("/git.properties")) {
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
                ? "/cap/src/CaptureT219W.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
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
            } catch (Throwable e) {
                // T116: Throwable, not RuntimeException. An Error raised while READING the ambient
                // MathContext would otherwise escape and kill the JVM before any JSON is printed,
                // which is the same class of hole T169 closed at the seam. See T169 follow-up 2.
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
        } catch (Throwable t) {
            // T169. Throwable, NOT RuntimeException. java.lang.StackOverflowError is an Error, so
            // the handler this replaces could not see it at all: it escaped run(), escaped main(),
            // and killed the JVM before a byte of JSON was printed. A throw is now a FIRST-CLASS
            // OUTCOME -- neither an observation nor an absence. The fatal rule, and the reason the
            // frames go to the JSON instead of to stderr, are documented in ThrewOutcome.java.
            if (ThrewOutcome.isFatal(t)) {
                ThrewOutcome.announceFatal(c.id(), t);
                throw t;
            }
            ThrewOutcome.appendThrew(b, t, 25);
            return b.toString();
        }

        b.append("      \"outcome\": \"observed\",\n");
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
