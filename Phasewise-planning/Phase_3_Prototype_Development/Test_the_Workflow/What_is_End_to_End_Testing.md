# End-to-End Testing

## MVP Test Case
```bash
python run.py --topic "SEBI Small and Medium REITs India 2024" --dry-run
```

Add a `--dry-run` flag that uses mocked agent responses (saved in `tests/fixtures/`) instead of real API calls. This lets you test the orchestrator wiring for free.

## What to Verify
1. Job is created in SQLite with correct status
2. Each agent's input is correctly transformed from previous agent's output
3. Gate 1 pauses execution and waits for operator input
4. After `--approve`, pipeline resumes from the correct stage
5. PDF is generated and saved to OUTPUT_DIR
6. Gumroad product is created in unpublished state
7. Gate 3 pauses before publishing

## Test Fixtures
Save real API response samples to `tests/fixtures/` after your first real run. Future test runs use these fixtures instead of calling APIs.
