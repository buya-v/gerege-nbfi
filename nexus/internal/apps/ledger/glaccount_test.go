package ledger

import (
	"fmt"
	"testing"
)

// glAccountRead is the GET /glaccounts shape. It exists only in the tests: the
// port does not define a wire struct for it, because the read model belongs to
// whatever adapter serves the endpoint.
type glAccountRead struct {
	ID                   int64          `json:"id"`
	Name                 string         `json:"name"`
	ParentID             *int64         `json:"parentId"`
	GLCode               string         `json:"glCode"`
	Disabled             bool           `json:"disabled"`
	ManualEntriesAllowed bool           `json:"manualEntriesAllowed"`
	Type                 EnumReadObject `json:"type"`
	Usage                EnumReadObject `json:"usage"`
	Description          string         `json:"description"`
	NameDecorated        string         `json:"nameDecorated"`
}

// TestChartDecodesFromTheCapturedDump grades the enum decoders against the
// database's own integers for all 21 accounts across all five classifications.
func TestChartDecodesFromTheCapturedDump(t *testing.T) {
	chart := loadChart(t)
	byClassification := map[Classification]int{}
	for _, a := range chart {
		byClassification[a.Classification]++
	}
	// The chart spans all five classifications. This is the measurement that
	// refuted gate G-9's "exactly four GL accounts and all four are ASSET".
	for _, c := range []Classification{
		ClassificationAsset, ClassificationLiability, ClassificationEquity,
		ClassificationIncome, ClassificationExpense,
	} {
		if byClassification[c] == 0 {
			t.Errorf("captured chart has no %s account; the whole chart is %v", c, byClassification)
		}
	}
	if len(chart) != 21 {
		t.Errorf("captured chart has %d accounts, want 21", len(chart))
	}
}

// TestGLAccountReadShapeMatchesTheOracle grades type/usage rendering and
// nameDecorated against GET /glaccounts, for every account the oracle returned.
func TestGLAccountReadShapeMatchesTheOracle(t *testing.T) {
	chart := loadChart(t)
	var observed []glAccountRead
	decodeCapture(t, "A2-200-glaccounts-live-precheck", &observed)
	if len(observed) != len(chart) {
		t.Fatalf("capture has %d accounts, dump has %d", len(observed), len(chart))
	}
	for _, o := range observed {
		a := accountByID(t, chart, o.ID)

		if got := a.Classification.ReadObject(); got != o.Type {
			t.Errorf("account %d (%s): type object %+v, oracle %+v", a.ID, a.GLCode, got, o.Type)
		}
		if got := a.Usage.ReadObject(); got != o.Usage {
			t.Errorf("account %d (%s): usage object %+v, oracle %+v", a.ID, a.GLCode, got, o.Usage)
		}
		if got := a.NameDecorated(); got != o.NameDecorated {
			t.Errorf("account %d (%s): nameDecorated %q, oracle %q (hierarchy %q)",
				a.ID, a.GLCode, got, o.NameDecorated, a.Hierarchy)
		}
		if a.Name != o.Name || a.GLCode != o.GLCode {
			t.Errorf("account %d: name/glCode %q/%q, oracle %q/%q", a.ID, a.Name, a.GLCode, o.Name, o.GLCode)
		}
		if a.Disabled != o.Disabled || a.ManualEntriesAllowed != o.ManualEntriesAllowed {
			t.Errorf("account %d: disabled/manual %v/%v, oracle %v/%v",
				a.ID, a.Disabled, a.ManualEntriesAllowed, o.Disabled, o.ManualEntriesAllowed)
		}
	}
}

// TestSingleAccountReadsMatch grades the nine mandatory slots' accounts plus the
// retyped one, one capture each.
func TestSingleAccountReadsMatch(t *testing.T) {
	chart := loadChart(t)
	for _, id := range []string{
		"A2-201-read-gl16-fundsource",
		"A2-202-read-gl4-loanportfolio",
		"A2-203-read-gl17-transferssuspense",
		"A2-204-read-gl8-interestonloans",
		"A2-205-read-gl9-incomefromfees",
		"A2-206-read-gl10-incomefrompenalty",
		"A2-207-read-gl11-incomefromrecov",
		"A2-208-read-gl13-losseswrittenoff",
		"A2-209-read-gl6-overpayment",
		"A2-209b-read-gl2-retyped-fundsrc",
		"A2-012-read-header-asset",
	} {
		if st := captureStatus(t, id); st != 200 {
			t.Fatalf("%s: status %d, want 200", id, st)
		}
		var o glAccountRead
		decodeCapture(t, id, &o)
		a := accountByID(t, chart, o.ID)
		if got := a.Classification.ReadObject(); got != o.Type {
			t.Errorf("%s: type %+v, oracle %+v", id, got, o.Type)
		}
		if got := a.Usage.ReadObject(); got != o.Usage {
			t.Errorf("%s: usage %+v, oracle %+v", id, got, o.Usage)
		}
		if got := a.NameDecorated(); got != o.NameDecorated {
			t.Errorf("%s: nameDecorated %q, oracle %q", id, got, o.NameDecorated)
		}
	}
}

