# baldrick_familiar
A clever little Docker familiar built with Python who always knows the shortest path to the best docs and the most useful code hints

![baldrick_familiar](./baldrick_familiar_hero.jpeg)

## Development

- Prereqs: Python 3.12+, uv, Ollama (for local models).
- Quickstart:
  - `uv sync`
  - `sh create-content.sh` (snapshot docs, collect files, build index)
  - `uv run familiar "List available docs" --format json`

### Broth Workflows (optional)

This repo includes `baldrick-broth.yaml` with Python‑centric tasks. Examples:

- `npx baldrick-broth@latest test all` — lint + sanity CLI check
- `npx baldrick-broth@latest rag content` — end‑to‑end content + index build
- `npx baldrick-broth@latest lint fix` — ruff fix + format

See `baldrick-broth.yaml` for all domains and tasks.
