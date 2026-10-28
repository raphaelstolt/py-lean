# Contributing

Thank you for your interest in contributing to `py-lean`.

## Code quality

### Installing dependencies

```bash
git clone https://github.com/raphaelstolt/py-lean.git && cd py-lean
uv sync
```

### Formatting

Format all source code:

```bash
uv run ruff format .
```

### Linting

Check for common mistakes and improve Python idioms and the leanness of `py-lint`:

```bash
uv run ruff check .
uv run --project . py-lean lint
```

### Testing

Run the full test suite:

```bash
uv run pytest
```

## Pull requests

Please open pull requests against the `main` branch from a dedicated feature branch. Use descriptive branch names that
reflect the change, such as:

- `feat/history-command`
- `fix/update`
- `docs/update-readme`

## Commit messages

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. This keeps the history readable
and enables automated changelog generation. You can inspect the message schema for this project via `git log --oneline -n 10`.