// TestGenerateHierarchyReproducesTheStoredStrings rebuilds every account's
// hierarchy from its parent chain and compares with what the database holds.
func TestGenerateHierarchyReproducesTheStoredStrings(t *testing.T) {
	chart := loadChart(t)
	byID := map[int64]GLAccount{}
	for _, a := range chart {
		byID[a.ID] = a
	}
	for _, a := range chart {
		rebuilt := GLAccount{ID: a.ID, Name: a.Name}
		if a.ParentID == nil {
			rebuilt.GenerateHierarchy(nil)
		} else {
			parent, ok := byID[*a.ParentID]
			if !ok {
				t.Fatalf("account %d names parent %d, which is not in the chart", a.ID, *a.ParentID)
			}
			rebuilt.GenerateHierarchy(&parent)
		}
		if rebuilt.Hierarchy != a.Hierarchy {
			t.Errorf("account %d (%s): rebuilt hierarchy %q, stored %q",
				a.ID, a.GLCode, rebuilt.Hierarchy, a.Hierarchy)
		}
	}

	// The counter-intuitive part, asserted explicitly: an account's OWN id is
	// in its own hierarchy string, and the ROOT's id is in nobody's.
	root := GLAccount{ID: 1, Name: "Assets"}
	root.GenerateHierarchy(nil)
	child := GLAccount{ID: 7, Name: "Child"}
	child.GenerateHierarchy(&root)
	grandchild := GLAccount{ID: 9, Name: "Grandchild"}
	grandchild.GenerateHierarchy(&child)
	if root.Hierarchy != "." || child.Hierarchy != ".7." || grandchild.Hierarchy != ".7.9." {
		t.Errorf("hierarchy chain = %q / %q / %q, want . / .7. / .7.9.",
			root.Hierarchy, child.Hierarchy, grandchild.Hierarchy)
	}
	if grandchild.NameDecorated() != "........Grandchild" {
		t.Errorf("grandchild nameDecorated = %q", grandchild.NameDecorated())
	}
}

// TestNameDecoratedSaturatesLikeTheOracleSql pins the two edge behaviours that
// come from reproducing a SQL SUBSTRING over a literal 40-dot string rather
// than a Go loop that "obviously" means the same thing.
//
// A2-12 CORRECTION (A2-9's F-B). Only ONE of the two is a reproduction. See
// the block at NameDecorated: PostgreSQL does NOT return the empty string for
// a negative SUBSTRING length, it raises `negative substring length not
// allowed`, so the zero-dot leg below pins THIS PORT'S total-function choice
// on input the oracle cannot write, not the oracle's behaviour. The assertion
// is unchanged; what it means is.
func TestNameDecoratedSaturatesLikeTheOracleSql(t *testing.T) {
	// Zero dots gives depth -1. The oracle's SQL would ERROR here; no oracle
	// writer can produce a dotless hierarchy (GLAccount.generateHierarchy
	// always emits at least one dot), so this pins the port's own refusal to
	// panic on unreachable input.
	bare := GLAccount{Name: "Odd", Hierarchy: ""}
	if got := bare.NameDecorated(); got != "Odd" {
		t.Errorf("zero-dot hierarchy: %q, want %q", got, "Odd")
	}
	// Beyond ten levels the 40-character pad is exhausted and the prefix
	// saturates rather than growing.
	deep := GLAccount{Name: "Deep", Hierarchy: ".1.2.3.4.5.6.7.8.9.10.11.12."}
	got := deep.NameDecorated()
	if len(got) != len(hierarchyDecorationRule)+len("Deep") {
		t.Errorf("deep nameDecorated has %d chars, want %d (40 dots saturated + name)",
			len(got), len(hierarchyDecorationRule)+len("Deep"))
	}
}

