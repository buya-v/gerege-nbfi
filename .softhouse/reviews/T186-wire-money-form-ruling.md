# T186 — Money on the capture wire in major-unit decimal form: the ruling

**Task:** T186. **Branch:** `softhouse/T186-wire-money-form-ruling`.
**Raised by:** T173 as its FU-1, confirmed independently by the driver on `main`.
**Fineract pinned commit:** `426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED: `git -C /Users/buv/fineract log -1`].
**Scope:** documentation only. **No captured byte is modified by this task.**

---

## 0. The ruling in one paragraph

`CLAUDE.md`'s first non-negotiable and Fineract's REST API do **not** conflict, because they are
about different objects. The non-negotiable governs **the numbers Gerege owns** — the Go module's
own types, its adapter surface, its schema, its stored vectors. The capture wire carries **the
oracle's numbers, in the oracle's own shape**, and a capture that reshaped them would no longer be
an observation of the oracle. So: major-unit decimal on the **oracle-facing request/response wire is
ADMISSIBLE and in fact mandatory** (a); it is a **REJECTION on the Go module's own adapter/API
surface** (b); and it is a **REJECTION in a stored vector** (c), where money is already `int64`
minor units and rates are already exact rationals. **T173's guard property — byte preservation under
a binary-double round trip — is not merely the weaker defensible choice. It is the exactly correct
property**, because it is precisely the necessary and sufficient condition for the corpus to survive
the one place a genuine IEEE-754 `double` sits on Fineract's own request path
(`ChargeRequest.amount`, §2.4). **No gate is needed** — the ruling changes no DEC-1 field, type,
enum member or predicate, and DEC-1 §4.3.1 and `contract.go` already say this (§7).

---

## 1. The three categories, and the ruling on each

### (a) The oracle-facing capture wire — MAJOR-UNIT DECIMAL IS MANDATORY

**Ruling: a float-shaped major-unit money token is ADMISSIBLE here, and a minor-unit integer would
be a DEFECT.**

Fineract's `/loans?command=calculateLoanSchedule` reads `principal` as a **major-unit decimal**
(§2). Sending `116250250` where the oracle expects `1162502.5` does not "comply with the
non-negotiable" — it asks the oracle a **different question** and produces a vector for a
MNT 116,250,250 loan mislabelled as a MNT 1,162,502.50 one. Fidelity to the oracle's API shape is
what makes a vector admissible at all; a capture harness that "corrected" the wire form would be
falsifying the observation.

The non-negotiable is not suspended here. It binds as: **the bytes on the wire must be exactly the
decimal the experiment intends, and must not have passed through a float on our side.** That is a
*byte-fidelity* obligation, not a *representation* obligation — and it is exactly what T173's guard
enforces.

### (b) The Go module's own adapter/API surface — BINDS ABSOLUTELY

**Ruling: a float-shaped money token here is a REJECTION, with no exception and no "the oracle does
it" defence.**

This is already the ratified position, not a new one. `contract.go` states it twice:

> `// - All monetary quantities are int64 counts of the currency's minor unit.`
> `//   There is no float32, float64, big.Float, decimal string or float-backed`
> [VERIFIED: `nexus/internal/apps/loanschedule/contract/contract.go:120-121`]

> `// Rationals rather than a float: a float rate is prohibited on any money path,`
> [VERIFIED: `contract.go:219`]

and DEC-1 anticipated this exact question in terms that settle it:

> "**No `float32`/`float64` may appear anywhere on this path**; the doubles in the Java source are
> an artefact of the reference implementation, **never a licence to introduce one here** (a float on
> a money path is a non-negotiable rejection)."
> [VERIFIED: `docs/adr/DEC-1-schedule-generator-adapter.md:829`]

**Consequence for parity.** Where Fineract's own answer is contaminated by a `double` (§2.4, §2.5),
the Go port must reproduce **the oracle's observed output value**, and must do so with exact
arithmetic — never by introducing a matching `double`. A port that "matches by copying the defect"
is a rejection even when the digits agree.

### (c) The stored vector — MINOR-UNIT INTEGER, AND THIS IS ALREADY TRUE

**Ruling: a float-shaped money token in a stored vector is a REJECTION. Measured state: zero
violations.**

> **`.softhouse/vectors` contains 50 JSON files and exactly ZERO float-typed JSON tokens of any
> kind, in any field, money or otherwise.**
> [VERIFIED: this task, raw-token scan via `json.load(..., parse_float=hook)`, §5]

