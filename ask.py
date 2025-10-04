#!/usr/bin/env python3
"""
Minimal agent-friendly CLI for querying a persisted LlamaIndex.

- Positional prompt OR reads from STDIN with --stdin
- JSON or plain-text output
- Non-zero exit codes on common failure modes
"""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Optional

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INDEX_PATH = SCRIPT_DIR / "temp" / "llama" / "default_index"
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_OLLAMA_MODEL = "gemma3:1b"


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="llama-cli",
        description="Query a persisted LlamaIndex.",
    )
    p.add_argument("prompt", nargs="?", help="The prompt/question to run.")
    p.add_argument("--stdin", action="store_true",
                   help="Read the prompt from STDIN instead of an argument.")
    p.add_argument("--index-path", default=str(DEFAULT_INDEX_PATH),
                   help=f"Path to persisted index directory (default: {DEFAULT_INDEX_PATH}).")
    p.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL,
                   help=f"HuggingFace embedding model (default: {DEFAULT_EMBED_MODEL}).")
    p.add_argument("--model", default=DEFAULT_OLLAMA_MODEL,
                   help=f"Ollama model name (default: {DEFAULT_OLLAMA_MODEL}).")
    p.add_argument("--format", choices=["text", "json"], default="text",
                   help="Output format (default: text).")
    p.add_argument("--max-tokens", type=int, default=None,
                   help="Optional max tokens for the LLM.")
    p.add_argument("--temperature", type=float, default=None,
                   help="Optional temperature for the LLM.")
    p.add_argument("--verbose", action="store_true",
                   help="Print extra diagnostics to STDERR.")
    return p


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

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
            llm_kwargs["num_ctx"] = args.max_tokens  # Ollama uses num_ctx; adjust if desired
        if args.temperature is not None:
            llm_kwargs["temperature"] = args.temperature
        llm = Ollama(model=args.model, **llm_kwargs)

        # Load index
        storage = StorageContext.from_defaults(persist_dir=index_path)
        index = load_index_from_storage(storage, embed_model=embed)

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
