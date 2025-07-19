# Plumbing-core

A lightweight Python package of reusable source-connectors, auth helpers and types for building extract-and-load pipelines.  
With this repository, I aim to decouple the core logic from orchestrators and other such tools. I want to experiment with different ways of running my code and orchestrating my pipelines through the pluggable nature of python packages.

## Features

- Modular source-connectors under `plumbing_core.sources.<vendor>` with typed data models
- SQLite destination under `plumbing_core.destinations.sqlite` with DuckDB integration for analytics
- Project Nessie / Iceberg destination under `plumbing_core.destinations.nessie`: Coming soon
- Utility helpers
- Logging: Each module exposes `logger = logging.getLogger(__name__)` and ships with a built-in `NullHandler`

## Getting Started

0. Prerequisite

`uv` and `python 3.12` installed on your system

1. Install

Clone the repository and install the `plumbing_core` package locally, in editable mode:

```bash
git clone https://github.com/jonathanschwarzhaupt/home-plumbing.git
cd src/plumbing_core

uv pip install .
```

2. Import

```python
from plumbing_core.sources.comdirect import (
  APIConfig, 
  authenticate_user_credentials,
  get_accounts_balances
)
from plumbing_core.destinations.sqlite import (
  SQLiteConfig,
  write_account_balances
)
```

3. Extract and Load data

```python
# Extract account balances
balances = get_accounts_balances(cfg=config, bearer_access_token=token)

# Load to SQLite
db_config = SQLiteConfig(db_path=Path("comdirect.db"))
write_account_balances(balances=balances, config=db_config)
```

4. Configuration

Environment variables:

- `COMDIRECT_CLIENT_ID`
- `COMDIRECT_CLIENT_SECRET`
- `COMDIRECT_USERNAME`
- `COMDIRECT_PASSWORD`

Use these to instantiate the `APIConfig`, or pass them explicitly.

For SQLite destinations:

- `SQLITE_DB_PATH` - Path to SQLite database file

## Code Structure

```
.
├── README.md
├── pyproject.toml
├── uv.lock
├── src
│   └── plumbing_core
│       ├── __init__.py
│       ├── sources
│       │   ├── __init__.py
│       │   └── comdirect
│       │       ├── __init__.py
│       │       ├── auth.py         <-- Comdirect auth flow logic
│       │       ├── data.py         <-- Data extraction methods
│       │       ├── helpers.py      <-- Supporting methods
│       │       └── types.py        <-- Typed dataclasses and settings
│       └── destinations
│           ├── __init__.py
│           └── sqlite
│               ├── __init__.py
│               ├── config.py       <-- SQLite configuration
│               ├── connection.py   <-- DuckDB connection manager
│               ├── writers.py      <-- Data writers with upsert logic
│               └── readers.py      <-- Data readers
├── examples                        <-- example scripts to try
│   ├── comdirect_auth.py
│   └── comdirect_account_balances.py
```

## Examples

- See `examples/comdirect_auth.py` for a complete authentication flow script
- See `examples/comdirect_account_balances.py` for end-to-end extract and load to SQLite

## Architecture Notes

### SQLite + DuckDB Integration

The SQLite destination uses an interesting architectural pattern: **SQLite for storage, DuckDB for analytics**.

- **SQLite**: Single-file databases with no infrastructure overhead. Each source gets its own `.db` file with a single writer, eliminating concurrency issues
- **DuckDB**: Acts as a bridge during analytics, allowing complex queries across multiple SQLite files and seamless integration with pandas/arrow ecosystems

This pattern scales well for modestly-sized data platforms where you want the simplicity of file-based storage but the analytical power of modern columnar query engines. DuckDB can attach multiple SQLite databases and perform federated queries, making it perfect for this use case.