The vector schema `gerege.loanschedule.vector/v1` already carries:

| quantity | vector representation | example |
|---|---|---|
| money | JSON **string** of integer minor units | `"principal_minor": "116250250"` |
| money (cross-check) | JSON **string**, oracle's own emitted characters | `"principal_major_text": "1162502.50"` |
| rate | **exact rational** object | `"annual_nominal_interest_rate": {"numerator": 27, "denominator": 125}` |
| rounding | integers + mode name | `{"significant_digits": 19, "mode": "HALF_UP"}` |

[VERIFIED: `.softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json`]

Note what the rate row does: **21.6% is not dyadic** (§6), and the vector stores it as the exact
rational 27/125 rather than as any decimal or float. The one category where the non-negotiable's
letter is hardest to satisfy is the one where the corpus is already strictest.

---

## 2. Fineract's declared wire type, with source citations

### 2.1 The request body is never parsed as a number by the JAX-RS layer

The loans resource method declares the body as a **raw `String`**:

```java
public String calculateLoanScheduleOrSubmitLoanApplication(
        @QueryParam("command") ... final String commandParam, @Context final UriInfo uriInfo,
        @Parameter(hidden = true) final String apiRequestBodyAsJson) {
```
[VERIFIED: `fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/api/LoansApiResource.java:570-572`]

and the Jersey reader short-circuits for `String`, so **Jackson never sees the numbers**:

```java
if (String.class == genericType) {
    // If the request type is String, keep it that way.
```
[VERIFIED: `fineract-provider/src/main/java/org/apache/fineract/infrastructure/core/jersey/JerseyJacksonObjectArgumentHandler.java:62-63`]

### 2.2 The declared type is `BigDecimal`, and the JSON-number branch parses the TOKEN TEXT

This is the load-bearing citation and it was re-verified by hand for this ruling:

```java
public BigDecimal extractBigDecimalNamed(final String parameterName, final JsonObject element, final Locale locale,
        final Set<String> modifiedParameters) {
    ...
            if (!primitive.isJsonNull()) {
                if (primitive.isNumber()) {
                    value = primitive.getAsBigDecimal();          // <-- line 152
                } else {
                    final String valueAsString = primitive.getAsString();
                    if (StringUtils.isNotBlank(valueAsString)) {
                        value = convertFrom(valueAsString, parameterName, locale);
                    }
                }
```
[VERIFIED: `fineract-core/src/main/java/org/apache/fineract/infrastructure/core/serialization/JsonParserHelper.java:142-157`, `getAsBigDecimal()` at `:152`]

**The declared wire type for `principal` is `BigDecimal`, not `Double` and not a string.** Confirmed
at every layer:

| layer | declaration | citation |
|---|---|---|
| schedule assembler | `final BigDecimal principal = this.fromApiJsonHelper.extractBigDecimalWithLocaleNamed("principal", element);` | `LoanScheduleAssembler.java:267` |
| rate, same | `final BigDecimal interestRatePerPeriod = ...extractBigDecimalWithLocaleNamed("interestRatePerPeriod", element);` | `LoanScheduleAssembler.java:252` |
| validator | `final BigDecimal principal = this.fromApiJsonHelper.extractBigDecimalWithLocaleNamed(LoanApiConstants.principalParamName, element);` | `LoanApplicationValidator.java:637-638` |
| entity field | `@Column(name = "principal_amount", scale = 6, precision = 19) private BigDecimal principal;` | `LoanProductRelatedDetail.java:61-62` |
| entity, rate | `@Column(name = "nominal_interest_rate_per_period", scale = 6, precision = 19) private BigDecimal nominalInterestRatePerPeriod;` | `LoanProductRelatedDetail.java:64-65` |
| DB column | `<column ... name="nominal_interest_rate_per_period" type="DECIMAL(19, 6)"/>` | `db/changelog/tenant/parts/0001_initial_schema.xml:2040`, `:3117` |
| Swagger POST /loans | `public BigDecimal principal;` / `public BigDecimal interestRatePerPeriod;` | `LoansApiResourceSwagger.java:1343`, `:1357` |
| tranche principals | `...getAsJsonPrimitive(...disbursementPrincipalParameterName).getAsBigDecimal();` | `LoanScheduleAssembler.java:648` |

