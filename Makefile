.PHONY: install dev test test-record lint

# Install for users
install:
	pip3 install .

# Install for development (editable + test deps)
dev:
	pip3 install -e ".[dev]"

# Run tests using recorded API responses (no API key needed)
test:
	python3 -m pytest tests/ -v

# Run tests against live API and record responses for replay
# Requires ANTHROPIC_API_KEY
test-record:
	python3 -m pytest tests/ -v --record-mode=rewrite

# Quick smoke test with a single image (requires API key or --provider cli)
smoke:
	digitize run tests/fixtures/sample.png --dry-run --skip-qa
