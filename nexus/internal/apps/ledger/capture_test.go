package ledger

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

// The capture loader.
//
// These tests are graded against BYTES CAPTURED FROM THE REFERENCE ORACLE and
// committed under .softhouse/capture/tierA-a2/. They are not fixtures written
// by this worker: every file named here was produced by task A2-3/A2-5/A2-7
// against the live Fineract instance and is covered by that directory's
// MANIFEST.sha256.
//
// TWO RULES THIS FILE ENFORCES ON ITSELF.
//
// 1. NO FLOATING POINT, ANYWHERE, INCLUDING THE JSON DECODER. encoding/json
//    decodes every JSON number into a float64 by default, so a test that
//    unmarshalled an amount into interface{} would silently route money through
//    a binary float — the exact defect P-25 records, one remove from money code.
//    Every decoder here calls UseNumber(), and every monetary value goes
//    through MinorUnitsFromDecimalText on the literal text.
//
// 2. A MISSING CAPTURE IS A FAILURE, NOT A SKIP. A t.Skip on a missing evidence
//    file converts "not checked" into a green run, which is P-22's vacuous
//    guard. If the capture directory is not found these tests fail loudly.

// repoRoot walks up from the test's working directory looking for the capture
// directory. It fails the test rather than skipping.
func repoRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, ".softhouse", "capture", "tierA-a2", "out")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatalf("could not find .softhouse/capture/tierA-a2/out above %q. "+
				"These tests grade the port against captured reference-oracle bytes; "+
				"without them nothing is graded, so this is a failure and not a skip.", dir)
		}
		dir = parent
	}
}

func captureDir(t *testing.T) string {
	t.Helper()
	return filepath.Join(repoRoot(t), ".softhouse", "capture", "tierA-a2", "out")
}

// captureBytes reads one capture file.
func captureBytes(t *testing.T, name string) []byte {
	t.Helper()
	p := filepath.Join(captureDir(t), name)
	b, err := os.ReadFile(p)
	if err != nil {
		t.Fatalf("reading capture %s: %v", name, err)
	}
	return b
}

// captureStatus reads the HTTP status recorded alongside a capture.
func captureStatus(t *testing.T, id string) int {
	t.Helper()
	s := strings.TrimSpace(string(captureBytes(t, id+".status")))
	n, err := strconv.Atoi(s)
	if err != nil {
		t.Fatalf("capture %s: unparseable status %q: %v", id, s, err)
	}
	return n
}

// decodeCapture decodes a capture's JSON body into v with UseNumber set, so no
// JSON number is ever routed through a float64.
func decodeCapture(t *testing.T, id string, v any) {
	t.Helper()
	dec := json.NewDecoder(bytes.NewReader(captureBytes(t, id+".json")))
	dec.UseNumber()
	if err := dec.Decode(v); err != nil {
		t.Fatalf("decoding capture %s: %v", id, err)
	}
}

// ---------------------------------------------------------------------------
// psql dump parsing
// ---------------------------------------------------------------------------

// psqlTable is one bordered table from a psql capture.
type psqlTable struct {
	columns []string
	rows    []map[string]string
}

func (tb psqlTable) get(row int, col string) string { return tb.rows[row][col] }

// parsePsqlTables splits a psql capture into its named sections and parses each
// bordered table. Section names come from the `--- name ---` lines the capture
// scripts emit; an unnamed leading table is keyed "".
func parsePsqlTables(t *testing.T, name string) map[string]psqlTable {
	t.Helper()
	out := map[string]psqlTable{}
	section := ""
	var pending []string
	flush := func() {
		if len(pending) == 0 {
			return
		}
		if tb, ok := parseBorderedTable(pending); ok {
			out[section] = tb
		}
		pending = nil
	}
	for _, line := range strings.Split(string(captureBytes(t, name)), "\n") {
		trimmed := strings.TrimSpace(line)
		if strings.HasPrefix(trimmed, "---") && strings.HasSuffix(trimmed, "---") && !strings.HasPrefix(trimmed, "+") {
			flush()
			section = strings.TrimSpace(strings.Trim(trimmed, "-"))
			continue
		}
		pending = append(pending, line)
	}
	flush()
	if len(out) == 0 {
		t.Fatalf("capture %s: no psql tables parsed", name)
	}
	return out
}