**Why this matters, exactly as the task framed it.** A `BigDecimal` parsed from a JSON number
literal is a fundamentally weaker exposure than a `double`. Gson is configured as a bare
`new Gson()` with **no `BigDecimal`/`Double`/`Number` type adapter registered anywhere in the
codebase** [VERIFIED: `FromJsonHelper.java:57-60`; adapter registry at
`GoogleGsonSerializerHelper.java:105-115` registers only date/time and `ExternalId` types]. Gson is
pinned at `com.google.code.gson:gson:2.14.0`
[VERIFIED: `buildSrc/src/main/groovy/org.apache.fineract.dependencies.gradle:55`].

> [UNVERIFIED — library source not present in this checkout] Upstream Gson 2.14.0 retains the raw
> decimal token in a `LazilyParsedNumber` and implements `getAsBigDecimal()` as
> `new BigDecimal(getAsString())`. Under that behaviour the JSON-number branch is a pure
> **token-text → `BigDecimal`** path with no binary64 intermediate. **I could not cite a
> `path:line` for this because no Gson jar or source is present on this machine.** It is the only
> link in the loans chain resting on library behaviour rather than on repository source. §9 records
> the check that would close it.

### 2.3 The INVERSION — sending money as a JSON *string* is the dangerous form

The `else` branch at `JsonParserHelper.java:154-157` routes a **quoted** value to `convertFrom`,
which ends:

```java
                final NumberStyleFormatter numberFormatter = new NumberStyleFormatter();
                final Number parsedNumber = numberFormatter.parse(source, clientApplicationLocale);
                if (parsedNumber instanceof BigDecimal) {
                    number = (BigDecimal) parsedNumber;
                } else {
                    number = BigDecimal.valueOf(parsedNumber.doubleValue());   // <-- line 737
                }
```
[VERIFIED: `JsonParserHelper.java:732-738`]

**Line 737 is a genuine `double` round trip.** It is reached only for string-valued amounts, and
only if Spring's `NumberStyleFormatter` returns a non-`BigDecimal` `Number`.

> [UNVERIFIED — Spring library source not present in this checkout] Spring's `NumberStyleFormatter`
> is documented to call `setParseBigDecimal(true)`, which would make line 737 unreachable in
> practice. **I could not verify this against a `path:line`; no `spring-context` jar is present on
> this machine.**

This inverts the naive intuition and is worth stating plainly for any future harness author:
**quoting a money value to "avoid a JSON float" would move it OFF the exact `getAsBigDecimal()` path
and ONTO the path that contains a `doubleValue()` call.** It would also make `locale` mandatory —
`convertFrom` throws `PlatformApiDataValidationException` with
`validation.msg.missing.locale.parameter` when the locale is null
[VERIFIED: `JsonParserHelper.java:704-715`]. The committed corpus sends unquoted JSON numbers and is
therefore on the exact branch.

### 2.4 THE ONE REAL `double` ON A FINERACT REQUEST PATH — `POST /charges`

```java
    private Double amount;
```
[VERIFIED: `fineract-charge/src/main/java/org/apache/fineract/portfolio/charge/request/ChargeRequest.java:41`]

Unlike `PostLoansRequest` (documentation-only, never instantiated), **this DTO is actually
deserialized**, because the resource method declares the DTO type rather than `String`:

```java
    public CommandProcessingResult createCharge(@Parameter(hidden = true) ChargeRequest chargeRequest) {
        final CommandWrapper commandRequest = new CommandWrapperBuilder().createCharge()
                .withJson(toApiJsonSerializer.serialize(chargeRequest)).build();
```
[VERIFIED: `fineract-charge/src/main/java/org/apache/fineract/portfolio/charge/api/ChargesApiResource.java:139-142`]

so `JerseyJacksonObjectArgumentHandler` falls through to Jackson, and the configured `ObjectMapper`
does **not** enable `DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS`
[VERIFIED: `JerseyJacksonConverterConfig.java:48-54`]. Note the DTO is internally inconsistent —
`minCap` and `maxCap` on the same class are `BigDecimal`
[VERIFIED: `ChargeRequest.java:52-53`], and the persisted column is
`@Column(name = "amount", scale = 6, precision = 19) private BigDecimal amount;`
[VERIFIED: `fineract-charge/.../domain/Charge.java:76-77`].

**So `POST /charges` `amount` genuinely transits an IEEE-754 `double` inside the oracle.** Chain:
JSON token → Jackson → `double` → Gson re-serialize → string → command layer `getAsBigDecimal()`.

