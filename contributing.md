# Contributing to CrashVault

Welcome! We're excited you're interested in contributing to CrashVault. This guide will help you get started.

## Code of Conduct

Please note that this project is governed by the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating, you agree to abide by its terms.

## First-Time Contributors

New to open source? Here's how to make your first contribution:

1. **Fork the repository** - Click the "Fork" button on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/crashvault.git
   cd crashvault
   ```
3. **Create a branch:**
   ```bash
   git checkout -b my-first-contribution
   ```
4. **Install in development mode:**
   ```bash
   pip install -e .
   ```
5. **Make your changes** and test with `crashvault --help`
6. **Run tests:**
   ```bash
   pytest
   ```
7. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add a descriptive commit message"
   git push origin my-first-contribution
   ```
8. **Open a Pull Request** - Go to the original repo and click "New Pull Request"

## Good First Issues

Looking for a place to start? These issues are labeled `good first issue` and are perfect for beginners:

- [ ] Documentation improvements
- [ ] Test coverage expansion
- [ ] Adding new webhook providers
- [ ] CLI command enhancements
- [ ] Bug fixes with clear reproduction steps

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Use the bug template** when creating new issues
3. **Include**:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - CrashVault version (`crashvault --version`)
   - Python version

### Suggesting Features

1. **Search issues** first to see if it's already been discussed
2. **Open a discussion** before implementing large changes
3. **Describe the problem** your feature solves
4. **Provide examples** of how it would work

### Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features
3. Ensure all tests pass (`pytest`)
4. Update the CHANGELOG.md if it exists
5. Request review from maintainers

### Coding Standards

We follow these conventions (also see our detailed [Style Guide](./contributing.md)):

- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Imports:** stdlib first, then third-party, then local
- **Formatting:** f-strings preferred
- **Type hints:** Required in webhooks/ and server.py

## Development Setup

```bash
# Clone and install
git clone https://github.com/Ak-dude/crashvault.git
cd crashvault
pip install -e ".[dev]"

# Install dev dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest

# Format code
black .

# Lint
flake8 .
```

## Project Structure

```
crashvault/
├── crashvault/          # Main package
│   ├── commands/        # CLI commands
│   ├── webhooks/        # Webhook providers
│   ├── core.py          # Core functionality
│   ├── cli.py           # CLI entry point
│   └── server.py        # HTTP server
├── tests/               # Test suite
├── contributing.md      # This file
└── README.md            # Project documentation
```

## Community

- **GitHub Discussions:** Ask questions and share ideas
- **Issues:** Report bugs and request features
- **Discord:** Join our community (link in README)

## Recognition

Contributors are recognized in the [README.md](./README.md#contributors). Thank you for your contributions!

---

*Last updated: February 2026*