// TestG10TheTwoDumpsDisagreeAboutAccountTwo makes the P-32 hazard executable
// rather than leaving it as a comment.
//
// A2-072-db-product-mapping-rows.txt joins acc_gl_account and reports GL
// account 2 as classification_enum 1 (ASSET). A2-150-db-final-state.txt, taken
// LATER, reports it as 4 (INCOME), because A2-111-update-retype-mapped retyped
// it — HTTP 200 — while five product mappings pointed at it. Both files are
// committed, both look authoritative, and a port built from the wrong one
// believes the FUND_SOURCE slot of five products points at an ASSET.
func TestG10TheTwoDumpsDisagreeAboutAccountTwo(t *testing.T) {
	stale := parsePsqlTables(t, "A2-072-db-product-mapping-rows.txt")[""]
	var staleClassification string
	for i := range stale.rows {
		if stale.get(i, "gl_account_id") == "2" {
			staleClassification = stale.get(i, "classification_enum")
			break
		}
	}
	if staleClassification != "1" {
		t.Fatalf("A2-072 should still show GL account 2 as classification_enum 1 (ASSET); got %q", staleClassification)
	}

	current := accountByID(t, loadChart(t), 2)
	if current.Classification != ClassificationIncome {
		t.Fatalf("A2-150 should show GL account 2 as INCOME; got %v", current.Classification)
	}

	// And the retype was accepted by the oracle, with five mappings live.
	if st := captureStatus(t, "A2-111-update-retype-mapped"); st != 200 {
		t.Errorf("A2-111-update-retype-mapped status %d, want 200 — the retype IS accepted", st)
	}
	// Yet re-creating the very same mapping is refused.
	if st := captureStatus(t, "A2-214-create-fundsource-retyped"); st != 403 {
		t.Errorf("A2-214-create-fundsource-retyped status %d, want 403", st)
	}
}

// TestPostedAccountSnapshotCarriesClassification is trap 3's port-side answer:
// A1 can embed the classification on the entry, so posted history cannot
// re-render when somebody retypes the account.
func TestPostedAccountSnapshotCarriesClassification(t *testing.T) {
	before := GLAccount{ID: 2, GLCode: "10100", Name: "Fund Source", Classification: ClassificationAsset, Usage: UsageDetail}
	snap := before.Snapshot()

	after := before
	after.Classification = ClassificationIncome // exactly what A2-111 did

	if snap.Classification != ClassificationAsset {
		t.Errorf("the snapshot re-rendered with the account: %v", snap.Classification)
	}
	if after.Snapshot().Classification != ClassificationIncome {
		t.Error("a snapshot taken after the retype should read INCOME")
	}
	if snap.AccountID != 2 || snap.GLCode != "10100" {
		t.Errorf("snapshot identity wrong: %+v", snap)
	}
}