**This is why T173's guard property is the right one.** A value survives that chain **exactly** iff
its token text is already the shortest round-trip repr of its double — which is precisely
`repr(float(tok)) == tok`, T173's property. T173 chose byte preservation as the weaker defensible
property; it turns out to be **the exact necessary and sufficient condition** for our corpus to be a
faithful observation across the one endpoint where Fineract itself uses a `double`. That is a
stronger justification than the one T173 recorded, and it should be recorded as such.

### 2.5 Two further `double` sites, downstream of the wire

- **Rate laundering in a domain getter** — the field is `BigDecimal` and the column is
  `DECIMAL(19,6)`, but every read passes through `Double.parseDouble`:
  ```java
  public BigDecimal getNominalInterestRatePerPeriod() {
      return this.nominalInterestRatePerPeriod == null ? null
              : BigDecimal.valueOf(Double.parseDouble(this.nominalInterestRatePerPeriod.stripTrailingZeros().toString()));
  }
  ```
  [VERIFIED: `LoanProductRelatedDetail.java:344-346`]
- **The EMI kernel is `double`** — `FinanicalFunctions.pmt(double, double, double, double, boolean)`
  [VERIFIED: `fineract-loan/.../loanschedule/domain/FinanicalFunctions.java:44-55`], called via
  `LoanApplicationTerms.paymentPerPeriod` at `:1604-1622`.

Both are **oracle-internal**, downstream of the wire, and already partly recorded in
`.softhouse/reference-oracle.md` (the EMI loop). They are stated here because they are the reason
category (b)'s rule is "reproduce the oracle's *output*, never its *arithmetic type*".

### 2.6 `MoneyHelper`, re-confirmed

`public static final int PRECISION = 19;` [VERIFIED: `MoneyHelper.java:34`] and
`return mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()));`
[VERIFIED: `MoneyHelper.java:89-92`]. Matches `CLAUDE.md`'s ratified `(19, HALF_UP)`.

---

## 3. The 38 files, categorised

Both driver figures reproduce exactly. The grep that yields **38** is *any float-shaped `"principal"`
token in any `*.json` under `.softhouse/capture`, including `out/`*; the **11** are the files under a
`req/` dir carrying the literal `1162502.5`, and they are exactly the non-`out/` subset of the 38.

| # | category | count | what they are |
|---|---|---|---|
| 1 | **(a) request bodies under `req/`** | **11** | T149 / T153 / T22-audit half-cent tie probes, all `"principal": 1162502.5` |
| 2 | **(a) request bodies stored under `out/`** | **18** | adversarial/mutation fixtures: `t76/out/attack-C-req.json` (`1162502.78`), `t80/out/attack-2-req-mutated.json` (`1162502.55`), and 16 × `t91/out/*/req-crafted-04.json` + `req-mutated-55.json` (`1162502.4`) across 8 shell/copy arms |
| 3 | **oracle RESPONSES under `out/`** | **9** | `pathb/out/product-{1,2}-asstored.json` and 7 × `tierA-a2/out/*` — Fineract's own emission, `"principal":1200000.000000` at scale 6 |
|  | **total** | **38** | |

Group 3 is a **fourth category the task's (a)/(b)/(c) trichotomy does not name**: the *response* leg.
It is an observation of the oracle and is no more amendable than group 1 — its scale-6 form is
itself information (it witnesses `DECIMAL(19,6)`).

### Is any of the 38 a parity vector?

**None of the 38 is a vector at all** — all 38 live under `.softhouse/capture/`, and vectors live
under `.softhouse/vectors/`. But the sharper question has a sharper answer:

> **YES — one of the 11 is the request that produced a promoted PARITY vector.**
>
> `.softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json` is
> `"class": "parity"`, `threaded_mathcontext` `{precision: 19, rounding_mode: "HALF_UP"}` — **the
> production setting** — `seam: path_b_server`, `fineract_commit: 426a23544…`, and its
> `provenance.capture_ref` is `.softhouse/capture/pathb/t149/out/gerege/T149-TIE-P9-raw.json`, whose
> request body is `.softhouse/capture/pathb/t149/req/calc-t149-tie-p9.json` — file 4 of the 11.
> [VERIFIED: this task, both files read directly]

So this is **not** confined to discrimination probes. `CLAUDE.md` demotes captures taken at precision
12 or 8 (`C-00`, `D-01`…`D-04`, `D-01-p8`, `D-01-mnt`) to probes; the T149 tie family is **not** in
that list and was taken at `(19, HALF_UP)`. **The wire-form question reaches the graded parity
corpus, and the ruling therefore had to be made rather than deferred.**

