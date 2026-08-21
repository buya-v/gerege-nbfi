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
 * WHY THIS PASS EXISTS -- task T159, the INDEPENDENT REVIEW of T117, gate G-8. T117 reported a
 * largest unamortized residual of 501 minor units (MNT 5.01) and -- the consequential part --
 * that NO UPPER BOUND is established, because "the largest failing principal tracks the largest
 * term asked" and nothing above n = 1000 has ever been asked. That is a claim about the SHAPE OF
 * T117'S PROBE SET, and a reviewer must not take it on trust. This pass asks the region directly:
 * n > 1000 (never asked by anybody), odd principals in the 501..1001 gap T117's ladder jumped
 * over, T117's reported band boundaries at B = 1, and straight re-asks of T117's headline cell
 * and its three PARTIAL-amortization cells under fresh tenant ids.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t159-review-t117/PREDICTION-T159.md and prediction-t159.json, committed in an
 * ANCESTOR COMMIT of the one carrying this file, and the classification is done afterwards by
 * census_t159.py reading only the emitted JSON.
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

public class CaptureT159 {

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
        cases.add(prodDates("T159-R600p0-N2000-B10001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10001).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b10001"));
        cases.add(prodDates("T159-R600p0-N401-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 401, new BigDecimal("600.0"), "t159_r600p0_n401_b1"));
        cases.add(prodDates("T159-R600p0-N392-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 392, new BigDecimal("600.0"), "t159_r600p0_n392_b1"));
        cases.add(prodDates("T159-R600p0-N2000-B501", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(501).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b501"));
        cases.add(prodDates("T159-R600p0-N3000-B100001", "T159 independent re-observation of T117 (TERM) — n > 1000 at a large principal", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100001).movePointLeft(2), 3000, new BigDecimal("600.0"), "t159_r600p0_n3000_b100001"));
        cases.add(prodDates("T159-R600p0-N1200-B1", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 1200, new BigDecimal("600.0"), "t159_r600p0_n1200_b1"));
        cases.add(prodDates("T159-R600p0-N1200-B1001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1001).movePointLeft(2), 1200, new BigDecimal("600.0"), "t159_r600p0_n1200_b1001"));
        cases.add(prodDates("T159-R600p0-N2000-B1", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b1"));
        cases.add(prodDates("T159-R600p0-N400-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 400, new BigDecimal("600.0"), "t159_r600p0_n400_b1"));
        cases.add(prodDates("T159-R600p0-N1500-B1001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1001).movePointLeft(2), 1500, new BigDecimal("600.0"), "t159_r600p0_n1500_b1001"));
        cases.add(prodDates("T159-R600p0-N391-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 391, new BigDecimal("600.0"), "t159_r600p0_n391_b1"));
        cases.add(prodDates("T159-R600p0-N361-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 361, new BigDecimal("600.0"), "t159_r600p0_n361_b1"));
        cases.add(prodDates("T159-R600p0-N1200-B10001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10001).movePointLeft(2), 1200, new BigDecimal("600.0"), "t159_r600p0_n1200_b10001"));
        cases.add(prodDates("T159-R600p0-N108-B11", "T159 independent re-observation of T117 (REP) — PARTIAL-amortization cell — re-asked under a fresh tenant id", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(11).movePointLeft(2), 108, new BigDecimal("600.0"), "t159_r600p0_n108_b11"));
        cases.add(prodDates("T159-R600p0-N150-B11", "T159 independent re-observation of T117 (REP) — PARTIAL-amortization cell — re-asked under a fresh tenant id", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(11).movePointLeft(2), 150, new BigDecimal("600.0"), "t159_r600p0_n150_b11"));
        cases.add(prodDates("T159-R600p0-N3000-B1001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1001).movePointLeft(2), 3000, new BigDecimal("600.0"), "t159_r600p0_n3000_b1001"));
        cases.add(prodDates("T159-R600p0-N389-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 389, new BigDecimal("600.0"), "t159_r600p0_n389_b1"));
        cases.add(prodDates("T159-R600p0-N1500-B10001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10001).movePointLeft(2), 1500, new BigDecimal("600.0"), "t159_r600p0_n1500_b10001"));
        cases.add(prodDates("T159-R600p0-N1000-B901", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(901).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b901"));
        cases.add(prodDates("T159-R600p0-N1000-B503", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(503).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b503"));
        cases.add(prodDates("T159-R600p0-N364-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 364, new BigDecimal("600.0"), "t159_r600p0_n364_b1"));
        cases.add(prodDates("T159-R600p0-N360-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 360, new BigDecimal("600.0"), "t159_r600p0_n360_b1"));
        cases.add(prodDates("T159-R600p0-N2000-B999", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap, at a term above 1000", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(999).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b999"));
        cases.add(prodDates("T159-R600p0-N3000-B1", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 3000, new BigDecimal("600.0"), "t159_r600p0_n3000_b1"));
        cases.add(prodDates("T159-R600p0-N3000-B10001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10001).movePointLeft(2), 3000, new BigDecimal("600.0"), "t159_r600p0_n3000_b10001"));
        cases.add(prodDates("T159-R600p0-N1000-B501", "T159 independent re-observation of T117 (REP) — THE HEADLINE CELL — MNT 5.01 residual, re-asked under a fresh tenant id", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(501).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b501"));
        cases.add(prodDates("T159-R600p0-N1000-B601", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(601).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b601"));
        cases.add(prodDates("T159-R600p0-N390-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 390, new BigDecimal("600.0"), "t159_r600p0_n390_b1"));
        cases.add(prodDates("T159-R600p0-N2000-B601", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap, at a term above 1000", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(601).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b601"));
        cases.add(prodDates("T159-R600p0-N3000-B501", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(501).movePointLeft(2), 3000, new BigDecimal("600.0"), "t159_r600p0_n3000_b501"));
        cases.add(prodDates("T159-R600p0-N393-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 393, new BigDecimal("600.0"), "t159_r600p0_n393_b1"));
        cases.add(prodDates("T159-R600p0-N1000-B801", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(801).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b801"));
        cases.add(prodDates("T159-R600p0-N1000-B551", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(551).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b551"));
        cases.add(prodDates("T159-R600p0-N1500-B501", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(501).movePointLeft(2), 1500, new BigDecimal("600.0"), "t159_r600p0_n1500_b501"));
        cases.add(prodDates("T159-R600p0-N362-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 362, new BigDecimal("600.0"), "t159_r600p0_n362_b1"));
        cases.add(prodDates("T159-R600p0-N2000-B801", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap, at a term above 1000", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(801).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b801"));
        cases.add(prodDates("T159-R600p0-N1000-B999", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(999).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b999"));
        cases.add(prodDates("T159-R600p0-N363-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 363, new BigDecimal("600.0"), "t159_r600p0_n363_b1"));
        cases.add(prodDates("T159-R600p0-N1500-B1", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 1500, new BigDecimal("600.0"), "t159_r600p0_n1500_b1"));
        cases.add(prodDates("T159-R600p0-N3000-B1000001", "T159 independent re-observation of T117 (TERM) — n > 1000 at a large principal", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1000001).movePointLeft(2), 3000, new BigDecimal("600.0"), "t159_r600p0_n3000_b1000001"));
        cases.add(prodDates("T159-R600p0-N365-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 365, new BigDecimal("600.0"), "t159_r600p0_n365_b1"));
        cases.add(prodDates("T159-R600p0-N1200-B501", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(501).movePointLeft(2), 1200, new BigDecimal("600.0"), "t159_r600p0_n1200_b501"));
        cases.add(prodDates("T159-R600p0-N121-B11", "T159 independent re-observation of T117 (REP) — PARTIAL-amortization cell — re-asked under a fresh tenant id", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(11).movePointLeft(2), 121, new BigDecimal("600.0"), "t159_r600p0_n121_b11"));
        cases.add(prodDates("T159-R600p0-N1000-B751", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(751).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b751"));
        cases.add(prodDates("T159-R600p0-N1000-B701", "T159 independent re-observation of T117 (PRIN) — odd principal in the 501..1001 gap T117's ladder jumped over", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(701).movePointLeft(2), 1000, new BigDecimal("600.0"), "t159_r600p0_n1000_b701"));
        cases.add(prodDates("T159-R600p0-N399-B1", "T159 independent re-observation of T117 (BAND) — band boundary re-ask at B = 1 — is the boundary where T117 says it is?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 399, new BigDecimal("600.0"), "t159_r600p0_n399_b1"));
        cases.add(prodDates("T159-R600p0-N2000-B1001", "T159 independent re-observation of T117 (TERM) — n > 1000 — never asked before; does the failing principal keep tracking the term?", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1001).movePointLeft(2), 2000, new BigDecimal("600.0"), "t159_r600p0_n2000_b1001"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"t83\",\n");
        sb.append("  \"harness\": \"CaptureT159.java\",\n");
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
        try (InputStream in = CaptureT159.class.getResourceAsStream("/git.properties")) {
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
                ? "/cap/src/CaptureT159.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
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
        } catch (Throwable e) { // T159: Throwable, not RuntimeException - a StackOverflowError must be RECORDED, not fatal
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
            // T159: the trace is kept in errorStackTop above; it is deliberately NOT printed to
            // stderr, because run-t159.sh refuses the run on non-empty stderr and an errored cell
            // is DATA for this probe, not a rig failure. postcheck_t159.py counts and names them.
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
