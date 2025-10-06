# Code Analysis

## Purpose & Goals
- Provide an offline‑first, agent‑friendly CLI to query a locally persisted LlamaIndex using small local LLMs (Ollama) on constrained macOS machines.
- Automate content collection from selected GitHub repos and local tools, index the corpus, and answer questions against it.

## Feature Overview
- CLI `familiar`: prompts via arg or `--stdin`, outputs `text` or `json`, configurable model/embedding, and quiet logging by default.
- Content pipeline: snapshot external repos, collect key docs, capture `--help` output of local CLIs, and build a vector index.
- Indexing: documents under `temp/data/` are embedded and persisted to `~/.baldrick_familiar/cache/llama/default_index`.

## Architecture & Data Flow
1) `script/snapshotter.py` clones configured repos into `temp/github/<name>` and records `commit-<name>.txt`.
2) `script/copy_by_filename.py` gathers specific files (README, ADRs, etc.) into `temp/data/` with sanitized names.
3) `script/copy-mac-cli.py` captures `--help` for selected tools into `temp/data/macos-terminal-cli.md`.
4) `script/indexer.py` reads `temp/data/`, builds a `VectorStoreIndex`, and persists it.
5) `src/baldrick_familiar/cli.py` opens the index and answers queries using `Ollama` + `HuggingFaceEmbedding`.

## Code Anatomy
- `src/baldrick_familiar/cli.py`
  - `resolve_index_path`, `configure_logging`, `load_index_quiet` (silence noisy libs), `build_arg_parser`, `main`.
  - Flags: `--stdin`, `--index-path`, `--embed-model`, `--model`, `--format`, `--max-tokens`, `--temperature`, `--verbose/--debug/--log-level`.
- `script/indexer.py`
  - Loads docs with `SimpleDirectoryReader`, builds `VectorStoreIndex`, persists to `~/.baldrick_familiar/cache/llama/default_index`.
- `script/snapshotter.py`
  - Uses `git`/`gh` to clone target repos, detects remote default branch, saves snapshot commit, removes origin.
- `script/copy_by_filename.py`
  - Walks `temp/github/`, copies matched filenames into `temp/data/` using `<sanitized-path>-<filename>`.
- `script/copy-mac-cli.py`
  - Runs `<cmd> --help` (with timeouts), writes a consolidated markdown under `temp/data/`.
- Root tooling: `create-content.sh` orchestrates the pipeline; `pyproject.toml` defines deps and console script; `uv.lock` pins env.

## Local Usage
- Setup: `uv sync`
- Full pipeline: `sh create-content.sh`
- Query: `uv run familiar "How do I rebuild the index?" --format json`

## Notes & Next Steps
- Tests not included; consider `pytest` for CLI arg parsing and index helpers.
- Ensure Ollama models (default `gemma3:1b`) are available locally; override with `--model`.
