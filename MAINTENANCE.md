# Maintenance

## Prerequisites
- Python 3.12+
- uv (https://docs.astral.sh/uv/getting-started/installation/)
- Ollama running locally (for `gemma3:1b` or your preferred model)

Install uv (macOS/Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup & Environment
```bash
uv sync  # install/resolve project dependencies
```

## Content Pipeline (RAG)
- End‑to‑end (snapshot repos, collect docs, capture CLI help, build index):
```bash
sh create-content.sh
```
- Build index only:
```bash
uv run python script/indexer.py
```

Default index path: `~/.baldrick_familiar/cache/llama/default_index`

## CLI Usage
```bash
uv run familiar --help
familiar "List available docs" --format json
familiar --index-path ~/.baldrick_familiar/cache/llama/default_index "What sources are indexed?"
```

## Linting & Formatting
- Ruff check/fix (via uvx):
```bash
uvx ruff check .
uvx ruff check . --fix
uvx ruff format
```
- Markdown format/check:
```bash
uvx mdformat .
uvx mdformat --check .
```

## Build / Install
- Build distributions (hatchling backend):
```bash
uv build
```
- Install CLI locally (toolshim):
```bash
uv tool install --force .
```

## Broth Workflows (optional)
Tasks are defined in `baldrick-broth.yaml` for a consistent DX:
```bash
npx baldrick-broth@latest test all     # lint + sanity
npx baldrick-broth@latest rag content  # content + index
npx baldrick-broth@latest lint fix     # ruff fix + format
```

## Troubleshooting
- Ollama model not found: ensure Ollama is running and the model is pulled, or pass `--model`.
- Missing index: run `sh create-content.sh` or `uv run python script/indexer.py`.