Vector corpus census: 50 files — **43 `parity`** (all at `(19, HALF_UP)`), 4 `contract-refusal`,
1 `selftest`. Of the 43, 42 trace to `capture/out/capture-prod3{b,c,d,e,f,g,i}-raw.json` and 1 to
the T149 tie [VERIFIED: this task, provenance scan].

---

## 4. Do not overstate the defect

**`1162502.5` major = `116250250` MNT minor units EXACTLY.** `0.5` is dyadic, so the value is
exactly representable in binary64 and round-trips a double byte-identically.

> **The defect, if any, is REPRESENTATIONAL, not a measured arithmetic error. No arithmetic error
> has been measured anywhere in this corpus.**

Confirmed by direct measurement, and the measurement is stronger than the single token:

> **Across all 71,527 float-typed JSON tokens in `.softhouse/capture` (1,970 distinct), ZERO lose
> their numeric value through a binary64 round trip.**
> [VERIFIED: this task, §6]

The vector proves the point in the other direction too: `1162502.5` is stored as
`"principal_minor": "116250250"` with `"principal_major_text": "1162502.50"` alongside, so the
major→minor scaling is mechanically re-checkable and no scaling was ever done in floating point.

---

## 5. Method (P-25 compliance)

All arithmetic in this ruling is exact: `fractions.Fraction` for exact decimal values and
`decimal.Decimal` for value comparison. **The single `float()` call SIMULATES the defect** — the
only way to measure it — and every conclusion drawn from it compares two *strings* or two
*`Decimal`s*, never two floats. Detection uses `json.load(..., parse_float=hook)`, which hands back
the **original source text** of each numeric token, so nothing depends on a regex guessing what is a
number (P-48 rule 1; same technique as T173's guard).

29 of 749 `*.json` files under `.softhouse/capture` are not parseable as a single JSON document
(concatenated/NDJSON raw transcripts, e.g. `periodratio/out/t39-*-raw.json`). They are excluded from
the token census and named here rather than silently skipped. **This is a stated limit of the
measurement, not a clean result** — see §9.

---

## 6. Dyadic analysis: which tokens do NOT round-trip

Three properties must be kept apart. Conflating them is how this question stayed open.

| | property | what it means | what it protects |
|---|---|---|---|
| **P1** | **exactly representable** — value *is* a binary64 | the decimal is a dyadic rational within 53 bits | a consumer that **keeps** the double and does arithmetic |
| **P2** | **byte preservation** — `repr(float(t)) == t` | text is already the shortest repr of its double | **capture/replay fidelity**; survival across `ChargeRequest.amount` (§2.4) — *this is T173's guard* |
| **P3** | **value preservation** — `Decimal(repr(float(t))) == Decimal(t)` | the *number* survives a double transit | the observation not being falsified |

### 6.1 Request bodies — T173's derived set, reproduced exactly

320 request bodies (`*.json` under a `req/` dir, plus `*.req`), 0 unparseable, **221 carrying at
least one float-shaped token — 214 `interestRatePerPeriod`, 53 `amount`, 11 `principal`.**
**T173's three counts reproduce digit for digit.** [VERIFIED: this task]

Those 278 occurrences are **only 15 distinct tokens**, so the question is fully enumerable:

| token | occ | P1 exact binary64 | P2 bytes | P3 value | what it is |
|---|---|---|---|---|---|
| `0.001875` | 1 | **NO** | OK | OK | charge % |
| `0.009375` | 1 | **NO** | OK | OK | charge % |
| `0.021875` | 1 | **NO** | OK | OK | charge % |
| `0.1` | 2 | **NO** | OK | OK | charge % |
| `0.5` | 3 | yes | OK | OK | charge % |
| `1.2345` | 31 | **NO** | OK | OK | charge % |
| `1.25` | 1 | yes | OK | OK | charge |
| `2.5` | 2 | yes | OK | OK | charge |
| `3.75` | 8 | yes | OK | OK | charge % |
| `12.0` | 3 | yes | OK | OK | **rate** |
| `21.6` | 211 | **NO** | OK | OK | **rate** |
| `333.33` | 1 | **NO** | OK | OK | flat charge (money) |
| `7777.77` | 1 | **NO** | OK | OK | flat charge (money) |
| `12345.67` | 1 | **NO** | OK | OK | flat charge (money) |
| `1162502.5` | 11 | yes | OK | OK | **principal (money)** |

**Answers to the task's sharp questions:**

- **Which are NOT dyadic? Nine of the fifteen:** `0.001875`, `0.009375`, `0.021875`, `0.1`,
  `1.2345`, `21.6`, `333.33`, `7777.77`, `12345.67`. Notably this includes **`21.6`, which is 211
  of the 214 `interestRatePerPeriod` tokens** — so the overwhelming majority of rate tokens are
  non-dyadic, and `1162502.5`, the token the driver flagged, is **not** among them.
- **Is any a value where a double round trip would change the bytes the oracle received? NO —
  zero, in the whole request corpus.** Each of the nine is already the shortest round-trip repr of
  its nearest double, so the bytes are stable even though the value is not exactly a binary64. The
  guard is **green on the committed corpus**, and green for a reason, not by luck.

### 6.2 Where the `amount` tokens actually go — the decisive split

The 53 `amount` tokens do **not** share one path:

- **7** are `POST /charges` bodies (top-level `chargeAppliesTo`/`chargeTimeType`) → `ChargeRequest.amount`,
  a Java **`Double`** (§2.4). Values `1.2345` ×4, `3.75` ×2, `0.5` ×1 — and **all seven carry
  `chargeCalculationType` ∈ {2, 3, 4}**, i.e. percent-of-amount, percent-of-amount-plus-interest,
  percent-of-interest. [VERIFIED: `.softhouse/capture/charges/req/charge-0{3,4,5,9}-*.json`,
  `charge-1{0,1,2}-*.json`]
- **46** are `charges[].amount` nested inside a loan calc/application body → the loans `String`
  path → `getAsBigDecimal()`. No `double`.

> **Therefore ZERO money-valued tokens in the committed corpus traverse Fineract's `Double`. All
> seven that do are PERCENTAGES.** The one non-dyadic value among them, `1.2345`, is byte-stable, so
> even that transit is lossless.

### 6.3 Whole-corpus sweep, including responses

| category | distinct tokens | occurrences | P1 fail | P2 fail | **P3 fail** |
|---|---|---|---|---|---|
| MONEY | 1,539 | 70,594 | 1,372 | 235 | **0** |
| RATE | 4 | 321 | 2 | 2 | **0** |
| OTHER | 427 | 612 | 409 | 8 | **0** |

**All 245 P2 failures are trailing-zero decimal forms** — `1200000.000000` → `1200000.0`,
`21.600000` → `21.6`, `0.100000` → `0.1` — i.e. **scale-6 emissions by Fineract itself on the
RESPONSE leg**, matching `DECIMAL(19,6)`. **The value is intact in every one; only the scale would
be lost.** That is still information (§8 R4), but it is not an arithmetic error.

Only 4 distinct RATE tokens exist corpus-wide: `21.6` (248 files), `21.600000` (46 occ, response
form), `12.0`, `0.000000`.

### 6.4 Headroom — how far the corpus is from the cliff

Binary64 begins losing decimal **value** above 17 significant digits.

- **MONEY tokens: max 10 significant digits, max scale 6.** Scale census: {1: 28, 2: 69 869,
  3: 28, 4: 43, 6: 626}.
- **RATE tokens: max 3 significant digits.**
- The only 17-significant-digit tokens in the whole tree are `gap_float`,
  `gap_display_only_float`, `B_times_a_display_only_float` — analysis diagnostics confined to
  exactly **two** files, `t100-g8-rescope/out/closed-form-check.json` and
  `t117-familyb/out/threshold-exact.json`, and self-labelled as floats in their own key names.

**So the money corpus sits ~7 orders of magnitude of significant digits below the value-loss
threshold.** That is the honest reason P3 is zero — the margin is enormous, not marginal. It is also
why P3 should **not** be adopted as the guard property: it would pass a corpus that had already
drifted badly, and it will keep passing right up until it doesn't.

### 6.5 Does the non-negotiable even bind a rate?

`CLAUDE.md`: *"Money is integer minor units. No floating-point in any **monetary** code path, struct
field, schema column, API field, or test fixture — including intermediate calculation."*

**A rate is not money**, so the non-negotiable's letter does not reach `interestRatePerPeriod`. But
it binds by two other routes, and the conclusion is the same:

1. **P-25** extends the no-float rule to *"anything whose output is used to reason about money"*.
   A rate multiplies a principal; an inexact rate yields an inexact amount.
2. **`contract.go:219` already rules on it explicitly**: *"a float rate is prohibited on any money
   path"*, and `Rate` is `{Numerator, Denominator int64}` [VERIFIED: `contract.go:230-233`].

So a rate is **prohibited as a float in (b) and (c)** by the contract, and **admissible as a decimal
in (a)** for the same fidelity reason as money — with the additional fact that 21.6 is non-dyadic
and therefore *must* be carried as text or as an exact rational, never as a float, anywhere on our
side. The corpus already does this: wire `21.6`, vector `{27, 125}`.

---

## 7. The enforcement boundary, mechanically stated

A future guard can implement this without judgement calls. **Path decides the rule.**

### Zone A — oracle-facing wire. `.softhouse/capture/**`

Float-shaped major-unit money tokens are **ADMISSIBLE**. Enforce instead:

- **A1 — byte preservation (P2).** Every numeric token in every **request body** must satisfy
  `repr(float(tok)) == tok`. **This is already implemented and wired**:
  `.softhouse/capture/lib/check_wire_float_roundtrip.py`, invoked from `.softhouse/conformance.sh:784`.
  *Justification strengthened by this task:* it is the exact survival condition across
  `ChargeRequest.amount`'s `double` (§2.4), not merely a defensible weaker property.
- **A2 — no blanket ban.** A rule of the form "no float-shaped token in a request body" is
  **WRONG** and must be rejected in review: it refuses 221 of 320 committed bodies and would pin
  `conformance.sh` at exit 2. T173 was right.
- **A3 — never quote a money value to avoid a JSON float.** Quoting moves it onto the
  `convertFrom` branch, which contains `BigDecimal.valueOf(parsedNumber.doubleValue())`
  [`JsonParserHelper.java:737`], and makes `locale` mandatory. Unquoted JSON number is the exact path.
- **A4 — responses are observations.** Never rewrite, never re-emit through a float, never
  normalise scale. `1200000.000000` is not a typo for `1200000.0`; the scale witnesses
  `DECIMAL(19,6)`.

### Zone B — the Go module. `nexus/**`

**Any** floating-point type on a money or rate path is a **REJECTION**, no exception. Money is
`int64` minor units; rates are `Rate{Numerator, Denominator int64}`. Mechanical test — reject a diff
under `nexus/**` where `float32`, `float64`, `big.Float`, or a float-backed decimal appears in the
same declaration, struct field, function signature, or expression as a money or rate identifier.
Already stated at `contract.go:120-121`, `:219`, `:738`, `:1091-1093` and `DEC-1:829`.

**Corollary (the trap this task exists to close):** discovering that Fineract uses a `double`
(§2.4, §2.5) is **never** a licence to introduce one in Go. Reproduce the oracle's observed
**output**; never import its arithmetic **type**.

### Zone C — stored vectors. `.softhouse/vectors/**`

A **float-typed JSON token of any kind is a REJECTION.** The mechanical test is total and needs no
key list, because the current measured count is zero:

```
json.load(path, parse_float=<hook that raises>)   # any hit  ->  reject
```

Money → JSON string of integer minor units (`*_minor`). Rates → `{numerator, denominator}` integers.
The oracle's own characters may be carried in a `*_major_text` **string** cross-check field, which
is a string and cannot be mangled.

### The boundary in one line

> **A float-shaped money token is admissible exactly where it is a faithful transcription of bytes
> the ORACLE defined, and is a rejection everywhere GEREGE defines the bytes.**
> Zone A: oracle defines them → admissible, byte-fidelity enforced.
> Zones B and C: Gerege defines them → rejection.

### Recommended guard additions (not implemented by this task — see §10)

- **G-A1.** Extend A1's derived set to the **18 request-shaped bodies stored under `out/`** (§3
  group 2). T173's set is `*.json` under a dir named `req` plus `*.req`, so `t76/out/attack-C-req.json`,
  `t80/out/attack-2-req-mutated.json` and the 16 `t91/out/*/req-*.json` are **currently
  uninspected**. *Caveat, stated rather than assumed:* these are deliberately-mutated adversarial
  fixtures whose purpose is to be corrupt, so P2 may be the wrong property for them and they may
  need an explicit allowlist rather than coverage. **Decide before implementing.**
