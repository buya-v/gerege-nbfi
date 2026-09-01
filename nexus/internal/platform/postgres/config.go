// Package postgres is the port's only PostgreSQL access layer. It owns
// connection/pool management, the integer-minor-unit money codec and the
// schema migration runner. Repository implementations in application packages
// depend on this package, never on a raw driver, so that the "one permitted
// database, one permitted driver" rule (pgx/v5) is enforced at the import
// graph rather than by convention.
package postgres

import (
	"context"
	"fmt"
	"net"
	"net/url"
	"os"
	"strconv"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Config carries the connection facts for the Go module's own PostgreSQL
// database. It is plain data: no offset, credential or hostname is hard-coded
// in this package, and the zero value is useless until the caller supplies the
// facts (ConfigFromEnv is the convenient non-hard-coded source).
type Config struct {
	Host     string
	Port     uint16
	User     string
	Password string
	Database string
	SSLMode  string
}

// ConfigFromEnv reads the standard PG* environment variables, falling back to
// localhost defaults only for the host and port. User, password and database
// have no default: a database connection that works by accident is a
// configuration bug.
func ConfigFromEnv() Config {
	return Config{
		Host:     envOr("PGHOST", "localhost"),
		Port:     envPort("PGPORT", 5432),
		User:     os.Getenv("PGUSER"),
		Password: os.Getenv("PGPASSWORD"),
		Database: os.Getenv("PGDATABASE"),
		SSLMode:  envOr("PGSSLMODE", "disable"),
	}
}

// DSN renders the configuration as a pgx connection string. It uses the URL
// form so that user and password are percent-encoded rather than escaped by
// hand, and it never exposes the password in the returned string's
// documentation surface.
func (c Config) DSN() string {
	host := c.Host
	if host == "" {
		host = "localhost"
	}
	port := c.Port
	if port == 0 {
		port = 5432
	}
	sslmode := c.SSLMode
	if sslmode == "" {
		sslmode = "disable"
	}

	u := url.URL{
		Scheme: "postgres",
		User:   url.UserPassword(c.User, c.Password),
		Host:   net.JoinHostPort(host, strconv.FormatUint(uint64(port), 10)),
		Path:   "/" + c.Database,
	}
	q := u.Query()
	q.Set("sslmode", sslmode)
	u.RawQuery = q.Encode()
	return u.String()
}

// NewPool opens a pgx connection pool and verifies it with a ping so a bad DSN
// fails here rather than on the first query. The returned pool is owned by the
// caller and must be closed.
func NewPool(ctx context.Context, cfg Config) (*pgxpool.Pool, error) {
	pool, err := pgxpool.New(ctx, cfg.DSN())
	if err != nil {
		return nil, fmt.Errorf("postgres: open pool: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("postgres: ping: %w", err)
	}
	return pool, nil
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func envPort(key string, fallback uint16) uint16 {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	n, err := strconv.ParseUint(v, 10, 16)
	if err != nil {
		return fallback
	}
	return uint16(n)
}
