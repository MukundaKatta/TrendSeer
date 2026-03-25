# Contributing to TrendSeer

Thank you for your interest in contributing to TrendSeer!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/TrendSeer.git
   cd TrendSeer
   ```
3. Install development dependencies:
   ```bash
   make dev
   ```

## Development Workflow

### Running Tests
```bash
make test
```

### Linting and Formatting
```bash
make lint      # Check for issues
make fmt       # Auto-fix formatting
make typecheck # Run mypy
```

### Before Submitting a PR
```bash
make all  # Runs lint, typecheck, and tests
```

## Code Style

- Follow PEP 8 conventions (enforced by ruff)
- Use type annotations for all public functions
- Write docstrings for all public classes and functions
- Keep functions focused and under 50 lines where possible

## Adding a New Data Source

1. Create a collector function that returns `list[Signal]`
2. Each signal must include: `text`, `source`, `timestamp`
3. Register it in `TrendDetector.add_source()` or call `detector.ingest(signals)` directly
4. Add tests in `tests/`

## Pull Request Guidelines

- Keep PRs focused on a single change
- Include tests for new functionality
- Update documentation if needed
- Ensure all CI checks pass

## Reporting Issues

Open a GitHub issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
