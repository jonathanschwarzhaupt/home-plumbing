# Plumbing-core

A lightweight Python package of reusable source-connectors, auth helpers and types for building extract-and-load pipelines.  
With this repository, I aim to decouple the core logic from orchestrators and other such tools. I want to experiment with different ways of running my code and orchestrating my pipelines through the pluggable nature of python packages.

## Features

- Modular source-connectors under `plumbing_core.sources.<vendor>` with typed data models
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
  authenticate_user_credentials
)
```

3. Fetch data

> Coming soon!

4. Configuration

Environment variables:

- `COMDIRECT_CLIENT_ID`
- `COMDIRECT_CLIENT_SECRET`
- `COMDIRECT_USERNAME`
- `COMDIRECT_PASSWORD`

Use these to instantiate the `APIConfig`, or pass them explicitly.

## Code Structure

```
.
├── README.md
├── pyproject.toml
├── uv.lock
├── src
│   └── plumbing_core
│       ├── __init__.py
│       └── sources
│           ├── __init__.py
│           └── comdirect
│               ├── __init__.py
│               ├── auth.py         <-- Comdirect auth flow logic
│               ├── helpers.py      <-- Supporting methods
│               └── types.py        <-- Typed dataclasses and settings
├── examples                        <-- example scripts to try
│   └── comdirect_auth.py
```

## Examples

- See `examples/comdirect_auth.py` for a complete authentication flow script.

## Contributing

> This is my personal plumbing toolbox - feel free to open issues o rPRs if you spot something, but no promises!