// TestGLAccountRefusalCodesMatchTheCaptures grades the refusal surface against
// the oracle's own globalisation codes, including the two where the OBSERVATION
// contradicts the source reading.
func TestGLAccountRefusalCodesMatchTheCaptures(t *testing.T) {
	cases := []struct {
		capture string
		want    *LedgerError
		note    string
	}{
		{"A2-bad-040-dup-glcode", ErrGLAccountDataIntegrity,
			"a duplicate glCode does NOT produce error.msg.glaccount.glcode.duplicate on this instance: the Liquibase unique index is unnamed, so the substring match at :242 never fires"},
		{"A2-bad-045-no-usage", ErrGLAccountDataIntegrity,
			"the create validator does not require `usage`, so a missing one reaches the NOT NULL column"},
		{"A2-bad-049-parent-missing", ErrGLAccountNotFound, ""},
		{"A2-125-delete-not-found", ErrGLAccountNotFound, ""},
		{"A2-112-update-disable-mapped", ErrGLAccountAttachedToProduct, ""},
		{"A2-120-delete-has-children", ErrGLAccountDeleteHasChildren, ""},
		{"A2-121-delete-product-mapped", ErrGLAccountDeleteProductMapping, ""},
		{"A2-122-delete-three-guards", ErrGLAccountDeleteTransactionsLogged,
			"the journal-entries guard runs BEFORE the product-mapping guard, and account 2 trips both"},
		{"A2-124-delete-clean-success", ErrDataIntegrity,
			"deleteGLAccount has no financial-activity guard, so the FK refuses it with the PLATFORM generic code, not the GL-account one"},
		{"A2-fin-102-duplicate-activity", ErrFinancialActivityAccountDuplicate, ""},
		{"A2-fin-103-wrong-account-type", ErrFinancialActivityAccountInvalid, ""},
		{"A2-fin-105-missing-account", ErrGLAccountNotFound, ""},
		{"A2-092-chargeoff-loan1-unmapped", ErrProductToGLAccountMappingNotFound, ""},
		{"A2-224-chargeoff-unmapped", ErrProductToGLAccountMappingNotFound, ""},
		{"A2-225-goodwillcredit-unmapped", ErrProductToGLAccountMappingNotFound, ""},
		{"A2-086-disburse-loan3-dupchannel", ErrNonUniqueMappingResult,
			"a duplicate acc_product_mapping row is a query-time refusal, never a take-the-first"},
	}
	for _, c := range cases {
		var body struct {
			Status string `json:"httpStatusCode"`
			Errors []struct {
				Code string `json:"userMessageGlobalisationCode"`
			} `json:"errors"`
		}
		decodeCapture(t, c.capture, &body)
		if len(body.Errors) == 0 {
			t.Errorf("%s: capture carries no errors array", c.capture)
			continue
		}
		if body.Errors[0].Code != c.want.Code {
			t.Errorf("%s: oracle code %q, port sentinel %q. %s",
				c.capture, body.Errors[0].Code, c.want.Code, c.note)
		}
		if st := captureStatus(t, c.capture); st != c.want.HTTPStatus {
			t.Errorf("%s: oracle HTTP %d, port sentinel HTTP %d", c.capture, st, c.want.HTTPStatus)
		}
		if fmt.Sprint(body.Status) != fmt.Sprint(c.want.HTTPStatus) {
			t.Errorf("%s: body httpStatusCode %q disagrees with the sentinel %d",
				c.capture, body.Status, c.want.HTTPStatus)
		}
	}
}

// TestValidationRefusalsAreTheValidationFamily checks that every A2-bad capture
// that is a 400 carries the validation family, so the port's ErrValidation is
// pointed at the right set.
func TestValidationRefusalsAreTheValidationFamily(t *testing.T) {
	for _, id := range []string{
		"A2-bad-041-empty-body", "A2-bad-042-no-name", "A2-bad-043-no-glcode",
		"A2-bad-044-no-type", "A2-bad-046-type-9", "A2-bad-047-type-0",
		"A2-bad-048-usage-5", "A2-bad-051-glcode-too-long", "A2-bad-052-name-too-long",
		"A2-bad-054-blank-name", "A2-bad-055-blank-glcode",
		"A2-110-update-header-to-detail", "A2-113-update-nomanual",
		"A2-141-update-usage-only", "A2-142-update-manual-only", "A2-143-update-usage-same-value",
		"A2-fin-104-unknown-activity",
	} {
		if st := captureStatus(t, id); st != ErrValidation.HTTPStatus {
			t.Errorf("%s: HTTP %d, want %d", id, st, ErrValidation.HTTPStatus)
		}
		var body struct {
			Code string `json:"userMessageGlobalisationCode"`
		}
		decodeCapture(t, id, &body)
		if body.Code != ErrValidation.Code {
			t.Errorf("%s: top-level code %q, want %q", id, body.Code, ErrValidation.Code)
		}
	}
}

// TestTheTypeAndUsageRangesMatchTheOracleMessages grades the validator bounds
// this port hard-codes against the oracle's own refusal text.
func TestTheTypeAndUsageRangesMatchTheOracleMessages(t *testing.T) {
	type errBody struct {
		Errors []struct {
			Dev string `json:"developerMessage"`
		} `json:"errors"`
	}
	var typeErr errBody
	decodeCapture(t, "A2-bad-046-type-9", &typeErr)
	want := fmt.Sprintf("The parameter `type` must be between %d and %d.", ClassificationMinValue, ClassificationMaxValue)
	if typeErr.Errors[0].Dev != want {
		t.Errorf("type range message %q, port would render %q", typeErr.Errors[0].Dev, want)
	}
	var usageErr errBody
	decodeCapture(t, "A2-bad-048-usage-5", &usageErr)
	want = fmt.Sprintf("The parameter `usage` must be between %d and %d.", UsageMinValue, UsageMaxValue)
	if usageErr.Errors[0].Dev != want {
		t.Errorf("usage range message %q, port would render %q", usageErr.Errors[0].Dev, want)
	}
}
