package savings

import (
	"os"
	"strconv"
)

// Config carries the runtime facts that gate savings/deposit behaviour.
//
// The single field is the activation flag. It is OFF by default and must
// remain OFF in any NBFI deployment: the ratified tenant licence is NBFI
// (ББСБ), and deposit-taking activation is a hard `user` licensing gate, not an
// engineering default. Porting this code is in scope; enabling it is not.
//
// The zero value is safe: Config{} is a disabled configuration, not a
// half-initialised one. DefaultConfig returns exactly that.
type Config struct {
	// Enabled gates every deposit-taking code path. When false (the default)
	// this package exposes no deposit endpoint and performs no deposit-taking
	// behaviour. There is deliberately no other field: anything else a savings
	// account needs is data, not a runtime gate.
	Enabled bool
}

// DefaultConfig returns the disabled configuration. This is the only value an
// NBFI deployment may use until Buyan settles the licensing position.
func DefaultConfig() Config {
	return Config{}
}

// EnvName is the environment variable that may enable savings behaviour. It is
// spelled out so that a deployment that sets it is an explicit, auditable act.
const EnvName = "GERE_SAVINGS_ENABLED"

// ConfigFromEnv reads the activation flag from EnvName. Absent, empty or
// unparseable input is disabled, so the default is OFF and a typo cannot
// silently switch deposit-taking on.
func ConfigFromEnv() Config {
	return Config{Enabled: envBool(EnvName, false)}
}

func envBool(key string, fallback bool) bool {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	b, err := strconv.ParseBool(v)
	if err != nil {
		return fallback
	}
	return b
}
