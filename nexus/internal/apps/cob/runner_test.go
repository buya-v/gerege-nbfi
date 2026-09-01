package cob

import (
	"context"
	"errors"
	"testing"
)

// recordStep is a test Step that appends its name to a shared slice so the
// caller can assert execution order and value threading.
type recordStep struct {
	name string
	rec  *[]string
	fail error
}

func (s *recordStep) Execute(_ context.Context, in int) (int, error) {
	*s.rec = append(*s.rec, s.name)
	if s.fail != nil {
		return in, s.fail
	}
	return in + 1, nil
}

func (s *recordStep) EnumStyledName() string { return s.name }

func (s *recordStep) HumanReadableName() string { return s.name }

func TestRunEmptyExecution(t *testing.T) {
	_, err := Run[int](context.Background(), 0, nil)
	if !errors.Is(err, ErrEmptyExecution) {
		t.Fatalf("Run() error = %v, want ErrEmptyExecution", err)
	}
}

func TestRunThreadsValuesInOrder(t *testing.T) {
	var rec []string
	steps := []Step[int]{
		&recordStep{name: "one", rec: &rec},
		&recordStep{name: "two", rec: &rec},
		&recordStep{name: "three", rec: &rec},
	}

	out, err := Run(context.Background(), 0, steps)
	if err != nil {
		t.Fatalf("Run() unexpected error: %v", err)
	}
	if out != 3 {
		t.Fatalf("Run() output = %d, want 3", out)
	}
	want := []string{"one", "two", "three"}
	if len(rec) != len(want) {
		t.Fatalf("executed %v, want %v", rec, want)
	}
	for i := range want {
		if rec[i] != want[i] {
			t.Fatalf("executed %v, want %v", rec, want)
		}
	}
}

func TestRunStopsOnErrorAndWraps(t *testing.T) {
	boom := errors.New("boom")
	var rec []string
	steps := []Step[int]{
		&recordStep{name: "one", rec: &rec},
		&recordStep{name: "two", rec: &rec, fail: boom},
		&recordStep{name: "three", rec: &rec},
	}

	out, err := Run(context.Background(), 0, steps)
	if err == nil {
		t.Fatal("Run() expected error, got nil")
	}
	if !errors.Is(err, boom) {
		t.Fatalf("Run() error = %v, want wrapped boom", err)
	}
	if out != 1 {
		t.Fatalf("Run() output = %d, want 1 (item unchanged by failing step)", out)
	}
	want := []string{"one", "two"}
	if len(rec) != len(want) {
		t.Fatalf("executed %v, want %v", rec, want)
	}
}

func TestOrderResolvesAndSorts(t *testing.T) {
	registry := map[string]Step[int]{
		"THIRD":  &recordStep{name: "THIRD"},
		"FIRST":  &recordStep{name: "FIRST"},
		"SECOND": &recordStep{name: "SECOND"},
	}
	config := []StepConfig{
		{StepName: "THIRD", StepOrder: 3},
		{StepName: "FIRST", StepOrder: 1},
		{StepName: "SECOND", StepOrder: 2},
	}

	steps, err := Order(registry, config)
	if err != nil {
		t.Fatalf("Order() unexpected error: %v", err)
	}
	want := []string{"FIRST", "SECOND", "THIRD"}
	if len(steps) != len(want) {
		t.Fatalf("Order() returned %d steps, want %d", len(steps), len(want))
	}
	for i := range want {
		if steps[i].EnumStyledName() != want[i] {
			t.Fatalf("Order()[%d] = %s, want %s", i, steps[i].EnumStyledName(), want[i])
		}
	}
}

func TestOrderUnknownStep(t *testing.T) {
	registry := map[string]Step[int]{}
	_, err := Order(registry, []StepConfig{{StepName: "MISSING", StepOrder: 1}})
	if !errors.Is(err, ErrUnknownStep) {
		t.Fatalf("Order() error = %v, want ErrUnknownStep", err)
	}
}

func TestOrderDuplicateOrder(t *testing.T) {
	registry := map[string]Step[int]{
		"A": &recordStep{name: "A"},
		"B": &recordStep{name: "B"},
	}
	_, err := Order(registry, []StepConfig{
		{StepName: "A", StepOrder: 1},
		{StepName: "B", StepOrder: 1},
	})
	if !errors.Is(err, ErrDuplicateOrder) {
		t.Fatalf("Order() error = %v, want ErrDuplicateOrder", err)
	}
}

func TestDefaultLoanConfig(t *testing.T) {
	cfg := DefaultLoanConfig()
	want := []struct {
		name  string
		order int64
	}{
		{StepApplyChargeToOverdueLoans, 1},
		{StepLoanDelinquencyClassification, 2},
		{StepCheckLoanRepaymentDue, 3},
		{StepCheckLoanRepaymentOverdue, 4},
		{StepUpdateLoanArrearsAging, 5},
		{StepAddPeriodicAccrualEntries, 6},
	}
	if len(cfg.BusinessSteps) != len(want) {
		t.Fatalf("DefaultLoanConfig() has %d steps, want %d", len(cfg.BusinessSteps), len(want))
	}
	for i, w := range want {
		if cfg.BusinessSteps[i].StepName != w.name || cfg.BusinessSteps[i].StepOrder != w.order {
			t.Fatalf("step[%d] = %+v, want {%s %d}", i, cfg.BusinessSteps[i], w.name, w.order)
		}
	}
}