- **G-C1.** Implement Zone C's total ban as a conformance step. It passes today at zero violations,
  so it can be added without refusing anything — the cheapest moment to add a guard is while it is
  already green.

---

## 8. What I did NOT establish

1. **Gson 2.14.0's `getAsBigDecimal()` internals are UNVERIFIED against source** (§2.2). No Gson jar
   or source exists on this machine. The loans path's freedom from `double` rests on that library
   behaviour for its final link. Everything upstream of it is verified from repository source.
2. **Spring's `NumberStyleFormatter.parse` return type is UNVERIFIED** (§2.3). Whether
   `JsonParserHelper.java:737`'s `doubleValue()` is reachable in practice is therefore **open**. The
   line's existence is verified; its reachability is not. Our corpus does not use the string form,
   so this is latent, not live.
3. **No live-oracle experiment was run.** I did not send `1162502.5` and `"1162502.5"` to the oracle
   and diff the answers. That experiment would settle items 1 and 2 empirically and is the single
   highest-value follow-up (FU-1).
4. **29 of 749 capture `*.json` files were not parsed** (§5). They are concatenated/NDJSON raw
   transcripts. **I did not measure their tokens**, so every corpus-wide count in §6.3 and §6.4
   excludes them. I did not verify they contain no value-losing token — I verified only that they
   are not single JSON documents.
