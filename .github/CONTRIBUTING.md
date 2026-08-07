# Contributing to ARKON

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Run tests
6. Submit a pull request

## Development Setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"

# Frontend
cd apps/desktop
npm install
```

## Code Standards

- **Python**: type hints, docstrings, Ruff formatting
- **TypeScript**: strict mode, ESLint
- **Rust**: cargo fmt, cargo clippy
- **Tests**: required for all new features

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Request review from maintainers

## Reporting Issues

Use GitHub Issues with the provided templates.
