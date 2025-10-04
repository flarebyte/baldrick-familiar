#!/usr/bin/env python3
"""
Minimal agent-friendly CLI for querying a persisted LlamaIndex.

- Positional prompt OR reads from STDIN with --stdin
- JSON or plain-text output
- Non-zero exit codes on common failure modes
"""

from __future__ import annotations
from contextlib import redirect_stderr, redirect_stdout
import os
import argparse, json, sys
from pathlib import Path
from typing import Optional
import logging
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama


APP_DIR = Path.home() / ".baldrick_familiar"
CACHE_DIR = APP_DIR / "cache" / "llama"
DEFAULT_INDEX_PATH = CACHE_DIR / "default_index"

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_OLLAMA_MODEL = "gemma3:1b"


def resolve_index_path(cli_arg: str | None = None) -> Path:
    """Return the index path, using CLI arg if provided, else default."""
    if cli_arg:
        return Path(cli_arg).expanduser()
    return DEFAULT_INDEX_PATH


def configure_logging(
    verbose: bool = False, debug: bool = False, level: str | None = None
):
    """
    Configure logging for CLI.
    - Default: WARNING (quiet)
    - --verbose: INFO
    - --debug: DEBUG
    - --log-level LEVEL: override manually
    """
    if level:
        lvl = getattr(logging, level.upper(), logging.WARNING)
    elif debug:
        lvl = logging.DEBUG
    elif verbose:
        lvl = logging.INFO
    else:
        lvl = logging.WARNING  # default minimum

    # Configure root logger
    logging.basicConfig(
        level=lvl,
        format="%(message)s",  # concise format for CLI output
    )

    # Quiet down noisy libs
    for name in (
        "llama_index",
        "llama_index.core",
        "llama_index.core.storage",
        "llama_index.core.storage.kvstore",
        "gpt_index",  # legacy
        "httpx",
        "urllib3",
        "openai",
    ):
        logging.getLogger(name).setLevel(lvl)
        logging.getLogger(name).propagate = False
        
def load_index_quiet(persist_dir, embed_model, verbose=False, debug=False):
    from llama_index.core import StorageContext, load_index_from_storage
    # only silence when not verbose/debug
    if verbose or debug:
        storage = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage, embed_model=embed_model)

    with open(os.devnull, "w") as devnull, redirect_stdout(devnull), redirect_stderr(devnull):
        storage = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage, embed_model=embed_model)
    

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="familiar",
        description="A clever little Docker familiar built with Python who always knows the shortest path to the best docs and the most useful code hints",
    )
    p.add_argument("prompt", nargs="?", help="The prompt/question to run.")
    p.add_argument(
        "--stdin",
        action="store_true",
        help="Read the prompt from STDIN instead of an argument.",
    )
    p.add_argument(
        "--index-path",
        default=str(DEFAULT_INDEX_PATH),
        help=f"Path to persisted index directory (default: {DEFAULT_INDEX_PATH}).",
    )
    p.add_argument(
        "--embed-model",
        default=DEFAULT_EMBED_MODEL,
        help=f"HuggingFace embedding model (default: {DEFAULT_EMBED_MODEL}).",
    )
    p.add_argument(
        "--model",
        default=DEFAULT_OLLAMA_MODEL,
        help=f"Ollama model name (default: {DEFAULT_OLLAMA_MODEL}).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--max-tokens", type=int, default=None, help="Optional max tokens for the LLM."
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Optional temperature for the LLM.",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="Show info-level logs.")
    p.add_argument(
        "--debug", action="store_true", help="Show debug logs for troubleshooting."
    )
    p.add_argument(
        "--log-level",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="Set an explicit log level (overrides --verbose/--debug).",
    )

    return p


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, level=args.log_level)
    
    index_path = resolve_index_path(args.index_path)

    # Ensure the directory exists
    index_path.mkdir(parents=True, exist_ok=True)

    if not index_path.exists():
        err(f"Index directory not found: {index_path}")
        return 3

    # Resolve prompt
    prompt: Optional[str] = args.prompt
    if args.stdin:
        prompt = sys.stdin.read().strip()
    if not prompt:
        err("No prompt supplied. Provide a positional prompt or use --stdin.")
        return 2  # usage error

    index_path = Path(args.index_path)
    if not index_path.exists():
        err(f"Index directory not found: {index_path}")
        return 3  # missing resource

    try:
        # Build components
        embed = HuggingFaceEmbedding(model_name=args.embed_model)
        llm_kwargs = {}
        if args.max_tokens is not None:
            llm_kwargs["num_ctx"] = (
                args.max_tokens
            )  # Ollama uses num_ctx; adjust if desired
        if args.temperature is not None:
            llm_kwargs["temperature"] = args.temperature
        llm = Ollama(model=args.model, **llm_kwargs)

        # Load index
        index = load_index_quiet(index_path, embed, verbose=args.verbose, debug=args.debug)

        # Query
        qe = index.as_query_engine(llm=llm)
        response = qe.query(prompt)

        if args.format == "json":
            payload = {
                "prompt": prompt,
                "response": str(response),
                "metadata": {
                    "index_path": str(index_path.resolve()),
                    "embed_model": args.embed_model,
                    "llm_model": args.model,
                },
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(str(response))

        return 0
    except KeyboardInterrupt:
        err("Interrupted.")
        return 130
    except Exception as e:
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            err(f"Error: {e}")
        return 1  # generic failure


if __name__ == "__main__":
    sys.exit(main())