func parseBorderedTable(lines []string) (psqlTable, bool) {
	var tb psqlTable
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if !strings.HasPrefix(trimmed, "|") || !strings.HasSuffix(trimmed, "|") {
			continue
		}
		cells := splitRow(trimmed)
		if tb.columns == nil {
			tb.columns = cells
			continue
		}
		if len(cells) != len(tb.columns) {
			continue
		}
		row := make(map[string]string, len(cells))
		for i, c := range cells {
			row[tb.columns[i]] = c
		}
		tb.rows = append(tb.rows, row)
	}
	return tb, tb.columns != nil
}

func splitRow(line string) []string {
	inner := strings.TrimSuffix(strings.TrimPrefix(line, "|"), "|")
	parts := strings.Split(inner, "|")
	out := make([]string, len(parts))
	for i, p := range parts {
		out[i] = strings.TrimSpace(p)
	}
	return out
}

func mustInt64(t *testing.T, s string) int64 {
	t.Helper()
	n, err := strconv.ParseInt(strings.TrimSpace(s), 10, 64)
	if err != nil {
		t.Fatalf("not an int64: %q: %v", s, err)
	}
	return n
}

func optInt64(t *testing.T, s string) *int64 {
	t.Helper()
	if strings.TrimSpace(s) == "" {
		return nil
	}
	n := mustInt64(t, s)
	return &n
}

func mustInt32(t *testing.T, s string) int32 {
	t.Helper()
	return int32(mustInt64(t, s))
}

func optInt32(t *testing.T, s string) *int32 {
	t.Helper()
	if strings.TrimSpace(s) == "" {
		return nil
	}
	n := mustInt32(t, s)
	return &n
}

// ---------------------------------------------------------------------------
// the tenant state, loaded from the captures
// ---------------------------------------------------------------------------

// loadChart builds the GL account model from A2-150-db-final-state.txt, which
// is the AUTHORITATIVE chart dump.
//
// It is deliberately NOT A2-019-db-glaccount-rows.txt: that file is a MID-RUN
// snapshot taken before run-020-accounts.sh created fourteen more accounts, it
// reads exactly like a final one, and reading it as the current state is what
// produced the driver's false "four accounts, all ASSET" claim that gate G-9
// had to retract. P-32, with a live instance in this very directory.
func loadChart(t *testing.T) []GLAccount {
	t.Helper()
	tables := parsePsqlTables(t, "A2-150-db-final-state.txt")
	tb, ok := tables["acc_gl_account"]
	if !ok {
		t.Fatal("A2-150-db-final-state.txt: no acc_gl_account section")
	}
	if len(tb.rows) != 21 {
		t.Fatalf("A2-150-db-final-state.txt: expected 21 acc_gl_account rows, parsed %d", len(tb.rows))
	}
	out := make([]GLAccount, 0, len(tb.rows))
	for i := range tb.rows {
		classification, ok := ClassificationFromStoredValue(mustInt32(t, tb.get(i, "classification_enum")))
		if !ok {
			t.Fatalf("row %d: classification_enum %q not decodable", i, tb.get(i, "classification_enum"))
		}
		usage, ok := UsageFromStoredValue(mustInt32(t, tb.get(i, "account_usage")))
		if !ok {
			t.Fatalf("row %d: account_usage %q not decodable", i, tb.get(i, "account_usage"))
		}
		out = append(out, GLAccount{
			ID:                   mustInt64(t, tb.get(i, "id")),
			ParentID:             optInt64(t, tb.get(i, "parent_id")),
			Hierarchy:            strings.TrimSpace(tb.get(i, "hierarchy")),
			Name:                 tb.get(i, "name"),
			GLCode:               tb.get(i, "gl_code"),
			Disabled:             tb.get(i, "disabled") == "t",
			ManualEntriesAllowed: tb.get(i, "manual_journal_entries_allowed") == "t",
			Classification:       classification,
			Usage:                usage,
		})
	}
	return out
}

