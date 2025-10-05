# Maintenance

https://docs.astral.sh/uv/getting-started/installation/

curl -LsSf https://astral.sh/uv/install.sh | sh

Install everything locally
```bash
uv sync 
```

Create and index the content
```bash
sh create-content.sh
```

Run the indexer
```bash
uv run python script/indexer.py
```

Install CLI on this machine
```bash
uv tool install --force . 
```