5. **The `chargeCalculationType` of 44 of the 53 `amount` tokens is not resolvable from the request
   body**, because a loan-attached charge carries only `chargeId` and the type lives on the charge
   definition. My money-vs-percentage split for those 44 rests on **magnitude inference**
   (`0.001875`…`3.75` read as percentages; `333.33`, `7777.77`, `12345.67` as flat money), **not on
   a verified type**. The 7 `POST /charges` bodies are verified.
6. **I did not verify that every `capture-prod3*-raw.json`-derived parity vector has a request body
   free of float-shaped money.** Those requests are generated inline by `src/run-pass3*.sh` rather
   than committed under `req/`, so they are outside both T173's derived set and my census. **42 of
   the 43 parity vectors descend from those captures.** This is the largest gap in this ruling's
   coverage and I am flagging it as such rather than implying the parity corpus is fully swept.
7. **No claim about arithmetic correctness of any vector.** This ruling is about representation and
   transit fidelity only. It does not re-derive a single money figure.

---

## 9. Gate needed? **NO**

The ruling changes **no** DEC-1 field, type, enum member, graded-domain predicate, pin or refusal,
and does not touch `contract.go`. It is a **clarification consistent with DEC-1 as ratified**, which
had already decided category (b):

> DEC-1:829 — *"No `float32`/`float64` may appear anywhere on this path; the doubles in the Java
> source are an artefact of the reference implementation, never a licence to introduce one here."*

