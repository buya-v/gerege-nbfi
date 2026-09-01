package cob

import "context"

// Step is the unit of Close-of-Business work applied to a single input item.
//
// The type parameter T is the item being processed (in Fineract this is an
// entity extending AbstractPersistableCustom<Long>, e.g. a Loan). A step
// receives an item, mutates or refetches it, and returns the result that is
// passed to the next step in the pipeline.
//
// This is the Go equivalent of org.apache.fineract.cob.COBBusinessStep<S>.
type Step[T any] interface {
	// Execute runs the business logic for this step.
	Execute(ctx context.Context, input T) (T, error)
	// EnumStyledName returns the stable machine identifier used in
	// configuration, e.g. "APPLY_CHARGE_TO_OVERDUE_LOANS".
	EnumStyledName() string
	// HumanReadableName returns the display name surfaced to operators.
	HumanReadableName() string
}

// StepConfig is a single configured business step with its execution order.
//
// It mirrors org.apache.fineract.cob.data.BusinessStepNameAndOrder, which is
// the unit stored in the m_batch_business_steps table and rendered by the
// business-step configuration API as
//
//	{"businessSteps":[{"stepName":"...","stepOrder":1}, ...]}
type StepConfig struct {
	StepName  string `json:"stepName"`
	StepOrder int64  `json:"stepOrder"`
}

// Config is the wire representation of a job's ordered business-step list.
//
// It corresponds to the JSON payload consumed by BusinessStepConfiguration and
// produced by COBBusinessStepServiceImpl.getCOBBusinessSteps for a single job.
type Config struct {
	BusinessSteps []StepConfig `json:"businessSteps"`
}
