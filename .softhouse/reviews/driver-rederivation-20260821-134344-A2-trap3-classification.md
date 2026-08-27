# Driver re-derivation — A2 trap (3): the ledger has no classification, and NOTHING guards a retype

**Fire** `20260821-134344` · **Re-derived by** the `/softhouse-program` driver, from the pinned Fineract
checkout `/Users/buv/fineract` at **`426a23544`** · **Status: CONFIRMED, and stronger than reported.**

## Why this file exists

A2-8's brief carried trap (3) as *"[A2-1's finding, **NOT driver-confirmed** — A2-9 must not treat it as
established]"*. Shipping a Go design decision — *the port MUST carry classification on the entry* — on an
unconfirmed premise is exactly the failure this program keeps recording (**P-42**: re-derive your own
premises; **P-40**: the driver's own enumerator reported a subset as the whole and overturned a gate
consequence). So the driver re-derived it rather than letting A2-8 inherit it. It holds.

## What the source says

### 1. The journal entry stores no classification

`fineract-accounting/.../journalentry/domain/JournalEntry.java` (`@Table(name = "acc_gl_journal_entry")`,
line 40). Every persisted column, enumerated:

| column | line | note |
|---|---|---|
| `office_id`, `payment_details_id` | 44, 48 | |
| **`account_id`** | 52-53 | `@ManyToOne` → `GLAccount`. **The only route to a classification.** |
| `currency_code` | 55 | |
| `reversal_id` | 60 | reversing entries — the append-only correction path |
| `transaction_id`, `loan_transaction_id`, `savings_transaction_id`, `client_transaction_id`, `share_transaction_id` | 63-76 | |
| `reversed`, `manual_entry` | 79, 82 | |
| `entry_date`, `submitted_on_date` | 85, 106 | |
| **`type_enum`** | 88 | DEBIT/CREDIT — **not** ASSET/LIABILITY/EQUITY/INCOME/EXPENSE |
| **`amount`** | 91 | `scale = 6, precision = 19` — **this is trap (4), also confirmed here** |
| `description`, `entity_type_enum`, `entity_id`, `ref_num` | 94-104 | |

There is **no classification column**. `type_enum` is the debit/credit side, a different axis entirely; a
port that reads the name `type` and thinks it has the account classification has conflated two axes.

### 2. Classification lives only on the account, and it is mutable

`fineract-core/.../glaccount/domain/GLAccount.java:73-74` — `@Column(name = "classification_enum",
nullable = false) private Integer type;`. And `GLAccount.update()` at `:99-113` handles
`GLAccountJsonInputParams.TYPE` (line 108). **`classification_enum` is an updatable property.**

### 3. THE FINDING: the only journal-entries-exist guard is on USAGE, not on TYPE

`fineract-accounting/.../glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImpl.java:151-159`:

```java
/** a detail account cannot be changed to a header account if transactions are already logged against it **/
if (changesOnly.containsKey(GLAccountJsonInputParams.USAGE.getValue()) && glAccount.isHeaderAccount()) {
    final boolean journalEntriesForAccountExist = this.glJournalEntryRepository.exists(...);
    if (journalEntriesForAccountExist) { throw new GLAccountInvalidUpdateException(TRANSANCTIONS_LOGGED, ...); }
}
```

That is the **entire** posted-history protection on the update path. It is keyed on `USAGE` and gated on
`isHeaderAccount()`. **`TYPE` is not mentioned.** `deleteGLAccount` has its own entries-exist check
(`:201-203`), so the repository query was available to the author of the update path and was simply not
applied to classification.

**Consequence, and it is exact:** an account carrying posted journal entries can be retyped ASSET→INCOME
with a plain `PUT`, and because the entries hold only `account_id`, **every entry ever posted to it
retroactively re-renders under the new classification**. An append-only ledger that displays mutated
history. This is what **G-10** observed from the other end — five product mappings whose GL account was
retyped underneath them, served without complaint — and the two now meet: G-10 is not an oddity of the
capture tenant, it is the documented behaviour of the update path.

### 4. The asymmetry worth naming

Fineract **does** guard `disabled`: `validateForAttachedProduct` (`:178-189`) refuses to disable an account
attached to any `acc_product_mapping` row. So the update path protects the **operationally visible** change
(you cannot disable an account a product points at) and leaves the **semantically destructive** one
(retyping an account with posted history) entirely open. A reader who sees the disable guard may reasonably
assume a retype guard exists. It does not.

## What A2-8 must take from this

- Trap (3) is **CONFIRMED**, promoted from *A2-1's unconfirmed finding* to *re-derived from pinned source*.
  **The Go port must carry the classification on the entry**, not resolve it through the account at read
  time. The write path is A1's; A2 owns the account model A1 reads, so model it so A1 *can*.
- Trap (4) is **CONFIRMED** at `JournalEntry.java:91` — `scale = 6, precision = 19`. Fineract can hold
  **sub-minor-unit residue** in a money column against MNT's minor unit of 2. A2-8 must **state the
  truncation rule it applies and name the vector that proves it**, or mark it `[UNVERIFIED]` and say so.
- `type_enum` on the entry is **DEBIT/CREDIT**, not classification. Do not conflate.

## Scope

Read-only re-derivation from the pinned checkout. No Fineract source was modified; nothing under `nexus/`
was touched. A2-9 may now treat trap (3) as established **against these citations** — and should re-derive
them rather than trust this file, on the same principle that produced it.
