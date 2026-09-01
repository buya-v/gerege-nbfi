package postgres

import "testing"

func TestPlanMigrationsOrdersAndSkipsApplied(t *testing.T) {
	in := []Migration{
		{Version: 30, Name: "third"},
		{Version: 10, Name: "first"},
		{Version: 20, Name: "second"},
	}
	got := planMigrations(in, 0)
	if len(got) != 3 || got[0].Version != 10 || got[1].Version != 20 || got[2].Version != 30 {
		t.Fatalf("planMigrations(..., 0) = %v, want versions [10 20 30]", versions(got))
	}

	got = planMigrations(in, 20)
	if len(got) != 1 || got[0].Version != 30 {
		t.Fatalf("planMigrations(..., 20) = %v, want only version 30 pending", versions(got))
	}

	got = planMigrations(in, 30)
	if len(got) != 0 {
		t.Fatalf("planMigrations(..., 30) = %v, want nothing pending (idempotent)", versions(got))
	}
}

func TestPlanMigrationsDoesNotMutateInput(t *testing.T) {
	in := []Migration{
		{Version: 20, Name: "b"},
		{Version: 10, Name: "a"},
	}
	_ = planMigrations(in, 0)
	if in[0].Version != 20 || in[1].Version != 10 {
		t.Fatalf("planMigrations mutated its input: %v", versions(in))
	}
}

func versions(ms []Migration) []int {
	out := make([]int, len(ms))
	for i, m := range ms {
		out[i] = m.Version
	}
	return out
}
