# Agent Instructions

### For AI Agents

When working on this codebase:

1. **Always use `uv`** instead of `pip` or `python -m venv`
2. **Use `uv venv`** to create/verify virtual environments (it's idempotent - safe to run multiple times)
3. **Use `uv run`** to execute Python scripts (no activation needed)
4. **Use the Makefile** targets (`make install`, `make run`, etc.) when available

### Examples

```bash
# Setup new environment
uv venv 

# Run tests
uv run pytest

# Run the example
uv run example.py

# Or use make targets
make install
make run
make test
```

## Project Conventions

- Dependencies are managed in `requirements.txt`
- Virtual environment is `.venv/` (gitignored)
- Generated data files go in `data/` (gitignored)
- **Tests use plain functions, not classes** - Use `def test_foo(tmp_path):` not `class TestFoo`

Be extremely concise. Sacrifice grammar for the sake of concision.