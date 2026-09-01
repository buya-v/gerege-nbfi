package loan

import (
	"reflect"
	"testing"
)

func TestWriteOffOutstanding(t *testing.T) {
	t.Run("empty schedule", func(t *testing.T) {
		if got := WriteOffOutstanding(nil); got != (Allocation{}) {
			t.Errorf("WriteOffOutstanding(nil) = %+v, want zero", got)
		}
	})

	t.Run("obligations met installments are skipped", func(t *testing.T) {
		in := []WriteOffInstallment{
			{PrincipalOutstanding: 100, InterestOutstanding: 10, FeeOutstanding: 5, PenaltyOutstanding: 1, ObligationsMet: true},
			{PrincipalOutstanding: 200, InterestOutstanding: 20, FeeOutstanding: 10, PenaltyOutstanding: 2, ObligationsMet: true},
		}
		if got := WriteOffOutstanding(in); got != (Allocation{}) {
			t.Errorf("WriteOffOutstanding() = %+v, want zero", got)
		}
	})

	t.Run("aggregates outstanding across buckets", func(t *testing.T) {
		in := []WriteOffInstallment{
			{PrincipalOutstanding: 100, InterestOutstanding: 10, FeeOutstanding: 5, PenaltyOutstanding: 1},
			{PrincipalOutstanding: 200, InterestOutstanding: 20, FeeOutstanding: 10, PenaltyOutstanding: 2, ObligationsMet: true},
			{PrincipalOutstanding: 400, InterestOutstanding: 40, FeeOutstanding: 20, PenaltyOutstanding: 4},
		}
		want := Allocation{Principal: 500, Interest: 50, Fee: 25, Penalty: 5}
		if got := WriteOffOutstanding(in); !reflect.DeepEqual(got, want) {
			t.Errorf("WriteOffOutstanding() = %+v, want %+v", got, want)
		}
	})
}
