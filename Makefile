.PHONY: all build test lint fmt clean check fix help

# Default target
all: check

# Build the project
build:
	cargo build

# Build for release
release:
	cargo build --release

# Run tests
test:
	cargo test --all-features

# Run tests with output
test-verbose:
	cargo test --all-features -- --nocapture

# Run clippy (linting)
lint:
	cargo clippy --all-features --tests --examples -- -D warnings

# Run rustfmt (formatting check)
fmt-check:
	cargo fmt -- --check

# Format code
fmt:
	cargo fmt

# Run all checks (format, lint, test)
check: fmt-check lint test

# Fix common issues automatically
fix:
	cargo fmt
	cargo clippy --fix --allow-dirty --allow-staged
	cargo fix --allow-dirty --allow-staged

# Clean build artifacts
clean:
	cargo clean

# Run benchmarks
bench:
	cargo bench

# Generate documentation
doc:
	cargo doc --no-deps --open

# Update dependencies
update:
	cargo update

# Security audit
audit:
	cargo audit

# Install development tools
install-tools:
	rustup component add clippy rustfmt
	cargo install cargo-audit cargo-watch cargo-expand

# Watch for changes and run checks
watch:
	cargo watch -x check -x test

# Help
help:
	@echo "Available targets:"
	@echo "  all          - Run all checks (default)"
	@echo "  build        - Build the project"
	@echo "  release      - Build for release"
	@echo "  test         - Run tests"
	@echo "  test-verbose - Run tests with output"
	@echo "  lint         - Run clippy linting"
	@echo "  fmt-check    - Check code formatting"
	@echo "  fmt          - Format code"
	@echo "  check        - Run all checks (format, lint, test)"
	@echo "  fix          - Fix common issues automatically"
	@echo "  clean        - Clean build artifacts"
	@echo "  bench        - Run benchmarks"
	@echo "  doc          - Generate and open documentation"
	@echo "  update       - Update dependencies"
	@echo "  audit        - Security audit"
	@echo "  install-tools- Install development tools"
	@echo "  watch        - Watch for changes and run checks"
	@echo "  help         - Show this help message"