// loadMappingRows builds acc_product_mapping from
// A2-072-db-product-mapping-rows.txt.
//
// ONLY the mapping columns are taken from this file. Its gl_code / gl_name /
// classification_enum columns are a JOIN taken at capture time and they are
// STALE: A2-111 later retyped GL account 2 from ASSET to INCOME, so this dump
// still shows classification_enum 1 for it while A2-150 shows 4. Account
// attributes come from loadChart; only the (product, type, slot, payment_type,
// charge, account_id) tuple comes from here. Two committed artefacts describing
// the same entity at different times is P-32's shape, and the defence is to
// name which file is authoritative for which column.
func loadMappingRows(t *testing.T) []MappingRow {
	t.Helper()
	tables := parsePsqlTables(t, "A2-072-db-product-mapping-rows.txt")
	tb, ok := tables[""]
	if !ok {
		t.Fatal("A2-072-db-product-mapping-rows.txt: no table parsed")
	}
	if len(tb.rows) != 56 {
		t.Fatalf("A2-072: expected 56 rows, parsed %d", len(tb.rows))
	}
	out := make([]MappingRow, 0, len(tb.rows))
	for i := range tb.rows {
		productID := mustInt64(t, tb.get(i, "product_id"))
		productType := mustInt32(t, tb.get(i, "product_type"))
		fat := mustInt32(t, tb.get(i, "financial_account_type"))
		accountID := mustInt64(t, tb.get(i, "gl_account_id"))
		out = append(out, MappingRow{
			ID:                   int64(i + 1),
			GLAccountID:          &accountID,
			ProductID:            &productID,
			ProductType:          &productType,
			FinancialAccountType: &fat,
			PaymentTypeID:        optInt64(t, tb.get(i, "payment_type")),
			ChargeID:             optInt64(t, tb.get(i, "charge_id")),
		})
	}
	return out
}

// loadFinancialActivities builds acc_gl_financial_activity_account from
// A2-150-db-final-state.txt.
func loadFinancialActivities(t *testing.T) []FinancialActivityAccountRow {
	t.Helper()
	tables := parsePsqlTables(t, "A2-150-db-final-state.txt")
	tb, ok := tables["acc_gl_financial_activity_account"]
	if !ok {
		t.Fatal("A2-150-db-final-state.txt: no acc_gl_financial_activity_account section")
	}
	out := make([]FinancialActivityAccountRow, 0, len(tb.rows))
	for i := range tb.rows {
		v := mustInt32(t, tb.get(i, "financial_activity_type"))
		activity, ok := FinancialActivityFromValue(v)
		if !ok {
			t.Fatalf("financial_activity_type %d not decodable", v)
		}
		out = append(out, FinancialActivityAccountRow{
			ID:          mustInt64(t, tb.get(i, "id")),
			Activity:    activity,
			GLAccountID: mustInt64(t, tb.get(i, "gl_account_id")),
		})
	}
	return out
}

// tenant assembles the whole captured state into a Resolver.
func tenant(t *testing.T) (*Resolver, *InMemoryAccountStore, *InMemoryMappingStore) {
	t.Helper()
	accounts := &InMemoryAccountStore{Accounts: loadChart(t)}
	mappings := &InMemoryMappingStore{Rows: loadMappingRows(t)}
	activities := &InMemoryFinancialActivityStore{Rows: loadFinancialActivities(t)}
	return &Resolver{
		Mappings:            mappings,
		FinancialActivities: activities,
		Accounts:            accounts,
	}, accounts, mappings
}

func accountByID(t *testing.T, accounts []GLAccount, id int64) GLAccount {
	t.Helper()
	for _, a := range accounts {
		if a.ID == id {
			return a
		}
	}
	t.Fatalf("no GL account %d in the captured chart", id)
	return GLAccount{}
}
