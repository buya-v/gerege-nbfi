/*
 * Golden-vector capture harness, PASS 3i — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * PASS 3i IS PASS 3h's RIG WITH ONE STRUCTURAL FIX AND A NEW CASE LIST. Every precondition,
 * attestation field, `observed` column, mechanism column and emission rule of pass 3h is preserved
 * and NOT ONE check was weakened. All EIGHT of pass 3h's rig calibrations are carried over
 * unchanged, ONE more is added, and TWO runner preconditions are added.
 *
 * WHY THIS PASS EXISTS — task T74, closing T21 required change P1-8 (which is T19's required
 * change 10 unfixed for five passes).
 *
 * THE HARNESS COULD NOT TELL THE TWO MULTIPLES-OF INPUTS APART. Passes 3 through 3h all built the
 * currency as `new CurrencyData(code, code, digits, c.installmentMultiplesOf(), ...)` AND passed
 * the same `c.installmentMultiplesOf()` as the model's `installmentAmountInMultiplesOf`, AND
 * emitted both JSON keys from that one field. Two entirely different mechanisms shared one slot,
 * so no capture taken through those harnesses could attribute an observed difference to either of
 * them. Pass 3i gives them SEPARATE slots in `Case`, in the model construction and in the emitted
 * JSON, and the runner refuses a run in which the two are not demonstrably independent.
 *
 * THE TWO MECHANISMS, read out of the pinned source:
 *
 *   CHANNEL 1 — the Money constructor leak, Money.java:48-51.
 *       if (currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0
 *               && currency.getInMultiplesOf() > 0 && MathUtil.isGreaterThanZero(amountScaled)) {
 *           amountScaled = roundToMultiplesOf(amountScaled, currency.getInMultiplesOf());
 *       }
 *   It is gated on the CURRENCY's own decimal places being ZERO. It rounds to the NEAREST multiple
 *   under the TENANT's rounding mode, not under the threaded MathContext's:
 *   roundToMultiplesOf(BigDecimal, Integer) at :150-157 is
 *   existingVal.divide(m, 0, MoneyHelper.getRoundingMode()).multiply(m). It sits in the PRIVATE
 *   CONSTRUCTOR, so it fires on EVERY Money the calculation builds — principal, interest, EMI,
 *   balance — and it has NO zero-guard beyond the amountScaled > 0 test.
 *
 *   CHANNEL 2 — the installment rounding, ProgressiveEMICalculator.java:1761-1776.
 *       applyInstallmentAmountInMultiplesOf -> safeRoundingForEMI -> Money.roundToMultiplesOf
 *       (Money.java:159-170)
 *   It is gated on the SCHEDULE MODEL's installmentAmountInMultiplesOf, applies to the EQUAL
 *   MONTHLY INSTALLMENT ONLY, and carries a zero-guard that channel 1 does not have: if rounding
 *   would zero a positive EMI, the UNROUNDED EMI is kept (:1772-1774).
 *
 * WHY SEPARATING THEM MOVES MONEY. T21's auditor observed, at (19, HALF_UP) through this same
 * seam, that MNT 5,000,000 / 18 x 18.5% with currencyDecimalPlaces = 0 emits total interest
 * 763994 at CurrencyData.inMultiplesOf = null and 764100 at 100, with all eighteen periods
 * differing. Nothing in the promoted corpus grades that, and with the fields aliased no capture
 * could even say WHICH of the two inputs did it.
 *
 * THE CASE LIST. NINE RIG CALIBRATIONS (eight carried from pass 3h unchanged plus P-CAL-MNT5M,
 * whose inputs are byte-identical to pass 3b's P-MNT-5M — an already-promoted parity vector, and
 * the dp = 2 control that the whole T74-A/B family differs from in one or two fields). Then a 2x2
 * FACTORIAL over {currency.inMultiplesOf} x {installmentAmountInMultiplesOf} at
 * currencyDecimalPlaces = 0 (group A) and the same factorial at the production
 * currencyDecimalPlaces = 2 (group B); five gate-and-rule probes for channel 1 (group C:
 * multiples of 1, 0, -100, 7 and 1000); a three-case zero-guard separator (group D); and the
 * 36 x 16.8% small-principal shape T21 required change P1-11 asked for, at production precision
 * and at precision 12 alongside it (group E).
 *
 * This harness ASSERTS NOTHING AND PREDICTS NOTHING. Every value it prints is what the oracle
 * emitted. The falsifiable prediction lives in
 * .softhouse/capture/t74-multiplesof/PREDICTION.md and predicted.json and was committed BEFORE
 * this file was run.
 *
 * PRODUCTION SETTINGS. Buyan ratified the tenant parameters on 2026-08-18: rounding mode HALF_UP,
 * licence NBFI. Precision is not a choice — MoneyHelper.PRECISION = 19 is a compile-time constant
 * and getMathContext() returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35,
 * 91-93]. So the PRODUCTION MathContext is (19, HALF_UP). The group E precision-12 companions are
 * DISCRIMINATION PROBES, never parity candidates, and the runner records them as such.
 *
 * PostgreSQL remains the only permitted database for this program; this seam opens no database
 * connection at all. "The oracle" here is the Fineract reference implementation, never Oracle
 * Database (a prohibited product).
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
import org.apache.fineract.portfolio.loanaccount.domain.Loan;
import org.apache.fineract.portfolio.loanaccount.domain.ProgressiveLoanModel;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.DefaultScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.ProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.ScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.service.InterestScheduleModelRepositoryWrapper;
import org.apache.fineract.portfolio.loanproduct.calc.EMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.ProgressiveEMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.data.ProgressiveLoanInterestScheduleModel;
import org.apache.fineract.portfolio.loanproduct.calc.data.RepaymentPeriod;
import org.apache.fineract.portfolio.loanproduct.domain.ILoanConfigurationDetails;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.io.File;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.Optional;
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

public class Capture3i {

    /**
     * One capture run.
     *
     * THE ONE STRUCTURAL CHANGE PASS 3i MAKES — T21 required change P1-8 / T19 required change 10.
     * Passes 3..3h carried a SINGLE component, {@code installmentMultiplesOf}, and spent it in
     * THREE places: the 4th argument of {@code new CurrencyData(...)} (which is
     * {@code CurrencyData.inMultiplesOf}), the 12th argument of
     * {@code LoanRepaymentScheduleModelData} (which is {@code installmentAmountInMultiplesOf}),
     * and BOTH emitted JSON keys. Two unrelated mechanisms therefore shared one slot and no
     * capture could attribute a difference to either. They are now two components:
     *
     *   currencyMultiplesOf     -> CurrencyData.inMultiplesOf        -> Money.java:48-51 (channel 1)
     *   installmentMultiplesOf  -> installmentAmountInMultiplesOf    -> ProgressiveEMICalculator
     *                                                                   .java:1761-1776 (channel 2)
     *
     * Every field a pass-3b/3c/3e/3g calibration compares against keeps its old meaning and its old
     * emitted key, and all nine calibrations pass both fields as null, so the calibration
     * comparisons are unaffected by the split.
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

    /**
     * ADDED BY PASS 3i. The ONLY constructor in this harness that can set the two multiples-of
     * inputs INDEPENDENTLY, and the only one that can move the currency off two decimal places.
     * Everything else is exactly what {@link #prodDates} leaves: MNT, start and disbursement dates
     * as given, MONTHS/1, DAYS_30 / DAYS_360, DECLINING_BALANCE, no down payment, no fixed length,
     * interestRecognitionOnDisbursementDate false, allowPartialPeriodInterestCalculation true,
     * allowFullTermForTranche false, tenant rounding HALF_UP (ordinal 4).
     *
     * {@code precision} is a parameter because group E carries a precision-12 companion for every
     * production-precision case; those companions are DISCRIMINATION PROBES and the runner refuses
     * to let one be recorded as a parity candidate.
     */
    static Case mult(String id, String purpose, LocalDate startDate, LocalDate disbursementDate,
            BigDecimal principal, int noRepayments, BigDecimal rate, int currencyDigits,
            Integer currencyMultiplesOf, Integer installmentMultiplesOf, int precision, String tenantId) {
        return new Case(id, purpose, startDate, disbursementDate, principal, noRepayments, rate, precision,
                RoundingMode.HALF_UP, "MNT", currencyDigits, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, currencyMultiplesOf, installmentMultiplesOf, null, false, true, false, tenantId, 4);
    }

    public static void main(String[] args) throws Exception {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATIONS — reproduce values ALREADY OBSERVED in the committed corpus ------
        // Inputs below are byte-identical to the passes they repeat, TENANT ID INCLUDED, so the
        // whole observed block of each must equal the committed entry of the same shape. If any
        // one differs, nothing else from this run is trustworthy and run-pass3f.sh refuses it.
        cases.add(prod("P-CAL", "RIG CALIBRATION at (12, HALF_UP) — inputs identical to pass 3b P-CAL; must reproduce it digit for digit; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_p_cal"));

        cases.add(prod("P-CAL-P00", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) — inputs identical to pass 3b P-00; must reproduce it digit for digit at the precision the parity candidates run at; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, false, "usd", "cap_p_00"));

        cases.add(prod("P-CAL-EMI6", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3c P-EMI-6-1M014632; must reproduce it digit for digit; NOT a parity vector",
                new BigDecimal("1014632"), 6, new BigDecimal("7.0"), 19, null, false, "MNT", "cap_p_emi_6"));

        // ---- FOURTH CALIBRATION, ADDED BY PASS 3f ------------------------------------------------
        // Inputs byte-identical to pass 3e's P-LAT-Q0a, tenant id included. That case is ALREADY a
        // promoted parity vector, and it is the SAME QUESTION as the three candidates below in
        // every field but the principal: same lattice date, same term, same rate, same currency,
        // same MathContext. A rig that reproduces it is calibrated on exactly the arithmetic the
        // promotion rests on, not merely on something nearby.
        cases.add(prodDates("P-CAL-LATQ0a", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3e P-LAT-Q0a, the on-lattice control the three candidates differ from ONLY in principal; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 6, new BigDecimal("21.6"), "cap_lat_q0a"));

        // ---- CALIBRATIONS ADDED BY PASS 3h -------------------------------------------------
        // Inputs byte-identical to the committed captures they repeat, tenant id included. They are
        // chosen for the AXES this pass extends: P-MNT-50M is the longest term in the promoted
        // corpus (n=36) and P-DRIFT-F is the smallest principal in it (MNT 1.00). The candidates
        // below run longer than the first and smaller than the second, so the rig is calibrated at
        // the far end of both axes rather than merely somewhere nearby.
        cases.add(prod("P-CAL-MNT50M", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3b P-MNT-50M, the LONGEST TERM in the promoted corpus; must reproduce it digit for digit; NOT a parity vector",
                new BigDecimal("50000000"), 36, new BigDecimal("16.8"), 19, null, false, "MNT", "cap_p_mnt50m"));

        cases.add(prodDates("P-CAL-DRIFTF", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3e P-DRIFT-F, the SMALLEST PRINCIPAL in the promoted corpus; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), new BigDecimal("100"), 6, new BigDecimal("21.6"), "cap_drift_f"));

        // ---- PARITY CANDIDATES — four MNT loans at the ROUNDING FLOOR ----------------------
        // Strictly inside the graded domain: single disbursement ON the schedule start date,
        // RepaymentEvery 1 MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, no
        // installment rounding, MNT 2 decimals, (19, HALF_UP). Only principal, term and rate move.
        //
        // ---- TWO MORE CALIBRATIONS, ADDED BY PASS 3h ------------------------------------------
        // Inputs byte-identical to pass 3g's T64-ZP-A and T64-ZP-B, tenant id included. BOTH are
        // ALREADY promoted parity vectors. ZP-B is the ONLY shape in the entire committed corpus
        // whose schedule carries a ZERO-EMI TAIL (installments 16..55 all zero), which is exactly
        // the precondition half that T63 could not test, so this pass calibrates ON the shape it
        // interrogates rather than merely near it.
        cases.add(prodDates("P-CAL-ZPA", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-A, an already-promoted parity vector at the rounding floor; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 56, new BigDecimal("21.6"), "cap_t64_zp_a"));

        cases.add(prodDates("P-CAL-ZPB", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-B, an already-promoted parity vector and the ONLY committed shape with a ZERO-EMI TAIL; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 55, new BigDecimal("21.6"), "cap_t64_zp_b"));

        // ---- NINTH CALIBRATION, ADDED BY PASS 3i ------------------------------------------------
        // Inputs byte-identical to pass 3b's P-MNT-5M, tenant id included. That case's observation
        // is ALREADY a promoted parity vector, and it is the EXACT CONTROL the whole T74-A/B family
        // is built around: same principal, same term, same rate, same dates, same currency code,
        // same MathContext — differing only in currencyDecimalPlaces and in the two multiples-of
        // inputs. A rig that reproduces it is calibrated on the very arithmetic the group A and B
        // comparisons are read against.
        cases.add(prod("P-CAL-MNT5M", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3b P-MNT-5M, the dp=2 / no-multiples-of control that groups A and B differ from in one or two fields; must reproduce it digit for digit; NOT a parity vector",
                new BigDecimal("5000000"), 18, new BigDecimal("18.5"), 19, null, false, "MNT", "cap_p_mnt5m"));

        // =====================================================================================
        // GROUP A — the 2x2 FACTORIAL at currencyDecimalPlaces = 0.
        //
        // This is the T21 P1-8 deliverable. All four cases are MNT 5,000,000 / 18 x 18.5%, start =
        // disbursement = 2024-01-01, at the production (19, HALF_UP), and differ ONLY in the two
        // multiples-of inputs — which, from this pass onward, are two different inputs.
        //
        //            currency.inMultiplesOf   installmentAmountInMultiplesOf
        //   A0             null                        null
        //   A1             100                         null
        //   A2             null                        100
        //   A3             100                         100
        //
        // A factorial rather than a pair because a pair can only show THAT something moved; the
        // factorial says WHICH input moved it, and the two "one factor at a time" arms plus the
        // interaction arm are what make that attribution complete rather than inferred.
        // =====================================================================================
        cases.add(mult("T74-A0-DP0-NONE", "FACTORIAL A(0,0): MNT 5,000,000 / 18 x 18.5% at currencyDecimalPlaces 0, BOTH multiples-of inputs null — the baseline the other three arms are read against",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, null, null, 19, "cap_t74_a0"));

        cases.add(mult("T74-A1-DP0-CUR100", "FACTORIAL A(1,0): the same loan with CurrencyData.inMultiplesOf = 100 and installmentAmountInMultiplesOf null — the ONLY multiples-of channel the Path A seam can reach (Money.java:48-51)",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, 100, null, 19, "cap_t74_a1"));

        cases.add(mult("T74-A2-DP0-INST100", "FACTORIAL A(0,1): the same loan with installmentAmountInMultiplesOf = 100 and CurrencyData.inMultiplesOf null — the channel LoanApplicationTerms.assembleFrom (:579-607) has no Builder setter for",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, null, 100, 19, "cap_t74_a2"));

        cases.add(mult("T74-A3-DP0-BOTH100", "FACTORIAL A(1,1): the same loan with BOTH multiples-of inputs = 100 — the interaction arm; up to pass 3h this was the only arm the harness could express at all",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, 100, 100, 19, "cap_t74_a3"));

        // =====================================================================================
        // GROUP B — the same factorial at the PRODUCTION currencyDecimalPlaces = 2.
        //
        // MNT is ISO 4217 numeric 496, minor unit 2, so group B is the arrangement an actual
        // Gerege deployment runs. The (null, null) arm of this factorial is not repeated here: it
        // IS the calibration P-CAL-MNT5M above, whose observation is already a promoted vector.
        // =====================================================================================
        cases.add(mult("T74-B1-DP2-CUR100", "FACTORIAL B(1,0): P-MNT-5M's loan at the PRODUCTION currencyDecimalPlaces 2 with CurrencyData.inMultiplesOf = 100",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                2, 100, null, 19, "cap_t74_b1"));

        cases.add(mult("T74-B2-DP2-INST100", "FACTORIAL B(0,1): P-MNT-5M's loan at currencyDecimalPlaces 2 with installmentAmountInMultiplesOf = 100",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                2, null, 100, 19, "cap_t74_b2"));

        cases.add(mult("T74-B3-DP2-BOTH100", "FACTORIAL B(1,1): P-MNT-5M's loan at currencyDecimalPlaces 2 with BOTH multiples-of inputs = 100",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                2, 100, 100, 19, "cap_t74_b3"));

        // =====================================================================================
        // GROUP C — the GATE and the RULE of channel 1, at currencyDecimalPlaces = 0.
        //
        // Money.java:48-51 gates on three properties of the CURRENCY and one of the amount:
        //   inMultiplesOf != null, decimalPlaces == 0, inMultiplesOf > 0, amountScaled > 0.
        // C1/C2/C3 walk the third of those (1, 0, -100). C4 and C5 vary the modulus itself, one
        // of them deliberately NOT a power of ten, so a port that implemented "round to multiples"
        // by shifting a decimal scale is separated from one that divides.
        // =====================================================================================
        cases.add(mult("T74-C1-DP0-CUR1", "CHANNEL-1 RULE: CurrencyData.inMultiplesOf = 1 at currencyDecimalPlaces 0 — the guard PASSES (1 > 0) and the rounding is applied, so this probes whether rounding to multiples of one is arithmetically inert at scale 0",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, 1, null, 19, "cap_t74_c1"));

        cases.add(mult("T74-C2-DP0-CUR0", "CHANNEL-1 GATE: CurrencyData.inMultiplesOf = 0 at currencyDecimalPlaces 0 — the third conjunct of Money.java:48 (inMultiplesOf > 0) is FALSE, so the leak must not fire",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, 0, null, 19, "cap_t74_c2"));

        cases.add(mult("T74-C3-DP0-CURNEG", "CHANNEL-1 GATE: CurrencyData.inMultiplesOf = -100 at currencyDecimalPlaces 0 — the same conjunct on the negative side; roundToMultiplesOf's own > 0 test (Money.java:153) is a second guard behind it",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, -100, null, 19, "cap_t74_c3"));

        cases.add(mult("T74-C4-DP0-CUR7", "CHANNEL-1 RULE: CurrencyData.inMultiplesOf = 7 at currencyDecimalPlaces 0 — a modulus that is NOT a power of ten, so decimal-scale shifting and integer division are separated",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, 7, null, 19, "cap_t74_c4"));

        cases.add(mult("T74-C5-DP0-CUR1000", "CHANNEL-1 RULE: CurrencyData.inMultiplesOf = 1000 at currencyDecimalPlaces 0 — ten times the A1 modulus on the same loan, so the size of the movement is read against the size of the modulus",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("5000000"), 18, new BigDecimal("18.5"),
                0, 1000, null, 19, "cap_t74_c5"));

        // =====================================================================================
        // GROUP D — the ZERO-GUARD, which is the sharpest structural difference between the two
        // channels.
        //
        // Channel 2 wraps its rounding in safeRoundingForEMI (ProgressiveEMICalculator.java:
        // 1770-1776): "if (roundedEMI.isZero() && unRoundedEMI.isGreaterThanZero()) return
        // unRoundedEMI". Channel 1 has no such fallback anywhere in Money.java:40-53.
        //
        // MNT 1,000 / 6 x 21.6% at currencyDecimalPlaces 0 is a shape whose level installment is
        // strictly between 0 and half of 1000, while the principal itself is exactly one multiple
        // of 1000. So the two channels make OPPOSITE predictions about the installment, and the
        // principal is left alone either way — which is what isolates the guard rather than
        // confounding it with a quantized principal.
        // =====================================================================================
        cases.add(mult("T74-D0-DP0-SMALL-NONE", "ZERO-GUARD BASELINE: MNT 1,000 / 6 x 21.6% at currencyDecimalPlaces 0, both multiples-of inputs null",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1000"), 6, new BigDecimal("21.6"),
                0, null, null, 19, "cap_t74_d0"));

        cases.add(mult("T74-D1-DP0-SMALL-CUR1000", "ZERO-GUARD, CHANNEL 1: the same loan with CurrencyData.inMultiplesOf = 1000 — channel 1 has no safeRoundingForEMI fallback, so this is where the two channels' rules are told apart",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1000"), 6, new BigDecimal("21.6"),
                0, 1000, null, 19, "cap_t74_d1"));

        cases.add(mult("T74-D2-DP0-SMALL-INST1000", "ZERO-GUARD, CHANNEL 2: the same loan with installmentAmountInMultiplesOf = 1000 — the arm on which safeRoundingForEMI would fire if the Path A seam delivered the field at all",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1000"), 6, new BigDecimal("21.6"),
                0, null, 1000, 19, "cap_t74_d2"));

        // =====================================================================================
        // GROUP E — the 36 x 16.8% SMALL-PRINCIPAL SHAPE, T21 required change P1-11.
        //
        // T21's auditor refuted the pass-3 report's "precision is load-bearing only above a size
        // threshold" by putting this shape to the oracle: it DIVERGES between MathContext
        // precision 12 and 19 at principals as small as MNT 4.00, while the same shape at
        // 50,000,000 and the 6 x 7.0% shape at 87,654,321 are identical. Sensitivity is a
        // rounding-boundary property of the (principal, n, rate) triple, not a magnitude property.
        //
        // Every case here is MNT at the production currencyDecimalPlaces 2, both multiples-of
        // inputs null, start = disbursement = 2024-01-01 — squarely inside DEC-1's graded domain.
        // Each production-precision case is paired with a precision-12 COMPANION carrying the same
        // request. The companions are DISCRIMINATION PROBES and never parity candidates; the
        // runner records that classification and PIN.json's never-promotable list carries their
        // ids. They exist so the margin between a port at the ratified 19 significant digits and a
        // port that quietly runs at 12 is MEASURED from the oracle rather than modelled.
        // =====================================================================================
        cases.add(mult("T74-E-P4", "PRECISION-BOUNDARY SHAPE: MNT 4.00 / 36 x 16.8% at PRODUCTION (19, HALF_UP) — the smallest principal T21 found on which precision 12 and 19 disagree",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("4"), 36, new BigDecimal("16.8"),
                2, null, null, 19, "cap_t74_e_p4"));

        cases.add(mult("T74-E-P4-p12", "DISCRIMINATION PROBE, NOT A PARITY CANDIDATE: T74-E-P4's request at MathContext precision 12",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("4"), 36, new BigDecimal("16.8"),
                2, null, null, 12, "cap_t74_e_p4_p12"));

        cases.add(mult("T74-E-P59", "PRECISION-BOUNDARY SHAPE: MNT 59.00 / 36 x 16.8% at PRODUCTION (19, HALF_UP)",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("59"), 36, new BigDecimal("16.8"),
                2, null, null, 19, "cap_t74_e_p59"));

        cases.add(mult("T74-E-P59-p12", "DISCRIMINATION PROBE, NOT A PARITY CANDIDATE: T74-E-P59's request at MathContext precision 12",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("59"), 36, new BigDecimal("16.8"),
                2, null, null, 12, "cap_t74_e_p59_p12"));

        cases.add(mult("T74-E-P72", "PRECISION-BOUNDARY SHAPE: MNT 72.00 / 36 x 16.8% at PRODUCTION (19, HALF_UP)",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("72"), 36, new BigDecimal("16.8"),
                2, null, null, 19, "cap_t74_e_p72"));

        cases.add(mult("T74-E-P72-p12", "DISCRIMINATION PROBE, NOT A PARITY CANDIDATE: T74-E-P72's request at MathContext precision 12",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("72"), 36, new BigDecimal("16.8"),
                2, null, null, 12, "cap_t74_e_p72_p12"));

        cases.add(mult("T74-E-P340", "PRECISION-BOUNDARY SHAPE: MNT 340.00 / 36 x 16.8% at PRODUCTION (19, HALF_UP)",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("340"), 36, new BigDecimal("16.8"),
                2, null, null, 19, "cap_t74_e_p340"));

        cases.add(mult("T74-E-P340-p12", "DISCRIMINATION PROBE, NOT A PARITY CANDIDATE: T74-E-P340's request at MathContext precision 12",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("340"), 36, new BigDecimal("16.8"),
                2, null, null, 12, "cap_t74_e_p340_p12"));

        cases.add(mult("T74-E-P426", "PRECISION-BOUNDARY SHAPE: MNT 426.00 / 36 x 16.8% at PRODUCTION (19, HALF_UP) — T21 recorded the widest small-principal precision gap on this one",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("426"), 36, new BigDecimal("16.8"),
                2, null, null, 19, "cap_t74_e_p426"));

        cases.add(mult("T74-E-P426-p12", "DISCRIMINATION PROBE, NOT A PARITY CANDIDATE: T74-E-P426's request at MathContext precision 12",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("426"), 36, new BigDecimal("16.8"),
                2, null, null, 12, "cap_t74_e_p426_p12"));

        cases.add(mult("T74-E-P6940", "PRECISION-BOUNDARY SHAPE: MNT 6,940.00 / 36 x 16.8% at PRODUCTION (19, HALF_UP)",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("6940"), 36, new BigDecimal("16.8"),
                2, null, null, 19, "cap_t74_e_p6940"));

        cases.add(mult("T74-E-P6940-p12", "DISCRIMINATION PROBE, NOT A PARITY CANDIDATE: T74-E-P6940's request at MathContext precision 12",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("6940"), 36, new BigDecimal("16.8"),
                2, null, null, 12, "cap_t74_e_p6940_p12"));
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 120, new BigDecimal("21.6"), "cap_t66_floor_long"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"3i\",\n");
        sb.append("  \"harness\": \"Capture3i.java\",\n");
        sb.append("  \"extends\": \"Capture3h.java / capture-prod3h-raw.json — same rig, same columns, same attestation, same mechanism columns, same emission rules, ALL EIGHT of pass 3h's calibrations carried over unchanged plus P-CAL-MNT5M, whose inputs are byte-identical to pass 3b's P-MNT-5M (an already-promoted parity vector, and the dp=2 / no-multiples-of control that the T74-A and T74-B factorials differ from in one or two fields). Pass 3i makes ONE STRUCTURAL FIX the earlier passes did not have — T21 required change P1-8, which is T19 required change 10 unfixed since pass 2: CurrencyData.inMultiplesOf and installmentAmountInMultiplesOf now have SEPARATE components in Case, SEPARATE arguments in the model construction and SEPARATE emitted JSON keys. Up to pass 3h one field fed all three, so no capture could attribute an observed difference to either input. The runner FAILS THE RUN if the emitted pair is not demonstrably independent (new precondition 16) and if any case's MathContext precision is not exactly the one its id is registered for (new precondition 17, an EXHAUSTIVE per-id table rather than a defaulted lookup).\",\n");
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
        try (InputStream in = Capture3i.class.getResourceAsStream("/git.properties")) {
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
                ? "/cap/src/Capture3i.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
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
                ? "/cap/out/capture-prod3i-classpath-sha256.txt" : System.getenv("ATTEST_CLASSPATH_OUT");
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
        // PASS 3i: the 4th argument of CurrencyData is inMultiplesOf [CurrencyData.java:59], and it
        // now comes from its OWN component. Up to pass 3h it came from c.installmentMultiplesOf(),
        // which is what made the two inputs indistinguishable.
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
        b.append("      },\n");

        // ---- MECHANISM COLUMNS + PATH IDENTITY, added by pass 3h -----------------------------
        b.append(mechanism(mc, config, plan));

        b.append("    }");
        return b.toString();
    }

    // ---------------------------------------------------------------------------------------
    // THE MECHANISM PROBE — task T66.
    //
    // It does NOT modify the seam class and does NOT reimplement anything. It builds the
    // oracle's OWN ProgressiveLoanScheduleGenerator around the oracle's OWN
    // ProgressiveEMICalculator (which is `final`, so a subclass is impossible) placed behind a
    // java.lang.reflect.Proxy whose entire behaviour is: delegate the call unchanged, and if the
    // method was generatePeriodInterestScheduleModel, remember the returned model reference. The
    // model the generator then mutates is that same object, so after generate() returns, the
    // per-period fields below are the oracle's own final state.
    //
    // WHAT IS OBSERVED, and why each field is here:
    //   futureUnrecognizedInterest  the field the port does not have. It is written ONLY at
    //                               ProgressiveEMICalculator.java:1250 and reset to zero at :1183
    //                               on entry to calculateLastUnpaidRepaymentPeriodEMI, and on the
    //                               ordinary generate path that method is entered on the real
    //                               model exactly once (:747). Nothing after :747 resets it on the
    //                               real model — :1288's calls run on the smoothing loop's trial
    //                               copy — so this final value IS the outcome of the one decision.
    //   interestMovedUpward         written true at :1249 on every period after the target, reset
    //                               false at :1185. Same argument.
    //   unrecognizedInterest        negativeToZero(calculatedDueInterest - dueInterest)
    //                               [RepaymentPeriod.java:381-383] — the quantity
    //                               getPeriodWithUnrecognizedInterest tests (:1806-1808).
    //   calculatedDueInterest/dueInterest/emi/isFullyPaid/totalPaidAmount
    //                               the inputs to that quantity, so a reader can re-derive it.
    //
    // PATH IDENTITY. The plan the instrumented generator returns is emitted alongside the
    // pristine seam's plan, cell for cell, and the runner FAILS THE RUN if they differ. That is
    // what makes the mechanism columns evidence about the seam's computation rather than about a
    // lookalike.
    // ---------------------------------------------------------------------------------------
    static String mechanism(final MathContext mc, final LoanRepaymentScheduleModelData config,
            final LoanSchedulePlan seamPlan) {
        final StringBuilder b = new StringBuilder();
        final ProgressiveLoanInterestScheduleModel[] captured = new ProgressiveLoanInterestScheduleModel[1];
        final ScheduledDateGenerator sdg = new DefaultScheduledDateGenerator();
        final EMICalculator realCalculator = new ProgressiveEMICalculator(sdg);
        final EMICalculator spy = (EMICalculator) Proxy.newProxyInstance(EMICalculator.class.getClassLoader(),
                new Class<?>[] { EMICalculator.class }, (proxy, method, args) -> {
                    final Object result;
                    try {
                        result = method.invoke(realCalculator, args);
                    } catch (InvocationTargetException ite) {
                        throw ite.getCause();
                    }
                    if ("generatePeriodInterestScheduleModel".equals(method.getName())
                            && result instanceof ProgressiveLoanInterestScheduleModel m) {
                        captured[0] = m;
                    }
                    return result;
                });

        final LoanSchedulePlan probePlan;
        try {
            probePlan = new ProgressiveLoanScheduleGenerator(sdg, spy, new NoopModelRepositoryWrapper())
                    .generate(mc, config);
        } catch (RuntimeException e) {
            b.append("      \"mechanism\": null,\n");
            b.append("      \"mechanismError\": ").append(q(e.getClass().getName() + ": " + e.getMessage())).append(",\n");
            b.append("      \"pathIdentity\": {\"identical\": false, \"reason\": \"instrumented run threw\"}\n");
            e.printStackTrace(System.err);
            return b.toString();
        }

        b.append("      \"mechanism\": {\n");
        b.append("        \"note\": \"Read off the ProgressiveLoanInterestScheduleModel the oracle's own ProgressiveLoanScheduleGenerator built and mutated. Nothing here is computed by this harness.\",\n");
        if (captured[0] == null) {
            b.append("        \"modelCaptured\": false,\n        \"periods\": []\n      },\n");
        } else {
            b.append("        \"modelCaptured\": true,\n");
            b.append("        \"periods\": [\n");
            final List<String> mr = new ArrayList<>();
            int idx = 0;
            for (RepaymentPeriod rp : captured[0].repaymentPeriods()) {
                mr.add("          {\"idx\": " + idx
                        + ", \"fromDate\": \"" + rp.getFromDate() + "\", \"dueDate\": \"" + rp.getDueDate()
                        + "\", \"emi\": \"" + pl(rp.getEmi().getAmount())
                        + "\", \"futureUnrecognizedInterest\": \"" + pl(rp.getFutureUnrecognizedInterest().getAmount())
                        + "\", \"interestMovedUpward\": " + rp.isInterestMovedUpward()
                        + ", \"calculatedDueInterest\": \"" + pl(rp.getCalculatedDueInterest().getAmount())
                        + "\", \"dueInterest\": \"" + pl(rp.getDueInterest().getAmount())
                        + "\", \"unrecognizedInterest\": \"" + pl(rp.getUnrecognizedInterest().getAmount())
                        + "\", \"duePrincipal\": \"" + pl(rp.getDuePrincipal().getAmount())
                        + "\", \"outstandingLoanBalance\": \"" + pl(rp.getOutstandingLoanBalance().getAmount())
                        + "\", \"totalPaidAmount\": \"" + pl(rp.getTotalPaidAmount().getAmount())
                        + "\", \"isFullyPaid\": " + rp.isFullyPaid() + "}");
                idx++;
            }
            b.append(String.join(",\n", mr)).append("\n");
            b.append("        ]\n      },\n");
        }

        // PATH IDENTITY — every cell of both plans, rendered by the same code path.
        final String seamRendered = renderPlan(seamPlan);
        final String probeRendered = renderPlan(probePlan);
        b.append("      \"pathIdentity\": {\n");
        b.append("        \"identical\": ").append(seamRendered.equals(probeRendered)).append(",\n");
        b.append("        \"seamPlan\": ").append(q(seamRendered)).append(",\n");
        b.append("        \"instrumentedPlan\": ").append(q(probeRendered)).append("\n");
        b.append("      }\n");
        return b.toString();
    }

    /** One canonical string for a whole plan, used only for the path-identity comparison. */
    static String renderPlan(final LoanSchedulePlan plan) {
        final StringBuilder s = new StringBuilder();
        s.append(plan.getLoanTermInDays()).append('|').append(pl(plan.getTotalDisbursedAmount())).append('|')
                .append(pl(plan.getTotalPrincipalAmount())).append('|').append(pl(plan.getTotalInterestAmount()))
                .append('|').append(pl(plan.getTotalFeeAmount())).append('|').append(pl(plan.getTotalPenaltyAmount()))
                .append('|').append(pl(plan.getTotalRepaymentAmount())).append('|')
                .append(pl(plan.getTotalOutstandingAmount()));
        for (LoanSchedulePlanPeriod p : plan.getPeriods()) {
            if (p instanceof LoanSchedulePlanDisbursementPeriod dp) {
                s.append("//D:").append(dp.periodFromDate()).append(':').append(dp.periodDueDate()).append(':')
                        .append(pl(dp.getPrincipalAmount())).append(':').append(pl(dp.getOutstandingLoanBalance()));
            } else if (p instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                s.append("//P:").append(dpp.periodNumber()).append(':').append(dpp.periodFromDate()).append(':')
                        .append(dpp.periodDueDate()).append(':').append(pl(dpp.getPrincipalAmount())).append(':')
                        .append(pl(dpp.getOutstandingLoanBalance())).append(':').append(pl(dpp.getTotalDueAmount()))
                        .append(':').append(pl(dpp.getTotalOutstandingLoanBalance()));
            } else if (p instanceof LoanSchedulePlanRepaymentPeriod rp) {
                s.append("//R:").append(rp.periodNumber()).append(':').append(rp.periodFromDate()).append(':')
                        .append(rp.periodDueDate()).append(':').append(pl(rp.getPrincipalAmount())).append(':')
                        .append(pl(rp.getInterestAmount())).append(':').append(pl(rp.getFeeAmount())).append(':')
                        .append(pl(rp.getPenaltyAmount())).append(':').append(pl(rp.getTotalDueAmount())).append(':')
                        .append(pl(rp.getOutstandingLoanBalance())).append(':')
                        .append(pl(rp.getTotalOutstandingLoanBalance()));
            } else {
                s.append("//?:").append(p.getClass().getName());
            }
        }
        return s.toString();
    }

    /**
     * Byte-for-byte the NoopInterestScheduleModelRepositoryWrapper the pinned seam class declares
     * privately (EmbeddableProgressiveLoanScheduleGenerator.java), reproduced here only because a
     * private nested class cannot be referenced from outside its own file. The seam class itself is
     * NOT modified and its byte identity against the pinned original is still asserted by the
     * runner.
     */
    private static final class NoopModelRepositoryWrapper implements InterestScheduleModelRepositoryWrapper {

        @Override
        public Optional<ProgressiveLoanModel> findOneByLoanId(Long loanId) {
            return Optional.empty();
        }

        @Override
        public Optional<ProgressiveLoanModel> findOneByLoan(Loan loan) {
            return Optional.empty();
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> extractModel(Optional<ProgressiveLoanModel> progressiveLoanModel) {
            return Optional.empty();
        }

        @Override
        public ProgressiveLoanInterestScheduleModel writeInterestScheduleModel(Loan loan, ProgressiveLoanInterestScheduleModel model) {
            return null;
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> readProgressiveLoanInterestScheduleModel(Long loanId,
                ILoanConfigurationDetails detail, Integer installmentAmountInMultipliesOf) {
            return Optional.empty();
        }

        @Override
        public boolean hasValidModelForDate(Long loanId, LocalDate targetDate) {
            return false;
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> getSavedModel(Loan loan, LocalDate businessDate) {
            return Optional.empty();
        }

        @Override
        public Long removeByLoanId(Long loanId) {
            return 0L;
        }
    }
}
