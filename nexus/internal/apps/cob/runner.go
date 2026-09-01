package cob

import (
	"context"
	"errors"
	"fmt"
	"sort"
)

// Sentinel errors returned by the orchestration layer. Concrete step
// implementations return their own wrapped errors, which are preserved via
// fmt.Errorf with %w in Run.
var (
	// ErrEmptyExecution reports a run with no configured steps.
	ErrEmptyExecution = errors.New("cob: execution map is empty")
	// ErrUnknownStep reports a configured step name with no registered step.
	ErrUnknownStep = errors.New("cob: unknown business step")
	// ErrDuplicateOrder reports two steps sharing a step order, which the
	// Fineract TreeMap silently collapses. We reject it explicitly.
	ErrDuplicateOrder = errors.New("cob: duplicate business step order")
)

// Run executes an ordered slice of steps against item, threading the result of
// each step into the next. It ports the core loop of
// COBBusinessStepServiceImpl.run, without the Spring-bean lookup (steps are
// already resolved by Order) and without the reloader/event-recording
// side-effects, which are application-layer concerns.
//
// The step slice must already be in execution order; use Order to derive it
// from a StepConfig list.
func Run[T any](ctx context.Context, item T, steps []Step[T]) (T, error) {
	if len(steps) == 0 {
		return item, ErrEmptyExecution
	}

	var err error
	current := item
	for _, step := range steps {
		current, err = step.Execute(ctx, current)
		if err != nil {
			return current, fmt.Errorf("cob: error during business step %q: %w", step.EnumStyledName(), err)
		}
	}
	return current, nil
}

// Order resolves a configured step list against a registry of named steps and
// returns the steps sorted by ascending step order.
//
// It reproduces COBBusinessStepServiceImpl.getCOBBusinessSteps (filtering the
// registry to the configured names) followed by
// BusinessStepNameAndOrder.getBusinessStepMap (sorting by step order).
func Order[T any](registry map[string]Step[T], config []StepConfig) ([]Step[T], error) {
	if len(config) == 0 {
		return nil, nil
	}

	type ordered struct {
		order int64
		step  Step[T]
	}
	resolved := make([]ordered, 0, len(config))
	seen := make(map[int64]struct{}, len(config))

	for _, c := range config {
		step, ok := registry[c.StepName]
		if !ok {
			return nil, fmt.Errorf("%w: %s", ErrUnknownStep, c.StepName)
		}
		if _, dup := seen[c.StepOrder]; dup {
			return nil, fmt.Errorf("%w: %d (%s)", ErrDuplicateOrder, c.StepOrder, c.StepName)
		}
		seen[c.StepOrder] = struct{}{}
		resolved = append(resolved, ordered{order: c.StepOrder, step: step})
	}

	sort.SliceStable(resolved, func(i, j int) bool {
		return resolved[i].order < resolved[j].order
	})

	steps := make([]Step[T], len(resolved))
	for i, r := range resolved {
		steps[i] = r.step
	}
	return steps, nil
}
