# T307 — grading `errors[0].args` in the Refusal shape

Working notes. **NO ORACLE CONTACT.** Every byte below is read from
`.softhouse/capture/t287-closure-refusals/out/` (T287's committed captures, `MANIFEST.sha256`
re-verified) and from the pinned Fineract checkout `/Users/buv/fineract` @
`426a23544e8426a38ae43ae404670a0a7e85b9eb` (`git rev-parse`, re-verified this fire).

---

## 1. The wire, all four date captures, verbatim

```
A1-01-future-far          "args":[{"value":"2026-12-31"},{},{}]   transactionDate 2026-12-31
A1-02-future-boundary+1   "args":[{"value":"2026-08-24"},{},{}]   transactionDate 2026-08-24
A2-01-preclosure-on-date  "args":[{"value":"2026-01-31"},{},{}]   transactionDate 2026-01-31
A2-02-preclosure-before   "args":[{"value":"2026-01-31"},{},{}]   transactionDate 2026-01-15  <-- ECHO != REQUEST
```

and OB-01, the capture T294 deliberately refused to grade:

```
OB-01  "args":[{"value":["a28f55a289cf","L1", ... 26 live transaction ids ... ,"L2"]}]
```

**The wire itself carries the discriminator.** On the four date refusals `args[0].value` is a
JSON **string**. On OB-01 it is a JSON **array**. §2 shows that is forced by the source and is
not an accident of formatting.

`args` on the date refusals has **three** elements, of which two are the empty object `{}`.
That is `JournalEntryInvalidException(reason, date, null, null)` →
`super(errorCode, errorMessage, date, accountName, accountGLCode)` — a three-element vararg
whose second and third members are `null`
[VERIFIED: `fineract-accounting/.../exception/JournalEntryInvalidException.java:91-94`].

---

## 2. WHY `args[0].value` is a string here and an array there — from source, not from shape

`ApiParameterError`'s constructor walks the vararg and wraps each member in an
`ApiErrorMessageArg`, with **exactly one special case**:

```java
for (final Object object : defaultUserMessageArgs) {
    if (object instanceof LocalDate) {
        final DateTimeFormatter dateFormatter = new DateTimeFormatterBuilder().appendPattern("yyyy-MM-dd").toFormatter();
        final String formattedDate = dateFormatter.format((LocalDate) object);
        messageArgs.add(ApiErrorMessageArg.from(formattedDate));
    } else {
        messageArgs.add(ApiErrorMessageArg.from(object));
    }
}
```

[VERIFIED: `fineract-core/.../infrastructure/core/data/ApiParameterError.java:95-105`, and
the identical block duplicated at `:118-128` for the other constructor.]

- A `LocalDate` arg becomes a **string** in `yyyy-MM-dd`.
- Anything else is handed to Gson as-is. On `OB-01` that "anything else" is a
  `List<String>` passed as a **single** vararg `Object`, so it serialises as a JSON **array**
  [T294 handoff §3 item 1, and the wire above].

So "`args[0].value` is a string" is equivalent to "the oracle put a `LocalDate` there", which
is a **source-level** property of the throw site, not a property of one day's tenant state.

---

## 3. THE ZONE/CLOCK DETERMINATION — per cell, before anything is graded

T329 established that two Fineract fields spelled `createdDate` are *different quantities*, one
a business date and one a JVM-zone audit insertion timestamp, and that grading a wall-clock-derived
date as a literal bakes an up-to-8-hour window into a parity vector. So each date this task
proposes to grade is traced to its clock **before** it is graded.

### 3a. The render itself reads no clock

`DateTimeFormatter.format(LocalDate)` with the pattern `yyyy-MM-dd`. A `java.time.LocalDate`
carries no instant and no zone; formatting it with a date-only pattern is a pure field render.
**The serialisation step adds nothing and can shift nothing.**
[VERIFIED: `ApiParameterError.java:97-99`.]

### 3b. `FUTURE_DATE` → the arg is `command.getTransactionDate()`

```java
if (DateUtils.isDateInTheFuture(transactionDate)) {
    throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.FUTURE_DATE, transactionDate, null, null);
}
```
[VERIFIED: `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:630-631`, pinned `426a23544`.]

`transactionDate` reaches that line from the request body via
`JsonParserHelper.convertDateTimeFrom` →
`LocalDateTime.parse(dateTimeAsString, formatter).toLocalDate()`
[VERIFIED: `fineract-core/.../serialization/JsonParserHelper.java:544-547, 558-586`].
`LocalDateTime.parse` takes **no `ZoneId`**, constructs **no `Instant`**, and `toLocalDate()` is
field extraction. On a `yyyy-MM-dd` input with `dateFormat: yyyy-MM-dd` the whole path is the
**identity function on the caller's own characters**.