and category (c) is already the contract's own typing (`int64` minor units, `Rate` rational). Only
category (a) — the capture harness's wire form — was genuinely unsettled, and **the frozen adapter
contract does not govern the capture harness.** No `user` decision is required.

**Nothing here is a RESERVED item**: it is not a licence fact, not a cutover, not regulatory
sign-off, and it spends no money and exposes no endpoint. Under `CLAUDE.md`'s answering gates it is
**ENGINEERING**, answerable from source and measurement, and is decided here.

---

## 10. Follow-ups

- **FU-1 (highest value).** Run the live-oracle experiment: POST the same loan with
  `"principal": 1162502.5` and with `"principal": "1162502.5"` (plus `locale`), and diff. Settles
  §8 items 1 and 2 empirically and would let A3 be stated as an observation rather than a source
  reading.
- **FU-2.** Extend the wire-float guard to `capture-prod3*` request generation (§8 item 6) —
  42 of 43 parity vectors descend from bodies no guard currently inspects.
- **FU-3.** Decide G-A1: cover the 18 `out/` request-shaped bodies, or allowlist them explicitly as
  adversarial fixtures. Either is defensible; leaving them silently uninspected is not.
- **FU-4.** Implement G-C1, the Zone C total ban on float-typed vector tokens, while it is green.
- **FU-5.** Parse or explicitly exempt the 29 NDJSON raw transcripts (§8 item 4) so the census can
  claim whole-corpus coverage.
- **FU-6.** Record in `reference-oracle.md` the three oracle `double` sites — `ChargeRequest.amount:41`,
  `LoanProductRelatedDetail.java:344-346`, `FinanicalFunctions.pmt` — as **porter's hazards**, in the
  style DEC-1 §4.1.2 uses for the `Money.java` list.
- **FU-7.** Amend `check_wire_float_roundtrip.py`'s header to record §2.4's stronger justification:
  the property is not just "the defensible weaker choice", it is the exact survival condition across
  `ChargeRequest.amount`'s `double`.
