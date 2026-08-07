# Support

## Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/karthik-ak-Git/ARKON/issues)
- **Discussions**: [GitHub Discussions](https://github.com/karthik-ak-Git/ARKON/discussions)

## Common Issues

### Backend won't start

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend build fails

```bash
cd apps/desktop
rm -rf node_modules
npm install
npm run dev
```

### Tauri build fails

Ensure Rust is installed: `rustup update`