**CLOCK: NONE. ZONE: NONE. Provenance: the caller's `.req` wire bytes.**

### 3c. `ACCOUNTING_CLOSED` → the arg is `latestGLClosure.getClosingDate()`

```java
if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)) {
    throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.ACCOUNTING_CLOSED, latestGLClosure.getClosingDate(),
            null, null);
}
```
[VERIFIED: `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:636-638`.]

`GLClosure.closingDate` is `private LocalDate closingDate;` on `@Column(name = "closing_date")`,
assigned in `fromJson` from `command.localDateValueOfParameterNamed(CLOSING_DATE)` — the same
zone-free parse as §3b
[VERIFIED: `fineract-accounting/.../closure/domain/GLClosure.java:53-54, 59-62, 70-72`].

**CLOCK: NONE. ZONE: NONE. Provenance: `req/a2-00-create-closure.json`'s `closingDate`,
confirmed in the DB by `out/M-09-state-during-closure.txt`.**

### 3d. The two clock-derived dates in this arm are NOT in `args` — and that is the finding

| quantity | clock | zone | appears in `args`? |
|---|---|---|---|
| `request.transaction_date` | none | none | **YES** — `FUTURE_DATE` |
| `request.latest_closing_date` | none | none | **YES** — `ACCOUNTING_CLOSED` |
| `request.business_date` (`DateUtils.getLocalDateOfTenant()`) | **wall clock** | tenant, `Asia/Ulaanbaatar` | **NO** |
| `glclosures.createdDate` (audit insert, T329) | **wall clock** | **JVM** | **NO** |

`:631` constructs `FUTURE_DATE` with `transactionDate` and **not** with the business date it
just compared against. So the guard that *reads* the wall clock does **not** *echo* it. The
exact hazard T329 warned about — a graded date literal that moves with the hour CI runs — is
absent from `args` on every capture in this corpus, and it is absent for a reason a reader can
check at `:631` rather than for a reason that happens to hold today.

`GLClosure extends AbstractAuditableCustom`, so a `createdDate` **exists** on that row
[VERIFIED: `GLClosure.java:44`]. It is simply not what `:637` passes.

---

## 4. THE FORMULATION

**An `args` cell is gradeable iff the wire value is a SCALAR the vector can name as a
DECLARED INPUT whose provenance is INDEPENDENT of the response body being graded.**

Mechanised as **a SELECTOR, not a date**:

```
expect.refusal.arg_echo : "transaction_date" | "latest_closing_date"   (CLOSED vocabulary)
graded cell             : refusal.arg0_value
want                    : ResolveArgEcho(arg_echo, v.Request)          (resolved at grading time)
got                     : the implementation's Refusal.Arg0Value
```

No calendar literal ever appears in an expectation, so the claim survives re-capture on any
dates. `Refusal.Arg0Value` carries `json:"-"`, so a vector **cannot write a date literal
there even deliberately** — it dies at strict decode with `unknown field`.

`admit.go` binds each selector to the refusal code whose throw site passes that date, in
both directions, and REQUIRES it on those two codes and FORBIDS it on every other.

## 5. T294's REFUSAL — RE-ADJUDICATED AND **UPHELD**, on two independent grounds

| ground | LDG-REFUSE-03 (OB-01) | LDG-REFUSE-04/05/06 |
|---|---|---|
| **structural** — `args[0].value` type | **JSON array** (26 live ids) | JSON string |
| **provenance** — where the declared input came from | `errors[0].args[0].value` **itself** | the caller's `.req` bytes / the create-closure request + SQL |

Either alone is disqualifying. `admit.go` enforces both, so the refusal no longer depends on
a later author remembering *why* OB-01 was left alone.

## 6. Instruments

| file | what it does | verdict |
|---|---|---|
| `instruments/10-amend-committed-date-vectors.py` | adds the selector to LDG-REFUSE-04/05 and RETRACTS their now-false "args is NOT graded" sentences in the same pass; refuses if a sentence is missing | OK, 2 amended |
| `instruments/20-build-ldg-refuse-06.py` | builds LDG-REFUSE-06 from A2-02's bytes behind 8 guards; **G-4 refuses unless echo != submitted date** | OK, 8/8 |
| `instruments/30-load-bearing-drive.sh` | 3 arms: mutant vs full store / mutant without the new vector / correct port vs full store | LOAD-BEARING |
| `instruments/40-amend-capability-row.py` | supersedes the half of the capability row T307 falsifies, appends the gap statement | OK |

`out/10-armA…`, `out/20-armB…`, `out/30-armC…` carry the drive transcripts.
